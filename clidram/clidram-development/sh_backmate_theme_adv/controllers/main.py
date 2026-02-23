# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo.tools.safe_eval import safe_eval
from odoo import http
from odoo.http import request
import json
from datetime import datetime
from odoo.tools.mimetypes import guess_mimetype
from odoo.modules import get_module_path, get_resource_path
import odoo
import io
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import functools
import base64
from io import BytesIO



dict_pre_theme_color_style = {
    'pre_color_1': {
        'theme_color': 'color_1',
        'theme_style': 'style_2',
        'primary_color': '#2C3782',
        'primary_hover': '#2C3782',
        'primary_active': '#2C3782',
        'secondary_color': '#EEEEEE',
        'secondary_hover': '#EEEEEE',
        'secondary_active': '#EEEEEE',
        'header_background_color': '#FFFFFF',
        'body_background_color': '#FFFFFF',
        'header_font_color': '#787373',
        'header_hover_color': '#2C3782',
        'header_active_color': '#2C3782',
        'h1_color': '#464d69',
        'h2_color': '#464d69',
        'h3_color': '#464d69',
        'h4_color': '#464d69',
        'h5_color': '#464d69',
        'h6_color': '#464d69',
        'p_color': '#464d69',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_font_hover_background_color': '#2C3782',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#FFFFFF',

        'separator_color': '#2C3782',
        'separator_style': 'style_7',

        'button_style': 'style_2',
        'body_background_type': 'bg_color',
        'body_font_color': '#787373',
        'body_font_family': 'Poppins',
        'body_google_font_family': 'Muli',
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#F2F2F2',
        'list_view_even_row_color': '#ECECEC',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_2',
        'login_page_style_comp_logo' : False,
        'login_page_background_type': 'bg_color',
        'loading_style': 'style_1',
        'progress_style':'style_1',
        'progress_height':'4px',
        'progress_color': '#2C3782',

        'modal_popup_style': 'style_2',
        'is_sticky_pivot': False,
        'horizontal_tab_style': 'style_5',
        'vertical_tab_style': 'style_5',
        'form_element_style': 'style_1',
        'breadcrumb_style': 'style_1',
        'search_style': 'expanded',
        'icon_style':'dual_tone',
        'dual_tone_icon_color_1':'#A3A5B7',
        'dual_tone_icon_color_2':'#2C3782',
        'checkbox_style':'style_1',
        'radio_btn_style':'style_1',
        'scrollbar_style' : 'style_1',
        'discuss_chatter_style' : 'style_1',
        'backend_all_icon_style' : 'style_2',
        'chatter_type' : 'bottom',
    },

    'pre_color_2': {
        'theme_color': 'color_7',
        'theme_style': 'style_1',
        'primary_color': '#43A047',
        'primary_hover': '#3B9141',
        'primary_active': '#3B9141',
        'secondary_color': '#EFF2F7',
        'secondary_hover': '#EFF2F7',
        'secondary_active': '#EFF2F7',
        'header_background_color': '#FFFFFF',
        'body_background_color': '#FFFFFF',
        'header_font_color': '#74788D',
        'header_hover_color': '#3B9141',
        'header_active_color': '#3B9141',
        'h1_color': '#495057',
        'h2_color': '#495057',
        'h3_color': '#495057',
        'h4_color': '#495057',
        'h5_color': '#495057',
        'h6_color': '#495057',
        'p_color': '#495057',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#FFFFFF',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#495057',
        'sidebar_font_hover_color': '#495057',

        'separator_color': '#43A047',
        'separator_style': 'style_5',

        'button_style': 'style_4',

        'body_background_type': 'bg_color',
        'body_font_color': '#74788D',
        'body_font_family': 'Poppins',
        'body_google_font_family': 'Muli',
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#E8F5E9',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_1',
        'login_page_style_comp_logo': False,
         'loading_style':'style_4',
         'progress_style':'style_1',
         'progress_height':'4px',
         'progress_color': '#43A047',
        'login_page_background_type': 'bg_color',

        'modal_popup_style': 'style_1',
        'is_sticky_form': True,
        'is_sticky_pivot': False,
        'horizontal_tab_style': 'style_4',
        'vertical_tab_style': 'style_4',
        'form_element_style': 'style_8',
        'breadcrumb_style': 'style_3',
        'search_style': 'collapsed',
        'icon_style':'line_icon',
        'dual_tone_icon_color_1':'#b4d9b5',
        'dual_tone_icon_color_2':'#ffffff',
        'checkbox_style':'style_2',
        'radio_btn_style':'style_2',
        'scrollbar_style' : 'style_2',
        'discuss_chatter_style' : 'style_2',
        'backend_all_icon_style' : 'style_3',
        'chatter_type' : 'bottom',
    },


    'pre_color_3': {
        'theme_color': 'color_3',
        'theme_style': 'style_3',
        'primary_color': '#ED4762',
        'primary_hover': '#DD3C54',
        'primary_active': '#DD3C54',
        'gradient_color': '#4F2499',
        'secondary_color': '#EEEEEE',
        'secondary_hover': '#EEEEEE',
        'secondary_active': '#EEEEEE',
        'header_background_color': '#FFFFFF',
        'body_background_color': '#FFFFFF',
        'header_font_color': '#787373',
        'header_hover_color': '#ED4762',
        'header_active_color': '#ED4762',
        'h1_color': '#585858',
        'h2_color': '#585858',
        'h3_color': '#585858',
        'h4_color': '#585858',
        'h5_color': '#585858',
        'h6_color': '#585858',
        'p_color': '#585858',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': False,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#FFFFFF',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_is_show_nav_bar': False,

        'separator_color': '#ED4762',
        'separator_style': 'style_2',

        'button_style': 'style_5',

        'body_background_type': 'bg_color',
        'body_font_color': '#787373',
        'body_font_family': 'Roboto',
        'body_google_font_family': 'Muli',
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#FCE4EC',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_style_comp_logo': False,
        'loading_style':'style_9',
        'progress_style':'style_1',
        'progress_height':'4px',
        'progress_color': '#ED4762',
        'login_page_background_type': 'bg_img',

        'modal_popup_style': 'style_1',
        'is_sticky_form': True,
        'is_sticky_chatter': True,
        'is_sticky_list': True,
        'is_sticky_list_inside_form': True,
        'is_sticky_pivot': True,
        'horizontal_tab_style': 'style_7',
        'vertical_tab_style': 'style_7',
        'form_element_style': 'style_7',
        'breadcrumb_style': 'style_5',
        'search_style': 'expanded',
        'icon_style':'three_d',
        'dual_tone_icon_color_1':'#A3A5B7',
        'dual_tone_icon_color_2':'#2C3782',
        'checkbox_style':'style_3',
        'radio_btn_style':'style_3',
        'scrollbar_style' : 'style_3',
        'discuss_chatter_style' : 'style_3',
        'backend_all_icon_style' : 'style_4',
        'chatter_type' : 'bottom',
    }

}

dict_theme_color_style = {

    'color_1_1': {

        'primary_color': '#2C3782',
        'primary_hover': '#141F76',
        'primary_active': '#141F76',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#2C3782',
        'header_active_color': '#2C3782',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#2C3782',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',

        'separator_color': '#141F76',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#2C3782',


    },
    'color_1_2': {

        'primary_color': '#2C3782',
        'primary_hover': '#141F76',
        'primary_active': '#141F76',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#2C3782',
        'header_active_color': '#2C3782',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#2C3782',
        'separator_color': '#141F76',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#2C3782',
    },
    'color_1_3': {
        'primary_color': '#2C3782',
        'primary_hover': '#141F76',
        'primary_active': '#141F76',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#2C3782',
        'header_active_color': '#2C3782',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#2C3782',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#141F76',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#2C3782',
    },
    'color_2_1': {
        'primary_color': '#ff9800',
        'primary_hover': '#F29107',
        'primary_active': '#F29107',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ff9800',
        'header_active_color': '#ff9800',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#ff9800',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'separator_style': 'style_7',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ff9800',
    },
    'color_2_2': {
        'primary_color': '#ff9800',
        'primary_hover': '#F29107',
        'primary_active': '#F29107',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ff9800',
        'header_active_color': '#ff9800',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#F29107',
        'separator_color': '#F29107',
        'body_font_color': '#787373',
        'login_page_style_comp_logo': False,
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ff9800',
    },
    'color_2_3': {
        'primary_color': '#ff9800',
        'primary_hover': '#F29107',
        'primary_active': '#F29107',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ff9800',
        'header_active_color': '#ff9800',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ff9800',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#F29107',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ff9800',
    },
    'color_3_1': {
        'primary_color': '#ED4762',
        'primary_hover': '#DD3C54',
        'primary_active': '#DD3C54',
        'gradient_color': '#4F2499',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ED4762',
        'header_active_color': '#ED4762',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#ED4762',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'separator_style': 'style_7',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ED4762',
    },
    'color_3_2': {
        'primary_color': '#ED4762',
        'primary_hover': '#DD3C54',
        'primary_active': '#DD3C54',
        'gradient_color': '#4F2499',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ED4762',
        'header_active_color': '#ED4762',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#ffffff',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#DD3C54',
        'separator_color': '#DD3C54',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ED4762',
    },
    'color_3_3': {
        'primary_color': '#ED4762',
        'primary_hover': '#DD3C54',
        'primary_active': '#DD3C54',
        'gradient_color': '#4F2499',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#ED4762',
        'header_active_color': '#ED4762',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': False,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ED4762',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#DD3C54',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#ED4762',
    },
    'color_4_1': {
        'primary_color': '#673AB7',
        'primary_hover': '#5C32A9',
        'primary_active': '#5C32A9',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#673AB7',
        'header_active_color': '#673AB7',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#673AB7',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'separator_color': '#5C32A9',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#673AB7',
    },
    'color_4_2': {
        'primary_color': '#673AB7',
        'primary_hover': '#5C32A9',
        'primary_active': '#5C32A9',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#673AB7',
        'header_active_color': '#673AB7',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#ffffff',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#5C32A9',
        'separator_color': '#5C32A9',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#673AB7',
    },
    'color_4_3': {
        'primary_color': '#673AB7',
        'primary_hover': '#5C32A9',
        'primary_active': '#5C32A9',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#673AB7',
        'header_active_color': '#673AB7',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#673AB7',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#5C32A9',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#673AB7',
    },
    'color_5_1': {
        'primary_color': '#5d4037',
        'primary_hover': '#56343C',
        'primary_active': '#56343C',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5d4037',
        'header_active_color': '#5d4037',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#5d4037',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'separator_color': '#56343C',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5d4037',
    },
    'color_5_2': {
        'primary_color': '#5d4037',
        'primary_hover': '#56343C',
        'primary_active': '#56343C',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5d4037',
        'header_active_color': '#5d4037',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#56343C',
        'separator_color': '#56343C',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5d4037',
    },
    'color_5_3': {
        'primary_color': '#5d4037',
        'primary_hover': '#56343C',
        'primary_active': '#56343C',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5d4037',
        'header_active_color': '#5d4037',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '47336B',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#56343C',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5d4037',
    },
    'color_6_1': {
        'primary_color': '#5B6DDB',
        'primary_hover': '#505DBE',
        'primary_active': '#505DBE',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5B6DDB',
        'header_active_color': '#5B6DDB',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#5B6DDB',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',

        'separator_color': '#505DBE',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5B6DDB',
    },
    'color_6_2': {
        'primary_color': '#5B6DDB',
        'primary_hover': '#505DBE',
        'primary_active': '#505DBE',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5B6DDB',
        'header_active_color': '#5B6DDB',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#ffffff',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#505DBE',
        'separator_color': '#505DBE',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5B6DDB',
    },
    'color_6_3': {
        'primary_color': '#5B6DDB',
        'primary_hover': '#505DBE',
        'primary_active': '#505DBE',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#5B6DDB',
        'header_active_color': '#5B6DDB',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#5B6DDB',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#505DBE',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#5B6DDB',
    },

    'color_7_1': {
        'primary_color': '#43A047',
        'primary_hover': '#3B9141',
        'primary_active': '#3B9141',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#43A047',
        'header_active_color': '#43A047',

        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_font_hover_background_color': '#43A047',
        'sidebar_background_style': 'color',
        'sidebar_background_color': '#ffffff',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'separator_color': '#3B9141',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#43A047',
    },
    'color_7_2': {
        'primary_color': '#43A047',
        'primary_hover': '#3B9141',
        'primary_active': '#3B9141',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#43A047',
        'header_active_color': '#43A047',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,

        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'expanded',
        'sidebar_background_color': '#ffffff',
        'sidebar_background_style': 'color',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#ffffff',
        'sidebar_font_hover_background_color': '#3B9141',
        'separator_color': '#3B9141',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#43A047',
    },
    'color_7_3': {
        'primary_color': '#43A047',
        'primary_hover': '#3B9141',
        'primary_active': '#3B9141',
        'secondary_color': '#e2e4e6',
        'secondary_hover': '#e2e4e6',
        'secondary_active': '#e2e4e6',
        'header_hover_color': '#43A047',
        'header_active_color': '#43A047',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 13,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'sidebar_is_show_nav_bar': True,
        'sidebar_collapse_style': 'collapsed',
        'sidebar_background_style': 'image',
        'sidebar_font_color': '#181F4C',
        'sidebar_font_hover_color': '#43A047',
        'sidebar_font_hover_background_color': '#fafafa',
        'separator_color': '#3B9141',
        'body_font_color': '#787373',
        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f2f2f2',
        'login_page_style_comp_logo': False,
        'loading_style': 'style_9',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color': '#43A047',
    },
}


class ThemeConfigController(http.Controller):

    @http.route('/firebase-messaging-sw.js', type='http', auth="public")
    def sw_http(self):
        if request.env.company and request.env.company.enable_web_push_notification:
            config_obj = request.env.company.config_details

            js = """
            this.addEventListener('install', function(e) {
         e.waitUntil(
           caches.open('video-store').then(function(cache) {
             return cache.addAll([
                 '/sh_backmate_theme_adv/static/index.js'
             ]);
           })
         );
        });
        
        this.addEventListener('fetch', function(e) {
          e.respondWith(
            caches.match(e.request).then(function(response) {
              return response || fetch(e.request);
            })
          );
        });
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-app.js');
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-messaging.js');
            var firebaseConfig =
            """ + config_obj + """ ;
            firebase.initializeApp(firebaseConfig);
    
            const messaging = firebase.messaging();
    
            messaging.setBackgroundMessageHandler(function(payload) {
            const notificationTitle = "Background Message Title";
            const notificationOptions = {
                body: payload.notification.body,
                icon:'https://i.pinimg.com/originals/3f/77/56/3f7756330cd418e46e642254a900a507.jpg',
            };
            return self.registration.showNotification(
                notificationTitle,
                notificationOptions,
            );
            });
    
            """
            return http.request.make_response(js, [('Content-Type', 'text/javascript')])
        else:

            js = """
           this.addEventListener('install', function(e) {
         e.waitUntil(
           caches.open('video-store').then(function(cache) {
             return cache.addAll([
                 '/sh_backmate_theme_adv/static/index.js'
             ]);
           })
         );
        });
        
        this.addEventListener('fetch', function(e) {
          e.respondWith(
            caches.match(e.request).then(function(response) {
              return response || fetch(e.request);
            })
          );
        });
    
            """
            return http.request.make_response(js, [('Content-Type', 'text/javascript')])

    @http.route('/web/push_token', type='http', auth="public", csrf=False)
    def getToken(self, **post):
        device_search = request.env['sh.push.notification'].sudo().search(
            [('register_id', '=', post.get('name'))], limit=1)

        if device_search and not request.env.user._is_public() and device_search.user_id != request.env.user.id:
            if request.env.user.has_group('base.group_portal'):
                device_search.write(
                    {'user_id': request.env.user.id, 'user_type': 'portal'})
            elif request.env.user:
                device_search.write(
                    {'user_id': request.env.user.id, 'user_type': 'internal'})

        if not device_search:
            vals = {
                'register_id': post.get('name'),
                'datetime': datetime.now()
            }
            print("\n\n\n\n self.env.user.has_group('base.group_portal')",
                  request.env.user.has_group('base.group_portal'))
            if request.env.user._is_public():
                public_users = request.env['res.users'].sudo()
                public_groups = request.env.ref(
                    "base.group_public", raise_if_not_found=False)
                if public_groups:
                    public_users = public_groups.sudo().with_context(
                        active_test=False).mapped("users")
                    if public_users:
                        vals.update(
                            {'user_id': public_users[0].id, 'user_type': 'public'})
            elif request.env.user.has_group('base.group_portal'):
                vals.update(
                    {'user_id': request.env.user.id, 'user_type': 'portal'})
            elif request.env.user:
                vals.update({'user_id': request.env.user.id,
                             'user_type': 'internal'})

            request.env['sh.push.notification'].sudo().create(vals)

    @http.route('/web/_config', type='json', auth="public")
    def sendConfig(self):

        config_vals = {}
        if request.env.company and request.env.company.enable_web_push_notification:

            config_obj = request.env.company.config_details.replace(" ", "")
            config_obj = request.env.company.config_details.replace("\n", "").replace("\t", "").replace(" ", "").replace("\"", "'").replace('apiKey', '\'apiKey\'').replace('authDomain', '\'authDomain\'').replace(
                'projectId', '\'projectId\'').replace('storageBucket', '\'storageBucket\'').replace('messagingSenderId', '\'messagingSenderId\'').replace('appId', '\'appId\'').replace('measurementId', '\'measurementId\'')

            config_vals['apiKey'] = safe_eval(config_obj)['apiKey']
            config_vals['authDomain'] = safe_eval(config_obj)['authDomain']
            config_vals['projectId'] = safe_eval(config_obj)['projectId']
            config_vals['storageBucket'] = safe_eval(config_obj)[
                'storageBucket']
            config_vals['messagingSenderId'] = safe_eval(config_obj)[
                'messagingSenderId']
            config_vals['appId'] = safe_eval(config_obj)['appId']
            config_vals['measurementId'] = safe_eval(config_obj)[
                'measurementId']

            vals = {
                'vapid': request.env.company.vapid,
                'config':   config_vals
            }
            print(vals)
            json_vals = json.dumps(vals)
            return json_vals

    def _get_manifest_json(self, company):
        if not company:
            company = 1
        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', int(company))], limit=1)
        vals = {
            "name": "Softhealer-APP",
            "short_name": "SH-APP",
            "scope": "/",
            "start_url": "/web",
            "background_color": "purple",
            "display": "standalone",
        }
        if pwa_config:
            if pwa_config.name:
                vals.update({'name': pwa_config.name})
            if pwa_config.short_name:
                vals.update({'short_name': pwa_config.short_name})
            if pwa_config.theme_color:
                vals.update({'theme_color': pwa_config.theme_color})
            if pwa_config.background_color:
                vals.update({'background_color': pwa_config.background_color})
            if pwa_config.display:
                vals.update({'display': pwa_config.display})
            if pwa_config.orientation:
                vals.update({'orientation': pwa_config.orientation})

            default_icon_list = []
            if pwa_config.icon_small and pwa_config.icon_small_mimetype and pwa_config.icon_small_size:
                default_icon_list.append({
                    'src': '/sh_backmate_theme_adv/pwa_icon_small/'+str(company),
                    'type': pwa_config.icon_small_mimetype,
                    'sizes': pwa_config.icon_small_size
                })
            if pwa_config.icon and pwa_config.icon_mimetype and pwa_config.icon_size:
                default_icon_list.append({
                    'src': '/sh_backmate_theme_adv/pwa_icon/'+str(company),
                    'type': pwa_config.icon_mimetype,
                    'sizes': pwa_config.icon_size
                })

            if len(default_icon_list) == 0:
                default_icon_list = [
                    {
                        "src": "/sh_backmate_theme_adv/static/icon/144x144.png",
                        "sizes": "144x144",
                        "type": "image/png"
                    }
                ]

            vals.update({'icons': default_icon_list})

        return vals

    @http.route('/manifest.json/<string:cid>', type='http', auth="public")
    def manifest_http(self, **post):
        company = post.get('cid')
        print(json.dumps(self._get_manifest_json(company)))
        return json.dumps(self._get_manifest_json(company))


    def get_icon(self, field_icon, company):
        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', int(company))], limit=1)
        if pwa_config:
            icon = pwa_config.icon
            if field_icon == 'icon_small':
                icon = pwa_config.icon_small

            icon_mimetype = getattr(pwa_config, field_icon + '_mimetype')
            if icon:
                icon = BytesIO(base64.b64decode(icon))
            return http.request.make_response(
                icon.read(), [('Content-Type', icon_mimetype)])

    @http.route('/sh_backmate_theme_adv/pwa_icon/<string:cid>', type='http', auth="none")
    def icon_small(self, **post):
        company = post.get('cid')
        return self.get_icon('icon', company)

    @http.route('/sh_backmate_theme_adv/pwa_icon_small/<string:cid>', type='http', auth="none")
    def icon(self, **post):
        company = post.get('cid')
        return self.get_icon('icon_small', company)

    @http.route('/iphone.json/<string:cid>', type='http', auth="public")
    def iphone_http(self, **post):
        company = post.get('cid')
        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', int(company))], limit=1)
        if pwa_config:
            icon = pwa_config.icon_iphone
            icon_mimetype = getattr(pwa_config, 'icon' + '_mimetype')
            if icon:
                icon = BytesIO(base64.b64decode(icon))
                return http.request.make_response(
                    icon.read(), [('Content-Type', icon_mimetype)])

    @http.route('/api/upload/multi', type='http', auth="none", csrf=False)
    def Upload_image(self, **kwargs):

        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        if kwargs.get('body_background_img'):
            body_background_img = base64.b64encode(
                kwargs.get('body_background_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'body_background_image': body_background_img})

        if kwargs.get('sidebar_background_img'):
            sidebar_background_img = base64.b64encode(
                kwargs.get('sidebar_background_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'sidebar_background_image': sidebar_background_img})

        if kwargs.get('discuss_chatter_style_image'):
            discuss_chatter_style_image = base64.b64encode(
                kwargs.get('discuss_chatter_style_image').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'discuss_chatter_style_image': discuss_chatter_style_image})

        if kwargs.get('loading_gif'):
            loading_gif = base64.b64encode(kwargs.get('loading_gif').read())
            if theme_setting_rec:
                theme_setting_rec.write({'loading_gif': loading_gif})

        if kwargs.get('login_page_banner_img'):
            login_page_banner_image = base64.b64encode(
                kwargs.get('login_page_banner_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'login_page_banner_image': login_page_banner_image})

        if kwargs.get('login_page_icon_img'):
            login_page_icon_img = base64.b64encode(
                kwargs.get('login_page_icon_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'login_page_icon_img': login_page_icon_img})
        if kwargs.get('login_page_icon_img_long'):
            login_page_icon_img_long = base64.b64encode(
                kwargs.get('login_page_icon_img_long').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'login_page_icon_img_long': login_page_icon_img_long})

        if kwargs.get('login_page_background_img'):
            login_page_background_image = base64.b64encode(
                kwargs.get('login_page_background_img').read())
            if login_page_background_image:
                theme_setting_rec.write(
                    {'login_page_background_image': login_page_background_image})

        print("\n\n theme_setting_rec ==>", theme_setting_rec.discuss_chatter_style_image)
        return json.dumps({})

    @http.route('/get_theme_style', type='json', auth="public")
    def get_theme_style(self):
        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        active_color = '1'
        active_style = '1'
        active_pre_color = 'pre_color_1'
        if theme_setting_rec.theme_style:
            active_style = str(theme_setting_rec.theme_style).split('_')[1]
        if theme_setting_rec.theme_color:
            active_color = str(theme_setting_rec.theme_color).split('_')[1]
        if theme_setting_rec.pre_theme_style:
            active_pre_color = theme_setting_rec.pre_theme_style

        data_html = ' <div class="sh_main_div">  <input type="hidden" class="current_active_style" value="style_' + \
            active_style+'"/><input type="hidden" class="current_active_style_pallete"/>'
        data_color = ' <div class="sh_main_div">  <input type="hidden" class="current_active_color" value="color_' + \
            active_color+'"/><input type="hidden" class="current_active_color_pallete"/>'
        data_pre_color = ' <div class="sh_main_div">  <input type="hidden" class="current_active_pre_color" value="' + \
            active_pre_color+'"/><input type="hidden" class="current_active_pre_color_pallete"/>'

        if theme_setting_rec:
            i = 1
            for theme_style in range(3):
                data_html += '<li class="sh_div_plt"><div class="theme_style_box" id="style_' + \
                    str(i)+'"><input type="radio" name="themeStyle"> <span class="circle fa fa-check-circle"></span> <div class="sh_style_box_' + \
                    str(i)+'"></div></label></li>'
                i += 1

            j = 1
            for theme_color in range(7):
                data_color += '<li class="sh_div_plt"><div class="theme_color_box" id="color_' + \
                    str(j)+'"><input type="radio" name="themeColor"> <i class="fa fa-check-circle"></i> <div class="sh_color_box_' + \
                    str(j)+'"></div></label></li>'
                j += 1

            k = 1
            for pre_theme_color in range(3):
                data_pre_color += '<li class="sh_div_plt"><div class="pre_theme_color_box" id="pre_color_' + \
                    str(k)+'"><input type="radio" name="preThemeColor"> <i class="fa fa-check-circle"></i> <div class="sh_pre_color_box_' + \
                    str(k)+'"></div></label></li>'
                k += 1

        return {'data_html': data_html,
                'data_color': data_color,
                'data_pre_color': data_pre_color,
                'primary_color': theme_setting_rec.primary_color,
                'primary_hover': theme_setting_rec.primary_hover,
                'primary_active': theme_setting_rec.primary_active,
                'gradient_color': theme_setting_rec.gradient_color,
                'secondary_color': theme_setting_rec.secondary_color,
                'secondary_hover': theme_setting_rec.secondary_hover,
                'secondary_active': theme_setting_rec.secondary_active,
                'header_background_color': theme_setting_rec.header_background_color,
                'header_font_color': theme_setting_rec.header_font_color,
                'header_hover_color': theme_setting_rec.header_hover_color,
                'header_active_color': theme_setting_rec.header_active_color,
                'body_font_color': theme_setting_rec.body_font_color,
                'body_background_color': theme_setting_rec.body_background_color,
                'body_font_family': theme_setting_rec.body_font_family,
                'body_google_font_family': theme_setting_rec.body_google_font_family,
                'body_background_type': theme_setting_rec.body_background_type,
                'h1_color': theme_setting_rec.h1_color,
                'h2_color': theme_setting_rec.h2_color,
                'h3_color': theme_setting_rec.h3_color,
                'h4_color': theme_setting_rec.h4_color,
                'h5_color': theme_setting_rec.h5_color,
                'h6_color': theme_setting_rec.h6_color,
                'p_color': theme_setting_rec.p_color,
                'h1_size': theme_setting_rec.h1_size,
                'h2_size': theme_setting_rec.h2_size,
                'h3_size': theme_setting_rec.h3_size,
                'h4_size': theme_setting_rec.h4_size,
                'h5_size': theme_setting_rec.h5_size,
                'h6_size': theme_setting_rec.h6_size,
                'p_size': theme_setting_rec.p_size,
                'button_style': theme_setting_rec.button_style,
                'separator_style': theme_setting_rec.separator_style,
                'separator_color': theme_setting_rec.separator_color,
                'icon_style': theme_setting_rec.icon_style,
                'dual_tone_icon_color_1': theme_setting_rec.dual_tone_icon_color_1,
                'dual_tone_icon_color_2': theme_setting_rec.dual_tone_icon_color_2,
                'sidebar_font_color': theme_setting_rec.sidebar_font_color,
                'sidebar_font_hover_color': theme_setting_rec.sidebar_font_hover_color,
                'sidebar_background_style': theme_setting_rec.sidebar_background_style,
                'sidebar_background_color': theme_setting_rec.sidebar_background_color,
                'sidebar_font_hover_background_color': theme_setting_rec.sidebar_font_hover_background_color,
                'sidebar_collapse_style': theme_setting_rec.sidebar_collapse_style,
                'predefined_list_view_boolean': theme_setting_rec.predefined_list_view_boolean,
                'predefined_list_view_style': theme_setting_rec.predefined_list_view_style,
                'list_view_border': theme_setting_rec.list_view_border,
                'list_view_even_row_color': theme_setting_rec.list_view_even_row_color,
                'list_view_odd_row_color': theme_setting_rec.list_view_odd_row_color,
                'list_view_is_hover_row': theme_setting_rec.list_view_is_hover_row,
                'list_view_hover_bg_color': theme_setting_rec.list_view_hover_bg_color,
                'login_page_style': theme_setting_rec.login_page_style,
                'login_page_style_comp_logo': theme_setting_rec.login_page_style_comp_logo,
                'login_page_background_type': theme_setting_rec.login_page_background_type,
                'login_page_box_color': theme_setting_rec.login_page_box_color,
                'login_page_background_color': theme_setting_rec.login_page_background_color,
                'is_sticky_form': theme_setting_rec.is_sticky_form,
                'is_sticky_chatter': theme_setting_rec.is_sticky_chatter,
                'is_sticky_list': theme_setting_rec.is_sticky_list,
                'is_sticky_list_inside_form': theme_setting_rec.is_sticky_list_inside_form,
                'is_sticky_pivot': theme_setting_rec.is_sticky_pivot,
                'modal_popup_style': theme_setting_rec.modal_popup_style,
                'tab_style': theme_setting_rec.tab_style,
                'tab_mobile_style': theme_setting_rec.tab_style_mobile,
                'horizontal_tab_style': theme_setting_rec.horizontal_tab_style,
                'vertical_tab_style': theme_setting_rec.vertical_tab_style,
                'form_element_style': theme_setting_rec.form_element_style,
                'search_style': theme_setting_rec.search_style,
                'chatter_type': theme_setting_rec.chatter_type,
                'breadcrumb_style': theme_setting_rec.breadcrumb_style,
                'loading_style':theme_setting_rec.loading_style,
                'progress_style':theme_setting_rec.progress_style,
                'progress_height':theme_setting_rec.progress_height,
                'progress_color':theme_setting_rec.progress_color,
                'checkbox_style': theme_setting_rec.checkbox_style,
                'radio_btn_style': theme_setting_rec.radio_btn_style,
                'scrollbar_style': theme_setting_rec.scrollbar_style,
                'discuss_chatter_style': theme_setting_rec.discuss_chatter_style,
                'discuss_chatter_style_image': theme_setting_rec.discuss_chatter_style_image,
                'backend_all_icon_style': theme_setting_rec.backend_all_icon_style,
                }

    @http.route('/update/theme_style', type='json', auth="public")
    def update_theme_style(self, color_id):
        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        theme_style = 'color_' + \
            theme_setting_rec.theme_color.split(
                '_')[1]+'_'+color_id.split('_')[1]

        selected_theme_style_dict = dict_theme_color_style.get(
            theme_style, False)

        if selected_theme_style_dict:
            theme_setting_rec.update(selected_theme_style_dict)
            theme_setting_rec.write(
                {'theme_style': 'style_'+color_id.split('_')[1]})

        return {}

    @http.route('/update/theme_style_color', type='json', auth="public")
    def theme_style_color(self, color_id):
        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        theme_color = 'color_' + \
            color_id.split('_')[1]+'_' + \
            theme_setting_rec.theme_style.split('_')[1]

        selected_theme_style_dict = dict_theme_color_style.get(
            theme_color, False)

        if selected_theme_style_dict:
            theme_setting_rec.update(selected_theme_style_dict)
            theme_setting_rec.write(
                {'theme_color': 'color_'+color_id.split('_')[1]})
        return {}

    @http.route('/update/theme_style_pre_color', type='json', auth="public")
    def theme_style_pre_color(self, pre_color_id):
        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        pre_theme_color = pre_color_id

        selected_theme_style_dict = dict_pre_theme_color_style.get(
            pre_theme_color, False)

        predefined_style_1_back_image = request.env.ref(
            'sh_backmate_theme_adv.sh_back_theme_config_adv_attachment_predefined_theme_1')

        selected_theme_style_dict.update({
            'body_background_image': predefined_style_1_back_image.datas
        })

        if selected_theme_style_dict:
            theme_setting_rec.update(selected_theme_style_dict)
            theme_setting_rec.write({'pre_theme_style': pre_theme_color})
        return {}

    @http.route('/update/theme_color', type='json', auth="public")
    def update_theme_color(self, primary_color_id, primary_hover_id, primary_active_id, gradient_color, secondary_color_id, secondary_hover_id, secondary_active_id,
                           header_background_color, header_font_color, header_hover_color, header_active_color, body_font_color, body_background_color,
                           body_font_family, body_background_type, h1_color, h2_color, h3_color, h4_color, h5_color, h6_color, p_color, h1_size, h2_size, h3_size, h4_size,
                           h5_size, h6_size, p_size, button_style, separator_style, separator_color, icon_style, dual_tone_icon_color_1 , dual_tone_icon_color_2 ,
                           sidebar_font_color, sidebar_font_hover_color, sidebar_background_style, sidebar_background_color, sidebar_font_hover_background_color, sidebar_collapse_style, predefined_list_view_boolean , predefined_list_view_style , list_view_border, list_view_even_row_color, list_view_odd_row_color, list_view_is_hover_row,
                           list_view_hover_bg_color, login_page_style, login_page_style_comp_logo , login_page_background_type, login_page_box_color, login_page_background_color,
                           is_sticky_form, is_sticky_chatter, is_sticky_list, is_sticky_list_inside_form, is_sticky_pivot, modal_popup_style, body_google_font_family,
                            horizontal_tab_style, form_element_style, search_style, breadcrumb_style, chatter_type, loading_style,progress_style,progress_height,progress_color,checkbox_style,radio_btn_style,scrollbar_style,discuss_chatter_style, discuss_chatter_style_image, backend_all_icon_style):
        theme_setting_rec = request.env['sh.back.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)
        is_used_google_font = False
        if body_font_family == 'custom_google_font':
            is_used_google_font = True
        else:
            is_used_google_font = False
            body_google_font_family = 'Muli'

        if theme_setting_rec:
            theme_setting_rec.write({
                                    'is_used_google_font': is_used_google_font,
                                    'body_google_font_family': body_google_font_family,
                                    'primary_color': primary_color_id,
                                    'primary_hover': primary_hover_id,
                                    'primary_active': primary_active_id,
                                    'gradient_color': gradient_color,
                                    'secondary_color': secondary_color_id,
                                    'secondary_hover': secondary_hover_id,
                                    'secondary_active': secondary_active_id,
                                    'header_background_color': header_background_color,
                                    'header_font_color': header_font_color,
                                    'header_hover_color': header_hover_color,
                                    'header_active_color': header_active_color,
                                    'body_font_color': body_font_color,
                                    'body_background_color': body_background_color,
                                    'body_font_family': body_font_family,
                                    'body_background_type': body_background_type,
                                    'h1_color': h1_color,
                                    'h2_color': h2_color,
                                    'h3_color': h3_color,
                                    'h4_color': h4_color,
                                    'h5_color': h5_color,
                                    'h6_color': h6_color,
                                    'p_color': p_color,
                                    'h1_size': h1_size,
                                    'h2_size': h2_size,
                                    'h3_size': h3_size,
                                    'h4_size': h4_size,
                                    'h5_size': h5_size,
                                    'h6_size': h6_size,
                                    'p_size': p_size,
                                    'button_style': button_style,
                                    'separator_style': separator_style,
                                    'separator_color': separator_color,
                                    'icon_style': icon_style,
                                    'dual_tone_icon_color_1': dual_tone_icon_color_1,
                                    'dual_tone_icon_color_2': dual_tone_icon_color_2,
                                    'sidebar_font_color': sidebar_font_color,
                                    'sidebar_font_hover_color': sidebar_font_hover_color,
                                    'sidebar_background_style': sidebar_background_style,
                                    'sidebar_background_color': sidebar_background_color,
                                    'sidebar_font_hover_background_color': sidebar_font_hover_background_color,
                                    'sidebar_collapse_style': sidebar_collapse_style,
                                    'predefined_list_view_boolean': predefined_list_view_boolean,
                                    'predefined_list_view_style': predefined_list_view_style,
                                    'list_view_border': list_view_border,
                                    'list_view_even_row_color': list_view_even_row_color,
                                    'list_view_odd_row_color': list_view_odd_row_color,
                                    'list_view_is_hover_row': list_view_is_hover_row,
                                    'list_view_hover_bg_color': list_view_hover_bg_color,
                                    'login_page_style': login_page_style,
                                    'login_page_style_comp_logo': login_page_style_comp_logo,
                                    'login_page_background_type': login_page_background_type,
                                    'login_page_box_color': login_page_box_color,
                                    'login_page_background_color': login_page_background_color,
                                    'is_sticky_form': is_sticky_form,
                                    'is_sticky_chatter': is_sticky_chatter,
                                    'is_sticky_list': is_sticky_list,
                                    'is_sticky_list_inside_form': is_sticky_list_inside_form,
                                    'is_sticky_pivot': is_sticky_pivot,
                                    'modal_popup_style': modal_popup_style,
                                    # 'tab_style': tab_style,
                                    # 'tab_style_mobile': tab_style_mobile,
                                    'horizontal_tab_style': horizontal_tab_style,
                                    # 'vertical_tab_style': vertical_tab_style,
                                    'form_element_style': form_element_style,
                                    'search_style': search_style,
                                    'breadcrumb_style': breadcrumb_style,
                                    'chatter_type':chatter_type,
                                    'loading_style':loading_style,
                                    'progress_style':progress_style,
                                    'progress_height':progress_height,
                                    'progress_color':progress_color,
                                    'checkbox_style': checkbox_style,
                                    'radio_btn_style': radio_btn_style,
                                    'scrollbar_style': scrollbar_style,
                                    'discuss_chatter_style': discuss_chatter_style,
                                    'backend_all_icon_style': backend_all_icon_style,
                                    })

            return {}


    # MULTI TAB START
    @http.route(['/add/mutli/tab'], type='json', auth='public')
    def add_multi_tab(self, **kw):
        user = request.env.user

        multi_tab_ids = user.multi_tab_ids.filtered(
            lambda mt: mt.name == kw.get('name'))
        if not multi_tab_ids:
            user.sudo().write({
                'multi_tab_ids': [(0, 0,  {
                    'name': kw.get('name'),
                    'url': kw.get('url'),
                    'actionId': kw.get('actionId'),
                    'menuId': kw.get('menuId'),
                    'menu_xmlid': kw.get('menu_xmlid'),
                })]
            })

        return True

    @http.route(['/get/mutli/tab'], type='json', auth='public')
    def get_multi_tab(self, **kw):
        obj = request.env['biz.multi.tab']
        user = request.env.user
        if user.multi_tab_ids:
            record_dict = user.multi_tab_ids.sudo().read(set(obj._fields))
            return record_dict
        else:
            return False

    @http.route(['/remove/multi/tab'], type='json', auth='public')
    def remove_multi_tab(self, **kw):
        multi_tab = request.env['biz.multi.tab'].sudo().search(
            [('id', '=', kw.get('multi_tab_id'))])
        multi_tab.unlink()
        user = request.env.user
        multi_tab_count = len(user.multi_tab_ids)
        values = {
            'removeTab': True,
            'multi_tab_count': multi_tab_count,
        }
        return values

    @http.route(['/update/tab/details'], type='json', auth='public')
    def update_tabaction(self, **kw):
        tabId = kw.get('tabId')
        TabTitle = kw.get('TabTitle')
        url = kw.get('url')
        ActionId = kw.get('ActionId')
        menu_xmlid = kw.get('menu_xmlid')

        multi_tab = request.env['biz.multi.tab'].sudo().search(
            [('id', '=', tabId)])
        if multi_tab:
            multi_tab.sudo().write({
                'name': TabTitle or multi_tab.name,
                'url': url or multi_tab.url,
                'actionId': ActionId or multi_tab.ActionId,
                'menu_xmlid': menu_xmlid or multi_tab.menu_xmlid,
            })
        return True
    # MULTI TAB END


    #recently viewd
    @http.route('/recent_records/fetch', type='json', auth='user')
    def fetch_recent_records(self):
        user_id = request.env.user.id
        recent_records = request.env['sh.recent.records'].sudo().search([('sh_user_id', '=', user_id)])
        return {
            'data': [{
                'sh_model': record.sh_model,
                'record_id': record.record_id,
                'name': record.name,
            } for record in recent_records]
        }