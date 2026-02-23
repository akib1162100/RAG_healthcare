odoo.define('apranik_hospital_management.PODetail', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    var { Orderline, Order } = require('point_of_sale.models');


    class PODetail extends AbstractAwaitablePopup {
        setup() {
            super.setup();
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        async _get_prescription_lines(lines) {
            let self = this;
            let prescription_line_domain = [
                ['id', 'in', lines]
            ];
            let pre_line_ids = {};
            try {
                await self.rpc({
                    model: 'prescription.order.line.knk',
                    method: 'search_read',
                    args: [prescription_line_domain],
                }).then(function(output) {
                    output.forEach(function(order) {
                        pre_line_ids[order.id] = order
                    });
                });
                return pre_line_ids
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to load products.'),
                    });
                } else {
                    throw error;
                }
            }
        }

        async addProducts(event) {
            let lines = []
            this.props.order.order_line_new_ids.forEach(function(line) {
                lines.push(line)
            })
            let pre_lines = await this._get_prescription_lines(lines)
            if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            this.currentOrder.prescription_order = true;
            this.currentOrder.pres_id = this.props.order.id
            for (let key of Object.keys(pre_lines)) {
                if (this.env.pos.db.get_product_by_id(pre_lines[key].product_id[0])) {
                    var orderline = Orderline.create({}, {
                        pos: this.env.pos,
                        order: this.currentOrder,
                        product: this.env.pos.db.get_product_by_id(pre_lines[key].product_id[0]),
                        price: pre_lines[key].unit_price,
                    });
                    orderline.quantity = pre_lines[key].quantity;
                    orderline.quantityStr = String(pre_lines[key].quantity);
                    orderline.discount = 0.0;
                    orderline.price = pre_lines[key].unit_price;
                    orderline.selected = false;
                    orderline.price_manually_set = true;
                    orderline.comment_dr = pre_lines[key].short_comment;
                    this.env.pos.get_order().add_orderline(orderline);
                    this.env.pos.get_order().doctor_note = this.props.order.notes;
                }
            }
            if (!this.currentOrder.get_partner()) {
                let newClient = this.env.pos.db.get_partner_by_id(this.props.order.patient_id[0]);
                this.currentOrder.set_partner(newClient);
                this.currentOrder.set_pricelist(
                    _.findWhere(this.env.pos.pricelists, {
                        id: newClient.property_product_pricelist[0],
                    }) || this.env.pos.default_pricelist
                );

            }
            this.cancel();
        }
    }

    PODetail.template = 'PODetail';
    Registries.Component.add(PODetail);
    return PODetail;
});