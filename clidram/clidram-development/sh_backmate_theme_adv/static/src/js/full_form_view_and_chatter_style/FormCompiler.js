/** @odoo-module **/
import {patch} from "@web/core/utils/patch";

import {FormCompiler} from "@web/views/form/form_compiler";
import {useExternalListener} from "@odoo/owl";
var session = require('web.session');

import {append,createElement,getTag, setAttributes} from "@web/core/utils/xml";
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

patch(FormCompiler.prototype, "sh_form_view_custom", {
    /**
     * Sets up the necessary event listener for the full-width form feature.
     * This function is called during the initialization of the FormCompiler.
     *
     * @function setup
     * @memberof FormCompiler.prototype
     * @instance
     *
     * @returns {void}
     */
    setup() {
        this._super();
        useExternalListener(window, "click", this._onClickFullWidthForm);
    },

    /**
     * Handles the click event on the full-width form toggle icon.
     * This function toggles the full-width form view and updates the UI accordingly.
     *
     * @param {Event} ev - The click event object.
     * @param {Event.target} ev.target - The element that received the click event.
     * @param {Event.target.parentNode} ev.target.parentNode - The parent element of the clicked element.
     * @param {Event.target.parentNode.parentNode} ev.target.parentNode.parentNode - The grandparent element of the clicked element.
     * @param {Event.target.parentNode.parentNode.querySelector} ev.target.parentNode.parentNode.querySelector('.o_form_sheet') - The form sheet element.
     * @param {Event.target.parentNode.parentNode.querySelector} ev.target.parentNode.parentNode.querySelector('.o_action_manager') - The action manager element.
     * @param {Event.target.parentNode.parentNode.querySelector} ev.target.parentNode.parentNode.querySelector('.full_form_toggle') - The full-width form toggle element.
     * @param {Event.target.parentNode.parentNode.querySelector} ev.target.parentNode.parentNode.querySelector('.sh_normal_form_content') - The element to add or remove the 'sh_normal_form_content' class.
     * @param {Event.composedPath|Event.path} ev.composedPath || ev.path - The path of the event target.
     * @param {localStorage.getItem} localStorage.getItem("is_full_width") - Retrieves the value of the 'is_full_width' item from the local storage.
     * @param {chatter_position} chatter_position - The position of the chatter in the form.
     * @param {this.uiService.bus.trigger} this.uiService.bus.trigger('resize') - Triggers a 'resize' event on the UI service bus.
     * @param {this.props.chatter.refresh} this.props.chatter.refresh() - Refreshes the chatter component.
     *
     * @returns {void}
     */
    _onClickFullWidthForm(ev) {
        var Path = ev.composedPath ? ev.composedPath() : ev.path;
        if(Path != undefined && Path[1] != undefined){
            if($(Path[1]).hasClass('sh_full_screen_icon_div') || $(Path[1]).hasClass('full_form_toggle') || $(Path[1]).hasClass('sh_ffw_svg')){
                if (localStorage.getItem("is_full_width") == 't') {
                    localStorage.setItem("is_full_width", "f");
                    $(ev.target).parents().find('.o_form_sheet').removeClass("sh_full_form")
                    $(ev.target).parents().find('.o_action_manager').removeClass("sh_full_content")
                    if (chatter_position === "sided"){
                        $(ev.target).parents().find('.o_action_manager').addClass("sh_normal_form_content")
                    }
                    $(ev.target).parents().find('.full_form_toggle').replaceWith('<span class="full_form_toggle"><svg class="sh_ffw_svg" id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 469.68 147.37"><title>full screen - new</title><path d="M233.65,236.91h-152l37-37s7-8-2-17c0,0-5-8-18-3l-69,65s-6,6,0,15l60,64s10,5,19-2c0,0,10-8,5-20l-33-35,152-1s11-1,13-14C245.65,251.91,246.65,236.91,233.65,236.91Z" transform="translate(-26.98 -178.27)"/><path d="M290,267H442l-37,37s-7,8,2,17c0,0,5,8,18,3l69-65s6-6,0-15l-60-64s-10-5-19,2c0,0-10,8-5,20l33,35-152,1s-11,1-13,14C278,252,277,267,290,267Z" transform="translate(-26.98 -178.27)"/></svg></span>')

                } else {
                    localStorage.setItem("is_full_width", "t");
                    $(ev.target).parents().find('.o_form_sheet').addClass("sh_full_form")
                    $(ev.target).parents().find('.o_action_manager').addClass("sh_full_content")
                    if (chatter_position === "sided"){
                        $(ev.target).parents().find('.o_action_manager').removeClass("sh_normal_form_content")
                    }
                    $(ev.target).parents().find('.full_form_toggle').replaceWith('<span class="full_form_toggle"><svg class="sh_ffw_svg" id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 469.68 147.37"><title>exit full screen - new</title><path d="M39,267H191l-37,37s-7,8,2,17c0,0,5,8,18,3l69-65s6-6,0-15l-60-64s-10-5-19,2c0,0-10,8-5,20l33,35L40,238s-11,1-13,14C27,252,26,267,39,267Z" transform="translate(-26.98 -178.27)"/><path d="M484.65,236.91h-152l37-37s7-8-2-17c0,0-5-8-18-3l-69,65s-6,6,0,15l60,64s10,5,19-2c0,0,10-8,5-20l-33-35,152-1s11-1,13-14C496.65,251.91,497.65,236.91,484.65,236.91Z" transform="translate(-26.98 -178.27)"/></svg></span>')

                }
                this.uiService.bus.trigger('resize');
                var chatterContainer = $(ev.target).parents().find('.o_FormRenderer_chatterContainer');
                if (chatterContainer.length > 0) {
                    if (this.props.chatter) {
                        this.props.chatter.refresh();
                    }
                } 
            }
        }
    },

    /**
 * This function compiles a sheet element for the form view.
 * It adds a background div and a foreground div to the sheet.
 * If the full width form feature is enabled, it adds a full screen icon to the sheet.
 * The function iterates through the child nodes of the sheet element, compiles each node,
 * and appends the compiled node to the foreground div.
 *
 * @param {HTMLElement} el - The sheet element to be compiled.
 * @param {Object} params - Additional parameters for the compilation process.
 *
 * @returns {HTMLElement} - The compiled sheet element with the background and foreground divs.
 */
    compileSheet(el, params) {
        const sheetBG = createElement("div");
        sheetBG.className = "o_form_sheet_bg";

        const sheetFG = createElement("div");

        if(session.sh_enable_full_width_form){
            if (localStorage.getItem("is_full_width") == 't') {
                sheetFG.className = "o_form_sheet position-relative sh_full_form";
                sheetFG.innerHTML = '<div class="sh_full_screen_icon_div"><span class="full_form_toggle" ><svg class="sh_ffw_svg" id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 469.68 147.37"><title>exit full screen - new</title><path d="M39,267H191l-37,37s-7,8,2,17c0,0,5,8,18,3l69-65s6-6,0-15l-60-64s-10-5-19,2c0,0-10,8-5,20l33,35L40,238s-11,1-13,14C27,252,26,267,39,267Z" transform="translate(-26.98 -178.27)"/><path d="M484.65,236.91h-152l37-37s7-8-2-17c0,0-5-8-18-3l-69,65s-6,6,0,15l60,64s10,5,19-2c0,0,10-8,5-20l-33-35,152-1s11-1,13-14C496.65,251.91,497.65,236.91,484.65,236.91Z" transform="translate(-26.98 -178.27)"/></svg></span></div>'
               append(sheetBG);
            }else{
                sheetFG.className = "o_form_sheet position-relative";
                sheetFG.innerHTML = '<div class="sh_full_screen_icon_div"><span class="full_form_toggle"><svg class="sh_ffw_svg" id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 469.68 147.37"><title>full screen - new</title><path d="M233.65,236.91h-152l37-37s7-8-2-17c0,0-5-8-18-3l-69,65s-6,6,0,15l60,64s10,5,19-2c0,0,10-8,5-20l-33-35,152-1s11-1,13-14C245.65,251.91,246.65,236.91,233.65,236.91Z" transform="translate(-26.98 -178.27)"/><path d="M290,267H442l-37,37s-7,8,2,17c0,0,5,8,18,3l69-65s6-6,0-15l-60-64s-10-5-19,2c0,0-10,8-5,20l33,35-152,1s-11,1-13,14C278,252,277,267,290,267Z" transform="translate(-26.98 -178.27)"/></svg></span></div>'
               append(sheetBG);
            }
        }else{
            sheetFG.className = "o_form_sheet position-relative";
        }
        append(sheetBG, sheetFG);
        for (const child of el.childNodes) {
            const compiled = this.compileNode(child, params);
            if (!compiled) {
                continue;
            }
            if (getTag(child, true) === "field") {
                compiled.setAttribute("showTooltip", true);
            }
        append(sheetFG, compiled);
        }
        return sheetBG;
    },
    
    /**
     * This function compiles the form view and handles the chatter position based on the provided parameters.
     * It modifies the DOM structure to accommodate the chatter position settings and ensures that the chatter
     * is displayed correctly in the form sheet.
     *
     * @param {HTMLElement} node - The root node of the form view.
     * @param {Object} params - Additional parameters for the compilation process.
     * @param {boolean} params.hasChatterPositionBottom - Indicates whether the chatter position is set to "bottom".
     * @param {boolean} params.hasChatterPositionSided - Indicates whether the chatter position is set to "sided".
     * @param {boolean} params.hasAttachmentViewerInArch - Indicates whether the form view has an attachment viewer.
     * @param {boolean} params.isfullformwidth - Indicates whether the full width form feature is enabled.
     *
     * @returns {HTMLElement} - The compiled form view with the modified DOM structure.
     */
    compile(node, params) {
        const res = this._super.apply(this, arguments);
        const chatterContainerHookXml = res.querySelector(
            ".o_FormRenderer_chatterContainer:not(.o-isInFormSheetBg)"
        );
        if (!chatterContainerHookXml) {
            return res;
        }
        if (chatterContainerHookXml.parentNode.classList.contains("o_form_sheet")) {
            return res;
        }
        // Don't patch anything if the setting is "auto": this is the core behaviour
        if (!params.hasChatterPositionBottom && !params.hasChatterPositionSided) {
            return res;
        }
        // For "bottom", we keep the chatter in the form sheet
        // (the one used for the attachment viewer case)
        // If it's not there, we create it.
        else if (params.hasChatterPositionSided) {
            if (params.hasAttachmentViewerInArch) {
                const sheetBgChatterContainerHookXml = res.querySelector(
                    ".o_FormRenderer_chatterContainer.o-isInFormSheetBg"
                );
                sheetBgChatterContainerHookXml.setAttribute("t-if", true);
                chatterContainerHookXml.setAttribute("t-if", false);

            } else {                
                const formSheetBgXml = res.querySelector(".o_form_sheet_bg");
                if (!formSheetBgXml) {
                    return res; // miss-config: a sheet-bg is required for the rest
                }
                const parentXml = formSheetBgXml && formSheetBgXml.parentNode;
                if (!parentXml) {
                    return res; // miss-config: a sheet-bg is required for the rest
                }
                // ====================================
                const sheetBgChatterContainerHookXml = chatterContainerHookXml.cloneNode(true);
                sheetBgChatterContainerHookXml.classList.add("o-isInFormSheetBg");
                sheetBgChatterContainerHookXml.setAttribute("t-if",  `this.props.isfullformwidth or uiService.size < ${SIZES.XXL}`);
                append(formSheetBgXml, sheetBgChatterContainerHookXml);
                const sheetBgChatterContainerXml = sheetBgChatterContainerHookXml.querySelector('ChatterContainer');
                setAttributes(sheetBgChatterContainerXml, {
                    "isInFormSheetBg": `this.props.isfullformwidth or uiService.size < ${SIZES.XXL}`,
                });
                setAttributes(chatterContainerHookXml, {
                    't-if': `!this.props.isfullformwidth and uiService.size >= ${SIZES.XXL} and uiService.size < ${SIZES.XXL}`,
                });
                append(parentXml, chatterContainerHookXml);

                // ====================================
                
            }
        }
         else {
            if (params.hasAttachmentViewerInArch) {
                const sheetBgChatterContainerHookXml = res.querySelector(
                    ".o_FormRenderer_chatterContainer.o-isInFormSheetBg"
                );
                sheetBgChatterContainerHookXml.setAttribute("t-if", true);
                chatterContainerHookXml.setAttribute("t-if", false);
            } else {
                const formSheetBgXml = res.querySelector(".o_form_sheet_bg");
                if (!formSheetBgXml) {
                    return res;
                }
                const sheetBgChatterContainerHookXml =
                    chatterContainerHookXml.cloneNode(true);
                sheetBgChatterContainerHookXml.classList.add("o-isInFormSheetBg");
                sheetBgChatterContainerHookXml.setAttribute("t-if", true);
                append(formSheetBgXml, sheetBgChatterContainerHookXml);
                const sheetBgChatterContainerXml =
                    sheetBgChatterContainerHookXml.querySelector("ChatterContainer");
                sheetBgChatterContainerXml.setAttribute("isInFormSheetBg", "true");
                chatterContainerHookXml.setAttribute("t-if", false);
            }
        }
        return res;
    },
});