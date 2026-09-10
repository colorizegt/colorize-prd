# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#############################################################################
from odoo import models


class PosSession(models.Model):
    """Load employee discount authorization data into the POS."""
    _inherit = "pos.session"

    def _load_pos_data_models(self, config):
        """Odoo 19: Define qué modelos cargar en el POS.
        
        En Odoo 19, la carga de datos se delega a los modelos individuales
        que implementan pos.load.mixin. Aquí solo declaramos que queremos
        cargar el modelo hr.employee.
        """
        result = super()._load_pos_data_models(config)
        if 'hr.employee' not in result:
            result.append('hr.employee')
        return result
