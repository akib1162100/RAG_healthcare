{
    'name': 'Image Preview Widget',
    'version': '16.0.1.0.0',
    'summary': """Image Preview enables to enlarge image while clicking on it""",
    'description': """Image Preview enables to enlarge image while clicking on it""",
    'author': '',
    'company': '',
    'website': '',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': {
            'widget_preview_image/static/src/js/image_preview_widget.js',
            'widget_preview_image/static/src/xml/widget_image_preview.xml',
        }
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
