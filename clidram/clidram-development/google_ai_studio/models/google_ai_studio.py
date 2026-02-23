from odoo import models, fields, api
import os
import google.generativeai as genai
from google.generativeai import types
import re

class MedicalConsultation(models.Model):
    _name = 'medical.consultation'
    _description = 'Medical Consultation with LLM'

    user_input = fields.Text(string='Question', required=True)
    llm_response = fields.Html(string='Response', readonly=True, sanitize=False)
    consultation_date = fields.Date(string='Consultation Date', default=fields.Date.today)
    attachment = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="File Name")
    name = fields.Char(string="Name", default='New', readonly=True, copy=False)
    history_ids = fields.One2many('medical.consultation.history', 'consultation_id',
                                  string="History")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('medical.consultation')
        return super(MedicalConsultation, self).create(vals_list)

    def _clean_markdown(self, text):
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
        return text

    def _format_llm_text_to_html(self, raw_text):
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

    # def _call_llm(self):
    #     try:
    #         api_key = 'AIzaSyA9sRlf4FVIwaoGX6E9Aaqab-D2jWoFMHg'
    #         if not api_key:
    #             self.llm_response = "Error: GEMINI_API_KEY environment variable not set."
    #             return
    #
    #         client = genai.Client(
    #             api_key=api_key,
    #         )
    #
    #         model_name = "gemma-3-27b-it"
    #         contents = [
    #             types.Content(
    #                 role="user",
    #                 parts=[
    #                     types.Part.from_text(text=self.user_input),
    #                 ],
    #             ),
    #         ]
    #         generate_content_config = types.GenerateContentConfig(
    #         )
    #         final_text = ''
    #         for chunk in client.models.generate_content_stream(
    #                 model=model_name,
    #                 contents=contents,
    #                 config=generate_content_config,
    #         ):
    #             if chunk.text:
    #                 final_text += str(chunk.text)
    #             else:
    #                 final_text += "\n"
    #
    #         self.llm_response = final_text
    #
    #     except Exception as e:
    #         self.llm_response = f"Error calling LLM: {e}"

    def _call_llm(self):
        for rec in self:
            try:
                IrConfigParam = self.env['ir.config_parameter']
                api_key = IrConfigParam.sudo().get_param("google_ai_studio.google_ai_api_key")
                # api_key = 'AIzaSyA9sRlf4FVIwaoGX6E9Aaqab-D2jWoFMHg'

                if not api_key:
                    rec.llm_response = "<p><b>Error:</b> GEMINI_API_KEY not set.</p>"
                    continue

                client = genai.Client(api_key=api_key)
                model_name = "gemma-3-27b-it"

                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=rec.user_input)],
                    ),
                ]

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                )

                raw_text = "".join([c.text for c in response.candidates[0].content.parts if c.text])

                clean_text = rec._clean_markdown(raw_text)

                formatted_html = rec._format_llm_text_to_html(clean_text)

                # paragraphs = [f"<p>{p.strip()}</p>" for p in raw_text.split("\n\n") if p.strip()]
                # formatted_html = "".join(paragraphs)

                rec.llm_response = formatted_html

            except Exception as e:
                rec.llm_response = f"<p><b>Error calling LLM:</b> {e}</p>"

    def process_consultation(self):
        self.ensure_one()
        self._call_llm()
        self.env['medical.consultation.history'].sudo().create({
            'consultation_id': self.id,
            'user_input': self.user_input,
            'llm_response': self.llm_response})



class MedicalConsultationHistory(models.Model):
    _name = 'medical.consultation.history'
    _description = 'Medical Consultation History'
    _order = 'create_date desc'

    consultation_id = fields.Many2one('medical.consultation', string="Consultation", ondelete='cascade')
    user_input = fields.Text(string="Question", required=True)
    llm_response = fields.Html(string="Response", sanitize=False)


# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     google_ai_api_key = fields.Char(string="Google AI API Key", config_parameter="google_ai_studio.google_ai_api_key")
