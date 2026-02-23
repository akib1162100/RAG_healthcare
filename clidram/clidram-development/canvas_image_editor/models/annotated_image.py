from odoo import models, fields

class AnnotatedImage(models.Model):
    _name = "annotated.image"
    _description = "Annotated Image Example"

    name = fields.Char("Name", required=True)
    image_to_edit = fields.Binary("Image", attachment=True)
