# -*- coding: utf-8 -*-

from odoo import models, fields

class Users(models.Model):
    _inherit = 'res.users'

    fel_gt_cancel_in_pos = fields.Boolean('Cancelar en Punto de Venta')
    fel_gt_motive_cancel_in_pos = fields.Boolean('Motivo de Cancelación en Punto de Venta')