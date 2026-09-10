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
from odoo import api, fields, models
import hashlib


class HrEmployee(models.Model):
    """Extend hr.employee for POS discount authorization."""

    _inherit = 'hr.employee'
    _inherit = ['hr.employee', 'pos.load.mixin']

    limited_discount = fields.Integer(
        string="Discount Limit",
        help="Provide discount limit to each employee"
    )

    discount_manager = fields.Boolean(
        string="Can Approve Discounts",
        help="Allow this employee to approve discounts above the salesperson limit."
    )

    # ============================================================
    # ODOO 19: Nuevos métodos de carga de datos para el POS
    # ============================================================

    @api.model
    def _load_pos_data_fields(self, config):
        """Odoo 19: Define los campos a cargar en el POS."""
        return [
            'id', 'name', 'limited_discount', 'discount_manager',
            'pin', 'write_date',
        ]

    @api.model
    def _load_pos_data_domain(self, data, config):
        """Odoo 19: Define el dominio para cargar datos en el POS.
        Solo cargamos empleados que son managers o que tienen un límite de descuento.
        """
        return [
            '|',
            ('discount_manager', '=', True),
            ('limited_discount', '>', 0),
        ]

    @api.model
    def _load_pos_data(self, data, config):
        """Odoo 19: Carga los datos de empleados en el POS."""
        fields = self._load_pos_data_fields(config)
        domain = self._load_pos_data_domain(data, config)
        employees = self.search_read(domain, fields)
        
        # Enmascarar el PIN por seguridad antes de enviarlo al frontend
        for emp in employees:
            if emp.get('pin'):
                emp['pin'] = '****'
        
        return employees

    @api.model
    def validate_discount_manager_pin(self, pin):
        """Validate PIN and return the manager who authorized the discount."""

        if not pin:
            return False

        pin_hash = hashlib.sha1(
            str(pin).encode('utf8')
        ).hexdigest()

        managers = self.sudo().search([
            ('discount_manager', '=', True),
            ('pin', '!=', False),
        ])

        for manager in managers:
            manager_pin_hash = hashlib.sha1(
                manager.pin.encode('utf8')
            ).hexdigest()

            if manager_pin_hash == pin_hash:
                return {
                    'id': manager.id,
                    'name': manager.name,
                }

        return False
