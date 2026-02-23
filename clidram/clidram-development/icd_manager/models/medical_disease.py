# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class MedicalDisease(models.Model):
    _name = "medical.disease"
    _description = "Medical disease"

    code = fields.Char(string='Code')
    name = fields.Char(string='Short name')
    long_name = fields.Char(string='Long name')
    snomed_ct_code = fields.Char(
        string="SNOMED-CT Code",
        help="Standard SNOMED-CT clinical terminology code"
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        Allows searching for medical.disease records by both `code` and `name`.
        """
        args = args or []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()
