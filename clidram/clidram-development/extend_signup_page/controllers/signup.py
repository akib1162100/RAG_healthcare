from datetime import datetime
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request, route
from odoo import fields
from odoo.fields import Date


class WebsiteSignupExtended(AuthSignupHome):

    @route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        phone_code = kw.get('phone_code', '').strip()
        phone_number = kw.get('phone', '').strip()

        # Combine phone code with phone number
        full_phone = phone_number
        if phone_code and phone_number:
            full_phone = f"+{phone_code} {phone_number}"
        elif not phone_code and phone_number:
            country_id = int(kw.get('country_id')) if kw.get('country_id') else False
            if country_id:
                country = request.env['res.country'].sudo().browse(country_id)
                if country.phone_code:
                    full_phone = f"+{country.phone_code} {phone_number}"

        # Call the original signup logic
        response = super().web_auth_signup(*args, **kw)

        # Post-signup: update partner info
        user = request.env['res.users'].sudo().search([('login', '=', kw.get('login'))], limit=1)

        if user:
            sequence = self.generate_sequence(request, user.company_id.id)
            user.partner_id.write({
                'seq': sequence,
                'date_of_birth': kw.get('date_of_birth'),
                'gender': kw.get('gender'),
                'partner_type': kw.get('partner_type') or 'patient',
                'mobile': full_phone,  # Store full phone with country code
                'street': kw.get('street'),
                'city': kw.get('city'),
                'zip': kw.get('zip'),
                'state_id': int(kw.get('state_id')) if kw.get('state_id') else False,
                'country_id': int(kw.get('country_id')) if kw.get('country_id') else False,
                'company_id': user.company_id.id,
            })
        return response

    def generate_sequence(self, current_request, company_id):
        year = fields.Date.today().year
        month = fields.Date.today().month
        total_patient = current_request.env['res.partner'].sudo().search_count(
            [('company_id', '=', company_id), ('partner_type', '=', 'patient')]
        )
        new_count = total_patient + 1
        seq = current_request.env['ir.sequence'].sudo().next_by_code('patient.id.knk') or ('New')
        sequence = f"{year:04d}{month:02d}{seq}{company_id}{new_count:03d}"
        return sequence

    def get_auth_signup_qcontext(self):
        """Extend context for signup form."""
        qcontext = super().get_auth_signup_qcontext()

        # Load country and state data
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        default_country = request.env['res.country'].sudo().search([('code', '=', 'IN')], limit=1)
        default_state = request.env['res.country.state'].sudo().search([('country_id', '=', default_country.id)],
                                                                       limit=1)

        qcontext.update({
            'countries': countries,
            'states': states,
            'default_country_id': default_country.id if default_country else None,
            'default_state_id': default_state.id if default_state else None,
        })
        return qcontext