/** @odoo-module **/

// import { ListController } from "@web/views/list/list_controller";
// import core from "web.core";
// var _t = core._t;
// import { patch } from "@web/core/utils/patch";

// patch(ListController.prototype, 'sh_backmate_theme_adv/static/src/js/list_controller.js', {
   
//     _onClickRefreshView (ev) { 
//         this.actionService.switchView('list');
//     }
  
// });

import { ListController } from "@web/views/list/list_controller";
import core from "web.core";
var _t = core._t;
import { patch } from "@web/core/utils/patch";
const rpc = require("web.rpc");
const session = require("web.session");

var show_expand_collapse = false
rpc.query({
    model: 'res.users',
    method: 'search_read',
    fields: ['sh_enable_expand_collapse'],
    domain: [['id', '=', session.uid]]
}, { async: false }).then(function (data) {
    if (data) {
        _.each(data, function (user) {
            if (user.sh_enable_expand_collapse) {
                show_expand_collapse = true
            }
        });

    }
});

patch(ListController.prototype, 'sh_backmate_theme_adv/static/src/js/list_controller.js', {
   
    setup(...args) {

        this._super(...args)
        this.show_expand_collapse = show_expand_collapse;    
    },

    _onClickRefreshView (ev) { 
        this.actionService.switchView('list');
    },

    shExpandGroups () {

        $(document).find('.o_group_header').each(function () {
            var $header = $(this);
            if (!$header.hasClass('o_group_open')) {
                $header.find('.o_group_name').click();
            }
        });
    },

    shCollapseGroups () {
        $(document).find('.o_group_header').each(function () {
            var $header = $(this);
            if ($header.hasClass('o_group_open')) {
                $header.find('.o_group_name').click();
            }
        });
    },
  
});


