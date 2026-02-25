import logging
import threading
import re
import time
from odoo import api, models, _
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class MailChannel(models.Model):
    _inherit = 'mail.channel'

    @api.model
    def _get_rag_partner(self):
        """Retrieve the configured RAG Bot partner from the database."""
        rag_partner_id = self.env['ir.config_parameter'].sudo().get_param('rag_controller.bot_partner_id')
        if rag_partner_id:
            try:
                # Value stored in ir.config_parameter might be 'res.partner,ID'
                partner_id = int(rag_partner_id.split(',')[1] if ',' in str(rag_partner_id) else rag_partner_id)
                return self.env['res.partner'].browse(partner_id)
            except Exception as e:
                _logger.error(f"Failed to parse RAG Partner ID '{rag_partner_id}': {e}")
        
        # Fallback to direct ref search if config param fails
        rag_partner = self.env.ref('rag_controller.partner_rag_bot', raise_if_not_found=False)
        return rag_partner

    def _is_rag_bot_channel(self, author_id):
        """Check if the RAG bot is active in this channel and if the current message is from a human."""
        rag_partner = self._get_rag_partner()
        if not rag_partner:
            return False
            
        # Is the bot deeply involved in this channel (e.g., DM), and is the author NOT the bot itself?
        is_member = rag_partner.id in self.channel_partner_ids.ids
        is_human = author_id != rag_partner.id
        
        return is_member and is_human

    def _clean_markdown(self, text):
        """Converts basic markdown bold and italic syntaxes to HTML tags."""
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
        return text

    def _format_llm_text_to_html(self, raw_text):
        """Converts markdown lists and paragraphs into formatted HTML."""
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

    def _post_rag_response(self, response_text, is_error=False):
        """Post the LLM's response or an error message back into the Odoo Discuss channel as the RAG Bot."""
        rag_partner = self._get_rag_partner()
        if not rag_partner:
            _logger.error("Cannot post response: RAG partner not found.")
            return

        body_html = f"<div style='color: {'red' if is_error else 'inherit'};'>{response_text}</div>"
        
        try:
            # Safely post the message into the channel as sudo to prevent background thread permission errors
            self.sudo().message_post(
                body=body_html,
                author_id=rag_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            _logger.info(f"Successfully posted RAG response to channel {self.id}")
        except Exception as e:
            _logger.error("Failed to post RAG bot response: %s", e)

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        """
        Core Odoo mail interceptor:
        Monitors every message sent in the channel. If the criteria match, captures the user's message
        and kicks off a background thread to ask the RAG AI to respond.
        """
        # 1. Execute the standard Odoo notification logic first
        result = super()._notify_thread(message, msg_vals=msg_vals, **kwargs)

        # 2. Extract author constraints
        author_id = msg_vals.get('author_id')
        
        # 3. Check if the bot should care about this message
        if not self._is_rag_bot_channel(author_id):
            return result

        # 4. Extract the human's plaintext prompt from the HTML body
        prompt = html2plaintext(msg_vals.get('body', '')).strip()
        if not prompt:
            return result

        # 5. Extract patient_seq if explicitly written (e.g. "patient_id:20250600042005" or "patient_id: 20250600042005")
        patient_seq = None
        patient_id_match = re.search(r'patient_id:\s*(\S+)', prompt, re.IGNORECASE)
        if patient_id_match:
            patient_seq = patient_id_match.group(1)
            # Remove the full patient_id:xxx pattern from the prompt
            prompt = re.sub(r'patient_id:\s*\S+', '', prompt, flags=re.IGNORECASE).strip()

        # 5b. Strip the bot mention text "RAG Medical Assistant" from the prompt
        prompt = re.sub(r'RAG\s+Medical\s+Assistant', '', prompt, flags=re.IGNORECASE).strip()

        # 6. Spin up a background thread to fetch the LLM response without freezing the Odoo UI
        # We pass self.id to easily reconstruct the channel in the new thread
        threading.Thread(
            target=self._async_call_rag_api,
            args=(prompt, self.id, patient_seq)
        ).start()

        return result

    @api.model
    def _async_call_rag_api(self, prompt, channel_id, patient_seq=None):
        """
        Background thread execution with retry logic for database concurrency.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Reconstruct environment context for the background thread
                with self.env.registry.cursor() as cr:
                    env = api.Environment(cr, self.env.uid, self.env.context)
                    rag_client = env['rag.api.client']
                    channel = env['mail.channel'].browse(channel_id)
                    
                    # The session_id maps cleanly to the unique channel ID for context tracking
                    session_id = f"odoo_channel_{channel_id}"
                    
                    # Proxy the request to the FastAPI application
                    result = rag_client.chat(
                        prompt=prompt,
                        session_id=session_id,
                        patient_seq=patient_seq
                    )
                    
                    # The FastAPI backend directly returns the RAGQueryResponse dictionary
                    if result and 'response' in result:
                        response_text = result.get('response', '')
                        clean_text = channel._clean_markdown(response_text)
                        formatted_response = channel._format_llm_text_to_html(clean_text)
                        channel._post_rag_response(formatted_response)
                    elif result and result.get('status') == 'success':
                        # Fallback for nested payloads if legacy routing was involved
                        response_text = result['data'].get('response', '')
                        clean_text = channel._clean_markdown(response_text)
                        formatted_response = channel._format_llm_text_to_html(clean_text)
                        channel._post_rag_response(formatted_response)
                    else:
                        error_msg = result.get('message', 'Unknown error connecting to RAG system.')
                        channel._post_rag_response(f"API Error: {error_msg}", is_error=True)
                    
                    env.cr.commit()  # Ensure the background thread saves the message_post to the DB!
                    return # Exit successfully if commit succeeds
                        
            except Exception as e:
                # If it's a serialization error, wait slightly and retry
                if "could not serialize access" in str(e).lower() and attempt < max_retries - 1:
                    _logger.warning(f"Concurrent update detected (attempt {attempt+1}/{max_retries}), retrying...: {e}")
                    time.sleep(1)
                    continue
                
                _logger.error(f"Error in async RAG execution (attempt {attempt+1}): {e}")
                
                # Final attempt error handling
                if attempt == max_retries - 1:
                    try:
                        with self.env.registry.cursor() as cr:
                            env = api.Environment(cr, self.env.uid, self.env.context)
                            channel = env['mail.channel'].browse(channel_id)
                            channel._post_rag_response(f"System Exception: {str(e)}", is_error=True)
                            env.cr.commit()
                    except Exception as fatal_e:
                        _logger.error(f"Fatal error posting exception to channel: {fatal_e}")
