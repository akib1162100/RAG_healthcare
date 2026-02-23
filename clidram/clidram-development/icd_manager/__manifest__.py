# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Medical Pathologies ICD10',
    'summary': 'Allows to browse all available diseases from ICD10 and their codes.'
               ' (ICD10 | International Classification of Diseases | Medical Pathology | ICD)',
    'description': 'Allows to browse all available diseases from ICD10 and their codes.',
    'version': '16.0.1.0',
    'category': 'Medical',
    'author': 'Visionee',
    'license': 'OPL-1',
    'website': 'https://visionee.net',
    'depends': [
        'base',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'data': [
        'views/medical_disease_views.xml',
        'security/ir.model.access.csv'
    ],
    'price': 60,
    'currency': "EUR",
    'license': 'AGPL-3',
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
