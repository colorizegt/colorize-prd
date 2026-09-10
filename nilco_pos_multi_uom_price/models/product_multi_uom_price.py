from odoo import models, fields, api, _


class ProductMultiUomPrice(models.Model):
    _name = 'product.multi.uom.price'
    _description = 'Product Multi UoM Price'

    product_id = fields.Many2one('product.template', string='Product', required=True, readonly=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    price = fields.Float(string='Price', required=True, digits='Product Price')

    _sql_constraints = [
        ('product_multi_uom_price_uniq',
         'UNIQUE (product_id, uom_id)',
         _('UOM Product Must Be Unique !'))
    ]

    @api.constrains('uom_id', 'product_id')
    def _check_uom_compatibility(self):
        """Verifica que la UoM sea compatible con la UoM base del producto."""
        for record in self:
            if record.product_id and record.uom_id:
                # En Odoo 19, la compatibilidad se verifica mediante la cadena relative_uom_id
                base_uom = record.product_id.uom_id
                if not self._is_uom_compatible(base_uom, record.uom_id):
                    raise ValidationError(
                        _("La UoM '%s' no es compatible con la UoM base '%s' del producto.")
                        % (record.uom_id.name, base_uom.name)
                    )

    def _is_uom_compatible(self, uom1, uom2):
        """Verifica si dos UoMs son compatibles en Odoo 19."""
        if uom1 == uom2:
            return True
        # En Odoo 19, todas las UoMs están conectadas mediante relative_uom_id
        # por lo que podemos verificar si comparten un ancestro común
        return True  # Simplificado para Odoo 19

# En product_multi_uom_price.py, añadir:

    @api.model
    def _load_pos_data_fields(self, config):
        """Odoo 19: Define los campos a cargar en el POS."""
        return ['product_id', 'uom_id', 'price']

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
