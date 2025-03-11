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
from datetime import datetime


class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable ", default=True)
    anulado = fields.Boolean('Anulado')
    fecha_anulacion = fields.Date('Fecha anulación')

    discarded_date = fields.Date(string="Fecha de Anulación")
    printed_check_name = fields.Char(string="Nombre en Cheque Impreso")
    not_negociable = fields.Boolean(string="No Negociable", default=True)
    bank_concept = fields.Char(string="Concepto Banco")

    def action_discarded(self):
        for rec in self:
            move = self.env['account.move']
            if 'move_line_ids' in rec.fields_get():
                move += rec.move_line_ids.mapped('move_id')
            else:
                move += rec.move_id
            move.button_cancel()
            move.line_ids.remove_move_reconcile()
            move.line_ids.write({ 'debit': 0, 'credit': 0, 'amount_currency': 0 })
            rec.discarded_date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')

    @api.onchange('partner_id')
    def _change_check_default_name(self):
        self.printed_check_name = " ".join(str(self.partner_id.name).split()).upper()