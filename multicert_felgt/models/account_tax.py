# -*- coding: utf-8 -*-

from odoo import models, fields, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    fel_gt_timbre_tax = fields.Boolean(string="Timbre FEL")
    fel_gt_tax = fields.Selection([
        ('IVA', 'IVA'),
        ('PETROLEO', 'PETROLEO'),
        ('TURISMO HOSPEDAJE', 'TURISMO HOSPEDAJE'),
        ('TURISMO PASAJES', 'TURISMO PASAJES'),
        ('TIMBRE DE PRENSA', 'TIMBRE DE PRENSA'),
        ('BOMBEROS', 'BOMBEROS'),
        ('TASA MUNICIPAL', 'TASA MUNICIPAL'),
    ], string="Tipo impuesto FEL", default="IVA")
    fel_gt_idp_tax_type = fields.Selection([
        ('super','Super'),
        ('regular','Regular'),
        ('disel','Disel'),
    ], string="Tipo de IDP FEL", default="super")