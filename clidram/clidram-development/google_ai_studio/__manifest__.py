# -*- coding: utf-8 -*-
{
    'name': "Google AI Studio",

    'summary': """""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Farhan",
    'website': "https://www.example.com",

    'category': 'Uncategorized',
    'version': '16.0.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base','base_setup', 'mail', 'mail_group'],

    # always loaded
    'data': [
        'data/sequence.xml',
        'views/inherit_res_setting.xml'
    ],

    'license': 'LGPL-3',
    'application': True,
    'installable': True
}
