# controllers/main.py
from odoo import http
from odoo.http import request
import random
from odoo import fields


class SignupOtpController(http.Controller):

    @http.route('/send/otp', type='json', auth='public', methods=['POST'], csrf=False)
    def send_otp(self, **kwargs):
        phone = kwargs.get('phone')
        if not phone:
            return {"success": False, "error": "Phone number is required."}

        # Generate OTP (for demo purposes only)
        otp = str(random.randint(100000, 999999))  # 6-digit OTP

        # Verify OTP before allowing signup
        otp_model = request.env['store.whatsapp.otp'].sudo()

        partner = request.env['res.partner'].sudo().search([('is_default_whatsapp_contact', '=', True)], limit=1)
        if partner:
            partner.sudo().write({
                'mobile': phone,
                'phone': phone
            })

        if not otp_model.validate_otp(phone, otp):
            record = otp_model.create({
                'signup_phone': phone,
                'signup_otp': otp,
                'date_time': fields.Datetime.now(),
                'is_verified': False,
                'partner_id': partner.id
            })
            record.action_send_otp()

        # In real case: send OTP via SMS/WhatsApp here
        return {"success": True, "message": f"OTP sent to {phone}"}

    @http.route('/verify/otp', type='json', auth='public', methods=['POST'], csrf=False)
    def verify_otp(self, **kwargs):
        phone = kwargs.get('phone')
        otp = kwargs.get('otp')
        otp_model = request.env['store.whatsapp.otp'].sudo()

        if not otp or not phone:
            return {"success": False, "error": "Phone and OTP are required."}

        if not otp_model.validate_otp(phone, otp):
            return {"success": False, "error": "Invalid OTP or phone number."}
        else:
            return {"success": True, "message": "OTP verified successfully!"}
