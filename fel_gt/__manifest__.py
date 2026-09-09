{
    'name': 'FEL Guatemala',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Facturación Electrónica para Guatemala',
    'description': """
        Campos y funciones base para la facturación electrónica en Guatemala.
        Requiere el módulo l10n_gt_extra para funcionar correctamente.
    """,
    'author': 'Rodrigo Fernandez',
    'website': 'https://www.tuempresa.com/',
    'depends': [
        'l10n_gt_extra',
    ],
    'data': [
        'views/account_view.xml',
        'views/partner_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
