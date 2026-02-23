{
    'name': 'Hide Powered By Odoo',
    'version': '16.0.0.0',
    'category': '',
    'author': 'Doyenhub Software Solution',
    'company': 'Doyenhub Software Solution',
    'maintainer': 'Doyenhub Software Solution',
    'sequence': -200,
    'summary': """ Hide Powered By Odoo Branding.
                    """,
        
    'description': """
                Hide Powered By Odoo login screen, 
            This module modifies the functionality of emails to remove the Odoo branding.
            With this module it is possible to hide the two promotional link in the Portal purchase invoice view.            
            Hide Powered By Odoo On Settings.
                    """,
    'depends': ['web', 'portal', 'auth_signup', 'mail', 'base_setup', 'base', 'sale', 'account'],
    'data': [
         'views/login_templates.xml',
         'views/hide_portal_menu.xml',

    ],
    'images': [
        'static/description/banner.png'
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
    'website':'https://www.doyenhub.com/',
}
