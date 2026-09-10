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


class AccountTax(models.Model):
    _inherit = "account.tax"

    sat_tax_type = fields.Selection([
        ('service_good', 'Bien/Servicio'),
        ('press_tax', 'Timbre de prensa'),
        ('gas', 'Combustible')
    ], string="Clasificación SAT", default="service_good")
