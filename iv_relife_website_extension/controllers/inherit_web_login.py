import json

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import _get_login_redirect_url


class ModelName(Home):
    def _login_redirect(self, uid, redirect=None):
        is_internal = request.env(user=uid)['res.users'].browse(uid)._is_internal()
        if not is_internal:
            return '/shop'
        return super()._login_redirect(uid=uid, redirect=redirect)
