import random
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StoreWhatsAappOTP(models.Model):
    _name = 'store.whatsapp.otp'
    _description = "Store Whatsapp OTP"

    def _get_default_partner(self):
        partner = self.env['res.partner'].sudo().search([('is_default_whatsapp_contact', '=', True)], limit=1)
        if partner:
            return partner
        else:
            return False

    signup_phone = fields.Char(string="Number")
    signup_otp = fields.Char(string="OTP")
    date_time = fields.Datetime(string="Datetime")
    is_verified = fields.Boolean(string="Is Verified", default=False)
    partner_id = fields.Many2one("res.partner", string="Patient", default=_get_default_partner)

    def action_send_otp(self):
        self.ensure_one()
        if not self.signup_phone:
            raise UserError(_("Partner must have a mobile/WhatsApp number."))

        template = self.env.company.signup_otp_template_id
        if not template:
            raise UserError(_("Please configure WhatsApp Template in Company Settings."))

        ctx = {
            'default_partner_id': self.partner_id.id,
            'default_model': self._name,
            'default_res_id': self.id,
            'default_template_id': template.id,
            'default_is_otp_message': True,
            'default_otp_code': self.signup_otp,
            'default_provider_id': template.provider_id.id
        }

        wizard = self.env['wa.compose.message'].with_context(ctx).sudo().create({
            'template_id': template.id,
            'partner_id': self.partner_id.id,
            'provider_id': template.provider_id.id
        })

        wizard.body = template._render_field('body_html', [self.id], compute_lang=True)[self.id]

        wizard.send_whatsapp_message()


    def validate_otp(self, phone, otp):
        """Validate OTP for phone"""
        otp_record = self.sudo().search([
            ('signup_phone', '=', phone),
            ('signup_otp', '=', otp),
        ], limit=1, order="date_time desc")

        if not otp_record:
            return False

        # Expire after 5 minutes
        if otp_record.date_time < (datetime.now() - timedelta(minutes=5)):
            return False

        otp_record.is_verified = True
        return True
