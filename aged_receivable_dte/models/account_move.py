# models/account_move.py

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super().write(vals)

        # Evitar recursión cuando nosotros mismos actualizamos payment_reference
        if self.env.context.get("skip_dte_payment_reference_sync"):
            return res

        # Solo actuar cuando el proceso FEL modifica el Número DTE
        if "fel_gt_dte_number" in vals:
            for move in self:
                if (
                    move.move_type in ("out_invoice", "out_refund")
                    and move.fel_gt_dte_number
                    and move.payment_reference != move.fel_gt_dte_number
                ):
                    move.with_context(
                        skip_dte_payment_reference_sync=True
                    ).write({
                        "payment_reference": move.fel_gt_dte_number,
                    })

        return res
