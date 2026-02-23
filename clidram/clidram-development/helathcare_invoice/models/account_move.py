from odoo import models, fields, api
from odoo.exceptions import UserError

class InvoiceCategory(models.Model):
    _name = 'invoice.category'
    _description = 'Invoice Category'

    name = fields.Char('Name', required=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_category_id = fields.Many2one('invoice.category', string='Invoice Category', tracking=True)
    discount_authorized_person = fields.Char('Discount Authorized Person', tracking=True)
    payment_methods = fields.Char(string='Payment Methods', compute='_compute_payment_methods')

    def _compute_payment_methods(self):
        for move in self:
            if move.name != '/':
                payments = self.env['account.payment'].search([('ref', 'ilike', move.name), ('state', '=', 'posted')])
                payment_methods = ', '.join(payment.payment_method_line_id.name for payment in payments)
                move.payment_methods = payment_methods if payment_methods else ''
            else:
                move.payment_methods = ''

    def button_print_invoice(self):
        report_action = self.env.ref('helathcare_invoice.action_report_custom_invoice')
        if not report_action:
            raise UserError("Report not found")

        return report_action.report_action(self)

    def button_print_invoice_with_header_footer(self):
        report_action = self.env.ref('helathcare_invoice.action_report_custom_invoice_with_header_footer')
        if not report_action:
            raise UserError("Report not found")

        return report_action.report_action(self)