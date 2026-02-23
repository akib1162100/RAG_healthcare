# models/mail_channel.py
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

    @api.model
    def _get_gemini_model(self):
        """Get the selected Gemini model"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'discuss_gemini_integration.gemini_model', default='gemini-pro')

    @api.model
    def _get_max_context_messages(self):
        """Get maximum context messages from system parameters"""
        default = 5
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'discuss_gemini_integration.max_context_messages', str(default)))

    @api.model
    def _get_gemini_partner(self):
        """Get the Gemini partner record from system parameters"""
        partner_id = self.env['ir.config_parameter'].sudo().get_param('discuss_gemini_integration.gemini_partner_id')
        if partner_id:
            return self.env['res.partner'].browse(int(partner_id))
        return None

    def _is_gemini_channel(self, author_id):
        """Check if current channel is a Gemini channel and message is from human"""
        gemini_partner = self._get_gemini_partner()
        return (
                'Gemini' in self.name and
                gemini_partner and
                author_id != gemini_partner.id
        )

    def _post_gemini_response(self, response_text, error=None):
        """Post Gemini's response or error message to the channel as the Gemini partner"""
        gemini_partner = self._get_gemini_partner()
        if not gemini_partner:
            _logger.error("Gemini partner is not configured. Please set it in Settings.")
            return

        message_body = error or response_text
        try:
            # Post as the Gemini partner
            self.with_user(gemini_partner.user_ids[0] if gemini_partner.user_ids else self.env.user).message_post(
                body=message_body,
                author_id=gemini_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.error("Failed to post Gemini response: %s", e)

    def _get_conversation_context(self, current_message_id):
        """
        Retrieve and format conversation context from previous messages
        """
        max_messages = self._get_max_context_messages()

        # Get previous messages in the channel, excluding system messages and bot messages
        domain = [
            ('model', '=', 'mail.channel'),
            ('res_id', '=', self.id),
            ('id', '!=', current_message_id),
            ('message_type', '=', 'comment'),
        ]

        # Exclude messages from Gemini bot
        gemini_partner = self._get_gemini_partner()
        if gemini_partner:
            domain.append(('author_id', '!=', gemini_partner.id))

        # Get messages in chronological order (oldest first)
        messages = self.env['mail.message'].sudo().search(
            domain,
            order='id asc',
            limit=max_messages
        )

        # Format messages for context
        context_parts = []
        for msg in messages:
            author_name = msg.author_id.name if msg.author_id else "Unknown"
            body = html2plaintext(msg.body).strip()
            if body:  # Only include non-empty messages
                context_parts.append(f"{author_name}: {body}")

        return "\n".join(context_parts)

    def _format_prompt_with_context(self, prompt, context):
        """
        Format the prompt with conversation context
        """
        if not context:
            return prompt

        return f"""Previous conversation:
{context}

Current question: {prompt}"""

    def _get_gemini_response(self, prompt, context=None):
        """
        Fetch response from Gemini API with optional context
        """
        api_key = self._get_gemini_api_key()
        if not api_key:
            raise UserError(_("Gemini API key is not configured in system parameters"))

        # Format prompt with context
        full_prompt = self._format_prompt_with_context(prompt, context)

        try:
            genai.configure(api_key=api_key)
            model_name = self._get_gemini_model()
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
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

        # Get conversation context
        try:
            context = self._get_conversation_context(message.id)
        except Exception as e:
            _logger.warning("Failed to retrieve conversation context: %s", e)
            context = None

        # Get Gemini partner for posting responses
        gemini_partner = self._get_gemini_partner()
        if not gemini_partner:
            _logger.warning("Gemini partner is not configured. Please set it in Settings.")
            return result

        # Process Gemini request with context
        try:
            response = self._get_gemini_response(prompt, context)
            self._post_gemini_response(response)
        except UserError as e:
            self._post_gemini_response(error=str(e))
        except Exception as e:
            error_msg = _("An unexpected error occurred with Gemini: %s") % str(e)
            self._post_gemini_response(error=error_msg)
            _logger.error("Gemini integration error: %s", e)

        return result