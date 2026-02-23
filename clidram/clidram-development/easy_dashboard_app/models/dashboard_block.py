# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.osv import expression
from ast import literal_eval
import json


class DashboardBlock(models.Model):
    _name = "dashboard.block"
    _description = "Dashboard Blocks"
    _rec_name = "name"

    def get_default_action(self):
        action_id = self.env.ref('easy_dashboard_app.action_dynamic_dashboard')
        if action_id:
            return action_id.id
        else:
            return False

    name = fields.Char(string="Name", help='Name of the block')
    sequence = fields.Integer(string='Sequence', default=lambda self: self._get_default_sequence())
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]")
    fa_icon = fields.Char(string="Icon")
    block_width = fields.Selection(
        selection=[
            ("col-lg-2", "Column 2/12"), 
            ("col-lg-3", "Column 3/12"), 
            ("col-lg-4", "Column 4/12"), 
            ("col-lg-5", "Column 5/12"), 
            ("col-lg-6", "Column 6/12"), 
            ("col-lg-7", "Column 7/12"), 
            ("col-lg-8", "Column 8/12"),
            ("col-lg-9", "Column 9/12"),
            ("col-lg-10", "Column 10/12"),
            ("col-lg-11", "Column 11/12"),
            ("col-lg-12", "Column 12/12")
            ],
        string="Block Width",default='col-lg-4')
    tiles_template = fields.Selection(
        selection=[
            ("DynamicDashboardTileStyle_00", "Style 0"), 
            ("DynamicDashboardTileStyle_01", "Style 1"), 
            ("DynamicDashboardTileStyle_02", "Style 2"), 
            ("DynamicDashboardTileStyle_03", "Style 3"), 
            ("DynamicDashboardTileStyle_04", "Style 4"), 
            ("DynamicDashboardTileStyle_05", "Style 5"), 
            ],
        string="Tiles Design",default='DynamicDashboardTileStyle_00')
    block_height = fields.Selection(
        selection=[
            ('50', "50 %"),
            ('75', "75 %"),
            ('100', "100 %"),
            ('125', "125 %"),
            ('150', "150 %"),
            ('175', "175 %"),
            ('200', "200 %"),
            ],
        string="Block Height",default='100')
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count")],
        string="Operation", help='Tile Operation that needs to bring values for tile')

    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"), ("line", "Line"), ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart',default="bar")
    measured_field = fields.Many2one("ir.model.fields", "Measured Field")
    client_action = fields.Many2one('ir.actions.client', default = get_default_action)

    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile")], string="Type", help='Type of Block ie, Chart or Tile')
    x_axis = fields.Char(string="X-Axis")
    y_axis = fields.Char(string="Y-Axis")
    group_by = fields.Many2one("ir.model.fields", store=True, string="Group by(Y-Axis)", help='Field value for Y-Axis')
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter")
    model_id = fields.Many2one('ir.model', 'Model')
    model_name = fields.Char(related='model_id.model', readonly=True)

    filter_by = fields.Many2one("ir.model.fields", string=" Filter By")
    filter_values = fields.Char(string="Filter Values")

    sequence = fields.Integer(string="Sequence")
    edit_mode = fields.Boolean(default=False, invisible=True)

    response_dataset = fields.Text(string="Response Data Set",compute="_compute_response_dataset_val")

    def _compute_response_dataset_val(self):
        for rec in self:
            try:
                rec.response_dataset = str(rec._prepare_chart_data())
            except Exception as e:
                rec.response_dataset = str(e)
                

    def get_dashboard_vals(self, action_id):
        """Dashboard block values"""
        dashboard_items = []
        dashboard_block = self.env['dashboard.block'].sudo().search([('client_action', '=', int(action_id))],order='sequence asc')
        for rec in dashboard_block:
            try:
                response = rec._prepare_dashboard_data()
                dashboard_items.append(response)
            except Exception as e:
                print(e)
        return dashboard_items
    
    def _prepare_dashboard_data(self):
        for rec in self:
            color = rec.tile_color if rec.tile_color else '#1f6abb;'
            icon_color = rec.fa_color if rec.fa_color else '#1f6abb;'
            text_color = rec.text_color if rec.text_color else '#FFFFFF;'
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'cols': rec.block_width,
                'tiles_template': rec.tiles_template,
                'graph_width':rec.block_height,
                'color': 'background-color: %s;' % color,
                'text_color': 'color: %s;' % text_color,
                'icon_color': 'color: %s;' % icon_color,
            }
            domain = []
            if rec.filter:
                domain = expression.AND([literal_eval(rec.filter)])
            if rec.model_name:
                if rec.type == 'graph':
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                               group_by=rec.group_by)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    x_axis = []
                    for record in records:
                        x_axis.append(record.get(rec.group_by.name))
                    y_axis = []
                    for record in records:
                        y_axis.append(record.get('value'))
                    xy_data = rec._prepare_chart_data()
                    vals.update(xy_data)
                else:
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    magnitude = 0
                    total = records[0].get('value')
                    while abs(total) >= 1000:
                        magnitude += 1
                        total /= 1000.0
                    # add more suffixes if you need them
                    val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
                    records[0]['value'] = val
                    vals.update(records[0])
            return vals
        
    def _prepare_chart_data(self):
        rec = self
        domain = []
        if rec.filter:
            domain = expression.AND([literal_eval(rec.filter)])
        query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                               group_by=rec.group_by)
        self._cr.execute(query)
        records = self._cr.dictfetchall()
        x_axis = []
        for record in records:
            x_axis.append(record.get(rec.group_by.name))
        y_axis = []
        for record in records:
            y_axis.append(record.get('value'))
        return {'x_axis': x_axis, 'y_axis': y_axis}
    @staticmethod
    def _get_default_sequence(self):
        last_sequence = self.env['dashboard.block'].search([], order='sequence desc', limit=1)
        return last_sequence.sequence + 1 if last_sequence else 1

class DashboardBlockLine(models.Model):
    _name = "dashboard.block.line"

    sequence = fields.Integer(string="Sequence")
    block_size = fields.Integer(string="Block size")
