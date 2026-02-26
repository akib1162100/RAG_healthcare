from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rag_api_url = fields.Char(
        string='RAG API URL',
        config_parameter='rag_controller.rag_api_url',
        help='The base URL of the FastAPI RAG service (e.g., http://localhost:8000)'
    )
    
    rag_api_key = fields.Char(
        string='RAG API Key',
        config_parameter='rag_controller.rag_api_key',
        help='Secure API key to communicate with the FastAPI RAG service'
    )

    rag_bot_partner_id = fields.Many2one(
        'res.partner',
        string='RAG Bot Partner',
        config_parameter='rag_controller.bot_partner_id',
        help='Select the Partner profile that will act as the RAG Assistant in Discuss.'
    )

    context_message_limit = fields.Integer(
        string='Chat History Context Limit',
        config_parameter='rag_controller.context_message_limit',
        default=3,
        help='Number of previous chat messages to include as context when sending a request '
             'to the RAG system. If set to 0, no previous context is sent. Default is 3.'
    )
