odoo.define('apranik_hospital_management.PrescriptionOrders', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");


    class PrescriptionOrders extends PosComponent {
        setup() {
            super.setup();
        }

        get order() {
            return this.props.order;
        }
        get highlight() {
            return this.props.order !== this.props.selectedPrescriptionOrder ?
                '' : 'highlight';
        }

        get patient() {
            return this.order.patient_id[1];
        }
        get name() {
            return this.order.name;
        }
        get date() {
            return moment(this.order.prescription_date).format('YYYY-MM-DD hh:mm A');
        }
        get physician() {
            const partner = this.order.physician_id;
            return partner ? partner[1] : null;
        }
    }
    PrescriptionOrders.template = 'PrescriptionOrders';

    Registries.Component.add(PrescriptionOrders);

    return PrescriptionOrders;
});