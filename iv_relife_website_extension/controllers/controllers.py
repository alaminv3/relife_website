# -*- coding: utf-8 -*-
import datetime
from odoo import http
from dateutil import tz
from markupsafe import Markup
from odoo.http import request, route
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


FORM_FIELD_STATIC_LIST = [
        ['date_of_purchase', 'date', 'Date of Purchase', True],
        ['invoice_number', 'string', 'Invoice Number', True],
        ['customer_first_name', 'string', 'Customer First Name', True],
        ['customer_last_name', 'string', 'Customer Last Name', True],
        ['customer_phone_number', 'string', 'Customer Phone Number', True],
        ['second_customer_phone_number', 'string', 'Second customer phone number', False],
        ['customer_email', 'string', 'Customer Email', True],
        ['delivery_address', 'string', 'Delivery Address', True],
        # ['country', 'selection', 'Country', True],
        ['state', 'selection', 'US State', True],
        ['city', 'string', 'City', True],
        ['zip', 'string', 'Zip', True],
        ['floor', 'string', 'Floor', True],
        ['delivery_method', 'selection', 'Delivery Method', True],
        ['warranty', 'selection', 'Warranty', True],
        ['sales_representative', 'string', 'Sales representative', True],
        ['purchase_price', 'number', 'Purchase Price', True],
        ['message', 'text', 'Message', False],
    ]


class CustomWebsiteSale(WebsiteSale):
    FORM_FIELD_LIST = []

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="user", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        return super(CustomWebsiteSale, self).shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, post=post)

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        # return request.render("website_sale.product", self._prepare_product_values(product, category, search, **kwargs))
        # values = self._prepare_product_values(product, category, search, **kwargs)
        return request.redirect(f"/shop/dealer_order_form?product={product.id}&category={category}")


class DealerWebForm(http.Controller):
    def _get_web_form_field_values(self, product, category=''):
        field_values = {}
        self.FORM_FIELD_LIST = FORM_FIELD_STATIC_LIST[:]
        # country_ids = request.env['res.country'].search([])
        state_ids = request.env['res.country.state'].search([('country_id.code', '=', 'US')])
        shipping_methods = request.env['delivery.carrier'].sudo().search([('is_published', '=', True)])
        utc_time = datetime.datetime.utcnow()
        users_timezone = tz.gettz(request.env.user.tz)
        users_time = utc_time.astimezone(users_timezone)

        attribute_line_ids = product.attribute_line_ids
        # Find the position where the product attribute fields should be added in the FORM_FIELD_LIST
        # Here I choose after 'delivery_method' field
        append_index = 0
        for index, form_field in enumerate(self.FORM_FIELD_LIST):
            if form_field[0] == 'delivery_method':
                append_index = index
                break

        # Now loop through all the attribute lines and Add them in to FORM_FIELD_LIST into append_index position
        for attribute_line in attribute_line_ids:
            new_field = ['attr-' + attribute_line.attribute_id.name, 'selection', attribute_line.attribute_id.name, True]
            self.FORM_FIELD_LIST.insert(append_index+1, new_field)
            append_index += 1
            # getting Field values of this attribute
            attribute_values = [[item.id, item.name] for item in attribute_line.value_ids]
            field_values.update({
                'attr-' + attribute_line.attribute_id.name: attribute_values
            })

        # Get all optional products
        optional_product_ids = product.optional_product_ids.product_variant_ids
        # Make the warranty field optional as there is no additional products
        if not optional_product_ids:
            for item in self.FORM_FIELD_LIST:
                if item[0] == 'warranty':
                    item[3] = False

        field_values.update({
            'date_of_purchase': users_time.date(),
            # 'country': [[item.id, item.name] for item in country_ids],
            'state': [[item.id, item.name, item.country_id.id] for item in state_ids],
            'delivery_method': [[item.id, item.name] for item in shipping_methods],
            'warranty': [[item.id, item.name + '  ' + ', '.join([attr_line.display_name for attr_line in item.product_template_attribute_value_ids])] for item in optional_product_ids],
            'customer_first_name': 'First Name',
            'customer_last_name': 'Last Name',
        })
        return field_values

    @http.route('/shop/dealer_order_form', type='http', auth="user", website=True, sitemap=True)
    def dealer_order_form(self, **kwargs):
        values = {}
        category = kwargs.get('category')
        product = kwargs.get('product')
        ProductTemplate = request.env['product.template']
        ProductCategroy = request.env['product.public.category']
        if product and ProductTemplate.browse(int(product)).exists():
            product = ProductTemplate.browse(int(product))
            values['product'] = product
        if category and ProductCategroy.browse(int(category)).exists():
            category = ProductCategroy.browse(int(category))
            values['category'] = category
        values['field_values'] = self._get_web_form_field_values(product, category)
        values['field_list'] = self.FORM_FIELD_LIST
        return request.render('iv_relife_website_extension.order_dealer_form', values)

    @http.route('/submit_order', type='http', auth="public", website=True, csrf=False)
    def submit_order(self, **post):
        # Process form submission here
        # Access submitted data using post['field_name']
        # Example:
        # product_name = post.get('product_name')
        # quantity = post.get('quantity')
        # Process the form data, create records, etc.

        if any(field[3] and not post.get(field[0], False) for field in self.FORM_FIELD_LIST):
            raise ValidationError('All required fields are not filled Up.')

        country_id = request.env['res.country'].sudo().search([('id', '=', int(post.get('country', 1)))])
        state_id = request.env['res.country.state'].sudo().search([('id', '=', int(post.get('state', 1)))])
        users_partner_id = request.env.user.partner_id
        users_price_list = users_partner_id.pricelist_id
        if not users_partner_id:
            raise ValidationError('Current user doesn\'t have a related partner.')

        partner_vals = {
            'name': post.get('customer_first_name', '') + ' ' + post.get('customer_last_name', ''),
            'parent_id': users_partner_id.id if users_partner_id else False,
            'phone': post.get('customer_phone_number', ''),
            'second_phone': post.get('second_customer_phone_number', ''),
            'email': post.get('customer_email', ''),
            'street': post.get('delivery_address', ''),
            'city': post.get('city', ''),
            'country_id': country_id.id if country_id else False,
            'state_id': state_id.id if state_id else False,
            'zip': post.get('zip', ''),
            'floor': post.get('floor', ''),
        }
        cur_partner = request.env['res.partner'].sudo().search([
            '|',
            ('name', '=', partner_vals['name']),
            '|',
            ('email', '=', partner_vals['email']),
            ('phone', '=', partner_vals['phone']),
        ], limit=1)
        if not cur_partner:
            try:
                cur_partner = request.env['res.partner'].sudo().create(partner_vals)
            except Exception as e:
                raise ValidationError('Cannot create partner with given information.')

        # Seperate actual attribute name that is comming from the form with a pattern
        product_attribute = request.env['product.attribute.value']
        attribute_fields = {key.split('-')[1]: product_attribute.sudo().search([('id', '=', int(value))]).name for key, value in post.items() if key.startswith('attr-')}

        # Fetch the product template and find the right variant that matches with given attribute values
        product_tmpl_id = request.env['product.template'].browse(int(post.get('product_id', 0)))
        product_variants = product_tmpl_id.product_variant_ids
        selected_variant = False
        if not attribute_fields or product_tmpl_id.product_variant_count == 1:
            selected_variant = product_tmpl_id.product_variant_id
        else:
            for variant in product_variants:
                att_vals = {}
                for item in variant.product_template_attribute_value_ids:
                    att_vals[item.attribute_id.name] = item.product_attribute_value_id.name
                if any(key not in att_vals.keys() or att_vals[key] != attribute_fields[key] for key in attribute_fields.keys()):
                    continue
                else:
                    selected_variant = variant
                    break
        if not selected_variant:
            raise ValidationError('Sorry!!! Product cannot be found with given attributes.')

        # Now select the additional products like warranty
        optional_product = request.env['product.product'].sudo().search([('id', '=', int(post.get('warranty', 0)))])
        # if not optional_product:
        #     raise ValidationError('Selected Warranty product cannot be found.')

        # Now fetch delivery method products
        delivery_method = request.env['delivery.carrier'].sudo().search([('id', '=', int(post.get('delivery_method')))])
        if not delivery_method:
            raise ValidationError('Delivery is not correct. Cannot found in the system.')

        order_line_vals = [(0, 0, {
            'name': selected_variant.name,
            'product_id': selected_variant.id,
            'price_unit': 0.0,
            'product_uom_qty': 1,
            'product_uom': selected_variant.uom_id.id,
        })]
        if optional_product:
            order_line_vals.append((0, 0, {
                'name': optional_product.name,
                'product_id': optional_product.id,
                'price_unit': optional_product.lst_price,
                'product_uom_qty': 1
            }))
        sale_order_vals = {
            'company_id': request.env.company.id,
            'partner_id': users_partner_id.id,
            'partner_invoice_id': users_partner_id.id,
            'partner_shipping_id': cur_partner.id if cur_partner else False,
            'date_order': post.get('date_of_purchase', False),
            'order_line': order_line_vals,
            'website_id': request.website.id,
            'invoice_number': post.get('invoice_number', ''),
            'pricelist_id': users_price_list.id if users_price_list else False
        }

        # Preparing chatter Log
        message_body = f"""
<h6 style="color: green;">Other Information:</h5>
<hr/>
<p><strong>Order Date: </strong>{post.get('date_of_purchase', '')}</p>
<p><strong>Invoice Number: </strong>{post.get('invoice_number', '')}</p>
<p><strong>Purchase Price: </strong>{post.get('purchase_price', 0.0)}</p>
<p><strong>Floor: </strong>{post.get('floor', '')}</p>
<p><strong>Sales Representative: </strong>{post.get('sales_representative', '')}</p>
<p><strong>Message: </strong>{post.get('message', '')}</p>
        """

        # Try to create Sale Order
        try:
            sale_order = request.env['sale.order'].sudo().create(sale_order_vals)
            sale_order._check_carrier_quotation(force_carrier_id=delivery_method.id)
            sale_order.message_post(body=Markup(message_body))
            sale_order.action_update_prices()
            request.session['sale_last_order_id'] = sale_order.id
        except Exception as e:
            raise ValidationError('Cannot create sale order with given information.')

        return request.redirect('/shop/dealer/confirmation')

    @http.route(['/shop/dealer/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_dealer_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            return request.render("iv_relife_website_extension.dealer_confirmation")
        else:
            return request.redirect('/shop')
