/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { Component, EventBus } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

const components = { Dropdown };

patch(components.Dropdown.prototype, 'sh_recently_viewed_records/static/src/js/dropdown.js', {
    onDropdownStateChanged(...args) {
        this._super.apply(this, args);
        if($('.o_recent_records_dropdown').css('display') == 'block'){
             $('.o_recent_records_dropdown').css('display','none')
        }
    }
});