# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import AND
from collections import defaultdict
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    fel_gt_dte_invoice = fields.Char(string='DTE', related='account_move.fel_gt_dte_number', readonly=True)
    fel_gt_uuid_invoice = fields.Char(string='Número de Autorización', related='account_move.fel_gt_uuid', readonly=True)
    fel_gt_serie_invoice = fields.Char(string='Serie', related='account_move.fel_gt_serie', readonly=True)
    fel_gt_cancel_motive = fields.Char(string='Motivo de Cancelación', related='account_move.fel_gt_cancel_motive', readonly=True)
    fel_gt_date_invoice = fields.Datetime(string='Fecha Autorización', related='account_move.fel_gt_dte_date', readonly=True)
    fel_gt_invoice_type = fields.Selection(string='Tipo de Factura', related='account_move.fel_gt_invoice_type', readonly=True)
    fel_gt_has_contingency = fields.Boolean(string="Tiene contingencia FEL")
    fel_gt_contingency_access_number = fields.Char(string="Numero de acceso FEL")

    def _order_fields(self, ui_order):
        result = super(PosOrder, self)._order_fields(ui_order)

        result.update({
            'fel_gt_has_contingency': ui_order['fel_gt_has_contingency'] if 'fel_gt_has_contingency' in ui_order else False,
            'fel_gt_contingency_access_number': int(ui_order['fel_gt_contingency_access_number']) if 'fel_gt_contingency_access_number' in ui_order else False
        })
        
        return result

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result['fel_gt_dte_invoice'] = order.fel_gt_dte_invoice
        result['fel_gt_uuid_invoice'] = order.fel_gt_uuid_invoice
        result['fel_gt_serie_invoice'] = order.fel_gt_serie_invoice
        result['fel_gt_has_contingency'] = order.fel_gt_has_contingency
        result['fel_gt_contingency_access_number'] = order.fel_gt_contingency_access_number
        result['fel_gt_date_invoice'] = order.fel_gt_date_invoice
        result['fel_gt_invoice_type'] = order.fel_gt_invoice_type
        return result
        
    def _get_default_fel_gt_invoice_type(self):
        if self.env.user.fel_gt_invoice_default_type and self.env.user.fel_gt_invoice_default_type in ['FACT','FCAM','FEXP','NDEB','RECI']:
            return self.env.user.fel_gt_invoice_default_type
        else:
            return 'FACT'

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        res['fel_gt_invoice_type'] = self._get_default_fel_gt_invoice_type()
        res['fel_gt_phrases'] = self.config_id.fel_gt_phrases
        if self.refunded_order_ids:
            uuid = False
            serie_original = False
            dte_number_original = False
            for order in self.refunded_order_ids:
                for invoice in order.account_move:
                    uuid = invoice.fel_gt_uuid
                    serie_original = invoice.fel_gt_serie_original
                    dte_number_original = invoice.fel_gt_dte_number_original
                    invoice_id = invoice.id
            if uuid:
                res['fel_gt_uuid_original'] = uuid
                res['fel_gt_serie_original'] = serie_original
                res['fel_gt_dte_number_original'] = dte_number_original
                res['fel_gt_invoice_type'] = 'NCRE'
                res['fel_gt_source_credit_note_id'] = invoice_id
        if self.fel_gt_has_contingency:
            res.update({
                'fel_gt_has_contingency': True,
                'fel_gt_contingency_access_number': self.fel_gt_contingency_access_number,
                'fel_gt_state': 'contingency'
            })
            invoice_journal_id = self.session_id.config_id.invoice_journal_id
            if int(self.fel_gt_contingency_access_number) > invoice_journal_id.fel_gt_contingency_actual_number:
                invoice_journal_id.write({'fel_gt_contingency_actual_number': int(self.fel_gt_contingency_access_number)+1})
        return res
    
    def _generate_pos_order_invoice(self):
        moves = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post(soft=False)

            # Send and Print
            if not order.config_id.fel_gt_disable_download_invoice_pdf:
                template = self.env.ref(new_move._get_mail_template())
                new_move.with_context(skip_invoice_sync=True)._generate_pdf_and_send_invoice(template)          

            moves += new_move
            payment_moves = order._apply_invoice_payments()

            if order.session_id.state == 'closed':  # If the session isn't closed this isn't needed.
                # If a client requires the invoice later, we need to revers the amount from the closing entry, by making a new entry for that.
                order._create_misc_reversal_move(payment_moves)

        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves and moves.ids[0] or False,
        }
    
    def _felgt_unreseve_qty(self):
        for move_line in self.sudo().mapped('picking_id').mapped('move_ids_without_package').mapped('move_line_ids'):

            # Check qty is not in draft and cancel state
            if self.sudo().mapped('picking_id').state not in ['draft', 'cancel', 'assigned', 'waiting']:

                # unreserve qty
                quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_id.id),('product_id', '=',move_line.product_id.id),('lot_id', '=', move_line.lot_id.id)], limit=1)

                if quant:
                    quant.write({'quantity': quant.quantity + move_line.quantity})

                quant = self.env['stock.quant'].sudo().search([('location_id', '=', move_line.location_dest_id.id),('product_id', '=',move_line.product_id.id),('lot_id', '=', move_line.lot_id.id)], limit=1)

                if quant:
                    quant.write({'quantity': quant.quantity - move_line.quantity})
    
    def fel_gt_cancel(self, cancel_invoice=True, motive='Anulación'):
        if self.session_id.state == 'opened' or not cancel_invoice:
            if self.picking_ids and self.config_id.fel_gt_cancel_stock_picking:
                self.picking_ids[0]._felgt_unreseve_qty()
                for picking in self.picking_ids:
                    if picking.sudo().mapped('move_ids_without_package'):
                        picking.sudo().mapped('move_ids_without_package').sudo().write({'state': 'cancel'})
                        picking.sudo().mapped('move_ids_without_package').mapped('move_line_ids').sudo().write({'state': 'cancel'})
                        picking_moves = picking.sudo().mapped('move_ids_without_package').mapped('account_move_ids')
                        if picking_moves:
                            for picking_move in picking_moves:
                                picking_move.button_draft()
                                picking_move.button_cancel()
                    picking.sudo().write({'state': 'cancel'})

            if cancel_invoice:
                if self.mapped('account_move'):
                    self.account_move.write({'fel_gt_cancel_motive': motive})
                    self.account_move.fel_gt_cancel(origin='point_of_sale')

            if self.mapped('payment_ids') and self.config_id.fel_gt_cancel_payment:
                pos_payment_ids = self.mapped('payment_ids')
                if pos_payment_ids:
                    payment_moves_ids = pos_payment_ids.mapped('account_move_id')
                    payment_moves_ids.button_draft()
                    payment_moves_ids.button_cancel()
                pos_payment_ids.sudo().unlink()
            if self.config_id.fel_gt_cancel_order:
                self.sudo().write({'state': 'cancel'})
        else:
            raise UserError('Solo es posible anular facturas de sesiones abiertas, favor realice una nota de crédito.')

    @api.model
    def search_cancel_order_ids(self, config_id, domain, limit, offset):
        """Search for 'cancel' orders that satisfy the given domain, limit and offset."""
        default_domain = [('state', '=', 'cancel')]
        if domain == []:
            real_domain = AND([[['config_id', '=', config_id]], default_domain])
        else:
            real_domain = AND([domain, default_domain])
        orders = self.search(real_domain, limit=limit, offset=offset)
        # We clean here the orders that does not have the same currency.
        # As we cannot use currency_id in the domain (because it is not a stored field),
        # we must do it after the search.
        pos_config = self.env['pos.config'].browse(config_id)
        orders = orders.filtered(lambda order: order.currency_id == pos_config.currency_id)
        orderlines = self.env['pos.order.line'].search(['|', ('refunded_orderline_id.order_id', 'in', orders.ids), ('order_id', 'in', orders.ids)])

        # We will return to the frontend the ids and the date of their last modification
        # so that it can compare to the last time it fetched the orders and can ask to fetch
        # orders that are not up-to-date.
        # The date of their last modification is either the last time one of its orderline has changed,
        # or the last time a refunded orderline related to it has changed.
        orders_info = defaultdict(lambda: datetime.min)
        for orderline in orderlines:
            key_order = orderline.order_id.id if orderline.order_id in orders \
                            else orderline.refunded_orderline_id.order_id.id
            if orders_info[key_order] < orderline.write_date:
                orders_info[key_order] = orderline.write_date
        totalCount = self.search_count(real_domain)
        return {'ordersInfo': list(orders_info.items())[::-1], 'totalCount': totalCount}

    def fel_gt_pos_cancel(self, uuid, motive='Anulación'):
        order = self.env['pos.order'].search([('fel_gt_uuid_invoice','=',uuid)], limit=1)
        if order:
            if order.session_id.state == 'opened':
                if order.state == 'invoiced':
                    order.fel_gt_cancel(cancel_invoice=True, motive=motive)
            else:
                raise UserError('Solo es posible anular facturas de sesiones abiertas, favor realice una nota de crédito.')
            
    def cancel_fel_gt(self):
        if self.env.user.fel_gt_cancel_in_pos and self.env.user.fel_gt_motive_cancel_in_pos:
            action = self.env.ref('pos_multicert_felgt.action_fel_gt_cancel_motive').read()[0]
            action['context'] = {
                'order': self.id,
            }
            return action
        elif self.env.user.fel_gt_cancel_in_pos:
            self.fel_gt_cancel()
        else:
            raise ValidationError('No tiene permisos para realizar la anulación.')