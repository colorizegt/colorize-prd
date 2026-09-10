# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        if move.company_id.country_id.code == "GT" and move.journal_id.fel_gt_active:
            values.update({
                'fel_gt_source_credit_note_id': move.id,
                'fel_gt_invoice_type': 'NCRE',
            })
        return values