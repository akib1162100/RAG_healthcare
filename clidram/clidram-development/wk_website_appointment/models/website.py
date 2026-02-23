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

from odoo import fields, models, _,api
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT, float_is_zero
from datetime import date,datetime,timedelta
import dateutil, pytz
from dateutil.relativedelta import relativedelta

class Website(models.Model):
    _inherit = 'website'

    def _check_appoint_already_booked(self, appoint_date, appoint_slot_id):
        appoint_slot_id = request.env["appointment.timeslot"].browse(int(appoint_slot_id))
        appoint_date = datetime.strptime(str(appoint_date), DEFAULT_SERVER_DATE_FORMAT).date()
        customer = request.env.user and request.env.user.partner_id
        if appoint_date and appoint_slot_id and customer:
            appointment_obj = request.env["wk.appointment"].search([
                ("appoint_date",'=', appoint_date),
                ("customer",'=', customer.id),
                ("time_slot","=", appoint_slot_id.id),
                ("appoint_state","not in", ['rejected']),
            ])
            if appointment_obj:
                return True
        return False


    def _is_slot_available(self, appoint_person_id, time_slot_id, appoint_date):
        appoint_person_obj = request.env["res.partner"].browse(int(appoint_person_id))
        time_slot_id = request.env["appointment.timeslot"].browse(int(time_slot_id))
        appoint_date = datetime.strptime(str(appoint_date), DEFAULT_SERVER_DATE_FORMAT).date()

        # case 1: Check for multiple appointment bookings
        if appoint_person_obj and not appoint_person_obj.allow_multi_appoints and time_slot_id and appoint_date:
            appointment_obj = request.env["wk.appointment"].search([
                ("appoint_date",'=', appoint_date),
                ("appoint_person_id",'=', appoint_person_obj.id),
                ("time_slot","=", time_slot_id.id),
                ("appoint_state","not in", ['rejected']),
            ])
            if appointment_obj:
                return False

        # case 2: Check for time slot not available for today
        if appoint_date:
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
                    return False
                if current_time.hour == int(time_to_hour) and current_time.minute >= int(time_to_min):
                    return False

        return True
