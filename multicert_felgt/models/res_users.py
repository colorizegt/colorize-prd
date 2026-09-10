# -*- coding: utf-8 -*-

from odoo import models, fields

class Users(models.Model):
    _inherit = 'res.users'

    fel_gt_invoice_default_type = fields.Selection([
        ('none', 'Ninguno'),
        ('FACT', 'Factura Normal'),
        ('FESP', 'Factura Especial'),
        ('FCAM', 'Factura Cambiaria'),
        ('FEXP', 'Factura Cambiaria Exp.'),
        ('NDEB', 'Nota de Débito'),
        ('NABN', 'Nota de Abono'),
        ('NCRE', 'Nota de Crédito'),
        ('REC', 'Recibo'),
    ], string='Tipo de Factura por Defecto', default='FACT')