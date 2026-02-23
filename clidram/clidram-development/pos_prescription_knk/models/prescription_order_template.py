# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, api, _

class PrescriptionTemplate(models.Model):
	_name='prescription.template'
	_description='Prescription Template'

	name = fields.Char(string="Prescription Template")
	company_id=fields.Many2one('res.company', default=lambda self: self.env.company.id)
	description = fields.Text(string="Diet",copy=True)
	complaint_res_ids = fields.One2many('complaint.record.line','temp_complain_res_id',copy=True)
	history_res_ids = fields.One2many('history.list.line','temp_history_res_id',copy=True)
	sign_res_ids = fields.One2many('sign.list.line','temp_sign_res_id',copy=True)
	inves_res_ids = fields.One2many('investigation.list.line','temp_inves_res_id',copy=True)
	excer_res_ids = fields.One2many('excercise.ex.line','temp_excer_res_id',copy=True)
	ortho_list_ids = fields.One2many('ortho.list.line','temp_ortho_list_id',copy=True)
	diagnosis_res_ids = fields.One2many('diagnosis.diagnosis','temp_diagnosis_res_id',copy=True)
	prescription_ids = fields.One2many('prescription.order.line.knk','temp_prescription_id',copy=True)
	prescription_new_ids = fields.One2many('prescription.order.line.knk.new','temp_prescription_id',copy=True)
	old_temp = fields.Boolean()
	template_note_ids = fields.Many2one('note.note', string="Notes")
	attachment = fields.Binary(string="Attachment")

	past_medical_history_line_ids = fields.One2many('past.medical.history', 'past_med_tmpl_id',
													string='Past Medical History')
	medication_history_line_ids = fields.One2many('medication.history', 'med_tmpl_id',
												  string='Medication History')
	family_history_line_ids = fields.One2many('family.history', 'family_tmpl_id',
											  string='Family History')
	social_history_line_ids = fields.One2many('social.history', 'social_tmpl_id',
											  string='Social History')


	
	
