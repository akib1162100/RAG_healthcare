/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";

patch(FormRenderer.prototype, 'sh_form_view_custom', {
    /**
     * This function compiles parameters for the form renderer.
     * It extends the parent class's compileParams method by adding custom parameters:
     * - hasChatterPositionSided: Indicates whether the chatter panel should be positioned on the side.
     * - hasChatterPositionBottom: Indicates whether the chatter panel should be positioned at the bottom.
     * - isfullformwidth: Indicates whether the form should take up the full width of the view.
     *
     * @returns {Object} An object containing the compiled parameters.
     */
    get compileParams() {
        return {
            ...this._super(),
            hasChatterPositionSided: this.props.hasChatterPositionSided,
            hasChatterPositionBottom: this.props.hasChatterPositionBottom,
            isfullformwidth: this.props.isfullformwidth,
        };
    },
});