# -*- encoding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError


class FelCancelMotive(models.TransientModel):
    _name = "fel_gt.tools.cancel_motive"
    _description = "Ask motive module for Fel Cancel"

    def _default_order(self):
        if self.env.context.get('order'):
            return self.env.context.get('order')
        else:
            return False
    
    order_id = fields.Many2one('pos.order', string="Orden", default=_default_order, required=True)
    motive = fields.Text(string="Motivo", required=True)

    def fel_gt_cancel(self):
        self.order_id.fel_gt_cancel(cancel_invoice=True, motive=self.motive)