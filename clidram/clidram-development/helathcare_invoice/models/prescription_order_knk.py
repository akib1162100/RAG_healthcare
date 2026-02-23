from odoo import models, fields, api


class PrescriptionOrder(models.Model):
    _inherit = 'prescription.order.knk'

    patient_sex = fields.Selection(related='patient_id.gender', store=True, string='Patient Sex')
    patient_phone = fields.Char(related='patient_id.mobile', store=True, string='Patient Phone')
    weight = fields.Char(compute='_compute_weight', store=True, string='Weight')
    unit = fields.Char(compute='_compute_unit', store=True, string='Unit')
    height = fields.Char(compute='_compute_height', store=True, string='Height')
    bmi = fields.Char(compute='_compute_bmi', store=True, string='BMI')
    systolic = fields.Char(compute='_compute_systolic_pressure', store=True, string='Systolic Pressure')
    diastolic = fields.Char(compute='_compute_diastolic_pressure', store=True, string='Diastolic Pressure')
    pulse = fields.Char(compute='_compute_pulse', store=True, string='Pulse')
    respiratory_rate = fields.Char(compute='_compute_respiratory_rate', store=True, string='Respiratory Rate')
    medicine_name = fields.Char(compute='_compute_medicine_name', store=True, string='Medicine Name')
    complain_list = fields.Char(compute='_compute_complain_list', store=True, string='Complain List')
    diagnosis = fields.Char(compute='_compute_diagnosis', store=True, string='Diagnosis')
    old_history = fields.Char(compute='_compute_old_history', store=True, string='Old History')

    @api.depends('medical_history_ids')
    def _compute_old_history(self):
        for record in self:
            if record.medical_history_ids:
                # Collecting formatted history data from `medical_history_ids`
                history_lines = [
                    f"{line.date.strftime('%Y-%m-%d')}: {line.name}"
                    for line in record.medical_history_ids if line.date and line.name
                ]
                # Joining all lines into a single string
                record.old_history = "\n".join(history_lines)
            else:
                record.old_history = ""

    @api.depends('vital_ids.name')
    def _compute_weight(self):
        for rec in self:
            weights = rec.mapped('vital_ids.name')
            rec.weight = ', '.join(map(str, weights))

    @api.depends('vital_ids.w_unit')
    def _compute_unit(self):
        for rec in self:
            units = rec.mapped('vital_ids.w_unit.name')
            rec.unit = ', '.join(units)

    @api.depends('vital_ids.height')
    def _compute_height(self):
        for rec in self:
            heights = rec.mapped('vital_ids.height')
            rec.height = ', '.join(map(str, heights))

    @api.depends('vital_ids.bmi')
    def _compute_bmi(self):
        for rec in self:
            bmis = rec.mapped('vital_ids.bmi')
            rec.bmi = ', '.join(map(str, bmis))

    @api.depends('vital_ids.blood_presure')
    def _compute_systolic_pressure(self):
        for rec in self:
            systolic_pressures = rec.mapped('vital_ids.blood_presure')
            # Filter out any False or None values and convert valid entries to strings
            rec.systolic = ', '.join(str(value) for value in systolic_pressures if value not in [False, None])

    @api.depends('vital_ids.blood_presure_2')
    def _compute_diastolic_pressure(self):
        for rec in self:
            diastolic_pressures = rec.mapped('vital_ids.blood_presure_2')
            # Filter out any False or None values and convert valid entries to strings
            rec.diastolic = ', '.join(str(value) for value in diastolic_pressures if value not in [False, None])

    @api.depends('vital_ids.pulse')
    def _compute_pulse(self):
        for rec in self:
            pulses = rec.mapped('vital_ids.pulse')
            # Filter out any False or None values and convert valid entries to strings
            rec.pulse = ', '.join(str(value) for value in pulses if value not in [False, None])

    @api.depends('vital_ids.respiratory_rate')
    def _compute_respiratory_rate(self):
        for rec in self:
            respiratory_rates = rec.mapped('vital_ids.respiratory_rate')
            # Filter out any False or None values and convert valid entries to strings
            rec.respiratory_rate = ', '.join(str(value) for value in respiratory_rates if value not in [False, None])

    @api.depends('order_line_new_ids.product_id')
    def _compute_medicine_name(self):
        for rec in self:
            medicine_names = rec.mapped('order_line_new_ids.product_id.display_name')
            rec.medicine_name = ', '.join(medicine_names)

    @api.depends('complaint_id.name')
    def _compute_complain_list(self):
        for rec in self:
            complain_lists = rec.mapped('complaint_id.name.name')
            rec.complain_list = ', '.join(complain_lists)

    @api.depends('diagnosis_ids.name')
    def _compute_diagnosis(self):
        for rec in self:
            diagnosis = rec.mapped('diagnosis_ids.name.name')
            rec.diagnosis = ', '.join(diagnosis)

