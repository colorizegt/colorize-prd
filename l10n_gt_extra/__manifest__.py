{
    'name': 'Guatemala - Reportes y funcionalidad extra',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Reportes SAT y funcionalidad extra para Guatemala',
    'description': """
        Reportes requeridos por la SAT y otra funcionalidad extra para llevar 
        una contabilidad en Guatemala.
        
        Incluye:
        - Libro de Compras
        - Libro de Ventas
        - Libro Diario
        - Libro Mayor
        - Libro de Inventario
        - Libro de Banco
        - Partida Contable
        - Validación de NIT
        - Impuestos especiales (IDP, Timbre de Prensa, ISR)
    """,
    'author': 'José Rodrigo Fernández Menegazzo',
    'website': 'https://www.tuempresa.com/',
    'depends': [
        'l10n_gt', 
        'product',
    ],
    'data': [
        'data/l10n_gt_extra_base.xml',
        'views/account_view.xml',
        'views/res_partner_view.xml',
        'views/product_views.xml',
        'views/report.xml',
        'views/reporte_banco.xml',
        'views/reporte_partida.xml',
        'views/reporte_compras.xml',
        'views/reporte_ventas.xml',
        'views/reporte_inventario.xml',
        'views/reporte_diario.xml',
        'views/reporte_mayor.xml',
        'views/l10n_gt_extra_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
