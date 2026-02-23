# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, api, _
from odoo.fields import Date
from dateutil.relativedelta import relativedelta
import random
from odoo.exceptions import UserError
from odoo import tools


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_medication_knk = fields.Boolean()
    med_group_id = fields.Many2one('medicine.group', string="Medicine Group")
    composition_id = fields.Many2one('medicine.composition', string="Composition")
    dose_id = fields.Many2one('medicine.dose', string="Dose")
    route_id = fields.Many2one('medicine.route', string="Route")
    whn_to_take_id = fields.Many2one('medicine.food',string="Relation With Food")
    frequency_id = fields.Many2one('med.frequency',string="Frequency")
    knk_t_qty = fields.Char(string="Total Quantity")
    med_group = fields.Char(string='Med Group Old')
    composition = fields.Char(string='Composition Old')
    dose = fields.Char(string='Dose Old')
    route = fields.Char(string="Route Old")
    whn_to_take = fields.Char(string="When to take Old")
    frequency = fields.Char(string='Frequency Old')
    t_qty = fields.Char(string='T Qty old')
    marketer_id = fields.Many2one('res.partner', string="Marketer/Manufacturer")
    medicine_type_id = fields.Many2one('medicine.type', string="Medicine Type")
    introduction = fields.Text(string="Introduction")
    benefits = fields.Text(string="Benefits")
    med_description = fields.Text(string="Description")
    how_to_use = fields.Text(string="How to Use")
    safety_advice = fields.Text(string="Safety Advice")
    if_miss = fields.Text(string="If Missed")
    med_product_type_id = fields.Many2one('product.type', string="Product Type")
    prescription_required = fields.Boolean(string="Prescription Required", default=False)
    fact_box = fields.Text(string="Fact Box")
    primary_use = fields.Text(string="Primary Use")
    storage = fields.Text(string="Storage")
    use_off_label = fields.Text(string="Use Off")
    common_side_effects = fields.Text(string="Common Side Effects")
    country_of_origin_id = fields.Many2one('res.country', string="Country of Origin")
    how_it_works = fields.Text(string="How It Works")
    reference = fields.Text(string="Reference")
    alcohol_interaction_id = fields.Many2one('interaction.interaction', string="Alcohol Interaction")
    pregnancy_interaction_id = fields.Many2one('interaction.interaction', string="Pregnancy Interaction")
    lactation_interaction_id = fields.Many2one('interaction.interaction', string="Lactation Interaction")
    driving_interaction_id = fields.Many2one('interaction.interaction', string="Driving Interaction")
    kidney_interaction_id = fields.Many2one('interaction.interaction', string="Kidney Interaction")
    liver_interaction_id = fields.Many2one('interaction.interaction', string="Liver Interaction")


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_medication_knk = fields.Boolean()

class MedicineDose(models.Model):
    _name="medicine.dose"

    name=fields.Char(string="Dose")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class MedicineGroup(models.Model):
    _name='medicine.group'

    name = fields.Char(string="Medicine Group")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class MedicineComposition(models.Model):
    _name='medicine.composition'

    name=fields.Char(string="Composition")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)



class MedicineRoute(models.Model):
    _name='medicine.route'

    name=fields.Char(string="Route")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class MedicineFood(models.Model):
    _name='medicine.food'

    name=fields.Char(string="Relation With Food")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class MedicineFrequency(models.Model):
    _name='med.frequency'

    name=fields.Char(string="Frequency")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class MedicineType(models.Model):
    _name='medicine.type'

    name = fields.Char(string="Type")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ProductType(models.Model):
    _name = "product.type"

    name = fields.Char(string="Type", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class Interaction(models.Model):
    _name = 'interaction.interaction'

    name = fields.Char(string="Interaction")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ResPartner(models.Model):
    _inherit = "res.partner"
    _order = 'priority desc, display_name ASC, id DESC'

    seq = fields.Char(string="Patient Id", readonly=True,
                      copy=False, default=lambda self: 'New' if self.partner_type == 'patients' else False)
    date_of_birth = fields.Date(string="Date of Birth", required=True, tracking=True)
    partner_type = fields.Selection(
        [('patient', 'Patient'), ('physician', 'Physician')])

    age = fields.Char(string="Age", compute="_compute_age", store=False)
    age_type = fields.Selection([('month','Months'),('year','Years')], default='year')
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string="Gender",
        required=True
    )
    prescription_count = fields.Integer(compute="_compute_prescription_order")
    physician_signature = fields.Binary('Signature', copy=False,)

    company_id = fields.Many2one('res.company', 'Company', index=True)

    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.in').id)
    zip = fields.Char(change_default=True, required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]", required=True)
    patient_medical_history = fields.Text(string="Medical History")
    pat_prescription_count = fields.Integer(string="Prescriptions", compute='_compute_patient_prescription_count', copy=False)
    phy_prescription_count = fields.Integer(string="Prescriptions", compute="_compute_patient_prescription_count_for_physcian", copy=False)
    patient_details = fields.Text(string='Patient Details')
    patient_history_ids = fields.One2many('patient.history', 'knk_patient_id')
    # ,compute="_get_medical_history_of_imported_patient"
    referral_partner_id = fields.Many2one("referral.partner", tracking=True)
    is_referral_editable = fields.Boolean(compute="_compute_is_referral_editable")
    designation = fields.Char()
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite'),
    ], default='0', string="Favorite")
    reg_no = fields.Char(string="Registration Number")
    registered_id = fields.Selection([('pan_number', 'PAN Number'), ('aadhar_number', 'Aadhar Number'),
                                      ('driver_license_number', 'Driver License Number'), ('employee_id', 'Employee ID')],
                                     string='Registered ID', tracking=True)
    id_number = fields.Char(string='ID Number', tracking=True)
    emergency_contact_number = fields.Char(string='Emergency Contact Number', tracking=True)
    emergency_contact_name = fields.Char(string='Emergency Contact Name', tracking=True)
    relation = fields.Char(string='Relation', tracking=True)

    otp_code = fields.Char(string="OTP Code", copy=False)
    otp_input = fields.Char(string="Enter OTP", copy=False)
    is_verified = fields.Boolean(string="Verified", default=False)
    is_default_whatsapp_contact = fields.Boolean(string="Default WhatsApp Contact", default=False)

    @api.constrains('is_default_whatsapp_contact')
    def _check_unique_default_whatsapp_contact(self):
        if self.is_default_whatsapp_contact:
            existing_default_contact = self.search([('is_default_whatsapp_contact', '=', True),
                                                    ('company_id', '=', self.company_id.id), ('id', '!=', self.id)])
            if existing_default_contact:
                raise UserError("Only one default WhatsApp contact can be set.")

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        for rec in self:
            if rec.partner_type == 'patient':
                rec.company_id = self.env.company.id
            else:
                rec.company_id = False

    # def action_send_otp(self):
    #     self.ensure_one()
    #     if not self.mobile:
    #         raise UserError(_("Partner must have a mobile/WhatsApp number."))
    #
    #     otp = str(random.randint(100000, 999999))
    #     self.otp_code = otp
    #     self.is_verified = False
    #
    #     template = self.env.company.whatsapp_otp_template_id
    #     if not template:
    #         raise UserError(_("Please configure WhatsApp Template in Company Settings."))
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'wa.compose.message',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_partner_id': self.id,
    #             'default_model': self._name,
    #             'default_res_id': self.id,
    #             'default_template_id': template.id,
    #             'default_is_otp_message': True,
    #             'default_otp_code': otp
    #         },
    #     }

    def action_send_otp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner must have a mobile/WhatsApp number."))

        otp = str(random.randint(100000, 999999))
        self.otp_code = otp
        self.is_verified = False

        template = self.env.company.whatsapp_otp_template_id
        if not template:
            raise UserError(_("Please configure WhatsApp Template in Company Settings."))

        ctx = {
            'default_partner_id': self.id,
            'default_model': self._name,
            'default_res_id': self.id,
            'default_template_id': template.id,
            'default_is_otp_message': True,
            'default_otp_code': otp,
        }

        wizard = self.env['wa.compose.message'].with_context(ctx).sudo().create({
            'partner_id': self.id,
            'template_id': template.id,
        })

        wizard.body = template._render_field('body_html', [self.id], compute_lang=True)[self.id]

        wizard.send_whatsapp_message()

    # def action_verify_otp(self):
    #     self.ensure_one()
    #     if not self.otp_input:
    #         raise UserError(_("Please enter the OTP received."))
    #
    #     if self.otp_input.strip() == self.otp_code:
    #         self.is_verified = True
    #         self.otp_code = False
    #         self.otp_input = False
    #     else:
    #         raise UserError(_("Incorrect OTP. Please try again."))

    def action_open_otp_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.otp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            }
        }

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.age = False
            if rec.date_of_birth:
                delta = relativedelta(today, rec.date_of_birth)
                rec.age = str(delta.years)
                rec.age_type = 'year'

    def _compute_is_referral_editable(self):
        for rec in self:
            rec.is_referral_editable = True if self.env.user.has_group("sales_team.group_sale_manager") or not rec.referral_partner_id else False

    def write(self,values):

        if len(self.patient_history_ids)==0:
            if values.get('patient_medical_history'):
                values['patient_history_ids'] =[(0,0,{
                    'name':values['patient_medical_history'],
                    'date':Date.today()
                    })]
        return super().write(values)



    @api.model_create_multi
    def create(self, values):

        for value in values:
            year = fields.Date.today().year
            month = fields.Date.today().month
            if value.get('partner_type') == 'patient':
                company_id = value['company_id']
                total_patient = self.env['res.partner'].search_count([('company_id', '=', company_id),('partner_type','=','patient')])
                new_count= total_patient+1
                if value.get('seq', _('New')) == 'New':
                    seq = self.env['ir.sequence'].next_by_code(
                        'patient.id.knk') or ('New')
                    value['seq']=f"{year:04d}{month:02d}{seq}{company_id}{new_count:03d}"
                    if value.get('patient_medical_history'):
                        value['patient_history_ids']=[(0,0,{
                        'name':value['patient_medical_history'],
                        'date':Date.today(),
                        })]

        return super().create(values)


    def _compute_prescription_order(self):
        for record in self:
            test_ids = self.env['prescription.order.knk'].search(
                [('patient_id', '=', self.id)])
            res = 0
            for id in test_ids:
                res += 1
            record.prescription_count = res

    def action_view_patient_prescription_order(self):
        '''
        This function returns an action that displays the prescription orders from partner.
        '''
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pos_prescription_knk.act_open_hms_prescription_order_view')
        action['domain'] = [('patient_id', '=', self.id)]
        return action

    def _compute_patient_prescription_count(self):
        for record in self:
            record.pat_prescription_count = self.env['pres.appointment'].search_count(
                [('patient_id', '=', self.id)])


    def view_appointment(self):
        domain = [('patient_id', '=', self.id),('partner_type','=','patient')]
        return {
            'name': 'Patients',
            'type': 'ir.actions.act_window',
            'res_model': 'pres.appointment',
            'view_mode': 'tree,form',
            'domain': domain,
        }

    def _compute_patient_prescription_count_for_physcian(self):
        for record in self:
            record.phy_prescription_count = self.env['prescription.order.knk'].search_count([('physician_id','=', self.id)])


    def view_appointment_physician(self):
        domain = [('physician_id','=', self.id),('partner_type','=','patient')]
        return {
            'name': 'Patients',
            'type': 'ir.actions.act_window',
            'res_model': 'pres.appointment',
            'view_mode': 'tree,form',
            'domain': domain
        }


class WAComposerInherit(models.TransientModel):
    _inherit = "wa.compose.message"

    is_otp_message = fields.Boolean(default=False, string="Is OTP Message")
    otp_code = fields.Char(string="OTP")

    # @api.model
    # def default_get(self, fields):
    #     res = super(WAComposerInherit, self).default_get(fields)
    #
    #     company = self.env.company
    #     template = company.whatsapp_otp_template_id
    #
    #     if template and self.env.context.get('default_is_otp_message') == True:
    #         record = None
    #         active_model = res.get('model') or self.env.context.get('active_model')
    #         active_id = res.get('res_id') or self.env.context.get('active_id')
    #         if active_model and active_id:
    #             record = self.env[active_model].browse(active_id)
    #
    #         if record:
    #             body = template._render_field('body_html', [record.id], compute_lang=True)[record.id]
    #         else:
    #             body = template.body_html or ''
    #
    #         otp = self.env.context.get('default_otp_code') or str(random.randint(100000, 999999))
    #         body = tools.plaintext2html(tools.html2plaintext(body) + f"\n\nOTP: {otp}")
    #
    #         res['template_id'] = template.id
    #         res['body'] = body
    #
    #     return res

    # @api.onchange('template_id')
    # def onchange_template_id_wrapper(self):
    #     self.ensure_one()
    #     otp = getattr(self, 'otp_code', False)
    #     if 'active_model' in self.env.context:
    #         active_model = str(self.env.context.get('active_model'))
    #         active_id = self.env.context.get('active_id') or self.env.context.get('active_ids')
    #         active_record = self.env[active_model].browse(active_id)
    #         for record in self:
    #             if record.template_id:
    #                 if record.template_id.components_ids.filtered(lambda comp: comp.type == 'body'):
    #                     variables_ids = record.template_id.components_ids.variables_ids
    #                     if variables_ids:
    #                         temp_body = tools.html2plaintext(record.template_id.body_html)
    #                         variables_length = len(record.template_id.components_ids.variables_ids)
    #                         for length, variable in zip(range(variables_length), variables_ids):
    #                             st = '{{%d}}' % (length + 1)
    #                             if variable.field_id.model == active_model or variable.free_text:
    #                                 value = active_record.read()[0][
    #                                     variable.field_id.name] if variable.field_id.name else variable.free_text
    #                                 if isinstance(value, tuple):
    #                                     value = value[1]
    #                                 temp_body = temp_body.replace(st, str(value))
    #                         body_html = tools.plaintext2html(temp_body)
    #                     else:
    #                         body_html = record.template_id._render_field(
    #                             'body_html', [active_record.id], compute_lang=True)[active_record.id]
    #                 else:
    #                     body_html = record.template_id._render_field(
    #                         'body_html', [active_record.id], compute_lang=True)[active_record.id]
    #             else:
    #                 body_html = ''
    #
    #             if otp:
    #                 body_html = f"{body_html}"
    #
    #             record.body = body_html
    #     else:
    #         active_record = self.env[self.model].browse(self.res_id)
    #         for record in self:
    #             if record.template_id:
    #                 body_html = record.template_id._render_field(
    #                     'body_html', [active_record.id], compute_lang=True)[active_record.id]
    #                 if otp:
    #                     body_html = f"{body_html}"
    #                 record.body = body_html
    #             else:
    #                 record.body = ''

    # def send_whatsapp_message(self):
    #     if not (self.body or self.template_id or self.attachment_ids):
    #         return {}
    #
    #     active_model = str(self.env.context.get('active_model')) if self.env.context.get('active_model',
    #                                                                                      False) else self.model
    #     active_id = self.env.context.get('active_id') if self.env.context.get('active_id', False) else self.res_id
    #     record = self.env[active_model].browse(active_id)
    #     if active_model in ['sale.order', 'purchase.order']:
    #         record.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
    #
    #     # Multi Companies and Multi Providers Code Here
    #     channel = self.provider_id.get_channel_whatsapp(self.partner_id, self.env.user)
    #
    #     if channel:
    #         message_values = {
    #             'body': tools.html2plaintext(self.body) if self.body else '',
    #             'author_id': self.provider_id.user_id.partner_id.id,
    #             'email_from': self.provider_id.user_id.partner_id.email or '',
    #             'model': active_model,
    #             'message_type': 'wa_msgs',
    #             'isWaMsgs': True,
    #             'subtype_id': self.env['ir.model.data'].sudo()._xmlid_to_res_id('mail.mt_comment'),
    #             'partner_ids': [(4, self.provider_id.user_id.partner_id.id)],
    #             'res_id': active_id,
    #             'reply_to': self.provider_id.user_id.partner_id.email,
    #             'attachment_ids': [(4, attac_id.id) for attac_id in self.attachment_ids],
    #         }
    #         context_vals = {'provider_id': self.provider_id, 'partner_id': self.partner_id.id if self.partner_id else False}
    #         if self.template_id:
    #             context_vals.update(
    #                 {'template_send': True, 'wa_template': self.template_id, 'active_model_id': active_id,
    #                  'active_model': active_model, 'partner_id': self._context.get('partner_id') or self.partner_id.id,
    #                  'attachment_ids': self.attachment_ids})
    #
    #         if not self.otp_code:
    #             mail_message = self.env['mail.message'].sudo().with_context(context_vals).create(
    #                 message_values)
    #             channel._notify_thread(mail_message, message_values)
    #             mail_message.chatter_wa_model = active_model
    #             mail_message.chatter_wa_res_id = record.id


class MedicalHistory(models.Model):
    _name = 'patient.history'

    name = fields.Text(string="Medical History")
    date = fields.Date(string='Date', default=fields.Date.context_today)
    knk_patient_id = fields.Many2one('res.partner')


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_prescription_enable = fields.Boolean()
    prescription_order = fields.Boolean()
    pres_id = fields.Char()

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['is_prescription_enable'] = ui_order.get(
            'is_prescription_enable', False)
        order_fields['prescription_order'] = ui_order.get(
            'prescription_order', False)
        order_fields['pres_id'] = ui_order.get(
            'pres_id', '')
        return order_fields

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result['is_prescription_enable'] = True
        result['prescription_order'] = True
        result['pres_id'] = ''
        return result

    def create_precription_order(self, values):
        lines = []
        for v in values.get('lines'):
            lines.append((0, 0, {
                'product_id': v[2].get('product_id', False),
                'quantity': v[2].get('qty', False),
            }))
        self.env['prescription.order.knk'].create({
            'order_line_new_ids': lines,
            'patient_id': values.get('partner_id', False),
            'state': 'prescribed'
        })

    @api.model_create_multi
    def create(self, values):
        res = super(PosOrder, self).create(values)
        for val in values:
            session = self.env['pos.session'].browse(val['session_id'])
            if session.config_id.pos_prescription_knk == 'always' and not val['prescription_order']:
                val['is_prescription_enable'] = True
                self.create_precription_order(val)
            else:
                if val.get('is_prescription_enable'):
                    self.create_precription_order(val)
        return res


class ResPartnerOtpWizard(models.TransientModel):
    _name = "res.partner.otp.wizard"
    _description = "Verify OTP for Patient"

    partner_id = fields.Many2one("res.partner", required=True, readonly=True, string="Patient")
    otp_input = fields.Char(string="Enter OTP", required=True)

    def action_verify_otp(self):
        self.ensure_one()
        partner = self.partner_id

        if not partner.otp_code:
            raise UserError(_("No OTP has been generated for this partner."))

        if self.otp_input.strip() == partner.otp_code:
            partner.is_verified = True
            partner.otp_code = False
            partner.otp_input = False
        else:
            raise UserError(_("Incorrect OTP. Please try again."))
