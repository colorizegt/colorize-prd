# -*- coding: utf-8 -*-
{
    'name': 'Discount Level Authorization',
    'description': """
        This module enables you to authorize the discount level in Odoo POS to enable the user to allow each product whether to give discount on or not. Also the cashiers of POS can now be allowed a fixed discount level, above which they require manager permission to give discount.
    """,
    'summary': """
        This module enables you to authorize the discount level in Odoo POS to enable the user to allow each product whether to give discount on or not. Also the cashiers of POS can now be allowed a fixed discount level, above which they require manager permission to give discount.
    """,
    "author": "One Stop Odoo",
    "website": "https://onestopodoo.com",
    "maintainer": "One Stop Odoo",
    'category': 'Point of Sale',
    'version': "1.5",

    'category': 'Point of Sale',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','hr','pos_hr','web','pos_sale'],

    # always loaded
    'data': [
        'views/hr_employee_ext.xml',
        'views/product_template_ext.xml',
    ],
    'application': True,
    "assets": {
        'point_of_sale._assets_pos': [
            'discount_level_authorization/static/src/**/*',
        ],
        "web.assets_backend": [],
        "point_of_sale.pos_assets_backend": [],
        "web.assets_qweb": [
            "discount_level_authorization/static/src/xml/Product/OrderLine.xml",
        ],
    },
    "images": [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],
    # Technical
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 50,
    "currency": 'USD' 
}

