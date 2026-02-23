odoo.define('pos_prescription_knk.pos_model', function(require) {
    "use strict";

    var { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');


    const PosPrescriptionPosGlobalState = (PosGlobalState) => class PosPrescriptionPosGlobalState extends PosGlobalState {
        constructor() {
            super(...arguments);
            this.is_prescription_order = false;

        }
    }
    Registries.Model.extend(PosGlobalState, PosPrescriptionPosGlobalState);

});