# -*- coding: utf-8 -*-
{
    'name': "Electronic Invoicing - SAT FEL",

    'summary': """
        Odoo module for Guatemalan Electronic Invoice System (SAT FEL).
        """,

    'description': """
        Odoo module for Guatemalan Electronic Invoice System (SAT FEL).
        """,

    'author': "Rodrigo Contreras",
    'website': "https://mrdc.tech",
    'category': 'Invoicing & Payments',
    'version': '1.0.8',

    'depends': ['base', 'web', 'base_setup', 'account', 'sale'],

    'data': [

        'data/fel_gt_ir_cron_actions.xml',
        'data/fel_gt_tools_phrases.xml',
        'data/fel_gt_tools_report_fonts_data.xml',
        'data/fel_gt_paperformat_data.xml',

        'security/fel_gt_security.xml',
        'security/ir.model.access.csv',

        'views/invoice_templates/templates.xml',
        'views/invoice_templates/invoice_templates.xml',
        'views/invoice_templates/template_report.xml',
        
        'views/invoice_templates/preview_template.xml',
        'views/invoice_templates/morden_invoice.xml',
        'views/invoice_templates/bold_invoice.xml',
        'views/invoice_templates/corporate_invoice.xml',
        'views/invoice_templates/polished_invoice.xml',
        'views/invoice_templates/classic_invoice.xml',
        'views/invoice_templates/infile_classic_invoice.xml',
        'views/invoice_templates/odoo_invoice.xml',
        'views/invoice_templates/ticket_invoice.xml',
        'views/invoice_templates/vintage_invoice.xml',
        'views/invoice_templates/report_invoice.xml',

        'views/fel_gt_tools_phrases_views.xml',
        'views/fel_gt_tools_log_xml_sent_views.xml',
        'views/fel_gt_tools_report_extra_content_views.xml',

        'views/account_move_views.xml',
        'views/account_journal_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_tax_views.xml',
        'views/account_fiscal_position_views.xml',
        'views/res_users_views.xml',

        'views/multicert_felgt_views.xml',

    ],

    'assets':{
        'web.assets_backend': [
            'multicert_felgt/static/src/js/multicert_felgt_action_manager.esm.js'
        ],
        'web.report_assets_common': [
            'multicert_felgt/static/src/css/template.css',
        ],
    },

    'external_dependencies': {
        'python': ['img2pdf', 'fpdf']
    },

    'demo': [],
    'license': 'OPL-1',
}
