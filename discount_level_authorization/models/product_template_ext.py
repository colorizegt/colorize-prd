from odoo import fields, models, api


class ProductTemplateExt(models.Model):
    _inherit = 'product.template'

    allow_discount = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes'),
    ], 'Allow Discount', default='no', help='Specify whether discounts are allowed for this product.')


class ProductProductExt(models.Model):
    _inherit = 'product.product'

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Override to include 'allow_discount' in the fields loaded for POS data."""
        fields = super()._load_pos_data_fields(config_id)
        if 'allow_discount' not in fields:
            fields.append('allow_discount')
        return fields

