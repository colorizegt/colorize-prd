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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    cui = fields.Char(string="CUI")
    no_validar_nit = fields.Boolean(string="No validar NIT")
    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")

    tax_withholding_isr = fields.Selection(
        [
            ('quarter_witholding', 'Sujeto a Pagos Trimestrales'),
            ('definitive_withholding', 'Sujeto a Retención Definitiva'),
            ('small_taxpayer_withholding', 'Pequeño Contribuyente')
        ], string="Régimen tributario", default="quarter_witholding"
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
            ('others', 'Otros Agentes de Retención'),
            ('iva_forgiveness', 'Exención de IVA')
        ], string='Retención IVA', default='no_witholding')

    user_country_id = fields.Char(string="UserCountry", default=lambda self: self.env.user.company_id.country_id.code)

    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente", compute="_get_pequenio_contribuyente")

    def _get_pequenio_contribuyente(self):
        for rec in self:
            if rec.tax_withholding_isr:
                if rec.tax_withholding_isr == "small_taxpayer_withholding":
                    rec.pequenio_contribuyente = True
                else:
                    rec.pequenio_contribuyente = False
            else:
                rec.pequenio_contribuyente = False

    @api.onchange('tax_withholding')
    def _onchange_tax_withholding(self):
        if self.tax_withholding_isr:
            if self.tax_withholding_isr == "small_taxpayer_withholding":
                self.pequenio_contribuyente = True
            else:
                self.pequenio_contribuyente = False
        else:
            self.pequenio_contribuyente = False

    @api.model
    def default_get(self, default_fields):
        """Sets the default values for the partner."""
        values = super(ResPartner, self).default_get(default_fields)
        if self.env.user.company_id.country_code == "GT":
            values['country_id'] = self.env.ref('base.gt').id
            values['state_id'] = self.env.ref('base.state_gt_gua').id
            values['city'] = 'Guatemala'
        return values
