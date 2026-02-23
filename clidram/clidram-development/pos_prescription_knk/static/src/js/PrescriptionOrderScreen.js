odoo.define('apranik_hospital_management.PrescriptionOrderScreen', function(require) {
    'use strict';


    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { debounce } = require("@web/core/utils/timing");
    const { useListener } = require("@web/core/utils/hooks");

    class PrescriptionOrderScreen extends PosComponent {
        setup() {
            super.setup();
            this.state = {
                query: null,
                selectedPrescriptionOrder: this.props.client,
            };

            useListener('click-showDetails', this.showDetails);
            this.prescriptionorders = this.get_prescription_orders()[0] || [];
            this.po_lines = this.get_prescription_orders()[1] || [];
            this.updatePrescriptionOrderList = debounce(this.updatePrescriptionOrderList, 70);
        }

        back() {
            this.props.resolve({ confirmed: false, payload: false });
            this.trigger('close-temp-screen');
        }

        addProducts(event) {
            if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            console.log("bbb")
            const product = event.detail;
            let price_extra = 0.0;
            let description, packLotLinesToEdit;
            this.currentOrder.add_product(product, {
                description: description,

            });
        }

        get prescription_orders() {

            let self = this;
            let query = this.state.query;
            if (query) {
                query = query.trim();
                query = query.toLowerCase();
            }
            if (this.prescriptionorders) {
                if (query && query !== '') {
                    return this.search_prescription_orders(this.prescriptionorders, query);
                } else {
                    return this.prescriptionorders;
                }
            } else {
                let odrs = this.get_prescription_orders()[0] || [];
                if (query && query !== '') {
                    return this.search_prescription_orders(odrs, query);
                } else {
                    return odrs;
                }
            }
        }

        async updatePrescriptionOrderList(event) {

            this.state.query = event.target.value;
            const prescription_orders = this.prescription_orders;
            if (event.code === 'Enter' && prescription_orders.length === 1) {
                this.state.selectedPrescriptionOrder = prescription_orders[0];

            } else {
                this.render();
            }
        }

        clickPrescriptionOrder(event) {
            let order = event.detail.order;
            if (this.state.selectedPrescriptionOrder === order) {
                this.state.selectedPrescriptionOrder = null;
            } else {
                this.state.selectedPrescriptionOrder = order;
            }
            this.render();
        }

        get_current_day() {
            let self = this;
            let days = self.env.pos.config.load_orders_days;
            let today = new Date();
            if (days > 0) {
                today.setDate(today.getDate() - days);
            }
            let dd = today.getDate();
            let mm = today.getMonth() + 1; //January is 0!
            let yyyy = today.getFullYear();
            if (dd < 10) {
                dd = '0' + dd;
            }
            if (mm < 10) {
                mm = '0' + mm;
            }
            today = yyyy + '-' + mm + '-' + dd;
            return today;
        }

        get_orders_domain() {

            let self = this;
            let pos_config = self.env.pos.config;
            let pos_partner = self.env.pos.selectedOrder.partner;
            let today = self.get_current_day();
            let days = self.env.pos.config.load_orders_days;
            if (days > 0) {

                if (pos_partner) {

                    return [
                        ['prescription_date', '>=', today],
                        ['partner_id', '=', pos_partner.id],
                        ['state', 'not in', ['canceled']]
                    ];
                } else {
                    return [
                        ['prescription_date', '>=', today],
                        ['state', 'not in', ['canceled']]
                    ];
                }
            } else {
                return [
                    ['state', 'in', ['draft', 'prescription']]
                ];
            }
        }

        async get_prescription_orders() {

            let self = this;
            let prescription_domain = self.get_orders_domain();
            let load_orders = [];
            let load_orders_line = [];
            let order_ids = [];
            try {
                await self.rpc({
                    model: 'prescription.order.knk',
                    method: 'search_read',
                    args: [prescription_domain],
                }).then(function(output) {
                    load_orders = output;
                    self.env.pos.db.get_so_by_id = {};
                    load_orders.forEach(function(order) {
                        order_ids.push(order.id)
                        self.env.pos.db.get_so_by_id[order.id] = order;
                    });
                    let fields_domain = [
                        ['prescription_id', 'in', order_ids]
                    ];
                    self.rpc({
                        model: 'prescription.order.line.knk',
                        method: 'search_read',
                        args: [fields_domain],
                    }).then(function(output1) {
                        load_orders_line = output1;
                        self.prescriptionorders = load_orders;
                        self.po_lines = output1;
                        self.env.pos.db.get_so_line_by_id = {};
                        output1.forEach(function(ol) {
                            self.env.pos.db.get_so_line_by_id[ol.id] = ol;
                        });
                        self.render();
                        return [load_orders, load_orders_line]
                    });

                });
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to load prescriptionorders.'),
                    });
                } else {
                    throw error;
                }
            }
        }

        showDetails(event) {
            let self = this;
            let o_id = parseInt(event.detail.id);
            let prescriptionorders = self.prescriptionorders;
            let po_lines = self.po_lines;
            let orders1 = [event.detail];

            let pos_lines = [];

            for (let n = 0; n < po_lines.length; n++) {
                if (po_lines[n]['prescription_id'][0] == o_id) {
                    pos_lines.push(po_lines[n])
                }
            }
            self.showPopup('PODetail', {
                'order': event.detail,
                'orderline': pos_lines,
            });
        }
    }


    PrescriptionOrderScreen.template = 'PrescriptionOrderScreen';
    PrescriptionOrderScreen.hideOrderSelector = true;
    Registries.Component.add(PrescriptionOrderScreen);
    return PrescriptionOrderScreen;
});