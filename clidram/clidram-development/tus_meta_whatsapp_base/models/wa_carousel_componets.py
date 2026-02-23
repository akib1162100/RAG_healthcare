from odoo import models, fields, api
from odoo.exceptions import ValidationError

image_type = ['image/avif', 'image/bmp', 'image/gif', 'image/vnd.microsoft.icon', 'image/jpeg', 'image/png',
              'image/svg+xml', 'image/tiff', 'image/webp']
document_type = ['application/xhtml+xml', 'application/vnd.ms-excel',
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/xml',
                 'application/vnd.mozilla.xul+xml', 'application/zip',
                 'application/x-7z-compressed', 'application/x-abiword', 'application/x-freearc',
                 'application/vnd.amazon.ebook', 'application/octet-stream', 'application/x-bzip',
                 'application/x-bzip2', 'application/x-cdf', 'application/x-csh', 'application/msword',
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 'application/vnd.ms-fontobject', 'application/epub+zip', 'application/gzip',
                 'application/java-archive', 'application/json', 'application/ld+json',
                 'application/vnd.apple.installer+xml', 'application/vnd.oasis.opendocument.presentation',
                 'application/vnd.oasis.opendocument.spreadsheet', 'application/vnd.oasis.opendocument.text',
                 'application/ogg', 'application/pdf', 'application/x-httpd-php', 'application/vnd.ms-powerpoint',
                 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.rar',
                 'application/rtf', 'application/x-sh', 'application/x-tar', 'application/vnd.visio']
audio_type = ['audio/aac', 'audio/midi', 'audio/x-midi', 'audio/mpeg', 'audio/ogg', 'audio/opus', 'audio/wav',
              'audio/webm', 'audio/3gpp', 'audio/3gpp2']
video_type = ['video/x-msvideo', 'video/mp4', 'video/mpeg', 'video/ogg', 'video/mp2t', 'video/webm', 'video/3gpp',
              'video/3gpp2']


class WaCarouselComponent(models.Model):
    _name = 'wa.carousel.component'
    _description = "Whatsapp carousel Template"

    header_formate = fields.Selection([('image', 'Image'),
                                       ('video', 'Video')])

    attachment_ids = fields.Many2many('ir.attachment', string="Attach Document")
    carousel_body = fields.Text("Body")
    wa_button_ids = fields.One2many('wa.button.component', 'carousel_id', string="Buttons")
    component_id = fields.Many2one('components')
    variables_ids = fields.One2many('variables', 'carousel_id', 'Variables')
    model_id = fields.Many2one('ir.model', related="component_id.model_id")

    @api.onchange('attachment_ids')
    def onchange_check_attachment(self):
        for rec in self:
            if rec.attachment_ids:
                for attachment_id in rec.attachment_ids:
                    if rec.header_formate == 'video':
                        if attachment_id.mimetype not in video_type:
                            raise ValidationError("Invalid type %s for video" % attachment_id.mimetype)
                    if rec.header_formate == 'image':
                        if attachment_id.mimetype not in image_type:
                            raise ValidationError("Invalid type %s for image" % attachment_id.mimetype)






