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

from odoo import api, fields, models, tools, SUPERUSER_ID


class GtReportConfig(models.Model):
    _name = "l10n_gt_extra.report_config"
    _description = 'Configuración de Reportes Guatemaltecos'

    name = fields.Char(string="Nombre")
    report_section_ids = fields.One2many('l10n_gt_extra.report_config.section', 'report_config_id', string='Secciones del Reporte')
    report_type = fields.Selection([
        ('result', 'Estado de Resultado'),
        ('balance', 'Balance General')
    ], string="Tipo de Reporte", default='result', required=True)
    column_numbers = fields.Selection([
        ('2', '2 Columnas'),
        ('3', '3 Columnas')
    ], string="Cantidad de Columnas del Reporte", default='2', required=True)
    accountant_name = fields.Char(string="Nombre Contador")
    legal_representative_name = fields.Char(string="Nombre Representante Legal")
    footer_phrase = fields.Text('Frase Pie de Pagina', index=True)
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)
    

class GtReportConfigSection(models.Model):
    _name = "l10n_gt_extra.report_config.section"
    _description = 'Secciones de Reportes Guatemaltecos'

    name = fields.Char('Nombre Sección')
    code = fields.Char('Codigo')
    not_show_name = fields.Boolean(string="No Mostrar Nombre")
    section_header = fields.Char('Encabezado Sección')
    report_config_id = fields.Many2one("l10n_gt_extra.report_config", string='Reporte', readonly=True)
    lines_ids = fields.One2many('l10n_gt_extra.report_config.section.lines', 'section_id', string='Secciones del Reporte')
    excluded_journal_ids = fields.Many2many("account.journal", string="Diarios Excluidos")
    codes_to_sum = fields.Char(string='Codigos a Sumar')
    total_name = fields.Char('Nombre Total Sección')
    not_show_totals = fields.Boolean(string="No Mostrar Totales")


class GtReportConfigSectionLines(models.Model):
    _name = "l10n_gt_extra.report_config.section.lines"
    _description = 'Lineas de Secciones de Reportes Guatemaltecos'

    name = fields.Char('Nombre Línea')
    code = fields.Char('Codigo')
    section_id = fields.Many2one("l10n_gt_extra.report_config.section", string='Sección', readonly=True)
    column_number = fields.Selection([('first_column', 'Primera Columna'),
                                  ('second_column', 'Segunda Columna'),
                                  ('total_column', 'Columna de Totales')], string="Columna Datos", required=True, default='first_column')
    account_ids = fields.Many2many("account.account", string="Cuentas a Considerar")
    codes_to_sum = fields.Char(string='Codigos a Sumar')
    calculate_subtotal = fields.Boolean(string="Calcular Subtotal")
