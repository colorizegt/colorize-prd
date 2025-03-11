# -*- coding: utf-8 -*-

from odoo import models, fields, _

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    fel_gt_tax_withold = fields.Boolean(string="Exención De IVA", default=False)