from odoo import models, fields


class RagChatMessage(models.Model):
    _name = 'rag.chat.message'
    _description = 'RAG Chat Message History'
    _order = 'create_date asc'

    channel_id = fields.Many2one(
        'mail.channel',
        string='Channel',
        ondelete='cascade',
        index=True,
        help='The Discuss channel this message belongs to'
    )
    session_id = fields.Char(
        string='Session ID',
        required=True,
        index=True,
        help='RAG session identifier (e.g. odoo_channel_123)'
    )
    role = fields.Selection(
        [('user', 'User'), ('assistant', 'Assistant')],
        string='Role',
        required=True,
        help='Who sent the message'
    )
    content = fields.Text(
        string='Content',
        required=True,
        help='The raw message content'
    )
    patient_seq = fields.Char(
        string='Patient Sequence',
        help='Patient context if applicable'
    )
