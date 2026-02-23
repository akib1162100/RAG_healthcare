# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.osv import expression


class DashboardMenu(models.Model):
    _name = "dashboard.menu"
    _description = "Dashboard Menu"
    _rec_name = "name"

    name = fields.Char(string="Name")
    menu_id = fields.Many2one('ir.ui.menu', string="Parent Menu")
    menu_sequence = fields.Integer(string='Menu Sequence', default=0)
    dashboard_menu_id = fields.Many2one('ir.ui.menu', string="Created Menu")
    group_ids = fields.Many2many('res.groups', string='Groups',
                                 related='menu_id.groups_id',
                                 help="User need to be at least in one of these groups to see the menu")
    client_action = fields.Many2one('ir.actions.client')

    @api.model
    def create(self, vals):
        """This code is to create menu"""
        values = {
            'name': vals['name'],
            'tag': 'dynamic_dashboard',
        }
        action_id = self.env['ir.actions.client'].create(values)
        vals['client_action'] = action_id.id
        menu_id = self.env['ir.ui.menu'].create({
            'name': vals['name'],
            'parent_id': vals['menu_id'],
            'sequence':vals.get('menu_sequence',0),
            'action': 'ir.actions.client,%d' % (action_id.id,)
        })
        vals['dashboard_menu_id'] = menu_id.id
        return super(DashboardMenu, self).create(vals)

    def write(self, vals):
        """Override write to update sequence in dashboard_menu_id"""
        if 'menu_sequence' in vals:
            self.dashboard_menu_id.write({'sequence': vals.get('menu_sequence',0)})
        if 'menu_id' in vals:
            self.dashboard_menu_id.write({'parent_id': vals.get('menu_id',0)})
        return super(DashboardMenu, self).write(vals)

    def unlink(self):
        """Override unlink to delete associated records"""
        for record in self:
            if record.dashboard_menu_id:
                # Delete associated ir.ui.menu
                record.dashboard_menu_id.unlink()

            if record.client_action:
                blocks = self.env['dashboard.block'].search([('client_action','=',record.client_action.id)])
                blocks.unlink()
                # Delete associated ir.actions.client
                record.client_action.unlink()

        return super(DashboardMenu, self).unlink()