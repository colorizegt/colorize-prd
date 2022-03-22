# -*- encoding: utf-8 -*-

{
    'name': 'FEL Infile',
    'version': '1.0',
    'category': 'Custom',
    'description': """ Integración con factura electrónica de Infile """,
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['fel_gt','point_of_sale'],
    'data': [
        'views/account_view.xml',
       # 'views/pos_templates.xml',    
    ],
    'demo': [],
    #'qweb': ['static/src/xml/custom_button.xml'],
    'assets': {
        'point_of_sale.assets': [
            '/fel_infile/static/src/js/custom.js',
        ],
        'web.assets_qweb': [
            'static/src/xml/custom_button.xml,
        ],
    },
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
