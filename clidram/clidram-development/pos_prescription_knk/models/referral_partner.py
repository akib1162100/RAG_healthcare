from odoo import models, fields


class ReferralPartner(models.Model):
    _name = "referral.partner"

    name = fields.Char(required=True, copy=False)
    email = fields.Char()
    phone = fields.Char(required=True)
    image_1920 = fields.Binary()
    age = fields.Char()
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
