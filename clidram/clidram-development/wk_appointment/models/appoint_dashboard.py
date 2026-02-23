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

from odoo import models, fields, api, _
import logging
import json,ast
from datetime import datetime, timedelta
from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
from odoo.tools.misc import formatLang
from lxml import etree
import random
_logger = logging.getLogger(__name__)

class AppointmentDashboard(models.Model):
    _name = "appointment.dashboard"
    _order = "sequence ASC"
    _description = "Appointment Dashboard"

    def _kanban_dashboard_graph(self):
        for rec in self:
            rec.kanban_dashboard_graph = json.dumps(rec.get_appoint_dashboard_datas())

    def _kanban_dashboard(self):
        for rec in self:
            rec.kanban_dashboard = json.dumps(rec.get_additional_appoint_values())

    def is_user_apointee(self):
        # Works with singal id
        appointee_group = self.env['ir.model.data']._xmlid_lookup(
            'wk_appointment.appointment_appointee_group')[2]
        officer_group = self.env['ir.model.data']._xmlid_lookup(
            'wk_appointment.appointment_officer_group')[2]
        manager_group = self.env['ir.model.data']._xmlid_lookup(
            'wk_appointment.appointment_manager_group')[2]
        groups_ids = self.env.user.sudo().groups_id.ids
        
        if appointee_group in groups_ids and officer_group not in groups_ids and manager_group not in groups_ids:
            return True
        else:
            return False

    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name", translate=True)
    sequence = fields.Integer("Sequence")
    state = fields.Selection([
        ('new', 'New'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done','Done')
    ], string="State")
    count_new_appoint = fields.Integer(compute='_get_new_appoint_count')
    count_pending_appoint = fields.Integer(compute='_get_pending_appoint_count')
    count_approved_appoint = fields.Integer(compute='_get_approved_appoint_count')
    count_rejected_appoint = fields.Integer(compute='_get_rejected_appoint_count')
    count_done_appoint = fields.Integer(compute='_get_done_appoint_count')

    def _get_new_appoint_count(self):
        company_id = self.env.company.id
        for rec in self:
            if rec.is_user_apointee():
                obj = self.env['wk.appointment'].search(
                    ['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id), ('appoint_state', '=', 'new')])
            else:
                obj = self.env['wk.appointment'].search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state', '=', 'new')])
            
            rec.count_new_appoint = len(obj)

    def _get_pending_appoint_count(self):
        company_id = self.env.company.id
        for rec in self:
            if rec.is_user_apointee():
                obj = self.env['wk.appointment'].search(
                    ['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id), ('appoint_state', '=', 'pending')])
            else:
                obj = self.env['wk.appointment'].search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state', '=', 'pending')])
            rec.count_pending_appoint = len(obj)

    def _get_approved_appoint_count(self):
        company_id = self.env.company.id
        for rec in self:
            if rec.is_user_apointee():
                obj = self.env['wk.appointment'].search(
                    ['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id), ('appoint_state', '=', 'approved')])
            else:
                obj = self.env['wk.appointment'].search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state', '=', 'approved')])
            rec.count_approved_appoint = len(obj)

    def _get_rejected_appoint_count(self):
        company_id = self.env.company.id
        for rec in self:
            if rec.is_user_apointee():
                obj = self.env['wk.appointment'].search(
                    ['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id), ('appoint_state', '=', 'rejected')])
            else:
                obj = self.env['wk.appointment'].search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state', '=', 'rejected')])
            rec.count_rejected_appoint = len(obj)

    def _get_done_appoint_count(self):
        company_id = self.env.company.id
        for rec in self:
            if rec.is_user_apointee():
                obj = self.env['wk.appointment'].search(
                    ['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id), ('appoint_state', '=', 'done')])
            else:
                obj = self.env['wk.appointment'].search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state', '=', 'done')])
            rec.count_done_appoint = len(obj)

    def open_action(self):
        """return action based on type for related appointment states"""
        action_name = self._context.get('action_name', False)
        if not action_name:
            if self.state == 'new':
                action_name = 'appoint_mgmt_new_appoint_dashboard_action'
            elif self.state == 'pending':
                action_name = 'appoint_mgmt_pending_appoint_dashboard_action'
            elif self.state == 'approved':
                action_name = 'appoint_mgmt_approved_appoint_dashboard_action'
            elif self.state == 'rejected':
                action_name = 'appoint_mgmt_rejected_appoint_dashboard_action'
            elif self.state == 'done':
                action_name = 'appoint_mgmt_done_appoint_dashboard_action'
            else:
                action_name = 'appoint_mgmt_all_appointment_action'
        ctx = self._context.copy()
        ctx.update({})
        [action] = self.env.ref('wk_appointment.%s' % action_name).read()
        action['context'] = ctx
        use_domain = self._context.get('use_domain',[])
        if use_domain:
            if use_domain == 'not_invoiced':
                action['domain'] = ast.literal_eval(action['domain']) + [('invoice_id','=',False)]
            if use_domain == 'invoice_to_validate':
                action['domain'] = ast.literal_eval(action['domain']) + [('invoice_id','!=',False),('invoice_status','=','draft')]
            if use_domain == 'invoice_unpaid':
                action['domain'] = ast.literal_eval(action['domain']) + [('invoice_id','!=',False),('invoice_status','=','open')]
            if use_domain == 'invoice_paid':
                action['domain'] = ast.literal_eval(action['domain']) + [('invoice_id','!=',False),('invoice_status','=','paid')]
        return action

    def action_create_new(self):
        return {
            'name': _('Create Appointment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': "wk.appointment",
            'view_id': self.env.ref('wk_appointment.appoint_mgmt_book_appointment_form_view').id,
            'context': {'default_appoint_date':str(fields.Date.today()),'default_name': 'New'},
        }

    def _get_bar_graph_select_query(self):
        self.ensure_one()
        return ('''
            SELECT
                SUM(amount_total) as total,
                MIN(appoint_date) as aggr_date from wk_appointment
                where appoint_state = %(appoint_state)s AND
                appoint_person_id = %(appoint_person_id)s AND
                company_id = %(company_id)s
        ''', {
            'appoint_state': self.state,
            'appoint_person_id' : self.env.user.partner_id.id,
            'company_id': self.env.user.company_id.id,
        })

    def get_state_color(self):
        color = '#6c757d61'
        if self.state == 'new':
            color = '#17a2b8'
        if self.state == 'pending':
            color = '#17a2b8'
        if self.state == 'approved':
            color = '#28a745'
        if self.state == 'rejected':
            color = '#dc3545'
        if self.state == 'done':
            color = '#9365b86b'
        return color

    def get_appoint_dashboard_datas(self):
        self.ensure_one()
        data = []
        today = fields.Datetime.now(self)
        data.append({'label': _('Past'), 'value':0.0, 'type': 'past'})
        day_of_week = int(format_datetime(today, 'e', locale=get_lang(self.env).code))
        first_day_of_week = today + timedelta(days=-day_of_week+1)
        for i in range(-1,4):
            if i==0:
                label = _('This Week')
            elif i==3:
                label = _('Future')
            else:
                start_week = first_day_of_week + timedelta(days=i*7)
                end_week = start_week + timedelta(days=6)
                if start_week.month == end_week.month:
                    label = str(start_week.day) + '-' + str(end_week.day) + ' ' + format_date(end_week, 'MMM', locale=get_lang(self.env).code)
                else:
                    label = format_date(start_week, 'd MMM', locale=get_lang(self.env).code) + '-' + format_date(end_week, 'd MMM', locale=get_lang(self.env).code)
            data.append({'label':label,'value':0.0, 'type': 'past' if i<0 else 'future'})

        (select_sql_clause, query_args) = self._get_bar_graph_select_query()
        query = ''
        start_date = (first_day_of_week + timedelta(days=-7))
        for i in range(0,6):
            if i == 0:
                query += "("+select_sql_clause+" and appoint_date < '"+start_date.strftime(DF)+"')"
            elif i == 5:
                query += " UNION ALL ("+select_sql_clause+" and appoint_date >= '"+start_date.strftime(DF)+"')"
            else:
                next_date = start_date + timedelta(days=7)
                query += " UNION ALL ("+select_sql_clause+" and appoint_date >= '"+start_date.strftime(DF)+"' and appoint_date < '"+next_date.strftime(DF)+"')"
                start_date = next_date
        self.env.cr.execute(query, query_args)
        query_results = self.env.cr.dictfetchall()
        for index in range(0, len(query_results)):
            if query_results[index].get('aggr_date') != None:
                data[index]['value'] = query_results[index].get('total')
        return [{'values': data, 'key': _('Total'), 'color': self.get_state_color(),}]

    def get_additional_appoint_values(self):
        AppointObj = self.env['wk.appointment'].sudo()
        currency = self.env.user.company_id.currency_id
        company_id = self.env.user.company_id.id
        for rec in self:
            if rec.is_user_apointee():
                not_invoiced = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','=',False)])
                amount_total_not_invoiced = sum(not_invoiced.mapped('amount_total'))
                invoice_to_validate = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','draft')])
                amount_total_invoice_to_validate = sum(invoice_to_validate.mapped('amount_total'))
                invoice_unpaid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','open')])
                amount_total_invoice_unpaid = sum(invoice_unpaid.mapped('amount_total'))
                invoice_paid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','paid')])
                amount_total_invoice_paid = sum(invoice_paid.mapped('amount_total'))

                not_invoiced = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','=',False)])
                amount_total_not_invoiced = sum(not_invoiced.mapped('amount_total'))
                invoice_to_validate = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','draft')])
                amount_total_invoice_to_validate = sum(invoice_to_validate.mapped('amount_total'))
                invoice_unpaid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','open')])
                amount_total_invoice_unpaid = sum(invoice_unpaid.mapped('amount_total'))
                invoice_paid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_person_id', '=', self.env.user.partner_id.id),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','paid')])
                amount_total_invoice_paid = sum(invoice_paid.mapped('amount_total'))
            else:
                not_invoiced = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','=',False)])
                amount_total_not_invoiced = sum(not_invoiced.mapped('amount_total'))
                invoice_to_validate = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','draft')])
                amount_total_invoice_to_validate = sum(invoice_to_validate.mapped('amount_total'))
                invoice_unpaid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','open')])
                amount_total_invoice_unpaid = sum(invoice_unpaid.mapped('amount_total'))
                invoice_paid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','paid')])
                amount_total_invoice_paid = sum(invoice_paid.mapped('amount_total'))

                not_invoiced = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','=',False)])
                amount_total_not_invoiced = sum(not_invoiced.mapped('amount_total'))
                invoice_to_validate = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','draft')])
                amount_total_invoice_to_validate = sum(invoice_to_validate.mapped('amount_total'))
                invoice_unpaid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','open')])
                amount_total_invoice_unpaid = sum(invoice_unpaid.mapped('amount_total'))
                invoice_paid = AppointObj.search(['|',('company_id','=',company_id),('company_id', '=', False),('appoint_state','=',rec.state),('invoice_id','!=',False),('invoice_status','=','paid')])
                amount_total_invoice_paid = sum(invoice_paid.mapped('amount_total'))
            return {
                'not_invoiced': len(not_invoiced),
                'amount_total_not_invoiced': formatLang(self.env, amount_total_not_invoiced or 0.0, currency_obj=currency),
                'invoice_to_validate': len(invoice_to_validate),
                'amount_total_invoice_to_validate': formatLang(self.env, amount_total_invoice_to_validate or 0.0, currency_obj=currency),
                'invoice_unpaid': len(invoice_unpaid),
                'amount_total_invoice_unpaid': formatLang(self.env, amount_total_invoice_unpaid or 0.0, currency_obj=currency),
                'invoice_paid': len(invoice_paid),
                'amount_total_invoice_paid': formatLang(self.env, amount_total_invoice_paid or 0.0, currency_obj=currency),
            }
