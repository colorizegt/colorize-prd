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

from odoo import api, models, fields, _


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_withholding_isr = fields.Selection(
        [
            ('quarter_witholding', 'Sujeto a Pagos Trimestrales'),
            ('definitive_withholding', 'Sujeto a Retención Definitiva'),
            ('small_taxpayer_withholding', 'Pequeño Contribuyente')
        ], string="Retención ISR", default="quarter_witholding"
    )
    tax_withholding_iva = fields.Selection(
        [
            ('no_witholding', 'No es agente rentenedor de IVA'),
            ('export', 'Exportadores'),
            ('decree_28_89', 'Beneficiarios del Decreto 28-89'),
            ('public_sector', 'Sector Público'),
            ('credit_cards_companies', 'Operadores de Tarjetas de Crédito y/o Débito'),
            ('special_taxpayer', 'Contribuyente Especiales'),
            ('special_taxpayer_export', 'Contribuyente Especial y Exportador'),
            ('others', 'Otros Agentes de Retención')
        ], string='Retención IVA', default='no_witholding')
    iva_retencion_account_id = fields.Many2one('account.journal', string='Diario de retención de IVA')
    isr_retencion_account_id = fields.Many2one('account.journal', string='Diario de retención de ISR')
    show_analytic_lines = fields.Boolean(string="Mostrar lineas analíticas", default=False)
    
    user_electronic_payment = fields.Many2one('res.users', string='B.O. Pagos Electronicos')
    manager_electronic_payment = fields.Many2one('res.users', string='Encargado Pagos Electronicos')

    journals_to_exclude = fields.Many2many('account.journal', string='Diarios a Excluir en Reportes', relation='gt_extra_company_journal_exclude_rel')

    iva_forgiveness_account_id = fields.Many2one('account.account', string="Cuenta exención ventas")
    isr_sales_account_id = fields.Many2one('account.account', string="Cuenta ISR ventas")
    isr_purchase_account_id = fields.Many2one('account.account', string="Cuenta ISR compras")
    
    iva_sales_account_id = fields.Many2one('account.account', string="Cuenta retención IVA ventas")
    iva_purchase_account_id = fields.Many2one('account.account', string="Cuenta retención IVA compras")

    sale_report_establishment_field = fields.Many2one('ir.model.fields', string="Campo Establecimiento")
    sale_report_invoice_number_field = fields.Many2one('ir.model.fields', string="Campo Numero Factura")
    sale_report_invoice_serie_field = fields.Many2one('ir.model.fields', string="Campo Serie Factura")

    ignore_tax_withholding = fields.Boolean(string="Ignorar Retenciones", default=True)