from odoo import models


class PosSessionExt(models.Model):
    _inherit = "pos.session"

    def _load_pos_data_models(self, config_id):
        """Override to include 'hr.employee' in the models loaded for POS data."""
        res = super()._load_pos_data_models(config_id)
        res.append('hr.employee')
        return res
