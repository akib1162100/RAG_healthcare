/** @odoo-module **/
import { ActionContainer } from '@web/webclient/actions/action_container';
import {patch} from "@web/core/utils/patch";
import {  xml } from "@odoo/owl";

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

patch(ActionContainer.prototype, 'sh_form_view_custom', {
    /**
     * This function is responsible for setting up the class attribute for the action manager container.
     * It checks the chatter position and the full width setting from local storage to determine the appropriate class names.
     *
     * @function setup
     * @memberof ActionContainer.prototype
     * @instance
     *
     * @returns {void}
     */
    setup() {
        this._super()
        alert('1234567')
        var action_manager_cls = 'o_action_manager'
        if(chatter_position == 'bottom'){
            action_manager_cls += ' sh_chatter_normal'
            if (localStorage.getItem("is_full_width") == 't') {
                action_manager_cls += ' sh_full_content'
            }
        }else{
            action_manager_cls += ' sh_chatter_sided'
        
        if (localStorage.getItem("is_full_width") == 't') {
            action_manager_cls += ' sh_full_content'
        }else{
            action_manager_cls += ' sh_normal_form_content'
        }}
        this.action_manager_cls = action_manager_cls
    }

});
ActionContainer.template = xml`
    <t t-name="web.ActionContainer">
      <div t-att-class="action_manager_cls">
        <t t-if="info.Component" t-component="info.Component" className="'o_action'" t-props="info.componentProps" t-key="info.id"/>
      </div>
    </t>`;
