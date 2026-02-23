from odoo import api, models, fields, _


class AppointmentExt(models.Model):
    _inherit = "wk.appointment"

    appoint_state = fields.Selection(selection_add=[('in_consultation', 'In Consultation'), ('done',)])
    wk_prescription_ids = fields.One2many('prescription.order.knk', 'wk_appointment_id')
    prescription_count = fields.Integer(compute='_compute_prescription_count', store=True)

    @api.depends('wk_prescription_ids')
    def _compute_prescription_count(self):
        for rec in self:
            rec.prescription_count = len(rec.wk_prescription_ids) if rec.wk_prescription_ids else 0

    def button_in_consultation(self):
        self.ensure_one()
        self.write({'appoint_state': 'in_consultation'})
        return True

    def button_create_prescription(self):
        self.ensure_one()

        lines = []
        for line in self.appoint_lines:
            lines.append((0, 0, {
                'product_id': line.appoint_product_id.id,
                'quantity': line.product_qty,
            }))

        data = {
            'default_wk_appointment_id': self.id,
            'default_patient_id': self.customer.id,
            'default_order_line_new_ids': lines,
            'default_physician_id': self.appoint_person_id.id,
            'default_state': 'draft',
        }
        return {
            'name': _('Prescription'),
            'type': 'ir.actions.act_window',
            'res_model': 'prescription.order.knk',
            'target': 'current',
            'view_mode': 'form',
            # 'domain': domain,
            'context': data,
        }

    def view_prescription(self):
        return {
            'name': "View Prescription",
            'view_mode': 'tree,form',
            'res_model': 'prescription.order.knk',
            'type': 'ir.actions.act_window',
            'domain': [('wk_appointment_id', '=', self.id)],
        }
