from odoo import models, fields, api, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _load_pos_data_models(self, config):
        """Odoo 19: Define qué modelos cargar en el POS."""
        result = super()._load_pos_data_models(config)
        if 'product.multi.uom.price' not in result:
            result.append('product.multi.uom.price')
        return result
