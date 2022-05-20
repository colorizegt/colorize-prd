# -*- coding: utf-8 -*-
{
    'name': "POS multi uom price",
    'summary': 'POS Price per unit of measure',
    'category': 'Point of Sale',
    'version': '15.0.1.0.1',
    'license': "AGPL-3",
    'description': """
        With this module you can sell your products with different units of measure in POS.
    """,

    'author': "ehuerta _at_ ixer.mx",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
    'images': [
        'static/description/POS_multi_uom_price.png',
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale.assets': [
            'pos_multi_uom_price/static/src/js/multi_uom_price.js',
            'pos_multi_uom_price/static/src/js/models.js',
        ],
        'web.assets_qweb': [
            'pos_multi_uom_price/static/src/xml/*',
        ],
    },
}
