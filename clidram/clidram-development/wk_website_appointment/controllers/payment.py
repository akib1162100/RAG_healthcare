# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
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

from odoo import http, _
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.http import request, route
import logging
_logger = logging.getLogger(__name__)

class PaymentPortal(payment_portal.PaymentPortal):

    @http.route(['/my/appointments/<int:appoint_id>/transaction/'], type='json', auth="public", website=True)
    def appoint_pay_form(self, appoint_id, save_token=False, access_token=None, **kwargs):
        payment_option_id = kwargs.get('payment_option_id')
        if not payment_option_id:
            return False

        try:
            payment_option_id = int(payment_option_id)
        except:
            return False

        appoint = request.env['wk.appointment'].sudo().browse(appoint_id)
        if not appoint or not appoint.appoint_lines:
            return False

        # Create transaction
        kwargs.update({
            'payment_option_id': payment_option_id,
            'landing_route': appoint.get_portal_url(),
        })
        transaction = appoint._create_payment_transaction(**kwargs)
        # transaction._set_pending()
        PaymentPostProcessing.monitor_transactions(transaction)

        last_tx_id = request.session.get('__wk_appointment_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        if last_tx:
            PaymentPostProcessing.remove_transactions(last_tx)
        request.session['__wk_appointment_last_tx_id'] = transaction.id

        if request.env['ir.default'].sudo().get('res.config.settings', 'website_appoint_payment_mode') == 'before_appoint':
            appoint.appoint_state = 'new' if appoint.appoint_state == 'new' else appoint.appoint_state
        return transaction._get_processing_values()


    @http.route('/my/appointments/<int:appoint_id>/transaction/token', type='http', auth='public', website=True)
    def appoint_payment_token(self, appoint_id, pm_id=None, **kwargs):

        appoint = request.env['wk.appointment'].sudo().browse(appoint_id)
        if not appoint:
            return request.redirect("/my/appointments")
        if not appoint.appoint_lines or pm_id is None:
            return request.redirect(appoint.get_portal_url())

        # try to convert pm_id into an integer, if it doesn't work redirect the user to the quote
        try:
            pm_id = int(pm_id)
        except ValueError:
            return request.redirect(appoint.get_portal_url())

        # Create transaction
        vals = {
            'payment_token_id': pm_id,
            'type': 'server2server',
            'return_url': appoint.get_portal_url(),
        }

        tx = appoint._create_payment_transaction(vals)
        PaymentPostProcessing.monitor_transactions(tx)
        return request.redirect('/payment/process')
