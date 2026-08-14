from odoo import fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    discount_authorized = fields.Boolean(
        string="Discount Authorized",
        default=False,
        copy=False,
        readonly=True,
    )

    discount_manager_id = fields.Many2one(
        'hr.employee',
        string="Discount Authorized By",
        copy=False,
        readonly=True,
    )

    discount_authorized_at = fields.Datetime(
        string="Discount Authorization Date",
        copy=False,
        readonly=True,
    )

    def _order_fields(self, ui_order):
        """Load discount authorization information from the POS."""

        vals = super()._order_fields(ui_order)

        vals['discount_authorized'] = ui_order.get(
            'discount_authorized',
            False
        )

        manager_id = ui_order.get('discount_manager_id')

        if manager_id:
            manager = self.env['hr.employee'].sudo().browse(manager_id)

            if manager.exists() and manager.discount_manager:
                vals['discount_manager_id'] = manager.id

                if vals['discount_authorized']:
                    vals['discount_authorized_at'] = fields.Datetime.now()

        return vals
