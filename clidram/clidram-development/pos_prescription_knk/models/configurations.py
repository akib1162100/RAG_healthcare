from odoo import models, fields, api, _


class SymptomConfig(models.Model):
    _name = 'symptom.config'
    _description = 'Symptom Configuration'

    name = fields.Char(string="Symptom", required=True)
    result_ids = fields.Many2many('result.config', string='Result',
                                  domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ResultConfig(models.Model):
    _name = 'result.config'
    _description = 'Result Configuration'

    name = fields.Char(string="Result", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class FamilyHistoryConfig(models.Model):
    _name = 'family.history.config'
    _description = 'Family History Configuration'

    name = fields.Char(string="Family History", required=True)
    result_ids = fields.Many2many('family.history.result', string='Result',
                                  domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class FamilyHistoryResult(models.Model):
    _name = 'family.history.result'
    _description = 'Family History Result'

    name = fields.Char(string="Result", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class SocialHistoryConfig(models.Model):
    _name = 'social.history.config'
    _description = 'Social History Configuration'

    name = fields.Char(string="Social History", required=True)
    result_ids = fields.Many2many('social.history.result', string='Result',
                                  domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class SocialHistoryResult(models.Model):
    _name = 'social.history.result'
    _description = 'Social History Result'

    name = fields.Char(string="Result", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class ProcedureConfig(models.Model):
    _name = 'procedure.config'
    _description = 'Procedure Configuration'

    name = fields.Char(string="Procedure", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class HistoryCategory(models.Model):
    _name = 'history.category'
    _description = 'History Category'

    name = fields.Char(string="Category", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)