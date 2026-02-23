import base64
from odoo import http
from odoo.http import request

class ImageEditorController(http.Controller):
    @http.route('/image_editor/save', type='json', auth='user')
    def save_image(self, record_id, model, field_name, image_data):
        record = request.env[model].browse(int(record_id))
        if record.exists() and field_name in record._fields:
            img_base64 = image_data.split(",")[1]
            record.write({field_name: img_base64})
        return {"status": "success"}

