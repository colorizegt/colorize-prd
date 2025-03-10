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

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_analytic_lines = fields.Boolean(string="Mostrar lineas analíticas", related="company_id.show_analytic_lines", readonly=False)
    
    user_electronic_payment = fields.Many2one('res.users', related="company_id.user_electronic_payment", string='B.O. Pagos Electronicos', readonly=False)
    manager_electronic_payment = fields.Many2one('res.users', related="company_id.manager_electronic_payment", string='Encargado Pagos Electronicos', readonly=False)

    journals_to_exclude = fields.Many2many('account.journal', related="company_id.journals_to_exclude", string='Diarios a Excluir en Reportes', readonly=False)

    iva_forgiveness_account_id = fields.Many2one('account.account', related="company_id.iva_forgiveness_account_id", string="Cuenta exención ventas", readonly=False)
    isr_sales_account_id = fields.Many2one('account.account', related="company_id.isr_sales_account_id", string="Cuenta ISR ventas", readonly=False)
    isr_purchase_account_id = fields.Many2one('account.account', related="company_id.isr_purchase_account_id", string="Cuenta ISR compras", readonly=False)
    
    iva_sales_account_id = fields.Many2one('account.account', related="company_id.iva_sales_account_id", string="Cuenta retención IVA ventas", readonly=False)
    iva_purchase_account_id = fields.Many2one('account.account', related="company_id.iva_purchase_account_id", string="Cuenta retención IVA compras", readonly=False)

    sale_report_establishment_field = fields.Many2one('ir.model.fields', related="company_id.sale_report_establishment_field", string="Campo Establecimiento", readonly=False)
    sale_report_invoice_number_field = fields.Many2one('ir.model.fields', related="company_id.sale_report_invoice_number_field", string="Campo Numero Factura", readonly=False)
    sale_report_invoice_serie_field = fields.Many2one('ir.model.fields', related="company_id.sale_report_invoice_serie_field", string="Campo Serie Factura", readonly=False)

    ignore_tax_withholding = fields.Boolean(string="Ignorar Retenciones", related="company_id.ignore_tax_withholding", readonly=False)