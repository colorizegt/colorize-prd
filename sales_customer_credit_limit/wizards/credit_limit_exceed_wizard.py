# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreditLimitExceedWizard(models.TransientModel):
    _name = 'credit.limit.exceed.wizard'
    _description = 'Credit limit exceed wizard'

    order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner',
                                 related='order_id.partner_id',
                                 readonly=1)
    partner_currency_id = fields.Many2one(
        'res.currency', related='order_id.partner_id.currency_id', readonly=1)
    credit_limit = fields.Float('Credit Limit',
                                related='order_id.partner_id.credit_limit',
                                
                                readonly=1)
    order_amount = fields.Float('Order Amount',
                                   
                                   readonly=1)
    pending_amount = fields.Float('Unpaid Amount',
                                     
                                     readonly=1)
    overdue_invoice_amount = fields.Float(
        'Overdue Amount',  readonly=1)
    exceeded_credit = fields.Float('Exceeded Amount',
                                      
                                      readonly=1)
    pending_invoice_ids = fields.Many2many('account.move',
                                           string='Pending invoices',
                                           readonly=1)
    unpaid_order_ids = fields.Many2many('sale.order',
                                        string='Sale orders (Unpaid)',
                                        readonly=1)
    message = fields.Char('Message')