from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    discount_manager_id = fields.Many2one(
        "hr.employee",
        string="Discount Authorized By",
        readonly=True,
        copy=False,
    )

    discount_manager_name = fields.Char(
        string="Discount Manager Name",
        readonly=True,
        copy=False,
    )
