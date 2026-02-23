# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, api, _
from odoo import tools


class PrescriptionReport(models.Model):
    _name = 'prescription.order.report'
    _auto = False
    _description = "Show the Pivot Report"

    patient_id = fields.Many2one("res.partner", "Patient")
    complaint = fields.Many2one('complaint.record.line', string="Complaint")
    history = fields.Many2one('history.list.line', string="History")
    symtoms = fields.Many2one('sign.list.line', string="Examination")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				SELECT
				row_number() OVER () AS id,				
				line.patient_id,
				line.complaint,
				line.history,
				line.symtoms				
				FROM
				(
					SELECT					
					rp.patient_id as patient_id,
					c.complaint_list_id as complaint,
					h.name as history,
					s.name as symtoms 					
					FROM
					prescription_order_knk rp
					LEFT JOIN
					complaint_record_line c ON (rp.id = c.id)								
					LEFT JOIN
					history_list_line h ON (c.id = h.id)
					LEFT JOIN
					sign_list_line s ON (h.id=s.id)
					) as line
				)
			""" % (self._table, ))
