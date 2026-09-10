# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import ast

# ⚠️ DESACOPLADO: import local en lugar de advanced_web_domain_widget
from .domain_prepare import prepare_domain_v2, compute_domain


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    @tools.ormcache(
        'self.env.uid', 'self.env.su', 'model_name', 'mode',
        'tuple(self._compute_domain_context_values())'
    )
    def _compute_domain(self, model_name, mode="read"):
        res = super()._compute_domain(model_name, mode)

        read_value = True
        self.env.cr.execute(
            "SELECT state FROM ir_module_module WHERE name = %s",
            ('simplify_access_management',)
        )
        data = self.env.cr.fetchone() or False

        self.env.cr.execute(
            "SELECT id FROM ir_module_module WHERE state IN ('to upgrade', 'to remove', 'to install')"
        )
        all_data = self.env.cr.fetchone() or False

        if data and data[0] != 'installed':
            read_value = False

        model_list = [
            'mail.activity', 'res.users.log', 'res.users',
            'mail.channel', 'mail.alias', 'bus.presence', 'res.lang'
        ]

        if self.env.user.id and read_value and not all_data:
            if model_name not in model_list:
                # ⚠️ CORREGIDO: Typo 'comapnay' -> 'company'
                self.env.cr.execute("""
                    SELECT am.id FROM access_management AS am
                    WHERE am.active = TRUE AND am.readonly = TRUE
                    AND am.id IN (
                        SELECT au.access_management_id
                        FROM access_management_users_rel_ah AS au
                        WHERE au.user_id = %s
                    )
                    AND am.id IN (
                        SELECT ac.access_management_id
                        FROM access_management_company_rel AS ac
                    )
                """, (self.env.user.id,))
                a = self.env.cr.fetchall()
                if bool(a):
                    if mode != 'read' and model_name not in ['mail.channel.partner']:
                        raise UserError(_(
                            '%s is a read-only user. So you can not make any changes in the system!'
                        ) % self.env.user.name)

        # Verificar si el módulo está desinstalado
        self.env.cr.execute(
            "SELECT value FROM ir_config_parameter WHERE key = 'uninstall_simplify_access_management'"
        )
        value = self.env.cr.fetchone()

        if not value:
            self.env.cr.execute(
                "SELECT state FROM ir_module_module WHERE name = 'simplify_access_management'"
            )
            value = self.env.cr.fetchone()
            value = value and value[0] or False

            if model_name and value == 'installed':
                self.env.cr.execute(
                    "SELECT id FROM ir_model WHERE model = %s",
                    (model_name,)
                )
                model_numeric_row = self.env.cr.fetchone()
                model_numeric_id = model_numeric_row[0] if model_numeric_row else False

                if model_numeric_id and isinstance(model_numeric_id, int) and self.env.user:
                    try:
                        self.env.cr.execute("""
                            SELECT dm.id
                            FROM access_domain_ah AS dm
                            WHERE dm.model_id = %s AND dm.apply_domain
                            AND dm.access_management_id IN (
                                SELECT am.id
                                FROM access_management AS am
                                WHERE am.active = TRUE
                                AND am.id IN (
                                    SELECT amusr.access_management_id
                                    FROM access_management_users_rel_ah AS amusr
                                    WHERE amusr.user_id = %s
                                )
                            )
                        """, [model_numeric_id, self.env.user.id])

                        access_domain_ah_ids = self.env['access.domain.ah'].sudo().browse(
                            row[0] for row in self.env.cr.fetchall()
                        )
                        access_domain_ah_ids -= access_domain_ah_ids.filtered(
                            lambda x: not x.access_management_id.is_apply_on_without_company
                                      and self.env.company.id not in x.access_management_id.company_ids.ids
                        )
                    except Exception:
                        access_domain_ah_ids = False

                    if access_domain_ah_ids:
                        domain_list = []
                        if model_name == 'res.partner':
                            self.env.cr.execute("SELECT partner_id FROM res_users")
                            partner_ids = [row[0] for row in self.env.cr.fetchall()]
                            if len(domain_list) > 1:
                                domain_list.insert(0, '|')
                            domain_list += [('id', 'in', partner_ids)]

                        left_user = False
                        length = len(access_domain_ah_ids.sudo()) if access_domain_ah_ids.sudo() else 0

                        for access in access_domain_ah_ids.sudo():
                            dom = ast.literal_eval(access.domain) if access.domain else []
                            if not dom and isinstance(dom, list):
                                if length > 1:
                                    domain_list.insert(0, '|')
                                domain_list += [('id', '!=', False)]
                                length -= 1

                            if dom:
                                dom = expression.normalize_domain(dom)
                                for dom_tuple in dom:
                                    if isinstance(dom_tuple, tuple):
                                        # ⚠️ compute_domain ahora retorna el tuple
                                        dom_tuple = compute_domain(dom_tuple, model_name, env=self.env)
                                        operator_value = dom_tuple[1]

                                        if operator_value == 'date_filter':
                                            domain_list += prepare_domain_v2(dom_tuple)
                                        else:
                                            domain_list.append(dom_tuple)
                                    else:
                                        domain_list.append(dom_tuple)
                                if length > 1:
                                    domain_list.insert(0, '|')
                                    length -= 1

                        if domain_list:
                            return domain_list

        return res
