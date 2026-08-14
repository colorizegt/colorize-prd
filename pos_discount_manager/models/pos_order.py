from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    discount_authorized = fields.Boolean(
        string="Discount Authorized",
        readonly=True,
        copy=False,
    )

    discount_manager_id = fields.Many2one(
        "hr.employee",
        string="Discount Authorized By",
        readonly=True,
        copy=False,
    )

    discount_authorized_at = fields.Datetime(
        string="Authorization Date",
        readonly=True,
        copy=False,
    )

    @api.model
    def _order_fields(self, ui_order):
        """Load discount authorization information from POS."""
        vals = super()._order_fields(ui_order)

        if ui_order.get("discount_authorized"):
            vals["discount_authorized"] = True

        if ui_order.get("discount_manager_id"):
            vals["discount_manager_id"] = ui_order[
                "discount_manager_id"
            ]

        if ui_order.get("discount_authorized_at"):
            vals["discount_authorized_at"] = ui_order[
                "discount_authorized_at"
            ]

        return vals
