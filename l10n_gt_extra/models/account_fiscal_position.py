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

from odoo import models, fields, _

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    tax_withold = fields.Boolean(string="Exención De IVA", default=False)