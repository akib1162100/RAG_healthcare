from odoo import models, fields, api

class WkAppointment(models.Model):
    _inherit = 'wk.appointment'

    is_rag_synced = fields.Boolean(string="Synced to RAG", default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'is_rag_synced' not in vals:
                vals['is_rag_synced'] = False
        records = super(WkAppointment, self).create(vals_list)
        return records

    def write(self, vals):
        # If any field changes (except the sync flag itself), reset the sync flag
        if 'is_rag_synced' not in vals:
            vals['is_rag_synced'] = False
        return super(WkAppointment, self).write(vals)


class PrescriptionOrderKnk(models.Model):
    _inherit = 'prescription.order.knk'

    is_rag_synced = fields.Boolean(string="Synced to RAG", default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'is_rag_synced' not in vals:
                vals['is_rag_synced'] = False
        records = super(PrescriptionOrderKnk, self).create(vals_list)
        return records

    def write(self, vals):
        # If any field changes (except the sync flag itself), reset the sync flag
        if 'is_rag_synced' not in vals:
            vals['is_rag_synced'] = False
        return super(PrescriptionOrderKnk, self).write(vals)
