/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : https://store.webkul.com/license.html/ */

odoo.define('wk_website_appointment.appoint_mgmt', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var Dialog = require('web.Dialog');
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var time = require('web.time');
    var _t = core._t;
    
    publicWidget.registry.WebsiteAppointment = publicWidget.Widget.extend({
        selector: '.container-fluid',
        events: _.extend({},{
            'input input.appoint_date': 'toggleDateValidationClass',
            'input input.appoint_group': 'toggleGorupValidationClass',
            'click button#button_find_appointee': '_findAppointee',
            'click button.button_book_now' : '_bookAppointment',
        }),
    
        init: function (parent, options) {
            _.extend(options,{
                data:null
            })
            this._super.apply(this, arguments);
        },
    
        start:function() {
            var self = this;
            var lang_date_format = $('.appoint_date_div').closest('form').find('input[name="lang_date_format"]').val()
            if (lang_date_format != undefined){
            $('.appoint_date_div').datetimepicker({
                format: time.strftime_to_moment_format(lang_date_format),
                pickTime: false,
                locale : moment.locale(),
                allowInputToggle: true,
                onSelect: function(date) {
                    $(this).hide();
                },
                minDate: new Date().setHours(0,0,0,0),
                defaultDate: new Date(),
                icons: {
                    date: 'fa fa-calendar',
                    next: 'fa fa-chevron-right',
                    previous: 'fa fa-chevron-left',
                },
            });
            $('.ui-datepicker').addClass('notranslate');
            }
           
            return this._super.apply(this,arguments);
        },
    
        _findAppointee:async function(ev){
            ev.preventDefault()
            var group_id =  parseInt($("select.appoint_groups option:selected" ).val())
            var appoint_date = $('#appoint_date').val()
            console.log('appoint_date',appoint_date)
            if (isNaN(group_id) && (appoint_date == '')){
                $('#appoint_groups').addClass("invalid");
                $('#appoint_datetime_picker').addClass("invalid");
            }
            else if (isNaN(group_id))
            {
                $('#appoint_groups').addClass("invalid");
            }
            else if (appoint_date == '') {
                $('#appoint_datetime_picker').addClass("invalid");
            }
            else{
                $('#appoint_groups').removeClass("invalid").removeClass("valid");
                $('#appoint_datetime_picker').removeClass("invalid").removeClass("valid");
                $('.appoint_loader').show();
                await this._rpc({
                    route : "/find/appointee/timeslot",
                    params:{
                    'group_id'  :   group_id,
                    'appoint_date': appoint_date,
                    }
                }).then(function(appointee_listing_div){
                    console.log("===========",group_id,appoint_date)
                    $('.appoint_loader').hide();
                    if(appointee_listing_div == undefined){
                        $('#appoint_datetime_picker').addClass("invalid");
                        bootbox.alert({
                            title: "Warning",
                            backdrop: true,
                            message: _t("Appointment Date should be today or later."),
                        })
                    }
                    else{
                        $('div#appointee_listing').html(appointee_listing_div)
                    }
                });
            }
        },

        _bookAppointment : async function(ev){
            ev.preventDefault()
            var already_booked = $(ev.currentTarget).parent().data('already-booked')
            var $form = $(ev.currentTarget).closest('form');

            // validate timeslot according to today date and time
            var appoint_date = $('#appoint_date').val()

            var lang_date_format = $('.appoint_date_div').closest('form').find('input[name="lang_date_format"]').val()
            if (lang_date_format != undefined){
                lang_date_format = time.strftime_to_moment_format(lang_date_format)
                appoint_date = moment(appoint_date, lang_date_format)
            }

            appoint_date = new Date(appoint_date)
            var today = new Date()

            if (appoint_date.setHours(0,0,0,0) < today.setHours(0,0,0,0)){
                bootbox.alert({
                    title: "Warning",
                    backdrop: true,
                    message: _t("Appointment Date should be today or later."),
                })
            }
            else{
                var time_slot_id = parseInt($(ev.currentTarget).parents('.appoint_timeslot_panel').first().attr('id'))
                var person_id =  parseInt($( "select.appoint_person option:selected" ).val())
                var appoint_person_id = parseInt($(ev.currentTarget).parents('.appoint_person_panel').first().attr('id'))
                $('.appoint_loader').show();
                // code added for booking restriction
                ajax.jsonRpc("/validate/appointment", 'call', {
                    // 'appoint_date' : moment.utc(appoint_date).local().format("YYYY-MM-DD"),
                    'appoint_date' : $('#appoint_date').val(),
                    'time_slot_id': time_slot_id,
                    'appoint_person_id': appoint_person_id,
                }).then(function(result){
                    $('.appoint_loader').hide();
                    console.log('result',result)
                    if(result.status == false){
                        bootbox.alert({
                            title: "Warning",
                            backdrop: true,
                            message: _t(result.message),
                        })
                    }
                    else if(already_booked && already_booked=='True'){
                        bootbox.alert({
                            title: "Warning",
                            backdrop: true,
                            message: _t("You have already booked an appointment for this slot."),
                        })
                    }
                    else{
                        $('#appointee_listing').append('<input type="hidden" name="appoint_timeslot_id" value="'+ time_slot_id + '" />');
                        if (isNaN(person_id)){
                            $('#appointee_listing').append('<input type="hidden" name="appoint_person" value="'+ appoint_person_id + '" />');
                        }
                        if(ev.isDefaultPrevented()){
                            console.log('ev.isDefaultPrevented()',$form)
                            $form.submit();
                        }
                    }
                });
            }
        },
    
        toggleDateValidationClass:function(ev){
            var input=$(ev.currentTarget);
        	var appoint_date=input.val();
        	if(appoint_date){$('#appoint_datetime_picker').removeClass("invalid").addClass("valid");
            }
        	else{$('#appoint_datetime_picker').removeClass("valid").addClass("invalid");}
        },
        toggleGorupValidationClass:function(ev){
            var input=$(ev.currentTarget);
        	var appoint_group=input.val();
        	if(appoint_group){
                input.removeClass("invalid").addClass("valid");}
            else{input.removeClass("valid").addClass("invalid");}
        },
    });
    publicWidget.registry.PortalListAppointment = publicWidget.Widget.extend({
        selector: '.o_portal_my_doc_table',
        events: _.extend({},{
            'click tr.my_appointments_row': '_openFormView',
        }),
    
        init: function (parent, options) {
            _.extend(options,{
                data:null
            })
            this._super.apply(this, arguments);
        },
        _openFormView : function(ev) {
            var href = $(ev.currentTarget).find("a").attr("href");
            if(href) {
                window.location = href;
            }
        },
    });
    publicWidget.registry.PortalCancelAppointment = publicWidget.Widget.extend({
        selector: '.o_portal_wrap',
        events: _.extend({},{
            'click #button_cancel_booking': '_cancelBooking',
        }),
    
        init: function (parent, options) {
            _.extend(options,{
                data:null
            })
            this._super.apply(this, arguments);
        },
        _cancelBooking : function(ev) {
            ev.preventDefault()
            var reason = ''
            var appoint_id = $(ev.currentTarget).data('appoint_id')
            bootbox.prompt({
                title: "Please enter the reason for your cancellation ?",
                inputType: 'textarea',
                callback: function(result){
                    reason = result
                    console.log('result', result, appoint_id)
                    if(appoint_id != undefined){
                        $('.appoint_loader').show();
                        ajax.jsonRpc("/cancel/booking", 'call', {
                            'appoint_id' : appoint_id,
                            'reason' : reason,
                        }).then(function(result){
                            $('.appoint_loader').hide();
                            if(result == false){
                                bootbox.alert({
                                    title: "Warning",
                                    backdrop: true,
                                    message: _t("Some error occurred..please try again later !!"),
                                })
                            }
                            else{
                                location.reload();
                            }
                        });
                    }
                },
                buttons: {
                    cancel: {
                        label: "Close",
                        className: 'btn-default',
                    },
                    confirm: {
                        label: "Cancel Now",
                        className: 'btn-danger',
                    },
                },
            });
        
        },
    });
    
    
 
    /** @odoo-module */

    // import publicWidget from 'web.public.widget';
    var publicWidget = require('web.public.widget');

    publicWidget.registry.PortalHomeCounters.include({
        /**
         * @override
         */
        _getCountersAlwaysDisplayed() {
            return this._super(...arguments).concat(['my_appoint_count']);
        },
    });
});
    