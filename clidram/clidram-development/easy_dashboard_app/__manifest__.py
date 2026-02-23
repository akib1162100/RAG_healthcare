# -*- coding: utf-8 -*-
#############################################################################

{
    'name': "All in One Dynamic Dashboard",
    'version': '16.0.1.0.0',
    'summary': """Create Multiple Dynamic Dashboards Easily""",
    'description': """Create Configurable Dashboard Dynamically to get the information that are relevant to your business, department, or a specific process or need, Dynamic Dashboard, Dashboard, Dashboard Odoo""",
 
    "author": "NxonBytes",
    "website": "",
    "support": "webdeveloper.inf@gmail.com",
    'category': 'Tools',
    'version': '0.1',
    'license': 'LGPL-3',
    'price': 00,
    'currency': 'USD',
    'depends': ['base', 'web'],
    'data': [
        'views/dashboard_view.xml',
        'views/dashboard_menu_view.xml',
        'views/dynamic_block_view.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'easy_dashboard_app/static/src/js/chart.js',
            'easy_dashboard_app/static/src/js/dynamic_dashboard.js',
            'easy_dashboard_app/static/src/scss/style.scss',
            'easy_dashboard_app/static/src/scss/lib.css',
            'easy_dashboard_app/static/src/xml/dynamic_dashboard_template.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
