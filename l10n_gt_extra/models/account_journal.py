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

import re

from odoo import fields, models
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento')
    usar_referencia = fields.Boolean(string='Usar referencia para libro de ventas', help='El número de la factua se ingresa en Referencia/Descripción')

    is_receipt_journal = fields.Boolean(string="¿Es recibo?")

    facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción')
    
    def _inverse_check_next_number(self):
        for journal in self:
            if journal.check_next_number and not re.match(r'^[0-9]+$', journal.check_next_number):
                raise ValidationError(_('Next Check Number should only contains numbers.'))
            if journal.check_sequence_id:
                journal.check_sequence_id.sudo().number_next_actual = int(journal.check_next_number)
                journal.check_sequence_id.sudo().padding = len(journal.check_next_number)