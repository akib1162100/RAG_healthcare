# -*- coding: utf-8 -*-
{
    'name': "Healthcare Invoice",

    'summary': """Customized Invoice Report""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Farhan",
    'website': "https://www.example.com",

    'category': 'Uncategorized',
    'version': '16.0.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'pos_prescription_knk', 'l10n_in'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/invoice_report.xml',
        'report/invoice_report_with_header_footer.xml',
        'views/account_move_view.xml',
        'views/prescription_order_view.xml',
        'views/invoice_category.xml',
        'views/res_company_view.xml'
    ],

    'license': 'LGPL-3',
    'application': True,
    'installable': True
}
