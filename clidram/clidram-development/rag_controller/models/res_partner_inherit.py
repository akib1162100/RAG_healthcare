from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # wk_appointment related OTP templates
    new_appointment_template_id = fields.Many2one('wa.template', string='New Appointment OTP Template', tracking=True)
    approved_appointment_template_id = fields.Many2one('wa.template', string='Approved Appointment OTP Template', tracking=True)

    # pos_prescription_knk related WhatsApp & OTP templates
    whatsapp_template_id = fields.Many2one('wa.template', string='WhatsApp Template', tracking=True)
    whatsapp_otp_template_id = fields.Many2one('wa.template', string='WhatsApp OTP Template', tracking=True)
    signup_otp_template_id = fields.Many2one('wa.template', string='Signup OTP Template', tracking=True)
