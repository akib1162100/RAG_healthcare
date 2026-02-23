{
    'name': 'ICA Web Responsive',
    "author":"Agga, Ideacode Academy",
    'category': 'Hidden',
    'depends': ['web'],
    'auto_install': True,
    'data': [
        'views/partner_view.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'ica_web_responsive/static/src/**/**/*.variables.scss'),
            ('before', 'web/static/src/scss/primary_variables.scss', 'ica_web_responsive/static/src/scss/primary_variables.scss'),
        ],
        'web._assets_secondary_variables': [
            ('before', 'web/static/src/scss/secondary_variables.scss', 'ica_web_responsive/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('before', 'web/static/src/scss/bootstrap_overridden.scss', 'ica_web_responsive/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_common': [
            'ica_web_responsive/static/src/webclient/home_menu/home_menu_background.scss',
            'ica_web_responsive/static/src/webclient/navbar/navbar.scss',
        ],
        'web.assets_frontend': [
            'ica_web_responsive/static/src/webclient/home_menu/home_menu_background.scss',
            'ica_web_responsive/static/src/webclient/navbar/navbar.scss',
        ],
        'web.assets_backend': [
            ('replace', 'web/static/src/legacy/scss/fields_extra.scss', 'ica_web_responsive/static/src/legacy/scss/fields.scss'),
            ('replace', 'web/static/src/legacy/scss/form_view_extra.scss', 'ica_web_responsive/static/src/legacy/scss/form_view.scss'),
            ('replace', 'web/static/src/legacy/scss/list_view_extra.scss', 'ica_web_responsive/static/src/legacy/scss/list_view.scss'),

            'ica_web_responsive/static/src/legacy/scss/dropdown.scss',
            'ica_web_responsive/static/src/legacy/scss/control_panel_mobile.scss',
            'ica_web_responsive/static/src/legacy/scss/kanban_view.scss',
            'ica_web_responsive/static/src/legacy/scss/touch_device.scss',
            'ica_web_responsive/static/src/legacy/scss/form_view_mobile.scss',
            'ica_web_responsive/static/src/legacy/scss/modal_mobile.scss',
            'ica_web_responsive/static/src/legacy/scss/promote_studio.scss',
            'ica_web_responsive/static/src/webclient/**/*.scss',
            ('remove', 'ica_web_responsive/static/src/webclient/home_menu/home_menu_background.scss'), # already in _assets_common_styles
            ('remove', 'ica_web_responsive/static/src/webclient/navbar/navbar.scss'), # already in _assets_common_styles
            'ica_web_responsive/static/src/views/**/*.scss',

            # Allows events to be added to the ListRenderer before it is extended.
            # for more info, see: https://github.com/odoo/enterprise/pull/30169#pullrequestreview-1064657223
            ('prepend', 'ica_web_responsive/static/src/legacy/js/views/list/list_renderer_mobile.js'),

            'ica_web_responsive/static/src/legacy/js/apps.js',

            'ica_web_responsive/static/src/core/**/*',
            'ica_web_responsive/static/src/webclient/**/*.js',
            ('after', 'web/static/src/views/list/list_renderer.xml', 'ica_web_responsive/static/src/views/list/list_renderer_desktop.xml'),
            'ica_web_responsive/static/src/webclient/**/*.xml',
            'ica_web_responsive/static/src/views/**/*.js',
            'ica_web_responsive/static/src/views/**/*.xml',

            'ica_web_responsive/static/src/legacy/**/*.js',
            'ica_web_responsive/static/src/legacy/**/*.xml',

            # Don't include dark mode files in light mode
            ('remove', 'ica_web_responsive/static/src/**/**/*.dark.scss'),
        ],
        'web.assets_backend_prod_only': [
            ('replace', 'web/static/src/main.js', 'ica_web_responsive/static/src/main.js'),
        ],
        # ========= Dark Mode =========
        "web.dark_mode_variables": [
            # web._assets_primary_variables
            ('before', 'ica_web_responsive/static/src/scss/primary_variables.scss', 'ica_web_responsive/static/src/scss/primary_variables.dark.scss'),
            ('before', 'ica_web_responsive/static/src/**/**/*.variables.scss', 'ica_web_responsive/static/src/**/**/*.variables.dark.scss'),
            # web._assets_secondary_variables
            ('before', 'ica_web_responsive/static/src/scss/secondary_variables.scss', 'ica_web_responsive/static/src/scss/secondary_variables.dark.scss'),
        ],
        "web.dark_mode_assets_common": [
            ('include', 'web.dark_mode_variables'),
        ],
        "web.dark_mode_assets_backend": [
            ('include', 'web.dark_mode_variables'),
            # web._assets_backend_helpers
            ('before', 'ica_web_responsive/static/src/scss/bootstrap_overridden.scss', 'ica_web_responsive/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'ica_web_responsive/static/src/scss/bs_functions_overridden.dark.scss'),
            # assets_backend
            'ica_web_responsive/static/src/**/**/*.dark.scss',
        ],
    },
    'license': 'LGPL-3',
    "images": ["static/description/img.png"],

}
