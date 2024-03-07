# -*- coding: utf-8 -*-
{
    'name': "iv_relife_website_extension",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
        Long description of module's purpose
    """,

    'author': "Al-Amin",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'website_sale', 'sale', 'sale_product_configurator'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/custom_website_layout.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # 'iv_relife_website_extension/static/src/js/dealer_form.js'
        ]
    }
}

