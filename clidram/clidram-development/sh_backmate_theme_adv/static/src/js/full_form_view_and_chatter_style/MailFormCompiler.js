/** @odoo-module **/


import {MailFormCompiler} from "@mail/views/form/form_compiler";
import {patch} from "@web/core/utils/patch";
import { uiService,SIZES } from "@web/core/ui/ui_service";

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

patch(MailFormCompiler.prototype, "sh_form_view_custom", {
    /**
     * This function is responsible for compiling the form view in the Odoo Mail module.
     * It modifies the XML structure of the form view to adjust the position of the chatter container based on the
     * 'chatter_position' configuration.
     *
     * @returns {XMLDocument} The modified XML structure of the form view.
     */
    compile() {
        const res = this._super.apply(this, arguments);
        const chatterContainerHookXml = res.querySelector(
            ".o_FormRenderer_chatterContainer"
        );

        // If the chatter container hook XML element is not found, return the original XML structure
        if (!chatterContainerHookXml) {
            return res;
        }

        // If the 'chatter_position' configuration is set to 'normal', hide the chatter container
        if (chatter_position === "bottom") {
            chatterContainerHookXml.setAttribute("t-if", false);
        }
        // If the 'chatter_position' configuration is not set to 'normal', show the chatter container only when there are no attachments or the screen is not in full-screen mode
        else {
            chatterContainerHookXml.setAttribute("t-if", `!hasAttachmentViewer() and !has_screen_full() and uiService.size >= ${SIZES.XXL}`);
        }

        return res;
    },
});




