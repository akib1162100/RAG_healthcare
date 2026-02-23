# models/mail_message.py
import base64
import os
# from google import genai
import google.generativeai as genai
from google.genai import types
import PIL.Image
from io import BytesIO
from odoo import api, models, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
import logging
import re
import pdfplumber
import docx2txt
import pandas as pd
from markupsafe import Markup

_logger = logging.getLogger(__name__)

# Constants
GEMINI_TRIGGER = "@gemma"
ERROR_MESSAGES = {
    "no_api_key": "Gemma API Key is not configured. Please set it in Settings.",
    "empty_prompt": "You mentioned me, but didn't ask a question!",
    "processing_error": "Sorry, I encountered an error. Please check the server logs.",
    "api_error": "An error occurred while communicating with Gemma: {}",
    "unsupported_attachment": "Sorry, I can't process this type of attachment: {}",
    "attachment_error": "Error processing attachment: {}",
}

# Supported attachment types
SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
SUPPORTED_DOCUMENT_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv'
]


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
            'discuss_gemini_integration.gemini_model', default='gemini-1.5-flash')

    @api.model
    def _get_gemini_vision_model(self):
        """Get the selected Gemini vision model"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'discuss_gemini_integration.gemini_vision_model', default='gemini-1.5-flash')

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
        will_add_gemini = self.env['ir.config_parameter'].sudo().get_param(
            'discuss_gemini_integration.is_gemini_response_added')
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
    def _extract_image_bytes(self, attachment):
        """Extract image bytes from attachment for the Google API"""
        try:
            # Decode the base64 content to get raw bytes
            image_bytes = base64.b64decode(attachment.datas)

            # Return the image bytes and mime type for the Google API
            return {
                'data': image_bytes,
                'mime_type': attachment.mimetype,
                'name': attachment.name
            }
        except Exception as e:
            _logger.error("Error processing image attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process image: {str(e)}")

    @api.model
    def _extract_pdf_bytes(self, attachment):
        """Extract PDF bytes from attachment for the Google API"""
        try:
            # Decode the base64 content to get raw bytes
            pdf_bytes = base64.b64decode(attachment.datas)

            # Return the PDF bytes and mime type for the Google API
            return {
                'data': pdf_bytes,
                'mime_type': attachment.mimetype,
                'name': attachment.name
            }
        except Exception as e:
            _logger.error("Error processing PDF attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process PDF: {str(e)}")

    @api.model
    def _extract_pdf_content(self, attachment):
        """Extract text content from PDF attachment for text inclusion"""
        try:
            pdf_data = base64.b64decode(attachment.datas)
            text_content = ""

            with pdfplumber.open(BytesIO(pdf_data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            return text_content.strip()
        except Exception as e:
            _logger.error("Error processing PDF attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process PDF: {str(e)}")

    @api.model
    def _extract_docx_content(self, attachment):
        """Extract text content from DOCX attachment"""
        try:
            docx_data = base64.b64decode(attachment.datas)
            text = docx2txt.process(BytesIO(docx_data))
            return text.strip()
        except Exception as e:
            _logger.error("Error processing DOCX attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process DOCX: {str(e)}")

    @api.model
    def _extract_text_content(self, attachment):
        """Extract text content from plain text attachment"""
        try:
            text_data = base64.b64decode(attachment.datas)
            return text_data.decode('utf-8').strip()
        except Exception as e:
            _logger.error("Error processing text attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process text file: {str(e)}")

    @api.model
    def _extract_excel_content(self, attachment):
        """Extract content from Excel attachment"""
        try:
            excel_data = base64.b64decode(attachment.datas)
            # Read Excel file
            df = pd.read_excel(BytesIO(excel_data))
            # Convert to markdown table format
            return df.to_markdown(index=False)
        except Exception as e:
            _logger.error("Error processing Excel attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process Excel file: {str(e)}")

    @api.model
    def _extract_csv_content(self, attachment):
        """Extract content from CSV attachment"""
        try:
            csv_data = base64.b64decode(attachment.datas)
            # Read CSV file
            df = pd.read_csv(BytesIO(csv_data))
            # Convert to markdown table format
            return df.to_markdown(index=False)
        except Exception as e:
            _logger.error("Error processing CSV attachment %s: %s", attachment.name, e)
            raise Exception(f"Failed to process CSV file: {str(e)}")

    @api.model
    def _extract_attachment_content(self, attachment):
        """Extract content from attachment based on its type"""
        if not attachment.datas:
            return None

        # Process based on mimetype
        if attachment.mimetype in SUPPORTED_IMAGE_TYPES:
            return {
                'type': 'image',
                'data': self._extract_image_bytes(attachment),
                'name': attachment.name
            }
        elif attachment.mimetype == 'application/pdf':
            # Return both the raw bytes and the extracted text
            return {
                'type': 'pdf',
                'bytes': self._extract_pdf_bytes(attachment),
                'text': self._extract_pdf_content(attachment),
                'name': attachment.name
            }
        elif attachment.mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return {
                'type': 'text',
                'data': self._extract_docx_content(attachment),
                'name': attachment.name
            }
        elif attachment.mimetype == 'text/plain':
            return {
                'type': 'text',
                'data': self._extract_text_content(attachment),
                'name': attachment.name
            }
        elif attachment.mimetype in ['application/vnd.ms-excel',
                                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return {
                'type': 'text',
                'data': self._extract_excel_content(attachment),
                'name': attachment.name
            }
        elif attachment.mimetype == 'text/csv':
            return {
                'type': 'text',
                'data': self._extract_csv_content(attachment),
                'name': attachment.name
            }
        else:
            raise Exception(f"Unsupported file type: {attachment.mimetype}")

    @api.model
    def _build_gemini_content(self, prompt, attachments=None, context=None):
        """Build a Gemini API content object with text and byte parts"""
        # Format prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"""Previous conversation:
{context}

Current question: {prompt}"""

        # Start with a text part
        parts = [types.Part.from_text(text=full_prompt)]

        # Add attachment information to the prompt for non-image/non-pdf attachments
        # and add byte parts for image and PDF attachments
        if attachments:
            attachment_info = []

            for att in attachments:
                if att['type'] == 'text':
                    # Include text content directly in the prompt
                    attachment_info.append(f"Attached document '{att['name']}':\n{att['data']}")
                elif att['type'] == 'image':
                    # Add image as a byte part
                    img_data = att['data']
                    parts.append(
                        types.Part.from_bytes(
                            data=img_data['data'],
                            mime_type=img_data['mime_type']
                        )
                    )
                    # Also add a reference in the text
                    attachment_info.append(f"Attached image: '{att['name']}'")
                elif att['type'] == 'pdf':
                    # Add PDF as a byte part
                    pdf_data = att['bytes']
                    parts.append(
                        types.Part.from_bytes(
                            data=pdf_data['data'],
                            mime_type=pdf_data['mime_type']
                        )
                    )
                    # Also add extracted text in the prompt for context
                    if att['text']:
                        attachment_info.append(f"Attached PDF '{att['name']}' with content:\n{att['text']}")
                    else:
                        attachment_info.append(f"Attached PDF: '{att['name']}'")

            # Update the text part to include attachment information
            if attachment_info:
                parts[0] = types.Part.from_text(text=full_prompt + "\n\n" + "\n\n".join(attachment_info))

        # Create the content object
        content = types.Content(
            role="user",
            parts=parts,
        )

        return content

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

        # Process attachments
        attachments = []
        if hasattr(message, 'attachment_ids') and message.attachment_ids:
            for attachment in message.attachment_ids:
                try:
                    attachment_content = self._extract_attachment_content(attachment)
                    if attachment_content:
                        attachments.append(attachment_content)
                except Exception as e:
                    _logger.error("Error processing attachment %s: %s", attachment.name, e)
                    self._post_error_message(channel, "attachment_error", f"{attachment.name}: {str(e)}")

        # Get Gemini response using the new API approach
        try:
            # Create client
            client = genai.Client(api_key=api_key)

            # Determine which model to use based on attachments
            has_image_or_pdf = any(att['type'] in ['image', 'pdf'] for att in attachments)
            # model_name = self._get_gemini_vision_model() if has_image_or_pdf else self._get_gemini_model()
            model_name = "gemma-3-27b-it"

            # Log the model being used for debugging
            _logger.info(f"Using Gemini model: {model_name}")

            # Build the content with text and byte parts
            content = self._build_gemini_content(prompt, attachments, context)

            # Generate content config without thinking_config to avoid errors
            generate_content_config = types.GenerateContentConfig()

            # Generate response using streaming
            response_text = ""
            for chunk in client.models.generate_content_stream(
                    model=model_name,
                    contents=[content],
                    config=generate_content_config,
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text

            # Clean and format the response
            clean_text = self._clean_markdown(response_text)
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