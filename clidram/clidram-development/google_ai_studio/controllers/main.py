# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class GeminiController(http.Controller):
    @http.route('/discuss_gemini_integration/enable', type='json', auth='user')
    def enable_gemini(self, **kwargs):
        config = request.env['ir.config_parameter'].sudo()
        config.set_param('discuss_gemini_integration.enable_gemini', True)
        return {'status': 'success'}