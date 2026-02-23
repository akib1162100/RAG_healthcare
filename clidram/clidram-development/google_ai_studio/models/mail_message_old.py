# models/mail_message_old.py
import google.generativeai as genai
from odoo import api, models, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
import logging
import re
from markupsafe import Markup

_logger = logging.getLogger(__name__)

# Constants
GEMINI_TRIGGER = "@gemma"
ERROR_MESSAGES = {
    "no_api_key": "Gemma API Key is not configured. Please set it in Settings.",
    "empty_prompt": "You mentioned me, but didn't ask a question!",
    "processing_error": "Sorry, I encountered an error. Please check the server logs.",
    "api_error": "An error occurred while communicating with Gemma: {}",
}

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def _is_gemini_enabled(self):
        """Check if Gemini integration is enabled"""
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

    @api.model
    def _is_gemini_trigger(self, message_body):
        """Check if message contains the Gemini trigger phrase"""
        clean_text = re.sub('<[^<]+?>', '', message_body).strip()
        return clean_text.startswith(GEMINI_TRIGGER)

    @api.model
    def _extract_prompt(self, message_body):
        """Extract the prompt from the message body"""
        clean_text = html2plaintext(message_body).strip()
        return clean_text.replace(GEMINI_TRIGGER, "", 1).strip()

    @api.model
    def _post_error_message(self, channel, error_key, error_param=None):
        """Post an error message to the channel as the Gemini partner"""
        gemini_partner = self._get_gemini_partner()
        if not channel or not gemini_partner:
            return
        error_text = ERROR_MESSAGES[error_key]
        if error_param:
            error_text = error_text.format(error_param)
        channel.message_post(
            body=error_text,
            author_id=gemini_partner.id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )

    @api.model
    def _get_message_channel(self, message):
        """Get the channel associated with a message"""
        # Check if message is directly linked to a channel
        if message.model == 'mail.channel' and message.res_id:
            return self.env['mail.channel'].browse(message.res_id)
        # Check if message has channel followers
        if hasattr(message, 'channel_ids') and message.channel_ids:
            return message.channel_ids[0]
        # For other cases, try to find related channels
        if message.model and message.res_id:
            # Check if the document has any channel followers
            document = self.env[message.model].browse(message.res_id)
            if hasattr(document, 'channel_ids') and document.channel_ids:
                return document.channel_ids[0]
        return None

    @api.model
    def _get_conversation_context(self, channel, current_message_id):
        """
        Retrieve and format conversation context from previous messages
        """
        max_messages = self._get_max_context_messages()
        # Get previous messages in the channel, excluding system messages and bot messages
        domain = [
            ('model', '=', 'mail.channel'),
            ('res_id', '=', channel.id),
            ('id', '!=', current_message_id),
            ('message_type', '=', 'comment'),
        ]
        # Exclude messages from Gemini bot
        gemini_partner = self._get_gemini_partner()
        will_add_gemini = self.env['ir.config_parameter'].sudo().get_param('discuss_gemini_integration.is_gemini_response_added')
        if gemini_partner and not will_add_gemini:
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

    def _clean_markdown(self, text):
        """Convert markdown to HTML for better display"""
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
        return text

    def _format_llm_text_to_html(self, raw_text):
        """Format LLM response text to HTML"""
        lines = raw_text.splitlines()
        html_parts = []
        list_open = False
        for line in lines:
            line = line.strip()
            if not line:
                if list_open:
                    html_parts.append("</ul>")
                    list_open = False
                html_parts.append("<br/>")
                continue
            if line.startswith(("*", "-")):
                if not list_open:
                    html_parts.append("<ul>")
                    list_open = True
                html_parts.append(f"<li>{line[1:].strip()}</li>")
            else:
                if list_open:
                    html_parts.append("</ul>")
                    list_open = False
                html_parts.append(f"<p>{line}</p>")
        if list_open:
            html_parts.append("</ul>")
        return "".join(html_parts)

    @api.model
    def _process_gemini_prompt(self, message_id):
        """Process a Gemini prompt and post the response as the Gemini partner"""
        # Fetch the message in the current environment
        message = self.browse(message_id)
        if not message.exists():
            return

        # Get the channel
        channel = self._get_message_channel(message)
        if not channel:
            _logger.info("Message %s is not associated with any channel, skipping Gemini processing", message_id)
            return

        # Get Gemini partner for posting responses
        gemini_partner = self._get_gemini_partner()
        if not gemini_partner:
            _logger.warning("Gemini partner is not configured. Please set it in Settings.")
            return

        # Check API key
        api_key = self._get_gemini_api_key()
        if not api_key:
            self._post_error_message(channel, "no_api_key")
            return

        # Extract and validate prompt
        prompt = self._extract_prompt(message.body)
        if not prompt:
            self._post_error_message(channel, "empty_prompt")
            return

        # Get conversation context
        try:
            context = self._get_conversation_context(channel, message.id)
        except Exception as e:
            _logger.warning("Failed to retrieve conversation context: %s", e)
            context = None

        # Get Gemini response
        try:
            genai.configure(api_key=api_key)
            model_name = self._get_gemini_model()
            # model = genai.GenerativeModel(model_name)
            model = genai.GenerativeModel('gemma-3-27b-it')

            # Format prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"""Previous conversation:
{context}

Current question: {prompt}"""

            response = model.generate_content(full_prompt)
            raw_text = "".join([c.text for c in response.candidates[0].content.parts if c.text])

            # Clean and format the response
            clean_text = self._clean_markdown(raw_text)
            formatted_html = self._format_llm_text_to_html(clean_text)

            # Post response as the Gemini partner
            channel.with_user(gemini_partner.user_ids[0] if gemini_partner.user_ids else self.env.user).message_post(
                body=formatted_html,
                author_id=gemini_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.error("Error calling Gemini API: %s", e)
            self._post_error_message(channel, "api_error", str(e))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to handle Gemini triggers"""
        # Create original messages first
        messages = super().create(vals_list)

        # Skip if Gemini integration is disabled
        if not self._is_gemini_enabled():
            return messages

        # Process each message
        for message in messages:
            # Check if message meets criteria for Gemini processing
            if (message.author_id and
                    message.body and
                    self._is_gemini_trigger(message.body)):
                try:
                    # Use a new cursor to avoid long transactions
                    with self.env.registry.cursor() as new_cr:
                        new_env = self.env(cr=new_cr)
                        self._process_gemini_prompt(message.id)
                except Exception as e:
                    _logger.error("Error processing Gemini prompt: %s", e)
                    channel = self._get_message_channel(message)
                    self._post_error_message(channel, "processing_error")
        return messages