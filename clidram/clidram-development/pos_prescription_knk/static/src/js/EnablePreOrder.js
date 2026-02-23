odoo.define('pos_prescription_knk.EnablePreOrder', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');

    class EnablePreOrder extends PosComponent {
        setup() {
            super.setup();
            useListener('click-enable-prescription', this._onClickEnablePre);
        }
        get _currentOrder() {

            return this.env.pos.get_order();
        }
        async _onClickEnablePre() {
            let elem = $(document.getElementById('prescription_enable'));
            if (!this._currentOrder.is_prescription_enable) {
                this._currentOrder.is_prescription_enable = true;
                elem.removeClass("odoo-theme-color1");
                elem.addClass("odoo-theme-color");
            } else {
                elem.removeClass("odoo-theme-color");
                elem.addClass("odoo-theme-color1");
                this._currentOrder.is_prescription_enable = false;
            }
        }
    }
    EnablePreOrder.template = 'EnablePreOrder';

    ProductScreen.addControlButton({
        component: EnablePreOrder,
        condition: function() {
            return this.env.pos.config.pos_prescription_knk == 'enable_option';
        },
    });

    Registries.Component.add(EnablePreOrder);

    return EnablePreOrder;
});