# -*- coding: utf-8 -*-
{
    'name': "Extend the Customer Signup Page",

    'summary': """Extend the Customer Signup Page""",

    'description': """
        Extend the Customer Signup Page
    """,

    'author': "Mehedi Khan",
    'website': "https://www.example.com",

    'category': 'tools',
    'version': '16.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'auth_signup', 'website', 'wk_appointment', 'pos_prescription_knk',
                'wk_website_appointment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/multi_company_security_rules.xml',

        'views/website_signup_inherit.xml',
        'views/res_wk_appointment_view.xml',
        'views/res_prescription_order.xml',
        'views/res_my_account_menu_template.xml',
        'views/store_whatsapp_otp_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'extend_signup_page/static/src/css/signup_custom.css',
        ],
    },

    # 'assets': {
    #     'web.assets_frontend': [
    #         'extend_signup_page/static/src/js/otp_verification.js'
    #     ],
    # },

    'license': 'LGPL-3',
    'application': True,
    'installable': True
}
