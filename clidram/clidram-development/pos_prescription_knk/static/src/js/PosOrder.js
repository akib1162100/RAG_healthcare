odoo.define('apranik_hospital_management.PosReceipt', function(require) {
    "use strict";

    var { Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const PosPrescriptionOrder = (Order) => class PosPrescriptionOrder extends Order {
        constructor(obj, options) {
            super(...arguments);
            this.is_prescription_enable = false;
            this.prescription_order = false;
            this.pres_id = '';
        }
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.is_prescription_enable = this.is_prescription_enable;
            json.prescription_order = this.prescription_order;
            json.presc_id = this.presc_id;
            return json;
        }
        //@override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.is_prescription_enable = json.is_prescription_enable;
            this.prescription_order = json.prescription_order;
            this.pres_id = json.pres_id;
        }
    }
    Registries.Model.extend(Order, PosPrescriptionOrder);


});