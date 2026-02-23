from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_header = fields.Binary(string='Invoice Header')
    invoice_footer = fields.Binary(string='Invoice Footer')