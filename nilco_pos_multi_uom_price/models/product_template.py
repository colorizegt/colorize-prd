from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom_price_id = fields.One2many(
        'product.multi.uom.price', 'product_id', string="UOM Price"
    )
    # NOTA: category_id ya no existe en Odoo 19 (eliminado de uom.uom)
    # Se elimina la línea: category_id = fields.Many2one(related='uom_id.category_id')
