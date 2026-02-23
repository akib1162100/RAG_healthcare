from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # @api.constrains('mobile')
    # def _check_mobile_duplicate(self):
    #     for record in self:
    #         if record.mobile and len(record.mobile) > 10:
    #             raise ValidationError(_("The mobile number must be exactly 10 digits."))

    # existing_partners = self.search([('mobile', '=', record.mobile), ('id', '!=', record.id)])
    # if existing_partners:
    #     partner_names = ', '.join(existing_partners.mapped('name'))
    #     record.message_post(
    #         body=_("The mobile number %s already exists in the following contacts: %s.") % (
    #         record.mobile, partner_names)
    #     )
