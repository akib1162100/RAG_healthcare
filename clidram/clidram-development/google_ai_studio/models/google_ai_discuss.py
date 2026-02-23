# addons/discuss_gemini_integration/models/mail_message_old.py

import google.generativeai as genai
from odoo import api, models, _
import logging
from odoo.tools import html2plaintext
from markupsafe import Markup
import re

_logger = logging.getLogger(__name__)

# Define the trigger phrase for the bot
GEMINI_TRIGGER = "@gemini"


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        # First, create the original messages
        messages = super().create(vals_list)

        # Get the system parameter to check if the feature is enabled
        # We check this once outside the loop for efficiency
        params = self.env['ir.config_parameter'].sudo()
        is_enabled = params.get_param('discuss_gemini_integration.enable_gemini')

        # If the feature is disabled, do nothing and return
        if not is_enabled:
            return messages

        for message in messages:
            # Check if the message is from a user, has a body, and starts with the trigger
            clean_text = re.sub('<[^<]+?>', '',  message.body).strip()
            if message.author_id and message.body and clean_text.startswith(GEMINI_TRIGGER):

                try:
                    with self.env.registry.cursor() as new_cr:
                        new_env = self.with_env(self.env(cr=new_cr))
                        new_env._process_gemini_prompt(message)
                except Exception as e:
                    _logger.error("Error processing Gemini prompt: %s", e)
                    channel = message.mail_channel_ids and message.mail_channel_ids[0]
                    if channel:
                        gemini_partner_id = self.env.ref('discuss_gemini_integration.gemini_partner').id
                        channel.message_post(
                            body="Sorry, I encountered an error. Please check the server logs.",
                            author_id=gemini_partner_id,
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment',
                        )

        return messages

    def _process_gemini_prompt(self, message):
        """
        Processes a message to call the Gemini API and post a response.
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('discuss_gemini_integration.gemini_api_key')

        # CORRECTED: The field is named channel_ids
        channel = message.channel_ids and message.channel_ids[0]
        if not channel:
            return

        gemini_partner_id = self.env.ref('discuss_gemini_integration.gemini_partner').id

        if not api_key:
            error_message = "Gemini API Key is not configured. Please set it in Settings > General Settings."
            _logger.warning(error_message)
            channel.message_post(
                body=error_message, author_id=gemini_partner_id, message_type='comment', subtype_xmlid='mail.mt_comment'
            )
            return

        # CORRECTED: Convert message body from HTML to plain text first
        message_text = html2plaintext(message.body).strip()

        # Now, get the prompt from the clean text
        prompt = message_text.replace(GEMINI_TRIGGER, "", 1).strip()

        if not prompt:
            channel.message_post(
                body="You mentioned me, but didn't ask a question!",
                author_id=gemini_partner_id, message_type='comment', subtype_xmlid='mail.mt_comment'
            )
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            # Send the clean prompt to the API
            response = model.generate_content(prompt)

            channel.message_post(
                body=response.text, author_id=gemini_partner_id, message_type='comment', subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.error("Error calling Gemini API: %s", e)
            error_text = f"An error occurred while communicating with Gemini: {e}"
            channel.message_post(
                body=error_text, author_id=gemini_partner_id, message_type='comment', subtype_xmlid='mail.mt_comment'
            )