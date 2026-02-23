# addons/discuss_gemini_integration/models/mail_channel.py
import google.generativeai as genai
from odoo import api, models, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    @api.model
    def _is_gemini_integration_enabled(self):
        """Check if Gemini integration is globally enabled"""
        return self.env['ir.config_parameter'].sudo().get_param('discuss_gemini_integration.enable_gemini')

    @api.model
    def _get_gemini_api_key(self):
        """Retrieve Gemini API key from system parameters"""
        return self.env['ir.config_parameter'].sudo().get_param('discuss_gemini_integration.gemini_api_key')

    def _is_gemini_channel(self, author_id):
        """Check if current channel is a Gemini channel and message is from human"""
        gemini_partner = self.env.ref('discuss_gemini_integration.gemini_partner', raise_if_not_found=False)
        return (
                'Gemini' in self.name and
                gemini_partner and
                author_id != gemini_partner.id
        )

    def _post_gemini_response(self, response_text, error=None):
        """Post Gemini's response or error message to the channel"""
        gemini_user = self.env.ref('discuss_gemini_integration.gemini_user', raise_if_not_found=False)
        if not gemini_user:
            _logger.error("Gemini user not found in system")
            return

        message_body = error or response_text
        try:
            self.with_user(gemini_user).message_post(
                body=message_body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.error("Failed to post Gemini response: %s", e)

    def _get_gemini_response(self, prompt):
        """Fetch response from Gemini API"""
        api_key = self._get_gemini_api_key()
        if not api_key:
            raise UserError(_("Gemini API key is not configured in system parameters"))

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            _logger.error("Gemini API Error: %s", e)
            raise UserError(_("Error contacting Gemini API: %s") % str(e))

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        """
        Override notification method to add AI responses in Gemini channels
        """
        # Execute original notification logic first
        result = super()._notify_thread(message, msg_vals=msg_vals, **kwargs)

        # Skip if Gemini integration is disabled
        if not self._is_gemini_integration_enabled():
            return result

        # Skip if not a Gemini channel or message is from AI
        author_id = msg_vals.get('author_id')
        if not self._is_gemini_channel(author_id):
            return result

        # Extract and validate prompt
        prompt = html2plaintext(msg_vals.get('body', '')).strip()
        if not prompt:
            return result

        # Process Gemini request
        try:
            response = self._get_gemini_response(prompt)
            self._post_gemini_response(response)
        except UserError as e:
            self._post_gemini_response(error=str(e))
        except Exception as e:
            error_msg = _("An unexpected error occurred with Gemini: %s") % str(e)
            self._post_gemini_response(error=error_msg)
            _logger.error("Gemini integration error: %s", e)

        return result