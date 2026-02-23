# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Backmate Backend Theme Advance",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "description": """
                Are you bored with your standard odoo backend theme? Are You are looking for modern, creative, clean, clear, materialize Odoo theme for your backend? So you are at right place, We have made sure that this theme is highly customizable and it comes with a premium look and feel. Our theme is not only beautifully designed but also fully functional, flexible, fast, lightweight, animated and modern multipurpose theme. Our backend theme is suitable for almost every purpose.
                """,
    "summary": "Advance Material Backend Theme, Responsive Theme, Fully functional Theme, flexible Backend Theme, fast Backend Theme, lightweight Backend Theme, Animated Backend Theme, Modern multipurpose theme, Customizable Backend Theme, Multi Tab Backend Theme Odoo",
    "category": "Themes/Backend",
    "version": "16.0.16",
    "depends":
    [
        "web", "mail"
    ],

    "data":
    [
        "security/base_security.xml",
        "security/ir.model.access.csv",
        "data/theme_config_data.xml",
        "data/pwa_configuraion_data.xml",
        "views/login_layout.xml",
        "views/back_theme_config_view.xml",
        "views/assets_backend.xml",
        "views/res_config_settings.xml",
        "views/base_view.xml",
        "views/global_search_view.xml",
        "views/pwa_configuration_view.xml",
        "views/views.xml",
        "views/notifications_view.xml",
        "views/send_notifications.xml",
        "views/web_push_notification.xml",
        "views/import_export_view.xml",
        'views/res_users_views.xml',
        
    ],
     'assets': {
       
        'web.assets_backend': [

            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/ActionContainer.js',
            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/FormCompiler.js',
            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/FormController.js',
            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/FormRenderer.js',
            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/MailFormCompiler.js',
            'sh_backmate_theme_adv/static/src/js/full_form_view_and_chatter_style/MessageList.js',
            # 'sh_backmate_theme_adv/static/src/scss/chatter_position.scss',
            'sh_backmate_theme_adv/static/src/xml/FormView.xml',

            # quick_create
            'sh_backmate_theme_adv/static/src/xml/quick_create/quick_create.xml',
            'sh_backmate_theme_adv/static/src/js/quick_create/quick_create.js',
            'sh_backmate_theme_adv/static/src/scss/quick_create/quick_create.scss',

            # recently viewed records
            'sh_backmate_theme_adv/static/src/js/recently_viewed_records/form_controller.js',
            'sh_backmate_theme_adv/static/src/js/recently_viewed_records/systray_recent_records.js',
            'sh_backmate_theme_adv/static/src/js/recently_viewed_records/dropdown.js',
            'sh_backmate_theme_adv/static/src/xml/recently_viewed_records/systray_recent_records.xml',
            'sh_backmate_theme_adv/static/src/scss/recently_viewed_records/recent_records_systray.scss',

            #menu structure
            "sh_backmate_theme_adv/static/src/js/navbar.js",
            'sh_backmate_theme_adv/static/src/js/dropdown.js',
            "sh_backmate_theme_adv/static/src/xml/menu.xml",
            'sh_backmate_theme_adv/static/src/js/custom.js',

            #Theme Config
            "sh_backmate_theme_adv/static/src/js/theme_config.js",
            "sh_backmate_theme_adv/static/src/js/theme_configuration_widget.js",
            "sh_backmate_theme_adv/static/src/xml/ThemeConfigSystray.xml",
            "sh_backmate_theme_adv/static/src/xml/theme_config.xml",

            #Night mode
            "sh_backmate_theme_adv/static/src/xml/nightMode.xml",
            "sh_backmate_theme_adv/static/src/scss/nightmode/night_mode_user.scss",
            "sh_backmate_theme_adv/static/src/js/night_mode.js",

            # Full Screen
            "sh_backmate_theme_adv/static/src/js/full_screen.js",
            "sh_backmate_theme_adv/static/src/xml/full_screen.xml",

            #To DO
            "sh_backmate_theme_adv/static/src/xml/todo_systray.xml",
            "sh_backmate_theme_adv/static/src/scss/todo/todo.scss",
            'sh_backmate_theme_adv/static/src/js/todo_widget.js',
            'sh_backmate_theme_adv/static/src/js/todo.js',
            "sh_backmate_theme_adv/static/src/xml/todo.xml",

            #Calculator
            "sh_backmate_theme_adv/static/src/js/calculator.js",
            "sh_backmate_theme_adv/static/src/scss/calculator/calculator.scss",
            "sh_backmate_theme_adv/static/src/xml/Calculator.xml",

            #Language Selection
            "sh_backmate_theme_adv/static/src/xml/Language.xml",
            'sh_backmate_theme_adv/static/src/js/language_selector.js',

            #Quick menu
            "sh_backmate_theme_adv/static/src/scss/quick_menu/quick_menu.scss",
            "sh_backmate_theme_adv/static/src/js/quick_menu.js",
            "sh_backmate_theme_adv/static/src/xml/web_quick_menu.xml",

            # Base odoo js
            # 'sh_backmate_theme_adv/static/src/js/action_service.js',
            'sh_backmate_theme_adv/static/src/js/route_service.js',
          
            #global Search
            "sh_backmate_theme_adv/static/src/js/global_search.js",
            "sh_backmate_theme_adv/static/src/scss/global_search/global_search.scss",
             "sh_backmate_theme_adv/static/src/xml/global_search.xml",


            #Tab style
            # "sh_backmate_theme_adv/static/src/js/vertical_pen.js",

            #Zoom Widget
            "sh_backmate_theme_adv/static/src/scss/zoom_in_out/zoom_in_out.scss",
             "sh_backmate_theme_adv/static/src/xml/zoom.xml",
            "sh_backmate_theme_adv/static/src/webclient/web_client.js",
             "sh_backmate_theme_adv/static/src/webclient/zoomwidget/zoomwidget.js",

             # discuss chatter desifn
            'sh_backmate_theme_adv/static/src/components/message/message.js',
            "sh_backmate_theme_adv/static/src/xml/message.xml",

             #ProgressBar
            "sh_backmate_theme_adv/static/src/js/nprogress.js",
            "sh_backmate_theme_adv/static/src/js/progressbar.js",

             #Firebase and PWA  and bus Notification
            # "sh_backmate_theme_adv/static/index.js",
            "https://www.gstatic.com/firebasejs/8.4.3/firebase-app.js",
            "https://www.gstatic.com/firebasejs/8.4.3/firebase-messaging.js",
            "sh_backmate_theme_adv/static/src/js/firebase.js",
            # 'sh_backmate_theme_adv/static/src/js/bus_notification.js',
            

            #multi tab
            # 'sh_backmate_theme_adv/static/src/js/action_service.js',


            "sh_backmate_theme_adv/static/src/xml/navbar.xml",
            "sh_backmate_theme_adv/static/src/js/owl.carousel.js",
            "sh_backmate_theme_adv/static/src/scss/owl.carousel.css",
            "sh_backmate_theme_adv/static/src/scss/owl.theme.default.min.css",
            "sh_backmate_theme_adv/static/src/webclient/navtab/navtab.js",
            'sh_backmate_theme_adv/static/src/webclient/action_container.js',

            # Refresh Feature
            "sh_backmate_theme_adv/static/src/js/kanban_controller.js",
            "sh_backmate_theme_adv/static/src/js/list_controller.js",
            'sh_backmate_theme_adv/static/src/js/calendar_controller.js',
            "sh_backmate_theme_adv/static/src/xml/refresh.xml",

            #On refresh custom js
            "sh_backmate_theme_adv/static/src/js/On_refresh.js",

            # fonts file
            "sh_backmate_theme_adv/static/src/scss/font/fonts.scss",
            "sh_backmate_theme_adv/static/src/scss/font/font.scss",

            # theme config panel design
            "sh_backmate_theme_adv/static/src/scss/switch_button.scss",
            "sh_backmate_theme_adv/static/src/scss/theme_config.scss",
            "sh_backmate_theme_adv/static/src/scss/theme.scss",
            
            # button style
            "sh_backmate_theme_adv/static/src/scss/button/buttons.scss",

            # body background type color/image
            "sh_backmate_theme_adv/static/src/scss/background/body_background_img/background-img.scss",
            "sh_backmate_theme_adv/static/src/scss/background/body_background_color/background-color.scss",

            # sidebar style
            "sh_backmate_theme_adv/static/src/scss/sidebar/sidebar_style_1.scss",
            "sh_backmate_theme_adv/static/src/scss/sidebar/sidebar_style_2.scss",
            "sh_backmate_theme_adv/static/src/scss/sidebar/sidebar_style_3.scss",
            "sh_backmate_theme_adv/static/src/scss/sidebar/expaned.scss",
            "sh_backmate_theme_adv/static/src/scss/sidebar/collapsed.scss",

            # breadcrumb style
            "sh_backmate_theme_adv/static/src/scss/breadcrumb/breadcrumb.scss",

            # separator style
            "sh_backmate_theme_adv/static/src/scss/separator/separator.scss",

            # Navbar
            "sh_backmate_theme_adv/static/src/scss/navbar/navbar.scss",

            # Form View
            "sh_backmate_theme_adv/static/src/scss/form_view/form_view.scss",

            # popup animation style
            "sh_backmate_theme_adv/static/src/scss/popup/popup_style.scss",

            # responsive view
            "sh_backmate_theme_adv/static/src/scss/responsive/responsive_theme.scss",

            # Tab Style
            "sh_backmate_theme_adv/static/src/scss/tab/tab.scss",
           
            # form element style
            "sh_backmate_theme_adv/static/src/scss/form_element_style/form_element_style.scss",
           
            # notification style
            "sh_backmate_theme_adv/static/src/scss/notification/notification.scss",

            # chatter position
            "sh_backmate_theme_adv/static/src/scss/chatter_position/chatter_position.scss",

            # checkbox style
            "sh_backmate_theme_adv/static/src/scss/checkbox_style/checkbox_style.scss",

            # radio button style
            "sh_backmate_theme_adv/static/src/scss/radio_btn_style/radio_btn_style.scss",

            # predefined list view style
            "sh_backmate_theme_adv/static/src/scss/predefine_list_view/predefine_list_view.scss",

            # loader style
            "sh_backmate_theme_adv/static/src/scss/loader/loader.scss",

            # nprogress
            "sh_backmate_theme_adv/static/src/scss/nprogress/nprogress.scss",
            
            # scrollbar style
            "sh_backmate_theme_adv/static/src/scss/scrollbar/scrollbar_style.scss",
            
            # multi tab 
            "sh_backmate_theme_adv/static/src/scss/multi_tab_at_control_panel/multi_tab.scss",
         
            # common file
            "sh_backmate_theme_adv/static/src/scss/predefine_style_1/body_style.scss",
            "sh_backmate_theme_adv/static/src/scss/predefine_style_1/navbar_style.scss",
            "sh_backmate_theme_adv/static/src/scss/predefine_style_1/control_panel_style.scss",
        
            # sticky 
            "sh_backmate_theme_adv/static/src/scss/sticky/sticky_chatter.scss",
            "sh_backmate_theme_adv/static/src/scss/sticky/sticky_form.scss",
            "sh_backmate_theme_adv/static/src/scss/sticky/sticky_list_inside_form.scss",
            "sh_backmate_theme_adv/static/src/scss/sticky/sticky_list.scss",
            "sh_backmate_theme_adv/static/src/scss/sticky/sticky_pivot.scss",
            "sh_backmate_theme_adv/static/src/js/pivot_view_sticky/pivot_sticky_dropdown.js",
                   
           
            # discuss chatter 
            "sh_backmate_theme_adv/static/src/scss/discuss_chatter/discuss_chatter.scss",

            # font icon 
            "sh_backmate_theme_adv/static/src/scss/icon_style/icon_style.scss",
            "sh_backmate_theme_adv/static/src/scss/font_awesome_light_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/font_awesome_thin_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/font_awesome_std_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/font_awesome_regular_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/oi_light_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/oi_regular_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/oi_thin_icon.scss",
            "sh_backmate_theme_adv/static/src/scss/style.css",
            
            # Disable Auto edit feature
            "sh_backmate_theme_adv/static/src/js/form_controller.js",
            "sh_backmate_theme_adv/static/src/xml/form_controller.xml",
            "sh_backmate_theme_adv/static/src/scss/form_controller.scss",

            # sh_attachment_in_tree_view
            '/sh_backmate_theme_adv/static/src/js/attachment/attachment.js',
            '/sh_backmate_theme_adv/static/src/js/attachment/document_viewer.js',
            '/sh_backmate_theme_adv/static/src/scss/attachment/attachment.scss',
            '/sh_backmate_theme_adv/static/src/xml/attachment.xml',
            '/sh_backmate_theme_adv/static/src/xml/document_viewer.xml',
            # 'web/static/lib/pdfjs/build/pdf.js',
            # 'web/static/lib/pdfjs/build/pdf.worker.js',
            # 'web/static/lib/pdfjs/web/viewer.js',

            # open record in new tab feature
            'sh_backmate_theme_adv/static/src/xml/open_record_in_new_tab/action_menus.xml',
            'sh_backmate_theme_adv/static/src/xml/open_record_in_new_tab/list_rendered.xml',
            
        ],
          'web.assets_frontend': [
            'sh_backmate_theme_adv/static/src/scss/login_page/login_style_1.scss',
            'sh_backmate_theme_adv/static/src/scss/login_page/login_style_2.scss',
            'sh_backmate_theme_adv/static/src/scss/login_page/login_style_3.scss',
            'sh_backmate_theme_adv/static/src/scss/login_page/login_style_4.scss'
           
        ],
         'web._assets_primary_variables': [
          ('after', 'web/static/src/scss/primary_variables.scss', '/sh_backmate_theme_adv/static/src/scss/back_theme_config_main_scss.scss'),        
        ],
        # 'web.assets_qweb': [
               
        # ],
        
      
       
    },
 
    'images': [
        'static/description/splash-screen.png',
        'static/description/splash-screen_screenshot.gif'
    ],
    "live_test_url": "https://softhealer.com/support?ticket_type=demo_request",
    "installable": True,
    "application": True,
    "price": 125,
    "currency": "EUR",
    "bootstrap": True,
    "license": "OPL-1",

}
