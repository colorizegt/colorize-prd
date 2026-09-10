# -*- coding: utf-8 -*-

from odoo import api, fields, models


class FelGTPhrases(models.Model):
    _name = "fel_gt.tools.phrases"
    _description = "Frases FEL para envio de XML hacia el certificador."

    name = fields.Char('Nombre Frase FEL', required=True)
    description = fields.Char('Descripcion Frase FEL', required=True)
    scenario_code = fields.Integer('Codigo Escenario', required=True)
    phrase_type = fields.Integer('Tipo Frase', required=True)
