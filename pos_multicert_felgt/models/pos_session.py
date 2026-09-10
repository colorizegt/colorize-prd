# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _load_pos_data_models(self, config):
        """Odoo 19: Define qué modelos cargar en el POS.
        
        En Odoo 17 había que sobreescribir _pos_ui_models_to_load y añadir
        _loader_params_* para cada modelo. En Odoo 19, la carga se delega
        a cada modelo que implementa pos.load.mixin.
        
        Solo declaramos modelos custom (no estándar) que no tienen
        pos.load.mixin, como fel_gt.tools.phrases.
        """
        result = super()._load_pos_data_models(config)
        # Solo añadimos modelos custom, los estándar ya vienen cargados
        # y sus campos extra se definen en el propio modelo con _load_pos_data_fields
        for model in ['fel_gt.tools.phrases']:
            if model not in result:
                result.append(model)
        return result

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
