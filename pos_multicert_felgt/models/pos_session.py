# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].append('fel_gt_passport_number')
        result['search_params']['fields'].append('fel_gt_dpi_number')
        return result

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'fel_gt.tools.phrases'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_fel_gt_tools_phrases(self):
        domain = [('id', 'in', self.config_id.fel_gt_phrases.ids)]
        return {'search_params': {'domain': domain, 'fields': ['name'],}}

    def _get_pos_ui_fel_gt_tools_phrases(self, params):
        return self.env['fel_gt.tools.phrases'].search_read(**params['search_params'])
    
    def _loader_params_account_tax(self):
        res = super()._loader_params_account_tax()
        res["search_params"]["fields"].append("python_compute")
        return res
    
    def _loader_params_res_users(self):
        result = super()._loader_params_res_users()
        result["search_params"]["fields"].append("fel_gt_cancel_in_pos")
        result["search_params"]["fields"].append("fel_gt_motive_cancel_in_pos")
        return result
    
    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(["type","qty_available","virtual_available","stock_quant_ids"])
        return result
    
    def _get_pos_ui_product_product(self, params):
        products = super()._get_pos_ui_product_product(params)
        for product in products:
            stock_quant_ids = product.get('stock_quant_ids')
            all_location = []
            locations  = self.env['stock.location'].search([('id', '=', self.config_id.picking_type_id.default_location_src_id.id)])
            all_location = list(locations.child_internal_location_ids.ids)
            quants = self.env['stock.quant'].search([('id', 'in', stock_quant_ids), ('location_id.usage', '=', 'internal'), ('location_id', 'in', all_location)])

            product['available_stock'] = 0.0
            product['on_hand_stock'] = 0.0
            for quant in quants:
                product['available_stock'] += quant.available_quantity
                product['on_hand_stock'] += quant.quantity
        return products

    def _check_invoices_are_posted(self):
        if not self.config_id.fel_gt_active:
            unposted_invoices = self._get_closed_orders().sudo().with_company(self.company_id).account_move.filtered(lambda x: x.state == 'draft')
            if unposted_invoices:
                raise UserError(_(
                    'You cannot close the POS when invoices are not posted.\nInvoices: %s',
                    '\n'.join(f'{invoice.name} - {invoice.state}' for invoice in unposted_invoices)
                ))
        else:
            unposted_invoices = self._get_closed_orders().sudo().with_company(self.company_id).account_move.filtered(lambda x: x.fel_gt_state == 'pending')
            if unposted_invoices:
                raise UserError(_(
                    'Favor verifique que estas facturas tengan firma o numero de acceso FEL: %s',
                    '\n'.join(f'{invoice.name} - {invoice.state}' for invoice in unposted_invoices)
                ))