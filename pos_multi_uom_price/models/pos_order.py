# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM')

    @api.depends('price_subtotal', 'total_cost')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - line.total_cost
            # En Odoo 19, el factor de conversión se obtiene de otra manera
            if line.product_uom_id and line.product_id and line.product_uom_id != line.product_id.uom_id:
                try:
                    converted_qty = line.product_uom_id._compute_quantity(
                        1, line.product_id.uom_id
                    )
                    if converted_qty:
                        line.margin = line.margin / converted_qty
                except Exception:
                    pass
            line.margin_percent = (
                not float_is_zero(line.price_subtotal, precision_rounding=line.currency_id.rounding)
                and line.margin / line.price_subtotal
                or 0
            )

    def _export_for_ui(self, orderline):
        res = super()._export_for_ui(orderline)
        res.update({'product_uom_id': orderline.product_uom_id.id})
        return res
