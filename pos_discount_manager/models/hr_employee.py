# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
import hashlib


class HrEmployee(models.Model):
    """Extend hr.employee for POS discount authorization."""

    _inherit = 'hr.employee'

    limited_discount = fields.Integer(
        string="Discount Limit",
        help="Provide discount limit to each employee"
    )

    discount_manager = fields.Boolean(
        string="Can Approve Discounts",
        help="Allow this employee to approve discounts above the salesperson limit."
    )

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
