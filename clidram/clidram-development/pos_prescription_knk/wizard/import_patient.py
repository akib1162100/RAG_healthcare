# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64
import xlrd

from io import BytesIO
from odoo import models, fields, tools, api, _
from odoo.exceptions import ValidationError


class PatientImport(models.TransientModel):
    _name = "patient.import"

    patient_file = fields.Binary(string="import Excel Files")

    def import_patient(self):        
        if self.patient_file:
            try:
                workbook = xlrd.open_workbook(
                    file_contents=base64.b64decode(self.patient_file))
                Sheet_name = workbook.sheet_names()
                sheet = workbook.sheet_by_name(Sheet_name[0])
                number_of_rows = sheet.nrows
                row = 1

                while(row < number_of_rows):
                    seq2 = tools.ustr(sheet.cell(row, 9).value)
                    if seq2:
                        patient_details = " ".join([
                            tools.ustr(sheet.cell(row, 13).value),
                            tools.ustr(sheet.cell(row, 14).value),
                            tools.ustr(sheet.cell(row, 15).value),
                            tools.ustr(sheet.cell(row, 16).value),
                            ])
                        value = tools.ustr(sheet.cell(row, 9).value)
                        float_value = float(value)
                        rounded_value = round(float_value)
                        seq = int(rounded_value)
                        gender = ''
                        if tools.ustr(sheet.cell(row, 12).value) == 'Male':
                            gender = 'male'
                        elif tools.ustr(sheet.cell(row, 12).value) == 'Female':
                            gender = 'female'
                        elif tools.ustr(sheet.cell(row, 12).value) == 'Other':
                            gender = 'other'
                        else:
                            gender = ''

                        patient = self.env['res.partner'].sudo().create({
                            'partner_type': 'patient',
                            'name': tools.ustr(sheet.cell(row, 4).value),
                            'city': tools.ustr(sheet.cell(row, 1).value),
                            'company_id': self.env['res.company'].search([('name', '=', tools.ustr(sheet.cell(row, 2).value))]).id,
                            'country_id': self.env['res.country'].search([('name', '=', tools.ustr(sheet.cell(row, 3).value))]).id,
                            'email': tools.ustr(sheet.cell(row, 5).value),
                            'phone': tools.ustr(sheet.cell(row, 6).value),
                            'state_id': self.env['res.country.state'].search([('name', '=', tools.ustr(sheet.cell(row, 8).value))]).id,
                            'seq': seq,
                            'age': tools.ustr(sheet.cell(row, 10).value),
                            'mobile': tools.ustr(sheet.cell(row, 11).value),
                            'gender': gender,
                            'mobile': tools.ustr(sheet.cell(row, 11).value),
                            'patient_details': patient_details
                        })
                    row += 1
            except:
                raise ValidationError("Please select .xls/xlsx file...")
