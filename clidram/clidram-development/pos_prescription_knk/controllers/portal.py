from odoo import http, _, fields
from odoo.addons.portal.controllers.portal import CustomerPortal, get_records_pager
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.http import request
from collections import OrderedDict
import logging

_logger = logging.getLogger(__name__)


class PortalAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalAccount, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        my_prescriptions_count = request.env['prescription.order.knk'].sudo().search_count([
            ('patient_id', '=', partner.id),
            ('company_id', '=', request.env.user.company_id.id)
        ])
        values['my_prescriptions_count'] = my_prescriptions_count
        return values

    def _prepare_home_portal_values(self, counters):
        values = super(PortalAccount, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        my_prescriptions_count = request.env['prescription.order.knk'].sudo().search_count([
            ('patient_id', '=', partner.id),
            ('company_id', '=', request.env.user.company_id.id)
        ])

        if 'my_prescriptions_count' in counters:
            values['my_prescriptions_count'] = my_prescriptions_count
        return values

    @http.route(['/my/prescriptions', '/my/prescriptions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_prescriptions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PrescriptionObj = request.env['prescription.order.knk'].sudo()

        domain = [
            ('patient_id', '=', partner.id),
        ]

        searchbar_sortings = {
            'create_date': {'label': _('Create Date'), 'order': 'create_date desc'},
            'date': {'label': _('Prescription Date'), 'order': 'date asc'},
            'name': {'label': _('Prescription Number'), 'order': 'name asc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'create_date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'prescribed_state': {'label': _('Prescribed'), 'domain': [('state', '=', 'prescribed')]},
            'draft_state': {'label': _('New'), 'domain': [('state', 'in', ['draft'])]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        prescriptions_count = PrescriptionObj.search_count(domain)

        # make pager
        pager = request.website.pager(
            url="/my/prescriptions",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=prescriptions_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        prescriptions = PrescriptionObj.search(domain, limit=self._items_per_page, offset=pager['offset'], order=order)
        request.session['my_prescriptions_history'] = prescriptions.ids[:100]

        values.update({
            'date': date_begin,
            'prescription_obj': prescriptions,
            'pager': pager,
            'default_url': '/my/prescriptions',
            'page_name': 'prescription_mgmt',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("pos_prescription_knk.portal_my_prescriptions", values)

    @http.route('/my/prescription/<int:prescription_id>', type='http', auth='user', website=True)
    def portal_prescription_report(self, prescription_id, format=None, **kw):
        prescription = request.env['prescription.order.knk'].sudo().browse(prescription_id)

        if not prescription.exists():
            return request.not_found()

        if format == 'pdf':
            pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'pos_prescription_knk.action_prescription_order_report',
                [prescription.id]
            )
            pdf_headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', 'attachment; filename="Prescription-%s.pdf"' % prescription.name)
            ]
            return request.make_response(pdf_content, headers=pdf_headers)

        # Default: HTML
        html_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_html(
            'pos_prescription_knk.action_prescription_order_report_html',
            [prescription.id]
        )
        return request.make_response(html_content)
