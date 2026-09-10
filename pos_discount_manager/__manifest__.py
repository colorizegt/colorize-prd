# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#############################################################################
{
    'name': "POS Discount Manager Approval",
    'version': '19.0.1.0.1',
    'category': 'Point Of Sale',
    'summary': "Discount limit for each employee in every point of sale",
    'description': """This module helps you to set a discount limit for each 
    employee in every point of sale. It facilitates the manager approval when 
    discount over the limit of employee.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'depends': ['pos_discount', 'hr'],
    'data': [
        'views/hr_employee_views.xml',
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_discount_manager/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
