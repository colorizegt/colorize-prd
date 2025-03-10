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
    'name': "Guatemala - Contabilidad Extra",

    'summary': """
        Odoo module to generate reports and funcionalities for Guatemalan Accounting.
        """,

    'description': """
        Odoo module to generate reports and funcionalities for Guatemalan Accounting.
        """,
    
    'author': "Rodrigo Contreras",
    'website': "https://mrdc.tech",
    'category': 'Localization',
    'version': '1.0.1',

    'depends': ['base', 'l10n_gt', 'account_tax_python', 'product', 'account', 'account_accountant', 'l10n_latam_check'],
    
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_gt_extra_paperformat.xml',
        'data/l10n_gt_extra_taxes.xml',
        'data/l10n_gt_extra_tax_withold.xml',
        'data/l10n_gt_extra_currency.xml',
        'views/l10_gt_extra_report.xml',
        'views/reporte_banco.xml',
        'views/reporte_partida.xml',
        'views/reporte_compras.xml',
        'views/reporte_ventas.xml',
        'views/reporte_inventario.xml',
        'views/reporte_diario.xml',
        'views/reporte_mayor.xml',
        'views/reporte_financiero.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/product_views.xml',
        'views/account_move_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_journal_view.xml',
        'views/account_payment_view.xml',
        'views/l10n_gt_extra_report_config_views.xml',
        'wizard/report_electronic_payment.xml',
        'wizard/wizard_electronic_payment_views.xml',
        'views/account_tax_views.xml',
        'views/account_fiscal_position_views.xml',
        'views/product_category_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'l10n_gt_extra/static/src/js/action_manager.js',
        ],
    },

    'external_dependencies': {
        'python': ['pandas']
    },

    'demo': [],
    'installable': True,
    'license': 'OPL-1',
}