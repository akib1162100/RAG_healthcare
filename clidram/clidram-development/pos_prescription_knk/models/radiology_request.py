from odoo import models, fields, api


class RadiologyRequest(models.Model):
	_name = 'radiology.request'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = "Radiology Request"

	name = fields.Char(string='Request Number')
	date = fields.Datetime('Date', required=True, default=fields.Datetime.now)
	patient_id = fields.Many2one('res.partner', ondelete="restrict",
								 string='Patient', domain="[('partner_type','=','patient')]", tracking=True, required=True)
	physician_id = fields.Many2one('res.partner', ondelete="restrict", string='Prescribing Doctor',
								   domain="[('partner_type','=','physician')]", tracking=True, required=True)
	patient_age = fields.Char(string='Age', store=True,
							  help="Computed patient age at the moment of the evaluation", related="patient_id.age")
	invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
	line_ids = fields.One2many('radiology.request.line', 'radiology_request_id',
							   string='Radiology Test Line',  copy=True)
	company_id = fields.Many2one(
		"res.company", default=lambda self: self.env.company.id)
	status = fields.Selection([('scheduled', 'Scheduled'), ('arrived', 'Arrived'), ('in_progress',
																					'In Progress'), ('completed', 'Completed'), ('done', 'Reports Done')], default='scheduled', tracking=True)

	pacs_url = fields.Char(string="URL")
	technique = fields.Html()
	findings = fields.Html()
	impression = fields.Html()
	signature = fields.Binary()
	procedure_physician_id = fields.Many2one("res.partner", domain="[('partner_type','=','physician')]")
	procedure_product_id = fields.Many2one("product.product",string="Procedure name")
	demo_html = fields.Html()

	def action_print_with_header(self):
		return self.env.ref('pos_prescription_knk.action_radiology_report').report_action(self)

	def action_print_without_header(self):
		return self.env.ref("pos_prescription_knk.action_radiology_report_without_header").report_action(self)
		
	def action_view_study(self):
		self.ensure_one()
		if self.pacs_url:
			url = "https://catalyst.pacsonline.co.in/viewer?StudyInstanceUIDs=" + self.pacs_url
			return {
				'type': 'ir.actions.act_url',
				'target': 'new',
				'url': url,
			}

	@api.model_create_multi
	def create(self, values):
		for value in values:
			if value.get('name', 'New') == 'New':
				value['name'] = self.env['ir.sequence'].next_by_code(
					'radiology.request') or ('New')
		return super().create(values)


class RadiologyRequestLine(models.Model):
	_name = "radiology.request.line"
	_description = "Radiology Request Line"

	radiology_request_id = fields.Many2one(
		'radiology.request', string='Lines', ondelete='cascade')
	test = fields.Char()
	product_id = fields.Many2one("product.product", string="Test")
	special_instruction = fields.Char()
	sale_price = fields.Float(related="product_id.lst_price")
