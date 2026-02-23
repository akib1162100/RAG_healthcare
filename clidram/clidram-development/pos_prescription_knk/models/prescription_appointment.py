# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, tools, api, _


class PrescriptionAppointment(models.Model):
    _name = 'pres.appointment'
    _description = 'Patient Appointment'

    name = fields.Char(string="Appointment Number",
                       readonly=True, default=lambda self: 'New', copy=False)
    patient_id = fields.Many2one('res.partner', ondelete="restrict",
                                 string='Patient', domain="[('partner_type','=','patient')]", tracking=True, required=True)
    physician_id = fields.Many2one('res.partner', ondelete="restrict", string='Prescribing Doctor',
                                   domain="[('partner_type','=','physician')]", tracking=True, required=True)
    patient_age = fields.Char(related='patient_id.age',
                              string='Age', store=True)
    patient_phone = fields.Char(related='patient_id.mobile',
                                string='Phone', store=True)
    patient_mail = fields.Char(related='patient_id.email',
                               string='Email', store=True)
    appointment_date = fields.Date(
        sting="Appointment Date", default=fields.Date.today(), copy=False, required=True)
    company_id = fields.Many2one(string="Hospital", comodel_name="res.company",
                                 default=lambda self: self.env.company.id, copy=False)
    appointment_status = fields.Selection(string="Appointment Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), (
        'in_consultation', 'In Examination'), ('done', 'Done'), ('cancel', 'Cancel')], default="draft", copy=False)
    patient_ident_nu = fields.Char(
        related='patient_id.seq', string="Patient Identity Number", readonly=True)
    weight = fields.Integer(string="Weight")
    w_unit = fields.Many2one('uom.uom', string="Unit")
    height = fields.Integer(string="Height")
    bmi = fields.Float(string="BMI", compute="_compute_bmi")
    blood_presure = fields.Char(string="Systolic Pressure")
    blood_presure_2 = fields.Char(string="Diastolic Pressure")
    pulse = fields.Char(string="Pulse")
    respiratory_rate = fields.Char(string="Respiratory Rate")
    medical_history = fields.Text(
        related="patient_id.patient_medical_history", string="Medical History")
    prescription_created = fields.Boolean(default=False, copy=False)
    prescription_id = fields.Many2one(
        string="Prescription id", comodel_name='prescription.order.knk', copy=False)
    partner_type = fields.Selection(
        [('patient', 'Patient'), ('physician', 'Physician')], related="patient_id.partner_type")
    schedule_id = fields.Many2one(
        "appointment.schedule.slot.lines",  required=True)

    @api.onchange('schedule_id', 'appointment_date', 'physician_id')
    def _onchange_schedule_id(self):
        Slot_obj = self.env['appointment.schedule.slot']
        domain = []
        if self.appointment_date:
            domain += [('slot_date', '=', self.appointment_date)]
        if self.physician_id:
            domain += [('physician_id', '=', self.physician_id.id)]
        slots = Slot_obj.search(domain, limit=1).slot_ids.filtered(
            lambda x: not x.is_booked)
        return {"domain": {"schedule_id": [("id", "in", slots.ids)]}}

    @api.model_create_multi
    def create(self, values):
        for value in values:
            if value.get('name', 'New') == 'New':
                value['name'] = self.env['ir.sequence'].next_by_code(
                    'appointment.id.knk') or ('New')
        return super().create(values)

    def action_confirm(self):
        if (not self.patient_id) and (not self.physician_id):
            raise UserError(
                'You have not enter patient or physician in appointment!!')
        self.appointment_status = 'confirm'
        self.schedule_id.is_booked = True

    def start_appointment(self):
        for res in self:
            res.appointment_status = 'in_consultation'

    def _get_qty(self, qty, to_unit, category, round=True, rounding_method='UP', raise_if_failure=True):
        if not self or not qty:
            return qty
        # self.ensure_one()
        if self != to_unit and category.id != to_unit.category_id.id:
            if raise_if_failure:
                raise UserError(_('The unit of measure %s defined on the order line doesn\'t belong to the same category as the unit of measure %s defined on the product. Please correct the unit of measure defined on the order line or on the product, they should belong to the same category.') % (self.name, to_unit.name))
            else:
                return qty
        if to_unit:
            amount = qty
        else:
            amount = qty / to_unit.factor
            if to_unit:
                amount = amount * to_unit.factor
        if to_unit and round:
            amount = tools.float_round(
                amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)
        return amount

    @api.depends('weight', 'w_unit', 'height')
    def _compute_bmi(self):
        for rec in self:
            height_in_cm = self.env['uom.uom'].search([('name', '=', 'm²')])
            weight_in_kg = self.env['uom.uom'].search([('name', '=', 'kg')])
            get_height_in_cm = self._get_qty(
                rec.height, height_in_cm, height_in_cm.category_id)
            get_weight_in_kg = self._get_qty(
                rec.weight, weight_in_kg, weight_in_kg.category_id)
            get_height_in_cm_2 = get_height_in_cm/100
            if get_height_in_cm != 0.0:
                rec.bmi = get_weight_in_kg/(get_height_in_cm_2**2)
            else:
                rec.bmi = 0.0

    def finish_appointment_create_prescription(self):
        for rec in self:
            value_list = []
            if (not rec.physician_id) and (not rec.patient_id):
                raise UserError(
                    'You have not either Physician or Patient in Appointment !')
            if rec.prescription_created == False:
                value_list.append([0, 0, {
                    'name': rec.weight,
                    'w_unit': rec.w_unit.id,
                    'w_unit': rec.w_unit.id,
                    'height': rec.height,
                    'bmi': rec.bmi,
                    'blood_presure': rec.blood_presure,
                    'blood_presure_2': rec.blood_presure_2,
                    'pulse': rec.pulse,
                    'respiratory_rate': rec.respiratory_rate,
                }])
                prescription = self.env['prescription.order.knk'].sudo().create({
                    'physician_id': rec.physician_id.id,
                    'patient_id': rec.patient_id.id,
                    'patient_medical_history': rec.medical_history,
                    'vital_ids': value_list,
                })
                if prescription:
                    rec.prescription_created = True
                    rec.prescription_id = prescription.id
                    rec.appointment_status = 'done'
                return self.view_prescription()

    def view_prescription(self):
        if self.prescription_id.id:
            return {
                'name': "Edit from",
                'target': 'current',
                'view_mode': 'form',
                'res_model': 'prescription.order.knk',
                'type': 'ir.actions.act_window',
                'res_id': self.prescription_id.id,
            }

    def cancel_appointment(self):
        for res in self:
            res.appointment_status = 'cancel'
            res.schedule_id.is_booked = False
