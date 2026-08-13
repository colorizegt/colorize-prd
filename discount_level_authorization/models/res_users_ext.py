from odoo import models, api


class ResUsersExt(models.Model):
    _inherit = 'res.users'

    @api.model
    def _load_pos_data_fields(self, config_id):
        """ Override to include additional fields for POS data loading."""
        fields = super()._load_pos_data_fields(config_id)
        fields_to_append = ['company_id', 'lang', 'login']
        # Add fields only if they're not already included
        for field in fields_to_append:
            if field not in fields:
                fields.append(field)
        return fields