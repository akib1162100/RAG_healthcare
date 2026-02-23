# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name" : "Appointment Management System",
    "summary" : """Now, manage customer appointments in Odoo backend. The module allows you to book and manage appointments in Odoo""",
    "category" : "Human Resources",
    "version" : "1.0.2",
    "sequence" : 0,
    "author" : "Webkul Software Pvt. Ltd.",
    "license" : "Other proprietary",
    "website" : "https://store.webkul.com/Odoo-Appointment-Management-System.html",
    "description" : """Odoo Appointment Management System
Odoo Booking & Reservation Management
Odoo booking & reservation management
Odoo appointment management
Odoo website Appointment Management
Schedule bookings
Tickets
Reservations
appointment Facility in Odoo
Website booking system
Appointment management system in Odoo
Booking & reservation management in Odoo
Reservation management in Odoo
Booking
Reservation""",
    "live_test_url" : "http://odoodemo.webkul.com/?module=wk_appointment&version=16.0&menu_id=296&lifetime=60&lout=0",
    "depends" : ['sale_management', 'pos_prescription_knk', 'tus_meta_whatsapp_base'],
    "data" : [
        'security/access_control_security.xml',
        'security/ir.model.access.csv',
        'edi/reminder_mail_templates.xml',
        'edi/appointment_mail_templates.xml',
        'views/res_config_view.xml',
        # 'views/templates.xml',
        'views/appoint_mgmt_view.xml',
        'views/appoint_slottime_view.xml',
        'views/res_partner_view.xml',
        'views/appoint_group_view.xml',
        'views/appoint_mgmt_appoint_source.xml',
        'views/appoint_dashboard_view.xml',
        'wizard/reject_reason_wizard_view.xml',
        'report/appoint_report_view.xml',
        'views/appoint_mgmt_menu_view.xml',
        'data/appoint_data.xml',
        'views/appoint_mgmt_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wk_appointment/static/src/css/wk_appoint.css',
        ],
    },
    "demo" : [],
    "images" : ['static/description/Banner.gif'],
    "application" : True,
    "installable" : True,
    "auto_install" : False,
    "price" : 70,
    "currency" : "USD",
    "pre_init_hook" : "pre_init_check",
}
