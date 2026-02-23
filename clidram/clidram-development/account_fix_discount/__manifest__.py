{
    "name": "Account Fix Discount",
    "summary": "Allows to apply fixed amount discounts in invoices.",
    "version": "16.1",
    "category": "Accounting & Finance",
    "website": "hunainfast@gmail.com",
    "author": "HAK Technologies",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    'images': ['static/description/banner.png'],
    "depends": ["account"],
    "data": [
        "views/account_move_view.xml",
        "reports/report_account_invoice.xml",
    ],
}
