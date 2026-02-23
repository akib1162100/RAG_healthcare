/** @odoo-module **/
import { MenuDropdown, MenuItem, NavBar } from '@web/webclient/navbar/navbar';
import { patch } from 'web.utils';
// import { ProfileSection } from "@sh_backmate_theme/js/profilesection";
import { ErrorHandler, NotUpdatable } from "@web/core/utils/components";

const components = { NavBar };
var rpc = require("web.rpc");
var ajax = require('web.ajax');
var theme_style = 'default';

var config = require("web.config");
var session = require('web.session');
var rpc = require('web.rpc')
var icon_style = 'standard';


rpc.query({
    model: 'sh.back.theme.config.settings',
    method: 'search_read',
    args: [[], ['icon_style']],
}, { async: false }).then(function (output) {
    if (output) {
        var i;
        for (i = 0; i < output.length; i++) {
            if (output[i]['icon_style']) {
                icon_style = output[i]['icon_style'];
            }

        }
    }
});

// Multi Tab Start
var enable_multi_tab = false

rpc.query({
    model: 'res.users',
    method: 'search_read',
    fields: ['sh_enable_multi_tab'],
    domain: [['id', '=', session.uid]]
}, { async: false }).then(function (data) {
    if (data) {
        _.each(data, function (user) {
            if (user.sh_enable_multi_tab) {
                enable_multi_tab = true
            }
        });

    }
});

rpc.query({
		model: 'sh.back.theme.config.settings',
		method: 'search_read',
		domain: [['id', '=', 1]],
		fields: ['theme_style']
	}).then(function (data) {
		if (data) {
			if (data[0]['theme_style'] == 'style_3') {
				theme_style = 'style_3'
			}
			else if (data[0]['theme_style'] == 'style_2') {
				theme_style = 'style_2'
			}
			else {
				theme_style = 'style_1'
			}

		}

	})


// Multi Tab End


// console.log(" NavBar.components", NavBar.components)

// NavBar.components = { MenuDropdown, MenuItem, NotUpdatable, ErrorHandler, ProfileSection };
// console.log(" NavBar.components", NavBar.components)
patch(components.NavBar.prototype, 'sh_backmate_theme_adv/static/src/js/navbar.js', {

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */

    // mobileNavbarTabs(...args) {
    //     return [...this._super(...args), {
    //         icon: 'fa fa-comments',
    //         id: 'livechat',
    //         label: this.env._t("Livechat"),
    //     }];
    // }

    async setup(parent, menuData) {
        this._super();
        if (enable_multi_tab){
            this.addmultitabtags()
            var self = this
            $(document).on('click', '.multi_tab_section .remove_tab', function(ev){self._RemoveTab(ev)});
            $(document).on('click', '.multi_tab_section .multi_tab_div a', function(ev){self._TabClicked(ev)});
        }
    },

    onNavBarDropdownItemSelection(menu) {
        $(".sh_backmate_theme_appmenu_div").toggleClass("sidebar_toggle");
        $(".blur_div").toggleClass("blur_toggle");
        $('.o_menu_systray').css("opacity", '1');

        if (enable_multi_tab){
            if(window.event.shiftKey){
                this._createMultiTab(menu)
            }
        }

        if(this.websiteCustomMenus){
            const websiteMenu = this.websiteCustomMenus.get(menu.xmlid);
            if (websiteMenu) {
                return this.websiteCustomMenus.open(menu);
            }
        }

        if (menu) {
            this.menuService.selectMenu(menu);
        }
    },

    _createMultiTab: function (ev) {
            var tab_name = ev.name
            var url = '#menu_id='+ev.id + '&action='+ ev.actionID
            var actionId = ev.actionID
            var menuId = ev.id
            var menu_xmlid = ev.xmlid
            var self = this
            localStorage.setItem('LastCreatedTab',actionId)

            ajax.jsonRpc('/add/mutli/tab','call', {
                'name':tab_name,
                'url':url,
                'actionId':actionId,
                'menuId':menuId,
                'menu_xmlid':menu_xmlid,
            }).then(function(rec) {
                self.addmultitabtags(ev)
            });
         },

    addmultitabtags: function (ev) {
            var self = this
            ajax.jsonRpc('/get/mutli/tab','call', {
            }).then(function(rec) {
                if (rec){
                    if (theme_style == 'theme_style'){ $('body > header').css("height", "48px"); }
                    $('.multi_tab_section').empty()
                    $.each(rec, function( key, value ) {
                        var tab_tag = '<div class="d-flex justify-content-between multi_tab_div align-items-center"><a href="'+ value.url +'"'+' class="flex-fill" data-xml-id="'+ value.menu_xmlid +'" data-menu="'+ value.menuId +'" data-action-id="'+ value.actionId +'" multi_tab_id="'+value.id+'" multi_tab_name="'+value.name+'"><span>'+value.name+'</span></a><span class="remove_tab ml-4">X</span></div>'
                        $('.multi_tab_section').append(tab_tag)
                    })
                    var ShstoredActionId = sessionStorage.getItem("sh_current_action_id");
                    var ShstoredAction = sessionStorage.getItem("sh_current_action");

                    if (ShstoredActionId){
                        var TabDiv = $('.multi_tab_section .multi_tab_div');
                        var ActiveMenu = TabDiv.find('a[data-action-id="'+ ShstoredActionId +'"]');
                        ActiveMenu.parent().addClass('tab_active')
                    }

                    if (ev) {
                        var actionId = ev.actionID
                        var menu_xmlid = ev.xmlid

                        if(localStorage.getItem('LastCreatedTab')){
                            var target = '.multi_tab_section .multi_tab_div a[data-action-id="'+ localStorage.getItem('LastCreatedTab') +'"]'
                            $(target).parent().addClass('tab_active')
                            $(target)[0].click()
                            localStorage.removeItem('LastCreatedTab')
                        } else {
                            var target = '.multi_tab_section .multi_tab_div a[data-xml-id="'+ menu_xmlid +'"]'
                            $(target).parent().addClass('tab_active')
                            $(target)[0].click()
                        }
                    }
                    $('body').addClass("multi_tab_enabled");
                } else {
                    $('body').removeClass("multi_tab_enabled");
                }
            });
         },

    _RemoveTab: function (ev) {
            var self = this
            var multi_tab_id = $(ev.target).parent().find('a').attr('multi_tab_id')
            ajax.jsonRpc('/remove/multi/tab','call', {
                'multi_tab_id':multi_tab_id,
            }).then(function(rec) {
                if (rec){
                    if(rec['removeTab']){
                        $(ev.target).parent().remove()
                        var FirstTab = $('.multi_tab_section').find('.multi_tab_div:first-child')
                        if(FirstTab.length){
                            $(FirstTab).find('a')[0].click()
                            $(FirstTab).addClass('tab_active')
                        }
                    }
                    if(rec['multi_tab_count'] == 0){
                        $('body').removeClass("multi_tab_enabled");
                    }
                }
            });
         },

    _TabClicked: function (ev){
     localStorage.setItem("TabClick", true);
     localStorage.setItem("TabClickTilteUpdate", true);
     if($(ev.target).data('action-id')){
        $('.multi_tab_section').find('.tab_active').removeClass('tab_active');
        $(ev.target).parent().addClass('tab_active')
     }
    },

    get_current_company(){
        let current_company_id;
        if (session.user_context.allowed_company_ids) {
            current_company_id = session.user_context.allowed_company_ids[0];
        } else {
            current_company_id = session.user_companies ?
                session.user_companies.current_company :
                false;
        }

        return current_company_id;
    },
    getIconStyle() {
        return icon_style;
    },
    getAppClassName(app){
        var app_name = app.xmlid
        return app_name.replaceAll('.', '_')
    },
    getXmlID(app_id) {
        return this.menuService.getMenuAsTree(app_id).xmlid;
    },
    OnClickDropdown(ev){

			if (!$(ev.currentTarget).next().hasClass('show_ul')) {
				$(ev.currentTarget).next('.dropdown-menu-right').first().slideDown('slow');


				$(ev.currentTarget).parents('.dropdown-menu').first().find('.show_ul').slideUp(600)
				$(ev.currentTarget).parents('.dropdown-menu').first().find('.show_ul').css("display", "none !important")
				$(ev.currentTarget).parents('.dropdown-menu').first().find('.show_ul').removeClass('show_ul');


				if ($(ev.currentTarget).next('.dropdown-menu').parents('.dropdown-header').length == 1) {
					$(ev.currentTarget).parents('.dropdown-menu').first().find('.sh_sub_dropdown').removeClass('sh_sub_dropdown');
					$(ev.currentTarget).next('.dropdown-menu').parents('.dropdown-header').children('.dropdown-item').addClass('sh_sub_dropdown');


				} else {
					$(ev.currentTarget).parents('.dropdown-menu').first().find('.sh_dropdown').removeClass('sh_dropdown');
					$(ev.currentTarget).parents('.dropdown-menu').first().find('.active').removeClass('active');

					$(ev.currentTarget).parents('.dropdown-menu').first().find('.sh_sub_dropdown').removeClass('sh_sub_dropdown');
					$(ev.currentTarget).next('.dropdown-menu').parents('.sh_dropdown_div').children('.dropdown-item').addClass('sh_dropdown');
					$(ev.currentTarget).next('.dropdown-menu').parents('.sh_dropdown_div').children('.dropdown-item').addClass('active');
				}
			}

			if ($(ev.currentTarget).next().hasClass('show_ul')) {
				$(ev.currentTarget).next('.dropdown-menu-right').first().slideUp(600);
				//  	  	$(this).next('.dropdown-menu-right').first().css("display","none");

				if ($(ev.currentTarget).next('.dropdown-menu').parents('.dropdown-header').length == 1) {
					$(ev.currentTarget).next('.dropdown-menu').parents('.dropdown-header').children('.dropdown-item').removeClass('sh_sub_dropdown');
				} else {

					$(ev.currentTarget).next('.dropdown-menu').parents('.sh_dropdown_div').children('span').removeClass('sh_dropdown');
					$(ev.currentTarget).next('.dropdown-menu').parents('.sh_dropdown_div').children('span').removeClass('active');
				}
			}

			var $subMenu = $(ev.currentTarget).next('.dropdown-menu');
			$subMenu.toggleClass('show_ul');
			// //$subMenu.parents('.dropdown-header').children('a.dropdown-item').toggleClass('sh_sub_dropdown');
			// $(ev.currentTarget).parents('.sh_backmate_theme_appmenu_div').find('.direct_menu').removeClass('focus')

			// $(ev.currentTarget).parents('li.nav-item.dropdown.show_ul').on('hidden.bs.dropdown', function (e) {
			// 	$('.dropdown-submenu .show_ul').removeClass('show_ul');
			// });


    },
    currentMenuAppSections(app_id) {

        return (
            (this.menuService.getMenuAsTree(app_id).childrenTree) ||
            []
        );
    },



    getThemeStyle(ev) {

        return theme_style;
    },
    isMobile(ev) {
        return config.device.isMobile;
    },
    click_secondary_submenu(ev) {
        if (config.device.isMobile) {
            $(".sh_sub_menu_div").addClass("o_hidden");
        }

        $(".o_menu_sections").removeClass("show")
    },
    click_close_submenu(ev) {
        $(".sh_sub_menu_div").addClass("o_hidden");
        $(".o_menu_sections").removeClass("show")
    },
    click_mobile_toggle(ev) {
        $(".sh_sub_menu_div").removeClass("o_hidden");

    },
    // click_app_toggle(ev) {
    //     console.log(">>>>>>>>>>>>h_backmate_theme_appmenu_div", $(".sh_backmate_theme_appmenu_div"))
    //     if ($(".sh_backmate_theme_appmenu_div").hasClass("show")) {
    //         $("body").removeClass("sh_sidebar_background_enterprise");
    //         $(".sh_search_container").css("display", "none");

    //         $(".sh_backmate_theme_appmenu_div").removeClass("show")
    //         $(".o_action_manager").removeClass("d-none");
    //         $(".o_menu_brand").css("display", "block");
    //         $(".full").removeClass("sidebar_arrow");
    //         $(".o_menu_sections").css("display", "flex");
    //     } else {
    //         $(".sh_backmate_theme_appmenu_div").addClass("show")
    //         $("body").addClass("sh_sidebar_background_enterprise");
    //         $(".sh_backmate_theme_appmenu_div").css("opacity", "1");
    //         //$(".sh_search_container").css("display","block");
    //         $(".o_action_manager").addClass("d-none");
    //         $(".full").addClass("sidebar_arrow");
    //         $(".o_menu_brand").css("display", "none");
    //         $(".o_menu_sections").css("display", "none");
    //     }


    // },





});


