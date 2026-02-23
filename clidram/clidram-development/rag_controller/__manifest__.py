{
    'name': 'RAG Integration Controller',
    'version': '16.0.1.0.0',
    'category': 'Healthcare/Medical',
    'summary': 'Integrates Odoo with FastAPI RAG System for Medical Records',
    'description': """
RAG Integration Controller
==========================
This module provides integration between Odoo and the external Medical RAG system.
It adds API endpoints and configuration settings for seamless query execution and data indexing.
    """,
    'author': 'Clidram',
    'depends': ['base', 'web', 'mail', 'tus_meta_whatsapp_base', 'pos_prescription_knk','wk_appointment'],
    'data': [
        'data/rag_bot_data.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_inherit_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
