{
    'name': 'Canvas Image Editor',
    'version': '16.0',
    'category': 'Tools',
    'summary': 'Upload and edit images with Fabric.js inside Odoo',
    'description': 'Upload image, edit (draw/text), save edited image inside Odoo',
    'author': 'Jobaer hossain - jobaer.jhs@gmail.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/annotated_image_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.2.4/fabric.min.js',
            'canvas_image_editor/static/src/js/image_editor.js',
            'canvas_image_editor/static/src/xml/image_editor_templates.xml',
            'canvas_image_editor/static/src/css/style.css',
        ]
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
