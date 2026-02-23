odoo.define('apranik_hospital_management.OpenPOButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');

    class OpenPOButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {

            await this.showTempScreen('PrescriptionOrderScreen');
        }
    }
    OpenPOButton.template = 'OpenPOButton';

    ProductScreen.addControlButton({
        component: OpenPOButton,
        condition: function() {
            return this.env.pos.config.check_prescription_knk;
        },
    });

    Registries.Component.add(OpenPOButton);

    return OpenPOButton;
});