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

from odoo import http,_,fields
from odoo.http import request
import base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_is_zero
import logging, pytz
_logger = logging.getLogger(__name__)

Days = {
    0 : 'monday',
    1 : 'tuesday',
    2 : 'wednesday',
    3 : 'thursday',
    4 : 'friday',
    5 : 'saturday',
    6 : 'sunday',
}

class WebsiteAppointment(http.Controller):

    def get_formatted_lang_date(self, appoint_date):
        lang = request.env['ir.qweb.field'].user_lang()
        appoint_date = datetime.strptime(appoint_date, lang.date_format).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return appoint_date

    @http.route(['/appointment'], type='http',auth='public' , website=True )
    def _get_appointment_page(self, **kw):
        company_id = request.env.user.company_id.id
        group_id = request.env['appointment.person.group'].sudo().search(['|',('company_id','=',company_id),('company_id', '=', False),])
        lang = request.env['ir.qweb.field'].user_lang()
        return request.render('wk_website_appointment.book_appoint_mgmt_template', {
            'group_id' : group_id,
            'lang_date_format' : lang.date_format,
        })

    @http.route(["/validate/appointment"], type="json", auth="public", website=True)
    def _check_multi_appointments(self, appoint_date, time_slot_id, appoint_person_id):
        result = {}
        appoint_person_obj = request.env["res.partner"].browse(appoint_person_id)
        time_slot_id = request.env["appointment.timeslot"].browse(time_slot_id)
        appoint_date = self.get_formatted_lang_date(appoint_date)
        appoint_date = datetime.strptime(str(appoint_date), DEFAULT_SERVER_DATE_FORMAT).date()

        # case 1: Check for multiple appointment bookings
        if appoint_person_obj and time_slot_id and not appoint_person_obj.allow_multi_appoints:
            appointment_obj = request.env["wk.appointment"].search([
                ("appoint_date",'=', appoint_date),
                ("appoint_person_id",'=', appoint_person_obj.id),
                ("time_slot","=", time_slot_id.id),
                ("appoint_state","not in", ['rejected']),
            ])
            if appointment_obj:
                return {
                    'status': False,
                    'message': "This slot is already booked for this person at this date. Please select any other."
                }

        # case 2: Check for time slot not available for today
        if appoint_date and time_slot_id:
            rd = relativedelta(date.today(), appoint_date)
            if rd.days == 0 and rd.months == 0 and rd.years == 0:
                time_to = str(time_slot_id.start_time).split('.')
                time_to_hour = str(time_to[0])[:2]
                minutes = int(round((time_slot_id.start_time % 1) * 60))
                if minutes == 60:
                    minutes = 0
                time_to_min = str(minutes).zfill(2)
                current_time = datetime.now().replace(microsecond=0).replace(second=0)
                user_tz = pytz.timezone(appoint_person_obj.tz or 'UTC')
                current_time = pytz.utc.localize(current_time).astimezone(user_tz).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                current_time = datetime.strptime(str(current_time), '%Y-%m-%d %H:%M:%S')
                if current_time.hour > int(time_to_hour):
                    return {
                        'status': False,
                        'message': "This slot is not available for today. Please select any other."
                    }
                if current_time.hour == int(time_to_hour) and current_time.minute >= int(time_to_min):
                    return {
                        'status': False,
                        'message': "This slot is not available for today. Please select any other."
                    }
        return {'status': True,'message': ''}

    @http.route(["/find/appointee/timeslot"], type="json", auth="public", website=True)
    def _get_appoint_person_date_timeslots(self, group_id, appoint_date):
        appoint_date = self.get_formatted_lang_date(appoint_date)
        if appoint_date:
            d1 = datetime.strptime(appoint_date,DEFAULT_SERVER_DATE_FORMAT).date()
            d2 = date.today()
            rd = relativedelta(d2,d1)
            if rd.days > 0 or rd.months > 0 or rd.years > 0:
                return
        app_group_obj = request.env['appointment.person.group'].sudo().search([('id', '=', int(group_id))])
        selected_day = datetime.strptime(appoint_date,DEFAULT_SERVER_DATE_FORMAT).weekday()
        vals = {
            'app_group_obj' : app_group_obj.sudo(),
            'selected_day': Days[selected_day],
            'appoint_date': appoint_date,
            'website_show_tz': request.env['ir.default'].sudo().get('res.config.settings', 'website_show_tz'),
        }
        return request.env['ir.ui.view']._render_template('wk_website_appointment.appointee_listing_template', vals)


    def get_appoint_pricelist(self):
        pricelist = False
        customer = request.env.user.partner_id
        irmodule_obj = request.env['ir.module.module']
        module_installed = irmodule_obj.sudo().search([('name', 'in', ['website_sale']), ('state', 'in', ['installed'])])
        if module_installed:
            pricelist = request.website.get_current_pricelist()
        else:
            pricelist = customer.property_product_pricelist
        return pricelist

    def _get_compute_currency(self, price, pricelist):
        company = pricelist.company_id or request.website.company_id
        from_currency = request.env['res.company']._get_main_company().currency_id
        to_currency = pricelist.currency_id
        return from_currency._convert(price, to_currency, company, fields.Date.today())

    @http.route("/appointment/book", type="http", auth="public", website=True )
    def _book_appointment(self, **appoint_dict):
        if appoint_dict=={}:
            return request.redirect("/appointment")
        customer = request.env.user.partner_id
        appoint_group = request.env['appointment.person.group'].sudo().search([('id', '=', int(appoint_dict.get('appoint_groups', False)))])
        appoint_person = request.env['res.partner'].sudo().search([('id', '=', int(appoint_dict.get('appoint_person', False)))])
        appoint_date = appoint_dict.get('appoint_date', False)
        appoint_slot = request.env['appointment.timeslot'].sudo().search([('id', '=', int(appoint_dict.get('appoint_timeslot_id', False)))])
        appoint_date = self.get_formatted_lang_date(appoint_date)
        # appoint_day = datetime.strptime(appoint_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%A")
        appoint_product, appoint_charge, name, flag = request.env['wk.appointment'].get_appoint_line_details(appoint_person.id, appoint_group.id)
        pricelist = self.get_appoint_pricelist()

        if flag == 1 and appoint_charge > 0 and pricelist and request.env['wk.appointment'].apply_pricelist():
            appoint_charge = request.env['wk.appointment'].get_appoint_pricelist_price(pricelist_id= pricelist.id, prod_tmpl_id= appoint_product, appoint_charge= appoint_charge)
        else:
            appoint_charge = self._get_compute_currency(appoint_charge, pricelist)
        vals = {
            'customer': customer,
            'appoint_group':appoint_group,
            'appoint_person': appoint_person,
            'appoint_date': appoint_date,
            # 'appoint_day': dict(appoint_slot._fields['day'].selection).get(appoint_slot.day),
            'appoint_slot': appoint_slot,
            'appoint_currency': pricelist.currency_id,
            # 'appoint_charge': self._get_compute_currency(appoint_charge, pricelist),
            'appoint_charge': appoint_charge,
        }
        if appoint_dict.get('appoint_error'):
            vals.update({
                'appoint_error' : appoint_dict.get('appoint_error'),
            })
        return request.render('wk_website_appointment.confirm_book_appoint_mgmt_template', vals)

    @http.route("/appointment/confirmation", type="http", auth="public", website=True )
    def _confirm_appointment(self, **post):
        AppointmentObj = request.env['wk.appointment']
        if post == {}:
            return request.redirect("/appointment")
        try:
            customer = request.env.user.partner_id
            appoint_group = request.env['appointment.person.group'].sudo().search([('id', '=', int(post.get('appoint_group', False)))])
            appoint_person = request.env['res.partner'].sudo().search([('id', '=', int(post.get('appoint_person', False)))])
            appoint_date = post.get('appoint_date', False)
            appoint_slot = request.env['appointment.timeslot'].sudo().search([('id', '=', int(post.get('appoint_slot', False)))])
            pricelist = self.get_appoint_pricelist()
            vals = {
                'customer': customer.id,
                'currency_id': pricelist.currency_id.id,
                'pricelist_id': pricelist.id,
                'appoint_group_id': appoint_group.id,
                'appoint_person_id': appoint_person.id,
                'appoint_date': appoint_date,
                'time_slot': appoint_slot.id,
                'appoint_state': 'new',
                'description' : post.get("appoint_desc", False) if post.get("appoint_desc") else '',
                'company_id': request.env.user.company_id.id,
            }
            test = request.website.sudo()._is_slot_available(appoint_person.id,appoint_slot.id,appoint_date)
            if not test or request.website.sudo()._check_appoint_already_booked(appoint_date, appoint_slot.id) :
                return request.redirect("/appointment")
            appoint_obj = AppointmentObj.sudo().with_context(website_appoint=True).create(vals)
            appoint_product, appoint_charge, name, flag = AppointmentObj.get_appoint_line_details(appoint_person.id, appoint_group.id)
            if flag == 1 and appoint_charge > 0 and pricelist and AppointmentObj.apply_pricelist():
                appoint_charge = AppointmentObj.get_appoint_pricelist_price(pricelist_id= pricelist.id, prod_tmpl_id= appoint_product, appoint_charge= appoint_charge)
            else:
                appoint_charge = self._get_compute_currency(appoint_charge, pricelist)
            prod_variant_obj = request.env['product.product'].browse(appoint_product.product_variant_id.id)
            appoint_line = {
                'appoint_product_id': prod_variant_obj.id,
                'tax_id': [(6, 0, prod_variant_obj.sudo().taxes_id.ids)],
                'appoint_id': appoint_obj.id,
                'name': name,
                'price_unit': appoint_charge,
                'product_qty' : 1.0,
                'price_subtotal': appoint_charge,
            }

            file = request.httprequest.files.get('appoint_attachments')
            if file:
                appoint_obj.website_attachment = base64.b64encode(file.read())
                _logger.info("File uploaded and saved to appointment: %s", file.filename)
            else:
                _logger.info("ℹ️ No file uploaded for this appointment.")

            request.env['appointment.lines'].sudo().create(appoint_line)

        except Exception as e:
            _logger.info("----------------- Some Error Occurred : %r ----------------", e)
            return request.redirect("/appointment")
        return request.redirect("/my/appointments/" + str(appoint_obj.id))
