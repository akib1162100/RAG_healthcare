from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import ValidationError
class ResUsers(models.Model):
    _inherit = 'res.users'

    recent_record_ids = fields.One2many('sh.recent.records','sh_user_id')

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['sh_enable_recent_record_view']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['sh_enable_recent_record_view']


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        info = super().session_info()
        user = request.env.user
        info["sh_enable_recent_record_view"] = user.sh_enable_recent_record_view
        return info
        
class CustomUsers(models.Model):
    _inherit = 'res.users'

    sh_quick_action_line_ids = fields.One2many(
        'sh.quick.create',
        'sh_user_id',
        string='Quick Action lines',
    )
