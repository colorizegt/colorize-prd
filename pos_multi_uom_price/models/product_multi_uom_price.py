from odoo import models, fields, api, _


class ProductMultiUomPrice(models.Model):
    _name = 'product.multi.uom.price'
    _description = 'Product Multi UoM Price'
    _inherit = ['pos.load.mixin']

    product_id = fields.Many2one('product.template', string='Product', required=True, readonly=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    price = fields.Float(string='Price', required=True, digits='Product Price')

    _sql_constraints = [
        ('product_multi_uom_price_uniq',
         'UNIQUE (product_id, uom_id)',
         _('UOM Product Must Be Unique !'))
    ]

    # ============================================================
    # ODOO 19: Métodos de carga de datos para el POS
    # ============================================================

    @api.model
    def _load_pos_data_fields(self, config):
        """Odoo 19: Define los campos a cargar en el POS."""
        return ['id', 'product_id', 'uom_id', 'price']

    @api.model
    def _load_pos_data_domain(self, data, config):
        """Odoo 19: Define el dominio para cargar datos en el POS."""
        return []

    @api.model
    def _load_pos_data(self, data, config):
        """Odoo 19: Carga los datos de UoM price en el POS."""
        fields = self._load_pos_data_fields(config)
        domain = self._load_pos_data_domain(data, config)
        records = self.search_read(domain, fields)
        
        # Transformar a la estructura esperada por el frontend
        product_uom_price = {}
        for unit in records:
            product_id = unit['product_id'][0]
            if product_id not in product_uom_price:
                product_uom_price[product_id] = {'uom_id': {}}
            product_uom_price[product_id]['uom_id'][unit['uom_id'][0]] = {
                'id': unit['uom_id'][0],
                'name': unit['uom_id'][1],
                'price': unit['price'],
            }
        return product_uom_price
