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
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    available_for_appoint = fields.Boolean(
        string='Can be Appointment Group Member',
        help="Check this box if this contact is available for Appointment."
        )
    time_slot_ids = fields.Many2many(comodel_name = "appointment.timeslot",
        column1= "parter_id",
        column2= "time_slot_id",
        relation= "partner_slot_rel",
        string = "Time Slots"
    )
    appoint_group_ids = fields.Many2many(
        comodel_name= "appointment.person.group",
        relation= "appoint_partner_table",
        column1= "res_partner_id",
        column2 = "appoint_group_id",
        string="Appointment Group"
    )
    appoint_person_charge = fields.Float("Appointment Charge")
    work_exp = fields.Char("Working Experience")
    about_person = fields.Text("About")
    specialist = fields.Char("Specialist")
    booked_appointment_ids = fields.One2many(
        comodel_name="wk.appointment",
        inverse_name="appoint_person_id",
        string="Appointments",
    )
    allow_multi_appoints = fields.Boolean(
        "Allow Multiple Appointments",
        default=lambda self: self.env['ir.default'].get("res.config.settings",'allow_multi_appoints'),
        help="If it is enabled then this member can handle multiple appointments in a particular timeslot."
    )
    use_addr_as_appoint = fields.Boolean("Use as Appointment Address",
        help="If it is enabled then this member address will be used as a appointment address.")
    appoint_product_id = fields.Many2one(
        "product.template",
        "Appointee Product",
        help="This product will be used for managing pricelist while\
        applying appointment charges."
    )

    def appoint_update_product_price(self):
        for rec in self:
            if rec.appoint_product_id and rec.appoint_product_id.list_price != rec.appoint_person_charge:
                rec.appoint_product_id.write({'list_price': rec.appoint_person_charge})
        return True

    def write(self, vals):
        if vals.get('appoint_person_charge') and vals.get('appoint_person_charge') < 0:
            raise UserError(_("Appointment charge cannot be less than zero"))
        res = super(ResPartner, self).write(vals)
        if vals.get("appoint_product_id") or "appoint_person_charge" in vals and vals.get("appoint_person_charge") >= 0:
            self.appoint_update_product_price()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('appoint_person_charge') and vals.get('appoint_person_charge') < 0:
                raise UserError(_("Appointment charge cannot be less than zero"))
            res = super(ResPartner, self).create(vals)
            if vals.get("appoint_product_id"):
                res.appoint_update_product_price()
            return res
