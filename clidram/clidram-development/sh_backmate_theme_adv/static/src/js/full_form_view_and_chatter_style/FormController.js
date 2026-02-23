/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

var rpc = require("web.rpc");
var chatter_position = 'bottom'
var config = require("web.config");

rpc.query({
    model: 'sh.back.theme.config.settings',
    method: 'search_read',
    domain: [['id', '=', 1]],
    fields: ['chatter_type']
}).then(function (data) {
    if (data) {
       
        if (data[0]['chatter_type']) {
            chatter_position = data[0]['chatter_type'];
        }        
    }
});

patch(FormController.prototype, "sh_form_view_custom", {
    /**
     * Patch the css classes of the form container, to include an extra `flex-row` class.
     * Without it, it'd go for flex columns direction and it won't look good.
     *
     * @override
     */
    /**
     * This function is a patch for the FormController class in Odoo. It sets up the necessary properties
     * for the form view based on the configuration settings.
     *
     * @override
     */
    setup(){
        this._super();        
        if (chatter_position === "bottom"){
            this.hasChatterPositionSided = false;
            this.hasChatterPositionBottom = true;
        }
        if (chatter_position === "sided"){
            this.hasChatterPositionBottom = false;
            this.hasChatterPositionSided = true;
        }
        if (localStorage.getItem("is_full_width") == 't'){
            this.isfullformwidth=true;
        }
        else{
            this.isfullformwidth=false;
        }
    },
    /**
     * This function overrides the default className method of the FormController class in Odoo.
     * It modifies the CSS classes of the form container based on the configuration settings.
     *
     * @override
     * @returns {Object} - Returns an object containing CSS classes to be applied to the form container.
     *
     * @example
     * // Example usage:
     * const formController = new FormController();
     * const formClasses = formController.className();
     * console.log(formClasses); // Output: { "flex-row": true }
     */
    get className() {
        const result = this._super();
        if (chatter_position === "sided" && localStorage.getItem("is_full_width") == 'f') {
            result["flex-row"] = true;
        }
        if (localStorage.getItem("is_full_width") == 't'){
            this.isfullformwidth=true;
        }
        else{
            this.isfullformwidth=false;
        }
        return result;
    },

    /**
     * Checks if the form view is displayed in full screen mode.
     *
     * @function has_screen_full
     * @returns {boolean} - Returns true if the form view is in full screen mode, false otherwise.
     *
     * @example
     * // Example usage:
     * if (formController.has_screen_full()) {
     *     console.log("Form view is in full screen mode.");
     * } else {
     *     console.log("Form view is not in full screen mode.");
     * }
     */
    has_screen_full(){
        if (localStorage.getItem("is_full_width") == 't'){
            return true;
        } else {
            return false;
        }
    }
});
