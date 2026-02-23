
//===========================================
// Night Mode
//===========================================

odoo.define('sh_backmate_theme_adv.night_mode_systray', function (require) {
	"use strict";

	var core = require('web.core');
	var Dialog = require('web.Dialog');
	var Widget = require('web.Widget');
	var rpc = require('web.rpc');
	var SystrayMenu = require('web.SystrayMenu');
	var session = require('web.session');
	var _t = core._t;
	var QWeb = core.qweb;
	var NightModeTemplate = Widget.extend({
		template: "NightModeTemplate",
		events: {
			'click #sun_button': '_click_sun_button',
			'click #moon_button': '_click_moon_button',
		},
		init: function () {
			this._super.apply(this, arguments);
			var self = this;
			
			if ($('.o_web_client').hasClass('sh_night_mode')) {
				this.day_mode = false;
			} else {
				this.day_mode = true;
			}
	   },

	   _click_sun_button: function (ev) {
		   ev.preventDefault();
		   var self = this;
		   $('.o_web_client').removeClass('sh_night_mode');
		   localStorage.setItem("is_night_mode", "f");
			  
		   $('#moon_button').css("display", "inline-flex");
		   $('#sun_button').css("display", "none");
	   },
	   _click_moon_button: function (ev) {
		   ev.preventDefault();
		   var self = this;
		   localStorage.setItem("is_night_mode", "t");
			  
		   $('.o_web_client').addClass('sh_night_mode');
		   $('#moon_button').css("display", "none");
		   $('#sun_button').css("display", "inline-flex");
	   },


	});

	NightModeTemplate.prototype.sequence = 99;
	rpc.query({
		model: 'res.users',
		method: 'search_read',
		fields: ['sh_enable_night_mode'],
		domain: [['id', '=', session.uid]]
	}, { async: false }).then(function (data) {
		if (data) {
			_.each(data, function (user) {
				if (user.sh_enable_night_mode) {
					SystrayMenu.Items.push(NightModeTemplate);

				}
			});

		}
	});

	return {
		NightModeTemplate: NightModeTemplate,
	};
});