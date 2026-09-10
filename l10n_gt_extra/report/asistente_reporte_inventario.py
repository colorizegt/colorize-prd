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


class AsistenteReporteInventario(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_inventario'
    _description = 'Asistente Report Inventario'

    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')
        else:
            return self.env['account.account'].search([]).ids

    cuentas_id = fields.Many2many("account.account", string="Cuentas", required=True, default=_default_cuenta, domain="[('company_id','=',company_id)]")
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'cuentas_id': [(5, 0, 0)]})

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_inventario',
             'form': self.read()[0],
             'company_id': self.company_id.id
        }
        return self.env.ref('l10n_gt_extra.action_reporte_inventario').report_action(self, data=data)