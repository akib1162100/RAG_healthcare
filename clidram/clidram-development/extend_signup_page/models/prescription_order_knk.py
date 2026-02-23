from odoo import fields, models, _


class PrescriptionOrderExt(models.Model):
    _inherit = 'prescription.order.knk'

    wk_appointment_id = fields.Many2one('wk.appointment', string='Appointment')

    def button_confirm(self):
        super(PrescriptionOrderExt, self).button_confirm()
        self.wk_appointment_id.appoint_state = 'done'
