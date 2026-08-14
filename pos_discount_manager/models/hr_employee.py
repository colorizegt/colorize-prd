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


class HrEmployee(models.Model):
    """Add discount management fields to hr.employee."""
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
        """Validate a manager PIN for POS discount approval."""

        manager = self.search([
            ('discount_manager', '=', True),
            ('pin', '!=', False),
        ], limit=1)

        if not manager:
            return False

        return manager._check_pin(pin)
