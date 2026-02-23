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

from odoo import models, fields, _,api
from odoo.exceptions import ValidationError
# from odoo.addons.base.models.res_partner import _tz_get
import logging
_logger = logging.getLogger(__name__)

class Appointment(models.Model):
    _inherit = "wk.appointment"

    tz = fields.Selection(string='Timezone', related="appoint_person_id.tz")
    transaction_ids = fields.Many2many('payment.transaction', 'appointment_transaction_rel', 'appoint_id', 'transaction_id',
                                       string='Transactions', copy=False, readonly=True)
    authorized_transaction_ids = fields.Many2many('payment.transaction', compute='_compute_authorized_transaction_ids',
                                                  string='Authorized Transactions', copy=False, readonly=True)

    payment_tx_ids = fields.One2many('payment.transaction', 'appointment_id', string='Payment Transactions')
    payment_tx_id = fields.Many2one('payment.transaction', string='Last Transaction', copy=False)
    payment_acquirer_id = fields.Many2one(
        'payment.provider', string='Payment Acquirer',
        related='payment_tx_id.provider_id', store=True)
    payment_tx_count = fields.Integer(string="Number of payment transactions", compute='_compute_payment_tx_count')

    def _compute_payment_tx_count(self):
        tx_data = self.env['payment.transaction'].read_group(
            [('appointment_id', 'in', self.ids)],
            ['appointment_id'], ['appointment_id']
        )
        mapped_data = dict([(m['appointment_id'][0], m['appointment_id_count']) for m in tx_data])
        for appoint in self:
            appoint.payment_tx_count = mapped_data.get(appoint.id, 0)

    def action_view_transactions(self):
        action = {
            'name': _('Payment Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'target': 'current',
        }
        tx = self.env['payment.transaction'].search([('appointment_id', 'in', self.ids)])
        if len(tx) == 1:
            action['res_id'] = tx.ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('appointment_id', 'in', self.ids)]
        return action

    def _create_payment_transaction(
        self, payment_option_id, amount, currency_id, partner_id, flow,tokenization_requested, landing_route, is_validation=False, invoice_id=None, **kwargs
        ):
        '''Similar to self.env['payment.transaction'].create(vals) but the values are filled with the
        current appointment fields (e.g. the partner or the currency).
        :For params check _create_transaction method of PaymentPortal controller in payment app.
        :return: The newly created payment.transaction record.
        '''
        # Ensure the currencies are the same.
        self.ensure_one()
        if flow in ['redirect', 'direct']:  # Direct payment or payment with redirection
            acquirer_sudo = self.env['payment.provider'].sudo().browse(payment_option_id)
            token_id = None
            tokenization_required_or_requested = acquirer_sudo._is_tokenization_required(
                provider=acquirer_sudo.code, **kwargs
            ) or tokenization_requested
            tokenize = bool(
                # Public users are not allowed to save tokens as their partner is unknown
                not self.env.user._is_public()
                # Don't tokenize if the user tried to force it through the browser's developer tools
                and acquirer_sudo.allow_tokenization
                # Token is only created if required by the flow or requested by the user
                and tokenization_required_or_requested
            )
        elif flow == 'token':  # Payment by token
            token_sudo = self.env['payment.token'].sudo().browse(payment_option_id)
            acquirer_sudo = token_sudo.acquirer_id
            token_id = payment_option_id
            tokenize = False
        else:
            raise UserError(
                _("The payment should either be direct, with redirection, or made by a token.")
            )

        currency = self[0].currency_id
        if any([appoint.currency_id != currency for appoint in self]):
            raise ValidationError(_('A transaction can\'t be linked to appointment having different currencies.'))

        # Ensure the partner are the same.
        partner = self[0].customer
        if any([appoint.customer != partner for appoint in self]):
            raise ValidationError(_('A transaction can\'t be linked to appointment having different partners.'))

        if is_validation:  # Acquirers determine the amount and currency in validation operations
            amount = acquirer_sudo._get_validation_amount()
            currency_id = acquirer_sudo._get_validation_currency().id

        tx_vals = {
            'amount': self[0].amount_total,
            'currency_id': currency.id,
            'partner_id': partner.id,
            'appointment_id': self[0].id,
            'provider_id': acquirer_sudo.id,
            'amount': self.amount_total,
            'currency_id': self.currency_id.id,
            'partner_id': self.customer.id,
            'token_id': token_id,
            'operation': f'online_{flow}',
            'tokenize': tokenize,
            'landing_route': landing_route,
        }
        tx_sudo = self.env['payment.transaction'].sudo().create(tx_vals)

        if flow == 'token':
            tx_sudo._send_payment_request()  # Payments by token process transactions immediately
        else:
            tx_sudo._log_sent_message()

        return tx_sudo

    def _compute_portal_url(self):
        super(Appointment, self)._compute_portal_url()
        for appoint in self:
            appoint.portal_url = '/my/appointments/%s' % (appoint.id)

    def _compute_access_url(self):
        super(Appointment, self)._compute_access_url()
        for appoint in self:
            appoint.access_url = '/my/appointments/%s' % (appoint.id)

    @api.depends('transaction_ids')
    def _compute_authorized_transaction_ids(self):
        for trans in self:
            trans.authorized_transaction_ids = trans.transaction_ids.filtered(lambda t: t.state == 'authorized')

    def get_portal_last_transaction(self):
        self.ensure_one()
        return self.transaction_ids.get_last_transaction()

    def payment_action_capture(self):
        for rec in self:
            self.authorized_transaction_ids.s2s_capture_transaction()

    def payment_action_void(self):
        for rec in self:
            self.authorized_transaction_ids.s2s_void_transaction()

    @api.model
    def set_default_source(self):
        source = super(Appointment, self).set_default_source()
        if self._context.get("website_appoint"):
            try:
                source = self.env.ref('wk_appointment.appoint_source3')
            except Exception as e:
                pass
        return source

    def _get_payment_type(self):
        self.ensure_one()
        return 'form'
