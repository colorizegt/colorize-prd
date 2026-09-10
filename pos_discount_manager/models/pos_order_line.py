from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    # Odoo 19: product_uom renombrado a product_uom_id
    # Este campo ya existe en Odoo 19, pero lo mantenemos por compatibilidad
    # con el frontend que envía 'product_uom_id' desde el POS.
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Product UoM",
        help="Unit of Measure for this order line."
    )
