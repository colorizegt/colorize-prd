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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time


class AsistenteReporteFinanciero(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_financiero'
    _description = 'Asistente Reporte Financiero'

    report_type = fields.Selection([
        ('result', 'Estado de Resultado'),
        ('balance', 'Balance General')
    ], string="Tipo de Reporte", default='result', required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    start_date = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-01-01'))
    end_date = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))

    def print_report_pdf(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_financiero',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.action_reporte_financiero').report_action(self, data=data)
