# addons/discuss_gemini_integration/models/res_config_settings.py
# models/res_config_settings.py
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Enable/disable integration
    enable_gemini = fields.Boolean(
        string="Enable Gemini Integration",
        config_parameter='discuss_gemini_integration.enable_gemini',
        help="When checked, users can trigger Gemini in Discuss channels."
    )

    # API key
    gemini_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter='discuss_gemini_integration.gemini_api_key',
        help="Enter your API key for the Google Gemini integration."
    )

    # Context settings
    max_context_messages = fields.Integer(
        string="Maximum Context Messages",
        config_parameter='discuss_gemini_integration.max_context_messages',
        default=5,
        help="Maximum number of previous messages to include as context."
    )

    # Model selection
    gemini_model = fields.Selection([
        ('gemini-pro', 'Gemini Pro'),
        ('gemma-3-27b-it', 'Gemma 3-27b-it'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
        ('gemini-2.0-flash', 'Gemini 2.0 Flash'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
    ],
    string="Gemini Model",
    config_parameter='discuss_gemini_integration.gemini_model',
    default='gemma-3-27b-it',
    help="Select the Gemini model to use for responses."
    )

    gemini_partner_id = fields.Many2one(
        'res.partner',
        string="Gemini Partner",
        config_parameter='discuss_gemini_integration.gemini_partner_id',
        help="Select the partner that will represent Gemini in discussions."
    )

    is_gemini_response_added = fields.Boolean(
        string="Is Gemini Response Added",
        config_parameter='discuss_gemini_integration.is_gemini_response_added',
        default=False,
        help="Flag to indicate if the gemini response has been added to the channel."
    )

    google_ai_api_key = fields.Char(string="Google AI API Key", config_parameter="google_ai_studio.google_ai_api_key")
