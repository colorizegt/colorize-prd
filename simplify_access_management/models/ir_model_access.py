# -*- coding: utf-8 -*-
import logging
from odoo.http import request
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    @tools.ormcache_context('self.env.uid', 'self.env.su', 'model', 'mode', 'raise_exception', keys=('lang',))
    def check(self, model, mode='read', raise_exception=True):
        if model == 'mail.thread':
            return True
        if self.env.su or model == 'ir.model':
            return True

        assert isinstance(model, str), 'Not a model name: %s' % (model,)
        assert mode in ('read', 'write', 'create', 'unlink'), 'Invalid access mode'

        if model not in self.env:
            _logger.error('Missing model %s', model)

        # Verificar el parámetro de desinstalación
        self.env.cr.execute(
            "SELECT value FROM ir_config_parameter WHERE key = 'uninstall_simplify_access_management'"
        )
        value = self.env.cr.fetchone()

        if not value:
            if model:
                try:
                    self.env.cr.execute(
                        "SELECT id FROM ir_model WHERE model = %s",
                        (model,)
                    )
                    row = self.env.cr.fetchone()
                    model_numeric_id = row[0] if row else None

                    if model_numeric_id and isinstance(model_numeric_id, int) and self.env.user:
                        self.env.cr.execute("""
                            SELECT dm.id
                            FROM access_domain_ah AS dm
                            WHERE dm.model_id = %s
                            AND dm.access_management_id IN (
                                SELECT am.id
                                FROM access_management AS am
                                WHERE active = 't'
                                AND am.id IN (
                                    SELECT amusr.access_management_id
                                    FROM access_management_users_rel_ah AS amusr
                                    WHERE amusr.user_id = %s
                                )
                            )
                        """, [model_numeric_id, self.env.user.id])

                        access_domain_ah_ids = self.env['access.domain.ah'].sudo().browse(
                            row[0] for row in self.env.cr.fetchall()
                        ).filtered(
                            lambda line: self.env.company in line.access_management_id.company_ids
                        )
                        if access_domain_ah_ids:
                            return True
                except Exception:
                    pass

        # Verificar regla específica
        self.env.cr.execute("""
            SELECT MAX(CASE WHEN perm_{mode} THEN 1 ELSE 0 END)
            FROM ir_model_access a
           
