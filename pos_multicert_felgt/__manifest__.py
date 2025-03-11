# -*- coding: utf-8 -*-
#################################################################################
# Author      : Rodrigo Contreras (<mrdc.tech>)
# Copyright(c): 2024
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': "POS Electronic Invoicing - SAT FEL",

    'summary': """
        Odoo module for Guatemalan Electronic Invoice System in Point of Sale (SAT FEL).
        """,

    'description': """
        Odoo module for Guatemalan Electronic Invoice System in Point of Sale (SAT FEL).
        """,

    'author': 'Rodrigo Contreras',
    'website': "https://mrdc.tech",
    'category': 'Point of Sale',
    'version': '1.0.2',
    
    'depends': ['base', 'point_of_sale', 'account_tax_python', 'multicert_felgt'],

    'data': [

        'security/ir.model.access.csv',

        'views/pos_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/report.xml',
        'views/pos_order_ticket.xml',
        'views/pos_config_views.xml',
        'views/res_users_views.xml',

        'wizard/fel_gt_tools_cancel_motive_views.xml',
        
        ],

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_multicert_felgt/static/src/**/*',
        ],
    },

    'demo': [],
    'license': 'OPL-1',
}
