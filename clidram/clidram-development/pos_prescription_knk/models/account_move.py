from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools import config


class AccountMove(models.Model):
	_inherit = "account.move"
	# _rec_names_search = ['name', 'partner_id.name', 'ref', 'custom_reference']

	custom_reference = fields.Char(string="Custom Reference", copy=False)
	referral_partner_id = fields.Many2one("referral.partner", tracking=True)
	source_doctor_id = fields.Many2one(
		"res.partner", domain="[('partner_type','=','physician')]", tracking=True)
	accession_no = fields.Char(tracking=True)
	age = fields.Char(related="partner_id.age", tracking=True)
	gender = fields.Selection(related="partner_id.gender", tracking=True)
	patient_type_id = fields.Many2one("patient.type", tracking=True)
	patient_type_name = fields.Char(related="patient_type_id.name", tracking=True)
	kmc_num = fields.Char(tracking=True)
	bed_num = fields.Char(tracking=True)
	ward_num = fields.Char(tracking=True)
	radiology_created = fields.Boolean(compute="_compute_radiology_created", tracking=True)
	radiology_id = fields.Many2one("radiology.request", readonly=True, tracking=True)

	move_type = fields.Selection(
		selection=[
			('entry', 'Journal Entry'),
			('out_invoice', 'Patient Invoice'),
			('out_refund', 'Customer Credit Note'),
			('in_invoice', 'Vendor Bill'),
			('in_refund', 'Vendor Credit Note'),
			('out_receipt', 'Sales Receipt'),
			('in_receipt', 'Purchase Receipt'),
		],
		string='Type',
		required=True,
		readonly=True,
		tracking=True,
		change_default=True,
		index=True,
		default="entry",
	)

	# @api.model_create_multi
	# def create(self, vals_list):
	# 	res = super(AccountMove, self).create(vals_list)
	# 	for rec in res:
	# 		if rec.move_type == 'out_invoice':
	# 			rec.custom_reference = self.env['ir.sequence'].next_by_code('custom.invoice') or '/'
	# 	return res

	@api.onchange('partner_id')
	def _onchange_partner_id_ref(self):
		if self.partner_id:
			self.referral_partner_id = self.partner_id.referral_partner_id.id

	def _compute_radiology_created(self):
		for rec in self:
			radiology = self.env['radiology.request'].search(
				[('invoice_id', '=', rec.id)])
			if radiology:
				rec.radiology_id = radiology[0].id
				if self.env.user.has_group('account.group_account_manager'):
					rec.radiology_created = False
				else:
					rec.radiology_created = True
			else:
				rec.radiology_created = False

	def action_view_radiology(self):
		return {
			'name': _('Radiology Request'),
			'res_model': 'radiology.request',
			'view_mode': 'tree,form',
			'view_type': 'tree,form',
			'type': 'ir.actions.act_window',
			'context': {
				'default_patient_id': self.partner_id.id,
				'default_date': fields.Date.today(),
				'default_invoice_id': self.id,
			},
			'domain': [('invoice_id', '=', self.id)]
		}

	def action_create_radiology_req(self):
		if not self.source_doctor_id:
			raise ValidationError("Please set Source Doctor")
		request = self.env['radiology.request'].create({
			'patient_id': self.partner_id.id,
			'physician_id': self.source_doctor_id.id,
			'invoice_id': self.id
		})
		for line in self.invoice_line_ids:
			lines = self.env['radiology.request.line'].create({
				'product_id': line.product_id.id,
				'radiology_request_id': request.id
			})
		return {
			'name': _('Radiology Request'),
			'res_model': 'radiology.request',
			'res_id': request.id,
			'view_mode': 'form',
			'view_type': 'form',
			'type': 'ir.actions.act_window',
			'context': {
					'default_patient_id': self.partner_id.id,
				'default_date': fields.Date.today(),
				'default_invoice_id': self.id,
			}
		}

	# Pricelist
	pricelist_id = fields.Many2one(
		comodel_name="product.pricelist",
		string="Category",
		states={"draft": [("readonly", False)]},
		compute="_compute_pricelist_id",
		tracking=True,
		store=True,
		readonly=True,
		precompute=True,
	)

	@api.constrains("pricelist_id", "currency_id")
	def _check_currency(self):
		if (
			not config["test_enable"]
			or (
				config["test_enable"]
				and self._context.get("force_check_currecy", False)
			)
		) and self.filtered(
			lambda a: a.pricelist_id
			and a.is_sale_document()
			and a.pricelist_id.currency_id != a.currency_id
		):
			raise UserError(
				_("Pricelist and Invoice need to use the same currency."))

	@api.depends("partner_id", "company_id")
	def _compute_pricelist_id(self):
		for invoice in self:
			if (
				invoice.partner_id
				and invoice.is_sale_document()
				and invoice.partner_id.property_product_pricelist
			):
				invoice.pricelist_id = invoice.partner_id.property_product_pricelist

	@api.depends("pricelist_id")
	def _compute_currency_id(self):
		res = super()._compute_currency_id()
		for invoice in self:
			if (
				invoice.is_sale_document()
				and invoice.pricelist_id
				and invoice.currency_id != invoice.pricelist_id.currency_id
			):
				invoice.currency_id = self.pricelist_id.currency_id
		return res

	def button_update_prices_from_pricelist(self):
		self.filtered(
			lambda r: r.state == "draft"
		).invoice_line_ids._compute_price_unit()


# Pricelist
class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	@api.onchange('product_id')
	def _onchange_product_id_domain(self):
		product_tmpls = self.move_id.pricelist_id.item_ids.filtered(lambda x: x.fixed_price).mapped('product_tmpl_id')
		products = self.env['product.product'].search([('product_tmpl_id','in',product_tmpls.ids)])
		if self.move_id.pricelist_id:
			return {"domain": {"product_id": [('id', 'in', products.ids)]}}

	@api.depends("quantity")
	def _compute_price_unit(self):
		res = super()._compute_price_unit()
		for line in self:
			if not line.move_id.pricelist_id:
				continue
			line.with_context(
				check_move_validity=False
			).price_unit = line._get_price_with_pricelist()
		return res

	def _calculate_discount(self, base_price, final_price):
		if base_price == 0.0:
			return 0.0
		discount = (base_price - final_price) / base_price * 100
		if (discount < 0 and base_price > 0) or (discount > 0 and base_price < 0):
			discount = 0.0
		return discount

	def _get_price_with_pricelist(self):
		price_unit = 0.0
		if self.move_id.pricelist_id and self.product_id and self.move_id.is_invoice():
			product = self.product_id
			qty = self.quantity or 1.0
			date = self.move_id.invoice_date or fields.Date.today()
			uom = self.product_uom_id
			(final_price, rule_id,) = self.move_id.pricelist_id._get_product_price_rule(
				product,
				qty,
				uom=uom,
				date=date,
			)
			if self.move_id.pricelist_id.discount_policy == "with_discount":
				price_unit = self.env["account.tax"]._fix_tax_included_price_company(
					final_price,
					product.taxes_id,
					self.tax_ids,
					self.company_id,
				)
				self.with_context(check_move_validity=False).discount = 0.0
				return price_unit
			else:
				rule_id = self.env["product.pricelist.item"].browse(rule_id)
				while (
					rule_id.base == "pricelist"
					and rule_id.base_pricelist_id.discount_policy == "without_discount"
				):
					new_rule_id = rule_id.base_pricelist_id._get_product_rule(
						product, qty, uom=uom, date=date
					)
					rule_id = self.env["product.pricelist.item"].browse(
						new_rule_id)
				base_price = rule_id._compute_base_price(
					product,
					qty,
					uom,
					date,
					target_currency=self.currency_id,
				)
				price_unit = max(base_price, final_price)
				self.with_context(
					check_move_validity=False
				).discount = self._calculate_discount(base_price, final_price)
		return price_unit


class AccountInvoiceReport(models.Model):
	_inherit = 'account.invoice.report'

	referral_partner_id = fields.Many2one("referral.partner")
	source_doctor_id = fields.Many2one("res.partner")

	@api.model
	def _select(self):
		return super(AccountInvoiceReport, self)._select() + ", move.referral_partner_id as referral_partner_id, move.source_doctor_id as source_doctor_id"
