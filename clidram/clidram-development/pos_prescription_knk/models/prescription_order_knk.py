# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import qrcode
import base64
from io import BytesIO
from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.fields import Date
from datetime import time, timedelta


class PrescriptionOrderKnk(models.Model):
    _name = 'prescription.order.knk'
    _description = "Prescription Order Knk"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, id desc'

    READONLY_STATES = {'cancelled': [('readonly', True)], 'prescribed': [
        ('readonly', True)]}

    name = fields.Char(size=256, string='Prescription Number', readonly=True, copy=False, tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite'),
    ], default='0', string="Favorite")
    patient_id = fields.Many2one(
        'res.partner', ondelete="restrict", string='Patient', domain="[('partner_type','=','patient')]",
        states=READONLY_STATES, tracking=True, required=True)
    patient_seq = fields.Char(related="patient_id.seq", string="Patient Id", readonly=True)
    order_line_ids = fields.One2many(
        'prescription.order.line.knk', 'prescription_id', string='Prescription line',
        states=READONLY_STATES, copy=True)
    order_line_new_ids = fields.One2many(
        "prescription.order.line.knk.new", "prescription_id", string="Prescription line",
        states=READONLY_STATES, copy=True)
    company_id = fields.Many2one(
        'res.company', ondelete="cascade", string='Hospital', default=lambda self: self.env.company.id,
        states=READONLY_STATES, required=True)
    date = fields.Datetime(
        string='Prescription Date', required=True, default=fields.Datetime.now, states=READONLY_STATES,
        tracking=True, copy=False)
    physician_id = fields.Many2one(
        'res.partner', ondelete="restrict", string='Prescribing Doctor',
        states=READONLY_STATES, domain="[('partner_type','=','physician'), ('company_id','=',company_id)]", tracking=True, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prescribed', 'Prescribed'),
        ('cancelled', 'Cancelled')], string='State', default='draft', tracking=True)
    patient_age = fields.Char(related='patient_id.age',
                              string='Age', store=True)
    old_prescription = fields.Boolean()

    patient_gender = fields.Selection(related="patient_id.gender")
    product_ids = fields.Many2many(
        "product.product", domain="[('is_medication_knk','=',True)]")

    amount_total = fields.Float(compute="_compute_amount_total")
    description = fields.Text(string="Description", states=READONLY_STATES)
    qr_image = fields.Binary("QR Code", attachment=True,
                             store=True, states=READONLY_STATES)
    complaint_id = fields.One2many(
        'complaint.record.line', 'complain_res_id', copy=True, states=READONLY_STATES)
    physical_examination_ids = fields.One2many(
        'physical.examination.line', 'prescription_id', string="Physical Examination"
    )
    has_any_red_flag = fields.Boolean(
        string="Red Flag",
        compute="_compute_has_any_red_flag",
        store=True
    )
    history_id = fields.One2many(
        'history.list.line', 'history_res_id', copy=True, states=READONLY_STATES)
    sign_ids = fields.One2many(
        'sign.list.line', 'sign_res_id', copy=True, states=READONLY_STATES)
    investigation_ids = fields.One2many(
        'investigation.list.line', 'inves_res_id', copy=True, states=READONLY_STATES)
    excercise_ids = fields.One2many(
        'excercise.ex.line', 'excer_res_id', copy=True, states=READONLY_STATES)
    ortho_ids = fields.One2many(
        'ortho.list.line', 'ortho_list_id', copy=True, states=READONLY_STATES)
    vital_ids = fields.One2many(
        'vital.list.line', 'vital_list_id', copy=True, states=READONLY_STATES)
    gcs_score_line_ids = fields.One2many(
        'gcs.score.line',
        'prescription_order_id',
        string='GCS Score Lines'
    )
    gcs_total_score = fields.Integer(
        string="Total GCS Score",
        compute="_compute_gcs_total_score",
        store=True
    )

    his_list = fields.Many2one('history.list', states=READONLY_STATES)
    sign_list = fields.Many2one('sign.list', states=READONLY_STATES)
    diagnosis_ids = fields.One2many(
        'diagnosis.diagnosis', 'diagnosis_res_id', copy=True, states=READONLY_STATES)
    prescription_template_ids = fields.Many2many(
        'prescription.template', states=READONLY_STATES)
    notes_line_id = fields.Many2one(
        'note.note', copy=True, states=READONLY_STATES)

    investigation_result = fields.Text(
        string="Investigation Result", tracking=True)

    procedure_result = fields.Text(
        string="Procedure Result", tracking=True)

    patient_history = fields.Text(
        string="Patient History", states=READONLY_STATES)
    patient_medical_history = fields.Text(
        related="patient_id.patient_medical_history", string="Medical History", readonly=True)
    active = fields.Boolean('Active', default=True)

    medical_history_ids = fields.One2many(
        'patient.history.line', 'pat_medical_his_id')
    check_patient = fields.Text(
        string="Medical History", states=READONLY_STATES)
    patient_details = fields.Text(states=READONLY_STATES)
    extra_notes = fields.Text()
    disease = fields.Char(compute="_compute_disease", store=True, string="Disease")
    short_code = fields.Char(compute="_compute_short_code", store=True, string="Short Code")
    prescription_template_id = fields.Many2one(
        'prescription.template', string="Prescription Template", domain="[('company_id', '=', company_id)]", states=READONLY_STATES)
    prescription_attachment = fields.Binary(related="prescription_template_id.attachment", string='Attachment')
    past_medical_history_line_ids = fields.One2many('past.medical.history', 'prescription_id',
                                                    string='Past Medical History')
    medication_history_line_ids = fields.One2many('medication.history', 'prescription_id',
                                                  string='Medication History')
    family_history_line_ids = fields.One2many('family.history', 'prescription_id',
                                              string='Family History')
    social_history_line_ids = fields.One2many('social.history', 'prescription_id',
                                              string='Social History')
    symptom_status = fields.Selection([
        ('resolved', 'Resolved'),
        ('improved', 'Improved'),
        ('stable', 'Stable'),
        ('not_improved', 'Not Improved'),
        ('worsened', 'Worsened'),
    ], string="Symptom Status", default='stable')

    medication_adherence = fields.Selection([('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')],
                                            string='Medication Adherence')

    performance_status_update = fields.Selection([
        ('good', 'Good (Normal activity)'),
        ('limited', 'Limited (Some activity restriction)'),
        ('poor', 'Poor (Difficulty with daily activities)'),
    ], string="Performance Status Update", default='good')

    additional_comments = fields.Text(string='Additional Comments')
    side_effects = fields.Selection([
        ('none', 'None'),
        ('mild', 'Mild'),
        ('significant', 'Significant'),
    ], string='Side Effects / Toxicities', default='none')
    counseling_behavioral_response = fields.Selection([
        ('well_understood', 'Well Understood'),
        ('partially_understood', 'Partially Understood'),
        ('not_understood', 'Not Understood'),
    ], string='Counseling & Behavioral Response', default='well_understood')

    next_visit_days = fields.Integer(string='Days of Next Visit')
    date_of_next_visit = fields.Date(string='Date of Next Visit',compute="_compute_date_of_next_visit", store=True)
    procedure_line_ids = fields.One2many('procedure.history', 'prescription_id', string="Procedure")

    #Vital Fields

    v_weight = fields.Integer(string="Weight", default=0)
    weight_uom_id = fields.Many2one('uom.uom', string="Unit")

    v_height = fields.Integer(string="height", default=0)
    h_unit = fields.Many2one('uom.uom', string="Unit")

    # bmi = fields.Float(string="BMI", default=0.00, store=True)
    v_bmi = fields.Float(compute='_compute_v_bmi_from_line', string="BMI", default=0.0, store=True)
    bmi_unit = fields.Char(string="Unit")

    blood_presure = fields.Float(string="Systolic Pressure")
    slash_tag = fields.Char(default="/")
    blood_presure_2 = fields.Float(string="Diastolic Pressure")
    blood_unit = fields.Many2one('uom.uom', string="Unit")

    v_pulse = fields.Float(string="Pulse")
    pulse_unit = fields.Many2one('uom.uom', string="Unit")

    v_respiratory_rate = fields.Float(string="Respiratory Rate")
    rr_unit = fields.Many2one('uom.uom', string="Unit")

    temperature = fields.Float(string="Temperature (°F/°C)")
    spo2 = fields.Integer(string="SpO₂ (%)", default=0)
    rbs = fields.Integer(string="Random Blood Sugar (RBS)", default=0)
    motor_power = fields.Integer(string="Motor Power", default=0)

    pupil_reaction = fields.Selection(
        [
            ('r', 'Unequal / Fixed'),
            ('a', 'Sluggish'),
            ('g', 'PERRLA'),
        ],
        string="Pupil Reaction (Left)"
    )

    pupil_reaction_right = fields.Selection(
        [
            ('r', 'Unequal / Fixed'),
            ('a', 'Sluggish'),
            ('g', 'PERRLA'),
        ],
        string="Pupil Reaction (Right)"
    )

    nihss = fields.Integer(string="Neuro (NIHSS)", default=0)

    bmi_line_ids = fields.One2many(
        'vital.bmi.line',
        'prescription_id',
        string="BMI Records"
    )

    pain_score = fields.Integer(string="Pain Score")

    dyspnea = fields.Selection(
        [
            ('i', 'i'),
            ('ii', 'ii'),
            ('iii', 'iii'),
            ('iv', 'iv'),
        ],
        string="Dyspnea (NYHA)"
    )

    cardiac_rythm_type = fields.Selection(
        [
            ('regular', 'Regular'),
            ('irregular', 'Irregular'),
        ], string="Cardiac Rythm Type")

    cardiac_rythm = fields.Selection(
        [
            ('new_a_f', 'New AF'),
            ('vt', 'VT'),
            ('brady', 'Brady'),
            ('irregular', 'Irregular'),
            ('sinus', 'Sinus'),
        ], string="Cardiac Rythm"
    )

    glassgow_coma_scale = fields.Integer(string="Glassgow Coma Scale")


    #Physical Examination
    general = fields.Selection([
        ('pallor', 'Pallor'),
        ('icterus', 'Icterus'),
        ('cyanosis', 'Cyanosis'),
        ('clubbing', 'Clubbing'),
        ('edema', 'Edema'),
        ('lymph_nodes', 'Lymph nodes'),
        ('hydration', 'Hydration'),
    ], string="General")

    heent = fields.Selection([
        ('normal', 'Normal'),
        ('pupils_abnormal', 'Pupils Abnormal'),
        ('throat_lesions', 'Throat Lesions'),
        ('other_abnormal', 'Other Abnormal'),
    ], string="HEENT")

    cvs = fields.Selection([
        ('normal', 'Normal'),
        ('murmur_present', 'Murmur Present'),
        ('pulses_unequal', 'Pulses Unequal'),
        ('edema_present', 'Edema Present'),
    ], string="CVS")

    respiratory = fields.Selection([
        ('clear', 'Clear Bilaterally'),
        ('wheeze', 'Wheeze'),
        ('crackles', 'Crackles'),
        ('reduced_sounds', 'Reduced Sounds'),
    ], string="Respiratory")

    abdomen = fields.Selection([
        ('soft', 'Soft Non-Tender'),
        ('tender_rlq', 'Tender RLQ'),
        ('hepatomegaly', 'Hepatomegaly'),
        ('splenomegaly', 'Splenomegaly'),
    ], string="Abdomen")

    msk = fields.Selection([
        ('normal', 'Normal Gait/Joints'),
        ('limited_rom', 'Limited ROM'),
        ('swelling_present', 'Swelling Present'),
    ], string="MSK")

    cns = fields.Selection([
        ('alert_oriented', 'Alert Oriented'),
        ('cn_deficit', 'CN Deficit'),
        ('weakness', 'Weakness'),
        ('sensory_loss', 'Sensory Loss'),
    ], string="CNS (Screen)")


    # Physical Examination Fields
    general_condition_id = fields.Many2one(
        'physical.general.condition',
        string="General Condition",
        domain="[('company_id', '=', company_id)]"
    )

    pallor_id = fields.Many2one(
        'physical.pallor',
        string="Pallor",
        domain="[('company_id', '=', company_id)]"
    )

    msk_id = fields.Many2one(
        'physical.msk',
        string="MSK (Musculoskeletal)",
        domain="[('company_id', '=', company_id)]"
    )

    edema_id = fields.Many2one(
        'physical.edema',
        string="Edema",
        domain="[('company_id', '=', company_id)]"
    )

    lymph_nodes_id = fields.Many2one(
        'physical.lymph.nodes',
        string="Lymph Nodes",
        domain="[('company_id', '=', company_id)]"
    )

    hydration_id = fields.Many2one(
        'physical.hydration',
        string="Hydration",
        domain="[('company_id', '=', company_id)]"
    )

    cvs_id = fields.Many2one(
        'physical.cvs',
        string="CVS",
        domain="[('company_id', '=', company_id)]"
    )

    rs_id = fields.Many2one(
        'physical.rs',
        string="RS",
        domain="[('company_id', '=', company_id)]"
    )

    abdomen_id = fields.Many2one(
        'physical.abdomen',
        string="Abdomen",
        domain="[('company_id', '=', company_id)]"
    )

    neuro_id = fields.Many2one(
        'physical.neuro',
        string="Neuro (CNS Screen)",
        domain="[('company_id', '=', company_id)]"
    )

    ent_id = fields.Many2one(
        'physical.ent',
        string="ENT",
        domain="[('company_id', '=', company_id)]"
    )

    @api.depends('bmi_line_ids.v_bmi')
    def _compute_v_bmi_from_line(self):
        for rec in self:
            if rec.bmi_line_ids:
                rec.v_bmi = rec.bmi_line_ids[-1].v_bmi
            else:
                rec.v_bmi = 0.0


    def _get_qty(self, qty, to_unit, category, round=True, rounding_method='UP', raise_if_failure=True):
        if not self or not qty:
            return qty

        if self != to_unit and category.id != to_unit.category_id.id:
            if raise_if_failure:
                raise UserError(_(
                    "The unit of measure %s defined on the order line doesn't belong "
                    "to the same category as the unit of measure %s defined on the product."
                ) % (self.name, to_unit.name))
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
                amount,
                precision_rounding=to_unit.rounding,
                rounding_method=rounding_method
            )

        return amount

    @api.depends('v_weight', 'weight_uom_id', 'v_height')
    def _compute_v_bmi(self):
        for rec in self:
            rec.v_bmi = 0.0
            rec.bmi_unit = 'kg/m²'

            try:
                height_in_cm = self.env['uom.uom'].search(
                    [('name', '=', 'm²')], limit=1
                )
                weight_in_kg = self.env['uom.uom'].search(
                    [('name', '=', 'kg')], limit=1
                )

                if not height_in_cm or not weight_in_kg:
                    rec.v_bmi = 0.0

                get_height_in_cm = rec._get_qty(
                    rec.v_height,
                    height_in_cm,
                    height_in_cm.category_id
                )

                get_weight_in_kg = rec._get_qty(
                    rec.v_weight,
                    weight_in_kg,
                    weight_in_kg.category_id
                )

                if not get_height_in_cm:
                    rec.v_bmi = 0.0

                height_m = (get_height_in_cm / 100)
                if height_m:
                    rec.v_bmi = get_weight_in_kg / (height_m ** 2)
                else:
                    rec.v_bmi = 0.0

            except Exception:
                rec.v_bmi = 0.0

    # def send_whatsapp_message(self):
    #     self.ensure_one()
    #
    #     report_xmlid = 'pos_prescription_knk.action_prescription_order_report'
    #     template = self.env.company.whatsapp_template_id
    #     if not template:
    #         raise UserError("Please configure Whatsapp Template in Company Settings")
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'wa.compose.message',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_partner_id': self.patient_id.id,
    #             'default_model': self._name,
    #             'default_res_id': self.id,
    #             'default_template_id': template.id,
    #             'report': report_xmlid,
    #         },
    #     }
    @api.depends('complaint_id.has_red_flag', 'complaint_id.red_flag_selection_ids')
    def _compute_has_any_red_flag(self):
        for rec in self:
            rec.has_any_red_flag = any(
                line.has_red_flag for line in rec.complaint_id
            )

    @api.depends('gcs_score_line_ids.total_score')
    def _compute_gcs_total_score(self):
        for rec in self:
            rec.gcs_total_score = sum(
                rec.gcs_score_line_ids.mapped('total_score')
            )

    # @api.onchange('complaint_id')
    # def _onchange_complaint_id_sync_history(self):
    #     """Create history lines based on complaint lines"""
    #     # Get existing complaint IDs already mapped to history
    #     existing_refs = {}
    #     for hist_line in self.history_id:
    #         if hist_line.source_complaint_line_id:
    #             src = hist_line.source_complaint_line_id
    #             # Store the reference itself, not just ID
    #             existing_refs[src] = True
    #
    #     # Process each complaint line
    #     for comp_line in self.complaint_id:
    #         # Skip if no complaint_list_id or already in history
    #         if not comp_line.complaint_list_id or comp_line in existing_refs:
    #             continue
    #
    #         # Mark as processed
    #         existing_refs[comp_line] = True
    #
    #         # Find or create history.list record
    #         history_record = self._find_or_create_history_list_from_complaint(comp_line.complaint_list_id)
    #
    #         if history_record:
    #             # Append new history line
    #             self.history_id = [(0, 0, {
    #                 'name': history_record.id,
    #                 'history_period': comp_line.period.id if comp_line.period else False,
    #                 'source_complaint_line_id': comp_line.id,
    #                 'history_category_id': history_record.history_category_id.id if history_record.history_category_id else False,
    #             })]

    def _find_or_create_history_list_from_complaint(self, complaint_list_record):
        """Find or create a history.list record from complaint.list"""
        HistoryList = self.env['history.list']

        history_record = HistoryList.search([
            ('name', '=', complaint_list_record.name),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not history_record and complaint_list_record.name:
            # Create a new history.list record
            history_record = HistoryList.create({
                'name': complaint_list_record.name,
                'company_id': self.env.company.id,
            })

        return history_record

    def send_whatsapp_message(self):
        self.ensure_one()

        template = self.env.company.whatsapp_template_id
        if not template:
            raise UserError(_("Please configure Whatsapp Template in Company Settings"))

        report_xmlid = 'pos_prescription_knk.action_prescription_order_report'

        ctx = {
            'default_partner_id': self.patient_id.id,
            'default_model': self._name,
            'default_res_id': self.id,
            'default_template_id': template.id,
            'report': report_xmlid,
            'active_model': self._name,
            'active_id': self.id
        }

        wizard = self.env['wa.compose.message'].with_context(ctx).sudo().create({
            'partner_id': self.patient_id.id,
            'template_id': template.id,
        })

        wizard.body = template._render_field('body_html', [self.id], compute_lang=True)[self.id]


        wizard.send_whatsapp_message()

    def button_print_prescription(self):
        report_action = self.env.ref('pos_prescription_knk.action_prescription_order_report')
        if not report_action:
            raise UserError("Report not found")

        return report_action.report_action(self)

    @api.depends('date', 'next_visit_days')
    def _compute_date_of_next_visit(self):
        for rec in self:
            if rec.next_visit_days != 0 and rec.date:
                rec.date_of_next_visit = rec.date + timedelta(days=rec.next_visit_days)
            else:
                rec.date_of_next_visit = False

    @api.depends('diagnosis_ids.disease_id.name')
    def _compute_disease(self):
        for rec in self:
            disease = rec.mapped('diagnosis_ids.disease_id.name')
            rec.disease = ', '.join(disease)

    @api.depends('diagnosis_ids.disease_short_code_id')
    def _compute_short_code(self):
        for rec in self:
            short_code = rec.mapped('diagnosis_ids.disease_short_code_id')
            # Filter out False values
            valid_short_codes = filter(None, short_code)
            rec.short_code = ', '.join(valid_short_codes)

    def _get_old_history(self, prescriptions):
        lines = []
        for pre in prescriptions:
            history_names = []
            for history in pre.history_id:
                name_part = history.name.name if history.name else ''
                period_part = history.history_period.name if history.history_period else ''
                category_name = history.history_category_id.name if history.history_category_id else ''
                full_text = f"{name_part} - {period_part} - {category_name}" if period_part else name_part
                if full_text:
                    history_names.append(full_text)
            history_text = " | ".join(history_names)

            if pre.patient_history:
                if history_text:
                    history_text += " | " + pre.patient_history
                else:
                    history_text = pre.patient_history

            medication_names = [line.product_id.name for line in pre.order_line_new_ids if line.product_id]
            medication_text = ", ".join(medication_names)

            investigation_names = []
            for inv_line in pre.investigation_ids:
                investigation_names += [tt.name for tt in inv_line.test_type if tt.name]
            investigation_text = ", ".join(investigation_names)

            line = (0, 0, {
                'date': pre.date.date(),
                'name': history_text,
                'medication': medication_text,
                'investigation': investigation_text
            })
            lines.append(line)

        last_pre = prescriptions[-1]
        last_history_names = []
        for his in last_pre.history_id:
            name_part = his.name.name if his.name else ''
            period_part = his.history_period.name if his.history_period else ''
            category_part = his.history_category_id.name if his.history_category_id else ''
            full_text = f"{name_part} - {period_part} - {category_part}" if period_part else name_part
            if full_text:
                last_history_names.append(full_text)

        last_history = ' | '.join(last_history_names)
        if last_pre.patient_history:
            if last_history:
                last_history += ' | ' + last_pre.patient_history
            else:
                last_history = last_pre.patient_history

        return lines, last_history

    @api.onchange('patient_id')
    def _onchange_history(self):
        prescriptions = self.env['prescription.order.knk'].search(
            [('patient_id', '=', self.patient_id.id), ('state', '=', 'prescribed')], order="date")
        if self.patient_id.patient_medical_history:
            self.medical_history_ids = [(0, 0, {
                'name': self.patient_id.patient_medical_history
            })]
        if prescriptions:
            history = self._get_old_history(prescriptions)
            self.medical_history_ids = history[0]
            self.check_patient = history[1]

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.open_prescription())
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_image = qr_image

    @api.depends('order_line_new_ids')
    def _compute_amount_total(self):
        for pre in self:
            pre.amount_total = sum(
                pre.order_line_new_ids.mapped('subtotal')) or 0.0

    @api.onchange("order_line_new_ids")
    def _onchange_product_ids(self):
        if self.order_line_new_ids:
            self.product_ids = [
                line.product_id.id for line in self.order_line_new_ids]

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(
                    _('Prescription Order can be delete only in Draft state.'))
        return super(PrescriptionOrderKnk, self).unlink()

    def button_reset(self):
        self.write({'state': 'draft'})

    def button_confirm(self):
        for app in self:
            if not app.order_line_new_ids:
                raise UserError(
                    _('You cannot confirm a prescription order without any Medication.'))

            app.state = 'prescribed'
            if not app.name:
                app.name = self.env['ir.sequence'].next_by_code(
                    'prescription.order.knk') or '/'
            app.generate_qr_code()
            
            # Auto-trigger RAG Syncing
            try:
                rag_client = self.env['rag.api.client']
                rag_client.trigger_indexing(
                    models_list=['prescription.order.knk'],
                    incremental=True
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Failed to auto-trigger RAG sync: %s", str(e))

    def open_prescription(self):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        report_url = f"/report/pdf/pos_prescription_knk.action_prescription_order_report/{self.id}"
        url = base_url + report_url
        return url

    def _prepare_diet_line_values(self):
        self.ensure_one()
        return {
            'description': self.description,
        }

    @api.onchange('prescription_template_id')
    def _onchange_sale_order_template_id(self):

        prescription_order_template = self.prescription_template_id.with_context(
            lang=self.patient_id.lang)

        complain_lines_data = [fields.Command.clear()]
        complain_lines_data += [
            fields.Command.create(line._prepare_complain_line_values())
            for line in prescription_order_template.complaint_res_ids
        ]
        self.complaint_id = complain_lines_data
        sign_lines_data = [fields.Command.clear()]
        sign_lines_data += [
            fields.Command.create(line._prepare_sign_line_values())
            for line in prescription_order_template.sign_res_ids
        ]
        self.sign_ids = sign_lines_data

        invs_lines_data = [fields.Command.clear()]
        invs_lines_data += [
            fields.Command.create(line._prepare_invs_line_values())
            for line in prescription_order_template.inves_res_ids
        ]
        self.investigation_ids = invs_lines_data

        excer_lines_data = [fields.Command.clear()]
        excer_lines_data += [
            fields.Command.create(line._prepare_excer_line_values())
            for line in prescription_order_template.excer_res_ids
        ]
        self.excercise_ids = excer_lines_data

        ortho_lines_data = [fields.Command.clear()]
        ortho_lines_data += [
            fields.Command.create(line._prepare_ortho_line_values())
            for line in prescription_order_template.ortho_list_ids
        ]
        self.ortho_ids = ortho_lines_data

        diagnosis_lines_data = [fields.Command.clear()]
        diagnosis_lines_data += [
            fields.Command.create(line._prepare_diagnosis_line_values())
            for line in prescription_order_template.diagnosis_res_ids
        ]
        self.diagnosis_ids = diagnosis_lines_data

        prescription_lines_data = [fields.Command.clear()]
        if self.old_prescription:
            prescription_lines_data += [
                fields.Command.create(line._prepare_prescription_line_values())
                for line in prescription_order_template.prescription_ids
            ]
        else:
            prescription_lines_data += [
                fields.Command.create(line._prepare_prescription_line_values())
                for line in prescription_order_template.prescription_new_ids
            ]
        self.order_line_new_ids = prescription_lines_data

        for rem in prescription_order_template:
            if rem.template_note_ids:
                self.notes_line_id = rem.template_note_ids.id
            else:
                self.notes_line_id = ''

        desc = []
        for rec in prescription_order_template:
            if rec.description:
                desc.append(rec.description)
            else:
                pass
        formatted_text = '\n'.join(desc)
        self.description = formatted_text

        # Past Medical History Lines
        past_lines_data = [fields.Command.clear()]
        past_lines_data += [
            fields.Command.create({
                'symptom_id': line.symptom_id.id,
                'result_id': line.result_id.id,
                'past_med_tmpl_id': line.past_med_tmpl_id.id,
            }) for line in prescription_order_template.past_medical_history_line_ids
        ]
        self.past_medical_history_line_ids = past_lines_data

        # Medication History Lines
        medication_lines_data = [fields.Command.clear()]
        medication_lines_data += [
            fields.Command.create({
                'medicine_id': line.medicine_id.id,
                'med_tmpl_id': line.med_tmpl_id.id,
            }) for line in prescription_order_template.medication_history_line_ids
        ]
        self.medication_history_line_ids = medication_lines_data

        # Family History Lines
        family_lines_data = [fields.Command.clear()]
        family_lines_data += [
            fields.Command.create({
                'family_history_config_id': line.family_history_config_id.id,
                'family_history_result_id': line.family_history_result_id.id,
                'family_tmpl_id': line.family_tmpl_id.id,
            }) for line in prescription_order_template.family_history_line_ids
        ]
        self.family_history_line_ids = family_lines_data

        # Social History Lines
        social_lines_data = [fields.Command.clear()]
        social_lines_data += [
            fields.Command.create({
                'social_history_config_id': line.social_history_config_id.id,
                'social_history_result_id': line.social_history_result_id.id,
                'social_tmpl_id': line.social_tmpl_id.id,
            }) for line in prescription_order_template.social_history_line_ids
        ]
        self.social_history_line_ids = social_lines_data

        history_lines_data = [fields.Command.clear()]
        history_lines_data += [
            fields.Command.create({
                'name': line.name.id,
                'history_period': line.history_period.id,
                'history_category_id': line.history_category_id.id,
                'temp_history_res_id': line.temp_history_res_id.id,
            }) for line in prescription_order_template.history_res_ids
        ]
        self.history_id = history_lines_data


class VitalBMILine(models.Model):
    _name = 'vital.bmi.line'
    _description = 'Vital BMI Line'

    prescription_id = fields.Many2one(
        'prescription.order.knk',
        ondelete='cascade'
    )

    v_weight = fields.Float(string="Weight")
    weight_uom_id = fields.Many2one('uom.uom', string="Weight Unit")

    v_height = fields.Float(string="Height")
    height_uom_id = fields.Many2one('uom.uom', string="Height Unit")

    v_bmi = fields.Float(
        string="BMI",
        compute="_compute_v_bmi",
        store=True
    )

    bmi_unit = fields.Char(string="Unit")

    def _get_qty(self, qty, to_unit, category, round=True, rounding_method='UP', raise_if_failure=True):
        if not self or not qty:
            return qty

        if self != to_unit and category.id != to_unit.category_id.id:
            if raise_if_failure:
                raise UserError(_(
                    "The unit of measure %s defined on the order line doesn't belong "
                    "to the same category as the unit of measure %s defined on the product."
                ) % (self.name, to_unit.name))
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
                amount,
                precision_rounding=to_unit.rounding,
                rounding_method=rounding_method
            )

        return amount

    @api.depends('v_weight', 'weight_uom_id', 'v_height', 'height_uom_id')
    def _compute_v_bmi(self):
        for rec in self:
            rec.v_bmi = 0.0
            rec.bmi_unit = 'kg/m²'

            try:
                height_in_cm = self.env['uom.uom'].search(
                    [('name', '=', 'm²')], limit=1
                )
                weight_in_kg = self.env['uom.uom'].search(
                    [('name', '=', 'kg')], limit=1
                )

                if not height_in_cm or not weight_in_kg:
                    rec.v_bmi = 0.0
                    continue

                get_height_in_cm = rec._get_qty(
                    rec.v_height,
                    height_in_cm,
                    height_in_cm.category_id
                )

                get_weight_in_kg = rec._get_qty(
                    rec.v_weight,
                    weight_in_kg,
                    weight_in_kg.category_id
                )

                if not get_height_in_cm:
                    rec.v_bmi = 0.0
                    continue

                height_m = (get_height_in_cm / 100)

                if height_m:
                    rec.v_bmi = get_weight_in_kg / (height_m ** 2)
                else:
                    rec.v_bmi = 0.0

            except Exception:
                rec.v_bmi = 0.0



class MedicalHistoryLine(models.Model):
    _name = 'patient.history.line'

    name = fields.Text(string="Medical History")
    date = fields.Date(string='Date', default=fields.Date.context_today)
    patient_id = fields.Many2one('res.partner', string="Patient id")
    pat_medical_his_id = fields.Many2one('prescription.order.knk')
    medication = fields.Text(string="Medication", store=True)
    investigation = fields.Text(string="Investigation", store=True)

    # def _compute_medication_investigation(self):
    #     for rec in self:
    #         prescription = rec.pat_medical_his_id
    #
    #         if prescription and prescription.order_line_new_ids:
    #             med_names = [line.product_id.name for line in prescription.order_line_new_ids if line.product_id]
    #             rec.medication = ', '.join(med_names)
    #         else:
    #             rec.medication = ''
    #
    #         if prescription and prescription.investigation_ids:
    #             inv_names = []
    #             for inv_line in prescription.investigation_ids:
    #                 inv_names += [tt.name for tt in inv_line.investigation_list_id]
    #             rec.investigation = ', '.join(inv_names)
    #         else:
    #             rec.investigation = ''


class PhysicalExaminationLine(models.Model):
    _name = "physical.examination.line"
    _description = "Physical Examination Line"

    prescription_id = fields.Many2one(
        'prescription.order.knk', string="Prescription", ondelete='cascade'
    )
    sequence = fields.Integer(string="Sequence", default=10)

    # Selection fields for different systems
    general = fields.Selection([
        ('pallor', 'Pallor'),
        ('icterus', 'Icterus'),
        ('cyanosis', 'Cyanosis'),
        ('clubbing', 'Clubbing'),
        ('edema', 'Edema'),
        ('lymph_nodes', 'Lymph nodes'),
        ('hydration', 'Hydration'),
    ], string="General")

    heent = fields.Selection([
        ('normal', 'Normal'),
        ('pupils_abnormal', 'Pupils Abnormal'),
        ('throat_lesions', 'Throat Lesions'),
        ('other_abnormal', 'Other Abnormal'),
    ], string="HEENT")

    cvs = fields.Selection([
        ('normal', 'Normal'),
        ('murmur_present', 'Murmur Present'),
        ('pulses_unequal', 'Pulses Unequal'),
        ('edema_present', 'Edema Present'),
    ], string="CVS")

    respiratory = fields.Selection([
        ('clear', 'Clear Bilaterally'),
        ('wheeze', 'Wheeze'),
        ('crackles', 'Crackles'),
        ('reduced_sounds', 'Reduced Sounds'),
    ], string="Respiratory")

    abdomen = fields.Selection([
        ('soft', 'Soft Non-Tender'),
        ('tender_rlq', 'Tender RLQ'),
        ('hepatomegaly', 'Hepatomegaly'),
        ('splenomegaly', 'Splenomegaly'),
    ], string="Abdomen")

    msk = fields.Selection([
        ('normal', 'Normal Gait/Joints'),
        ('limited_rom', 'Limited ROM'),
        ('swelling_present', 'Swelling Present'),
    ], string="MSK")

    cns = fields.Selection([
        ('alert_oriented', 'Alert Oriented'),
        ('cn_deficit', 'CN Deficit'),
        ('weakness', 'Weakness'),
        ('sensory_loss', 'Sensory Loss'),
    ], string="CNS (Screen)")

    patient_id = fields.Many2one(
        'res.partner', related='prescription_id.patient_id', string="Patient", readonly=True
    )


class NotesRecord(models.Model):
    _name = 'note.note'

    name = fields.Text(string="Notes")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class DiagnosislistRecord(models.Model):
    _name = 'diagnosis.diagnosis.list'

    name = fields.Text(string="Diagnosis")
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company.id
    )
    icd10_code_id = fields.Many2one(
        'medical.disease',
        string="ICD-10-CM Code",
        domain="[('code','!=',False)]"
    )
    snomed_ct_code = fields.Char(
        string="SNOMED-CT Code",
        readonly=True,        # users cannot edit
        store=True            # store in DB so it persists
    )
    secondary_ids = fields.Many2many(
        'diagnosis.secondary',
        string="Secondary Diagnoses"
    )

    # Auto-fill when ICD is selected or changed
    @api.onchange('icd10_code_id')
    def _onchange_icd10_code(self):
        for record in self:
            if record.icd10_code_id:
                record.snomed_ct_code = record.icd10_code_id.snomed_ct_code
            else:
                record.snomed_ct_code = False

    # Ensure saved value on create/write
    @api.model
    def create(self, vals):
        if vals.get('icd10_code_id'):
            disease = self.env['medical.disease'].browse(vals['icd10_code_id'])
            vals['snomed_ct_code'] = disease.snomed_ct_code
        return super().create(vals)

    def write(self, vals):
        if vals.get('icd10_code_id'):
            disease = self.env['medical.disease'].browse(vals['icd10_code_id'])
            vals['snomed_ct_code'] = disease.snomed_ct_code
        return super().write(vals)



class DiagnosisRecord(models.Model):
    _name = 'diagnosis.diagnosis'

    name = fields.Many2one('diagnosis.diagnosis.list', string="Diagnosis")
    diagnosis_res_id = fields.Many2one('prescription.order.knk')
    temp_diagnosis_res_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    disease_id = fields.Many2one('medical.disease', string="Disease Name")
    disease_short_code_id = fields.Char(related='name.icd10_code_id.code', string="Disease Short Code", store=True)
    # --- Domain field ---
    icd10_code_id = fields.Many2one(
        'medical.disease',
        string="ICD-10-CM Code",
        related='name.icd10_code_id',
        store=True,
        readonly=True
    )

    snomed_ct_code = fields.Char(
        string="SNOMED-CT Code",
        related='name.snomed_ct_code',
        store=True,
        readonly=True
    )
    secondary_diagnosis_ids = fields.Many2many(
        'diagnosis.secondary',
        compute='_compute_secondary_diagnosis_ids',
        string="Available Secondary Diagnoses"
    )

    selected_secondary_diagnosis_id = fields.Many2one(
        'diagnosis.secondary',
        string="Secondary Diagnosis",
        domain="[('id','in', secondary_diagnosis_ids)]"
    )

    selected_secondary_diagnosis_ids = fields.Many2many(
        'diagnosis.secondary',
        string="Secondary Diagnosis",
        domain="[('id','in', secondary_diagnosis_ids)]"
    )

    @api.depends('name')
    def _compute_secondary_diagnosis_ids(self):
        for rec in self:
            if rec.name:
                rec.secondary_diagnosis_ids = rec.name.secondary_ids
            else:
                rec.secondary_diagnosis_ids = False
    def _prepare_diagnosis_line_values(self):
        self.ensure_one()
        return {
            'name': self.name.id,
        }


class Complaintlist(models.Model):
    _name = "complaint.list"
    _description = 'Show List of Complaints '

    name = fields.Char(string="Complaint")
    period_ids = fields.Many2many("period.record", string="Period", domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    complain_image_line_ids = fields.One2many('complain.image.line', 'complain_id')
    clinical_overview = fields.Text(
        string="Clinical Overview",
        help="Detailed clinical summary, symptoms, or observations related to the complaint"
    )
    trigger_context_ids = fields.Many2many(
        'trigger.context',
        string="Triggers / Contexts",
        relation='complaint_trigger_rel',
        column1='complaint_id',
        column2='trigger_id'
    )

    temporal_pattern_ids = fields.Many2many(
        'temporal.pattern',
        string="Temporal Patterns / Timeline Tags",
        relation='complaint_temporal_rel',
        column1='complaint_id',
        column2='temporal_id'
    )
    allergy_reaction_ids = fields.Many2many(
        'allergy.reaction',
        string="Allergy Reactions",
        relation='complaint_allergy_reaction_rel',
        column1='complaint_id',
        column2='reaction_id'
    )
    red_flag_ids = fields.Many2many(
        'red.flag.indicator',
        string="Red Flags Indicators",
        relation='complaint_red_flag_rel',
        column1='complaint_id',
        column2='red_flag_id'
    )


class ComplainImageLine(models.Model):
    _name = "complain.image.line"
    _description = 'Complain Image Line'

    name = fields.Char(string="Name")
    image = fields.Binary(string="Image")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self:  self.env.company.id)
    complain_id = fields.Many2one('complaint.list', ondelete="cascade")


class complaintPeriodRecord(models.Model):
    _name = "period.record"
    _description = 'Display period records'

    name = fields.Char(string="Periods")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ComplaintRecordline(models.Model):
    _name = "complaint.record.line"
    _description = 'Complaint Line Records'

    name = fields.Many2one('complaint.list', string="Complaint List") # need to remove it
    complaint_list_id = fields.Many2one('complaint.list', string="Complaint List") # Use appropriate field name
    clinical_overview = fields.Text(related='complaint_list_id.clinical_overview',string="Clinical Overview",readonly=True,store=False)

    trigger_domain_ids = fields.Many2many(
        'trigger.context',
        compute='_compute_trigger_domain_ids',
        string="Trigger Domain"
    )

    temporal_domain_ids = fields.Many2many(
        'temporal.pattern',
        compute='_compute_temporal_domain_ids',
        string="Temporal Domain"
    )

    allergy_domain_ids = fields.Many2many(
        'allergy.reaction',
        compute='_compute_allergy_domain_ids',
        string="Allergy Domain"
    )
    red_flag_domain_ids = fields.Many2many(
        'red.flag.indicator',
        compute='_compute_red_flag_domain_ids',
        string="Red Flag Domain"
    )

    trigger_context_ids = fields.Many2many(
        'trigger.context',
        string="Triggers / Contexts",
        domain="[('id', 'in', trigger_domain_ids)]"
    )

    red_flag_selection_ids = fields.Many2one(
        'red.flag.indicator',
        string="Red Flag",
        domain="[('id', 'in', red_flag_domain_ids)]"
    )
    has_red_flag = fields.Boolean(
        compute="_compute_has_red_flag",
        store=True
    )
    complain_res_id = fields.Many2one(
        'prescription.order.knk',
        string="Prescription"
    )

    temporal_pattern_id = fields.Many2one(
        'temporal.pattern',
        string="Temporal Pattern",
        domain="[('id', 'in', temporal_domain_ids)]"
    )

    allergy_reaction_ids = fields.Many2one(
        'allergy.reaction',
        string="Allergy Reaction",
        domain="[('id', 'in', allergy_domain_ids)]"
    )

    period = fields.Many2one('period.record', string="Onset & Duration")

    clinical_overview = fields.Text(
        related='complaint_list_id.clinical_overview',
        readonly=True
    )
    allergy_severity = fields.Selection(
        [
            ('none', 'No allergy'),
            ('mild', 'Mild allergy'),
            ('moderate', 'Moderate allergy'),
            ('severe', 'Severe allergy'),
        ],
        string="Allergy Severity",
        default='none',  # Changed from False to 'none'
        required=True
    )

    allergy_color = fields.Selection(
        [
            ('green', 'Green'),
            ('yellow', 'Yellow'),
            ('amber', 'Amber'),
            ('red', 'Red'),
        ],
        string="Color Code",
        compute="_compute_allergy_color",
        store=True,
        readonly=True
    )

    @api.depends('red_flag_selection_ids')
    def _compute_has_red_flag(self):
        for rec in self:
            rec.has_red_flag = bool(rec.red_flag_selection_ids)
            if rec.complain_res_id:
                rec.complain_res_id._compute_has_any_red_flag()

    @api.depends('allergy_severity')
    def _compute_allergy_color(self):
        mapping = {
            'none': 'green',
            'mild': 'yellow',
            'moderate': 'amber',
            'severe': 'red',
        }
        for rec in self:
            if rec.allergy_severity:
                rec.allergy_color = mapping.get(rec.allergy_severity)
            else:
                rec.allergy_color = False

    @api.depends('complaint_list_id')
    def _compute_trigger_domain_ids(self):
        for rec in self:
            rec.trigger_domain_ids = rec.complaint_list_id.trigger_context_ids

    @api.depends('complaint_list_id')
    def _compute_red_flag_domain_ids(self):
        for rec in self:
            rec.red_flag_domain_ids = rec.complaint_list_id.red_flag_ids

    @api.depends('complaint_list_id')
    def _compute_temporal_domain_ids(self):
        for rec in self:
            rec.temporal_domain_ids = rec.complaint_list_id.temporal_pattern_ids

    @api.depends('complaint_list_id')
    def _compute_allergy_domain_ids(self):
        for rec in self:
            rec.allergy_domain_ids = rec.complaint_list_id.allergy_reaction_ids

    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self:  self.env.company.id)
    patient_id = fields.Many2one(
        'res.partner', ondelete="restrict", related='complain_res_id.patient_id')

    temp_complain_res_id = fields.Many2one('prescription.template')
    sequence = fields.Integer(string="Sequence", default=10)
    location_id = fields.Many2one("location.location", string='Anatomy')
    period_domain_ids = fields.Many2many("period.record", string="Period", compute="_compute_period_domain_ids")
    image = fields.Binary(string="Selected Image", attachment=True)
    view_all_buttons = fields.Boolean(string="View All Buttons", default=False)

    # def get_image_url(self):
    #     """Return the URL to access the image via web."""
    #     self.ensure_one()
    #     if not self.image:
    #         return False
    #     return f'/web/image/{self._name}/{self.id}/image'

    # def action_open_image_editor(self):
    #     self.ensure_one()
    #     return {
    #         "type": "ir.actions.client",
    #         "tag": "image_editor_action",
    #         "target": "new",
    #         "context": {
    #             "record_id": self.id,
    #             "image_url": self.get_image_url(),
    #             "model_name": self._name
    #         },
    #     }

    # def action_open_canvas(self):
    #     pass

    @api.depends('complaint_list_id')
    def _compute_period_domain_ids(self):
        for rec in self:
            if rec.complaint_list_id:
                rec.period_domain_ids = rec.complaint_list_id.period_ids
            else:
                rec.period_domain_ids = []

    def action_select_image(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Complaint Image',
            'res_model': 'complaint.image.select.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_complaint_record_id': self.id,
                'default_complaint_id': self.complaint_list_id.id,
            }
        }

    # @api.onchange('name')
    # def _onchange_name(self):
    #     if self.name:
    #         self.period = self.name.period_ids.ids
    #         return {
    #             'domain': {
    #                 'period': [('id', 'in', self.name.period_ids.ids)]
    #             }
    #         }
    #     else:
    #         return {
    #             'domain': {
    #                 'period': []
    #             }
    #         }

    def _prepare_complain_line_values(self):
        self.ensure_one()
        return {
            'name': self.complaint_list_id.id,
            'complaint_list_id': self.complaint_list_id.id,
            'period': self.period,
            'location_id': self.location_id.id
        }

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._sync_history_line()
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._sync_history_line()
        return res

    def _sync_history_line(self):
        self.ensure_one()

        if not self.complain_res_id or not self.complaint_list_id:
            return

        HistoryLine = self.env['history.list.line']

        history_line = HistoryLine.search([
            ('source_complaint_line_id', '=', self.id),
            ('history_res_id', '=', self.complain_res_id.id),
        ], limit=1)

        history_list = self.complain_res_id._find_or_create_history_list_from_complaint(
            self.complaint_list_id
        )

        vals = {
            'history_res_id': self.complain_res_id.id,
            'name': history_list.id,
            'history_period': self.period.id if self.period else False,
            'history_category_id': history_list.history_category_id.id if history_list.history_category_id else False,
            'source_complaint_line_id': self.id,
        }

        if history_line:
            history_line.write(vals)
        else:
            HistoryLine.create(vals)


class ComplaintImageSelectWizard(models.TransientModel):
    _name = "complaint.image.select.wizard"
    _description = "Complaint Image Selection Wizard"

    complaint_record_id = fields.Many2one('complaint.record.line', required=True)
    complaint_id = fields.Many2one('complaint.list', required=True)
    image_line_ids = fields.One2many('complaint.image.select.wizard.line', 'wizard_id', string="Images")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        complaint_id = self.env.context.get('default_complaint_id')
        if complaint_id:
            complaint = self.env['complaint.list'].browse(complaint_id)
            res['image_line_ids'] = [(0, 0, {
                'image_id': img.id,
                'image': img.image
            }) for img in complaint.complain_image_line_ids]
        return res

    def action_confirm(self):
        selected_line = self.image_line_ids.filtered(lambda l: l.is_selected)
        if not selected_line:
            raise UserError("Please select one image.")
        self.complaint_record_id.image = selected_line[0].image


class ComplaintImageSelectWizardLine(models.TransientModel):
    _name = "complaint.image.select.wizard.line"
    _description = "Complaint Image Selection Wizard Line"

    wizard_id = fields.Many2one('complaint.image.select.wizard', required=True)
    image_id = fields.Many2one('complain.image.line')
    image = fields.Binary(string="Image")
    is_selected = fields.Boolean(string="Select")


class historyList(models.Model):
    _name = 'history.list'
    _description = 'Patient History'

    name = fields.Char(string="History")
    period_ids = fields.Many2many("period.record", string="Period", domain="[('company_id', '=', company_id)]")
    history_category_id = fields.Many2one('history.category', string='Category', domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class historyListLine(models.Model):
    _name = "history.list.line"
    _description = 'Patient History Line'
    _order = 'sequence'

    history_res_id = fields.Many2one('prescription.order.knk')
    name = fields.Many2one('history.list', string="History List")
    history_period = fields.Many2one('period.record', string="Factors")
    history_category_id = fields.Many2one('history.category', string='Category')
    patient_id = fields.Many2one(
        'res.partner', ondelete="restrict", related='history_res_id.patient_id')
    temp_history_res_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self: self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    progression = fields.Selection([
        ('improving', 'Improving'),
        ('worsening', 'Worsening'),
        ('intermittent', 'Intermittent'),
        ('stable', 'Stable')
    ], string="Progression")

    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe')
    ], string="Severity")

    associated_symptoms = fields.Selection([
        ('fever', 'Fever'),
        ('pain', 'Pain'),
        ('gi', 'GI symptoms'),
        ('respiratory', 'Respiratory symptoms'),
        ('cardiac', 'Cardiac symptoms'),
        ('neuro', 'Neuro symptoms'),
        ('urinary', 'Urinary symptoms'),
        ('constitutional', 'Constitutional symptoms')
    ], string="Associated Symptoms")

    source_complaint_line_id = fields.Many2one('complaint.record.line', string="Source Complaint", ondelete="cascade")

    @api.onchange('source_complaint_line_id')
    def _onchange_source_complaint_line_id(self):
        """Auto-populate name and history_period from complaint.record.line"""
        if self.source_complaint_line_id and self.source_complaint_line_id.complaint_list_id:

            HistoryList = self.env['history.list']

            history_record = HistoryList.search([
                ('name', '=', self.source_complaint_line_id.complaint_list_id.name),
                ('company_id', '=', self.company_id.id if self.company_id else self.env.company.id)
            ], limit=1)

            if not history_record:
                history_record = HistoryList.create({
                    'name': self.source_complaint_line_id.complaint_list_id.name,
                    'company_id': self.company_id.id if self.company_id else self.env.company.id,
                })

            if history_record:
                self.name = history_record.id
                self.history_period = self.source_complaint_line_id.period.id
                self.history_category_id = history_record.history_category_id.id


    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.history_period = self.name.period_ids.ids
            return {
                'domain': {
                    'history_period': [('id', 'in', self.name.period_ids.ids)],
                    'history_category_id': [('id', '=', self.name.history_category_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'history_period': [],
                }
            }

    @api.onchange('history_category_id')
    def _onchange_history_category_id(self):
        if self.history_category_id:
            return {
                'domain': {
                    'name': [('history_category_id', '=', self.history_category_id.id)]
                }
            }

    # def _prepare_history_line_values(self):
    #     self.ensure_one()
    #     return {
    #         'name': self.name.id,
    #         'history_period': self.history_period.id,
    #     }


class signList(models.Model):
    _name = 'sign.list'
    _description = 'Show Signs'

    name = fields.Char(string="Examination")
    intensity_ids = fields.Many2many("intensity.intensity", string="Intensity",
                                     domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class Location(models.Model):
    _name = 'location.location'
    _description = 'Shows Location'

    name = fields.Char(string="Anatomy")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class InstensityInstensity(models.Model):
    _name = 'intensity.intensity'
    _description = 'Display Intensity'

    name = fields.Char(string="Intensity")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class signListLine(models.Model):
    _name = 'sign.list.line'
    _description = 'Display Sign Line'

    name = fields.Many2one("sign.list", string="Examination List")
    location = fields.Many2one('location.location', string="Anatomy")
    intensity = fields.Many2one('intensity.intensity', string="Intensity")
    sign_res_id = fields.Many2one('prescription.order.knk')
    patient_id = fields.Many2one(
        'res.partner', ondelete="restrict", related='sign_res_id.patient_id')
    temp_sign_res_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self:  self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            intensity_ids = self.name.intensity_ids.ids
            return {
                'domain': {
                    'intensity': [('id', 'in', intensity_ids)]
                }
            }
        else:
            return {
                'domain': {
                    'intensity': []
                }
            }

    def _prepare_sign_line_values(self):
        self.ensure_one()
        return {
            'name': self.name.id,
            'location': self.location.id,
            'intensity': self.intensity.id,
        }


class TestType(models.Model):
    _name = "test.type"

    name = fields.Char()
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class InvestigationList(models.Model):
    _name = "investigation.list"
    _description = 'Investigation List'

    name = fields.Char(string="Test Item/Sample")
    category_id = fields.Many2one(
        'test.category',
        string='Test Category',
        ondelete='restrict'
    )
    test_type = fields.Many2many("test.type")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class InvestigationListline(models.Model):
    _name = 'investigation.list.line'
    _description = 'Investigation Lines'

    investigation_list_id = fields.Many2one("investigation.list")
    category_id = fields.Many2one(
        'test.category',
        string='Test Category'
    )
    test_type = fields.Many2many(comodel_name='test.type', string="Test Type")
    inves_res_id = fields.Many2one('prescription.order.knk')
    temp_inves_res_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self: self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            return {
                'domain': {
                    'investigation_list_id': [
                        ('category_id', '=', self.category_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'investigation_list_id': []
                }
            }

    @api.onchange('investigation_list_id')
    def _onchange_investigation_list_id(self):
        if self.investigation_list_id:
            self.category_id = self.investigation_list_id.category_id

    @api.onchange('investigation_list_id', 'test_type')
    def get_test_type(self):
        domain = [
            ('name', '=', self.investigation_list_id.name)
        ]
        result = self.env['investigation.list'].search(domain)
        return {'domain': {'test_type': [('id', 'in', result.test_type.ids)]}}

    def _prepare_invs_line_values(self):
        self.ensure_one()
        return {
            'investigation_list_id': self.investigation_list_id.id,
            'test_type': self.test_type.ids,
        }


class PartLocation(models.Model):
    _name = 'part.location'

    name = fields.Char(string="Part Location")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ExcerciseEx(models.Model):
    _name = "excercise.excercise"
    _description = 'Patient Excercise'

    name = fields.Char(string="Activity Level")
    part_location = fields.Many2one('part.location', string="Part Location")
    move2 = fields.Char(string="Move")
    instruction_ids = fields.Many2many(
        'exercise.instruction',
        string="Allowed Instructions"
    )
    type_of_test2 = fields.Char(string="Repitition")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ExcerciseExLine(models.Model):
    _name = "excercise.ex.line"
    _description = 'Patient Excercise Line'

    name= fields.Many2one(
        'excercise.excercise',
        string="Activity Level",
        required=True
    )

    instruction_domain_ids = fields.Many2many(
        'exercise.instruction',
        compute='_compute_instruction_domain_ids',
        string="Instruction Domain"
    )

    instruction_id = fields.Many2one(
        'exercise.instruction',
        string="Instruction Notes",
        domain="[('id', 'in', instruction_domain_ids)]"
    )

    @api.depends('name')
    def _compute_instruction_domain_ids(self):
        for rec in self:
            rec.instruction_domain_ids = rec.name.instruction_ids

    part_location = fields.Many2one('part.location', string="Part Location")
    move2 = fields.Char(string="Move")
    type_of_test2 = fields.Char(string="Repitition")
    excer_res_id = fields.Many2one('prescription.order.knk')
    temp_excer_res_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self: self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    @api.onchange('name')
    def get_part_location(self):
        domain = [
            ('name', '=', self.name.name)
        ]
        result = self.env['excercise.excercise'].search(domain)

        return {'domain': {'part_location': [('id', 'in', result.part_location.ids)]}}

    @api.onchange('name', 'part_location')
    def get_move_test_type(self):

        for rec in self:
            domain = [
                ('name', '=', self.name.name), ('part_location',
                                                '=', rec.part_location.id)
            ]
            result = self.env['excercise.excercise'].search(domain)
            if result:
                rec.move2 = result.move2
                rec.type_of_test2 = result.type_of_test2
            else:
                rec.move2 = ''
                rec.type_of_test2 = ''

    def _prepare_excer_line_values(self):
        self.ensure_one()
        return {
            'name': self.name.id,
            'part_location': self.part_location.id,
            'move2': self.move2,
            'type_of_test2': self.type_of_test2
        }


class orthoList(models.Model):
    _name = 'ortho.list'
    _description = 'Side'

    name = fields.Char(string="Side")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class itemList(models.Model):
    _name = "item.item"
    _description = "Ortho Items"

    name = fields.Char(string="Item Name")
    material = fields.Char(string="Material")
    comments = fields.Text(string="Instruction")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class orthoListLine(models.Model):
    _name = 'ortho.list.line'
    _description = 'Ortho List'

    name = fields.Many2one('item.item', string="Item Name")
    location = fields.Many2one('location.location', string="Anatomy")
    side = fields.Many2one('ortho.list', string="side")
    material = fields.Char(related='name.material', string="Material")
    comments = fields.Text(related="name.comments", string="Instruction")
    ortho_list_id = fields.Many2one('prescription.order.knk')
    temp_ortho_list_id = fields.Many2one('prescription.template')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',
                                 default=lambda self: self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    def _prepare_ortho_line_values(self):
        self.ensure_one()
        return {
            'name': self.name.id,
            'location': self.location.id,
            'side': self.side.id,
            'material': self.material,
            'comments': self.comments
        }


class VitalUnit(models.Model):
    _name = 'vital.uom'

    name = fields.Char(string="Unit")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class vitalListLine(models.Model):
    _name = "vital.list.line"
    _description = "Vital Signs"

    name = fields.Integer(string="Weight")
    w_unit = fields.Many2one('uom.uom', string="Unit")
    height = fields.Integer(string="height")
    # height = fields.Float(string="Height")
    h_unit = fields.Many2one('uom.uom', string="Unit")
    bmi = fields.Float(string="BMI", compute='_compute_bmi')
    bmi_unit = fields.Char(string="Unit")
    blood_presure = fields.Char(string="Systolic Pressure")
    slash_tag = fields.Char(default="/")
    blood_presure_2 = fields.Char(string="Diastolic Pressure")
    blood_unit = fields.Many2one('uom.uom', string="Unit")
    pulse = fields.Char(string="Pulse")
    pulse_unit = fields.Many2one('uom.uom', string="Unit")
    respiratory_rate = fields.Char(string="Respiratory Rate")
    rr_unit = fields.Many2one('uom.uom', string="Unit")
    vital_list_id = fields.Many2one('prescription.order.knk')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    sequence = fields.Integer(string="Sequence", default=10)

    temperature = fields.Integer(
        string="Temperature (°F/°C)"
    )

    spo2 = fields.Integer(
        string="SpO₂ (%)"
    )

    rbs = fields.Integer(
        string="Random Blood Sugar (RBS)"
    )

    motor_power = fields.Integer(
        string="Motor Power"
    )

    pupil_reaction = fields.Selection(
        [
            ('r', 'Unequal / Fixed'),
            ('a', 'Sluggish'),
            ('g', 'PERRLA'),
        ],
        string="Pupil Reaction"
    )

    nihss = fields.Integer(
        string="Neuro (NIHSS)"
    )
    vital_list_id = fields.Many2one(
        'prescription.order.knk',
        ondelete='cascade'
    )

    gcs_total_score = fields.Integer(
        string="Total GCS",
        related='vital_list_id.gcs_total_score',
        store=True,
        readonly=True
    )

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

    @api.depends('name', 'w_unit', 'height')
    def _compute_bmi(self):

        for rec in self:
            height_in_cm = self.env['uom.uom'].search([('name', '=', 'm²')])
            weight_in_kg = self.env['uom.uom'].search([('name', '=', 'kg')])

            get_height_in_cm = self._get_qty(
                rec.height, height_in_cm, height_in_cm.category_id)
            get_weight_in_kg = self._get_qty(
                rec.name, weight_in_kg, weight_in_kg.category_id)
            get_height_in_cm_2 = get_height_in_cm/100

            if get_height_in_cm != 0.0:
                rec.bmi = get_weight_in_kg/(get_height_in_cm_2**2)
                rec.bmi_unit = 'kg/m²'
            else:
                rec.bmi = 0.0


class PrescriptionOrderLineKnkNew(models.Model):
    _name = "prescription.order.line.knk.new"
    _description = "Prescription Order Line Knk New"

    prescription_id = fields.Many2one(
        'prescription.order.knk', ondelete="cascade", string='Prescription')
    temp_prescription_id = fields.Many2one('prescription.template')
    product_id = fields.Many2one(
        'product.product', ondelete="cascade", string='Name', required=True, domain="[('is_medication_knk','=',True)]")
    quantity = fields.Float(string='Units',
                            help="Number of units of the medicament. Example : 30 capsules of amoxicillin", default=1.0)
    short_comment = fields.Char(
        string='Comment', help='Short comment on the specific drug')
    company_id = fields.Many2one('res.company', ondelete="cascade",
                                 string='Hospital', related='prescription_id.company_id')
    qty_available = fields.Float(
        related='product_id.qty_available', string='Available Qty')
    days = fields.Float("Days", default=1.0)
    qty_per_day = fields.Float(string='Qty Per Day', default=1.0)
    unit_price = fields.Float(
        string="Unit Price", related="product_id.lst_price")
    subtotal = fields.Float(string="Sub Total")
    allergy_status = fields.Selection(
        [
            ('no', 'No'),
            ('yes', 'Yes'),
        ],
        string="Allergy Status",
        default='no',
        required=True
    )
    duration_type = fields.Selection(
        [
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('chronic', 'Continue (chronic)')
        ],
        string="Duration",
        default='days',
        required=True
    )

    duration_value = fields.Integer(
        string="Duration",
        default=1,
        help="Number of days or weeks, depending on the selection"
    )

    med_group_id = fields.Many2one('medicine.group', string="Medicine Group")
    composition_id = fields.Many2one(
        'medicine.composition', string="Composition")
    dose_id = fields.Many2one('medicine.dose', string="Dose")
    route_id = fields.Many2one('medicine.route', string="Route")
    whn_to_take_id = fields.Many2one(
        'medicine.food', string="Relation With Food")
    frequency_id = fields.Many2one('med.frequency', string="Frequency")
    knk_t_qty = fields.Char(string="Total Quantity")
    sequence = fields.Integer(string="Sequence", default=10)
    display_type = fields.Selection(
        selection=[
            ('line_note', "Note"),
        ],
        default=False)
    name = fields.Text(string="Name")

    @api.onchange('unit_price', 'quantity')
    def _onchange_subtotal(self):
        self.subtotal = self.unit_price * self.quantity

    @api.onchange('qty_per_day', 'days')
    def _get_total_qty(self):
        self.quantity = self.days * self.qty_per_day

    def _prepare_prescription_line_values(self):
        self.ensure_one()
        return {
            'med_group_id': self.med_group_id.id,
            'composition_id': self.composition_id,
            'product_id': self.product_id.id,
            'route_id': self.route_id.id,
            'dose_id': self.dose_id.id,
            'whn_to_take_id': self.whn_to_take_id.id,
            'frequency_id': self.frequency_id.id,
            'knk_t_qty': self.knk_t_qty
        }

    @api.onchange('product_id')
    def get_product_type(self):
        result = self.product_id.product_tmpl_id
        if result:
            self.med_group_id = result.med_group_id.id
            self.composition_id = result.composition_id.id
            self.route_id = result.route_id.id
            self.dose_id = result.dose_id.id
            self.whn_to_take_id = result.whn_to_take_id.id
            self.frequency_id = result.frequency_id.id
            self.knk_t_qty = result.knk_t_qty

    @api.onchange('med_group_id')
    def _onchange_med_group_id(self):
        if self.med_group_id:
            return {
                'domain': {
                    'product_id': [
                        ('is_medication_knk', '=', True),
                        ('med_group_id', '=', self.med_group_id.id),
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'product_id': [('is_medication_knk', '=', True)]
                }
            }


class PrescriptionOrderLineKnk(models.Model):
    _name = "prescription.order.line.knk"
    _description = "Prescription Order Line Knk"

    prescription_id = fields.Many2one(
        'prescription.order.knk', ondelete="cascade", string='Prescription')
    temp_prescription_id = fields.Many2one('prescription.template')
    product_id = fields.Many2one(
        'product.product', ondelete="cascade", string='Name', required=True, domain="[('is_medication_knk','=',True)]")
    quantity = fields.Float(string='Units',
                            help="Number of units of the medicament. Example : 30 capsules of amoxicillin", default=1.0)
    short_comment = fields.Char(
        string='Comment', help='Short comment on the specific drug')
    company_id = fields.Many2one('res.company', ondelete="cascade",
                                 string='Hospital', related='prescription_id.company_id')
    qty_available = fields.Float(
        related='product_id.qty_available', string='Available Qty')
    days = fields.Float("Days", default=1.0)
    qty_per_day = fields.Float(string='Qty Per Day', default=1.0)
    unit_price = fields.Float(
        string="Unit Price", related="product_id.lst_price")
    subtotal = fields.Float(string="Sub Total")
    med_group = fields.Char(string="Med Group", related="product_id.med_group")
    composition = fields.Char(string="Composition",
                              related="product_id.composition")

    dose = fields.Char(
        string="Dose", related="product_id.dose", readonly=False)
    route = fields.Char(
        string="Route", related="product_id.route", readonly=False)
    whn_to_take = fields.Char(
        string="Relation With Food", related="product_id.whn_to_take", readonly=False)
    frequency = fields.Char(
        string="Frequency", related="product_id.frequency", readonly=False)
    t_qty = fields.Char(string="Total Quantity",
                        related="product_id.t_qty", readonly=False)
    sequence = fields.Integer(string="Sequence", default=10)
    # new fields
    duration_unit = fields.Selection(
        [('days', 'Days'), ('week', 'Week'), ('month', 'Month'), ('continue', 'Continue')],
        string="Duration Unit"
    )
    duration_value = fields.Integer(string="Duration Value")
    allergy_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Allergy Status"
    )

    @api.onchange('unit_price', 'quantity')
    def _onchange_subtotal(self):
        self.subtotal = self.unit_price * self.quantity

    @api.onchange('qty_per_day', 'days')
    def _get_total_qty(self):
        self.quantity = self.days * self.qty_per_day

    def _prepare_prescription_line_values(self):
        self.ensure_one()
        return {
            'med_group': self.med_group,
            'composition': self.composition,
            'product_id': self.product_id.id,
            'route': self.route,
            'dose': self.dose,
            'whn_to_take': self.whn_to_take,
            'frequency': self.frequency,
            't_qty': self.t_qty
        }


class PosConfig(models.Model):
    _inherit = 'pos.config'

    check_prescription_knk = fields.Boolean(
        string='Import Prescription')
    pos_prescription_knk = fields.Selection([
        ('always', 'Always Create Prescription Order'),
        ('enable_option', 'Enable Options')
    ])


class PastMedicalHistory(models.Model):
    _name = 'past.medical.history'

    prescription_id = fields.Many2one('prescription.order.knk', ondelete='cascade')
    symptom_id = fields.Many2one('symptom.config', string='Symptoms', domain="[('company_id', '=', company_id)]")
    result_id = fields.Many2one('result.config', string='Result')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    past_med_tmpl_id = fields.Many2one('prescription.template', string='Template')
    result_domain_ids = fields.Many2many('result.config', compute='_compute_result_domain_ids')

    @api.depends('symptom_id')
    def _compute_result_domain_ids(self):
        for rec in self:
            if rec.symptom_id:
                rec.result_domain_ids = rec.symptom_id.result_ids
            else:
                rec.result_domain_ids = []

    # @api.onchange('symptom_id')
    # def _onchange_symptom_id(self):
    #     if self.symptom_id:
    #         result_ids = self.symptom_id.result_ids.ids
    #         return {
    #             'domain': {'result_id': [('id', 'in', result_ids)]}
    #         }
    #     else:
    #         return {'domain': {'result_id': []}}


class MedicationHistory(models.Model):
    _name = 'medication.history'

    prescription_id = fields.Many2one('prescription.order.knk', ondelete='cascade')
    medicine_id = fields.Many2one('product.product', string='Medicine', domain="[('is_medication_knk', '=', True)]")
    medicine_group_id = fields.Many2one('medicine.group', string='Medicine Group', related='medicine_id.med_group_id',
                                        store=True)
    med_tmpl_id = fields.Many2one('prescription.template', string='Template')
    dose = fields.Char(string="Dose")
    frequency = fields.Char(string="Frequency")
    otc_herbal_supplement = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="OTC / Herbal / Supplement"
    )


class FamilyHistory(models.Model):
    _name = 'family.history'

    prescription_id = fields.Many2one('prescription.order.knk', ondelete='cascade')
    family_history_config_id = fields.Many2one('family.history.config', string='Family History',
                                               domain="[('company_id', '=', company_id)]")
    family_history_result_id = fields.Many2one('family.history.result', string='Family History Result')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    family_tmpl_id = fields.Many2one('prescription.template', string='Template')
    result_domain_ids = fields.Many2many('family.history.result', compute='_compute_result_domain_ids')

    @api.depends('family_history_config_id')
    def _compute_result_domain_ids(self):
        for rec in self:
            if rec.family_history_config_id:
                rec.result_domain_ids = rec.family_history_config_id.result_ids
            else:
                rec.result_domain_ids = []

    # @api.onchange('family_history_config_id')
    # def _onchange_family_history_config_id(self):
    #     if self.family_history_config_id:
    #         result_ids = self.family_history_config_id.result_ids.ids
    #         return {
    #             'domain': {
    #                 'family_history_result_id': [('id', 'in', result_ids)]
    #             }
    #         }
    #     else:
    #         return {
    #             'domain': {
    #                 'family_history_result_id': []
    #             }
    #         }



class SocialHistory(models.Model):
    _name = 'social.history'

    prescription_id = fields.Many2one('prescription.order.knk', ondelete='cascade')
    social_history_config_id = fields.Many2one('social.history.config', string='Social History',
                                               domain="[('company_id', '=', company_id)]")
    social_history_result_id = fields.Many2one('social.history.result', string='Result')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    social_tmpl_id = fields.Many2one('prescription.template', string='Template')
    result_domain_ids = fields.Many2many('social.history.result', compute='_compute_result_domain_ids')

    @api.depends('social_history_config_id')
    def _compute_result_domain_ids(self):
        for rec in self:
            if rec.social_history_config_id:
                rec.result_domain_ids = rec.social_history_config_id.result_ids
            else:
                rec.result_domain_ids = []

    # @api.onchange('social_history_config_id')
    # def _onchange_social_history_config_id(self):
    #     if self.social_history_config_id:
    #         result_ids = self.social_history_config_id.result_ids.ids
    #         return {
    #             'domain': {
    #                 'social_history_result_id': [('id', 'in', result_ids)]
    #             }
    #         }
    #     else:
    #         return {
    #             'domain': {
    #                 'social_history_result_id': []
    #             }
    #         }


class ProcedureHistory(models.Model):
    _name = 'procedure.history'

    prescription_id = fields.Many2one('prescription.order.knk', ondelete='cascade')
    procedure_config_ids = fields.Many2many('procedure.config', string='Procedure', domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class WaCompose(models.TransientModel):
    _inherit = 'wa.compose.message'

    @api.model
    def default_get(self, fields):
        res = super(WaCompose, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'prescription.order.knk' and active_id:
            active_record = self.env[active_model].sudo().browse(active_id)
            if 'report' in self.env.context:
                report_xmlid = 'pos_prescription_knk.action_prescription_order_report'
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_xmlid, active_record.id)
                b64_pdf = base64.b64encode(pdf_content)
                pdf_name = f"Prescription-{active_record.name or active_record.id}.pdf"

                attachment = self.env['ir.attachment'].sudo().create({
                    'name': pdf_name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'res_model': active_model,
                    'res_id': active_record.id,
                    'mimetype': 'application/pdf',
                })

                res['attachment_ids'] = [(4, attachment.id)]

            template = self.env.company.whatsapp_template_id
            if not template:
                raise UserError("Please configure Whatsapp Template in Company Settings")

            res['template_id'] = template.id
        return res


class GSCMotorResponse(models.Model):
    _name = 'gsc.motor.response'
    _description = 'GSC Motor Response'

    name = fields.Char(string='Motor Response', required=True)
    score = fields.Integer(string='Score', required=True)


class GSCVerbalResponse(models.Model):
    _name = 'gsc.verbal.response'
    _description = 'GSC Verbal Response'

    name = fields.Char(string='Verbal Response', required=True)
    score = fields.Integer(string='Score', required=True)


class GSCEyeResponse(models.Model):
    _name = 'gsc.eye.response'
    _description = 'GSC Eye Response'

    name = fields.Char(string='Eye Response', required=True)
    score = fields.Integer(string='Score', required=True)



class GCSScoreLine(models.Model):
    _name = 'gcs.score.line'
    _description = 'GCS Score Line'

    prescription_order_id = fields.Many2one(
        'prescription.order.knk',
        string='Prescription Order',
        required=True,
        ondelete='cascade'
    )


    motor_response_id = fields.Many2one(
        'gsc.motor.response',
        string='Motor Response',
        required=True
    )

    verbal_response_id = fields.Many2one(
        'gsc.verbal.response',
        string='Verbal Response',
        required=True
    )

    eye_response_id = fields.Many2one(
        'gsc.eye.response',
        string='Eye Response',
        required=True
    )

    total_score = fields.Integer(
        string='Total GCS Score',
        compute='_compute_total_score',
        store=True
    )


    @api.depends(
        'motor_response_id.score',
        'verbal_response_id.score',
        'eye_response_id.score'
    )
    def _compute_total_score(self):
        for record in self:
            record.total_score = (
                (record.motor_response_id.score or 0) +
                (record.verbal_response_id.score or 0) +
                (record.eye_response_id.score or 0)
            )

class TriggerContext(models.Model):
    _name = "trigger.context"
    _description = "Trigger / Context"

    name = fields.Char(string="Name", required=True)


class TemporalPattern(models.Model):
    _name = "temporal.pattern"
    _description = "Temporal Pattern / Timeline Tag"

    name = fields.Char(string="Name", required=True)

class AllergyReaction(models.Model):
    _name = 'allergy.reaction'
    _description = 'Allergy Reaction Selector'
    _order = 'name'

    name = fields.Char(
        string="Reaction",
        required=True,
        translate=True
    )

    description = fields.Text(
        string="Description / Notes"
    )
class RedFlagIndicator(models.Model):
    _name = 'red.flag.indicator'
    _description = 'Red Flags Indicator'
    _order = 'name'

    name = fields.Char(
        string="Red Flag",
        required=True,
        translate=True
    )
    description = fields.Text(string="Description / Notes")

class ExerciseInstruction(models.Model):
    _name = "exercise.instruction"
    _description = "Exercise Instruction Notes"

    name = fields.Char(
        string="Instruction",
        required=True
    )
class SecondaryDiagnosis(models.Model):
    _name = "diagnosis.secondary"
    _description = "Secondary Diagnosis"

    name = fields.Char(string="Secondary Diagnosis", required=True)

class TestCategory(models.Model):
    _name = 'test.category'
    _description = 'Test Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)



class PhysicalGeneralCondition(models.Model):
    _name = 'physical.general.condition'
    _description = 'General Condition'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalPallor(models.Model):
    _name = 'physical.pallor'
    _description = 'Pallor'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalMSK(models.Model):
    _name = 'physical.msk'
    _description = 'MSK (Musculoskeletal)'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalEdema(models.Model):
    _name = 'physical.edema'
    _description = 'Edema'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalLymphNodes(models.Model):
    _name = 'physical.lymph.nodes'
    _description = 'Lymph Nodes'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalHydration(models.Model):
    _name = 'physical.hydration'
    _description = 'Hydration'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalCVS(models.Model):
    _name = 'physical.cvs'
    _description = 'CVS'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalRS(models.Model):
    _name = 'physical.rs'
    _description = 'RS'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalAbdomen(models.Model):
    _name = 'physical.abdomen'
    _description = 'Abdomen'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalNeuro(models.Model):
    _name = 'physical.neuro'
    _description = 'Neuro (CNS Screen)'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )


class PhysicalENT(models.Model):
    _name = 'physical.ent'
    _description = 'ENT'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company.id
    )

