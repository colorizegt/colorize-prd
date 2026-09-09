{
    'name': 'FEL Infile',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Integración con factura electrónica de Infile',
    'description': """
        Integración con el certificador FEL de Infile para Guatemala.
        Permite la certificación de facturas electrónicas a través del
        servicio de Infile.
    """,
    'author': 'aquíH',
    'website': 'https://www.tuempresa.com/',
    'depends': [
        'fel_gt',
        'point_of_sale',
    ],
    'data': [
        'views/account_view.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_common': [
            'fel_infile/static/src/js/custom.js',
        ],
        'web.assets_qweb': [
            'fel_infile/static/src/xml/custom_button.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
