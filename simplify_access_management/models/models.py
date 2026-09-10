from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

# ⚠️ DESACOPLADO: import local
from .domain_prepare import prepare_domain_v2


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)

        # Odoo 19: 'tree' -> 'list'
        form_toolbar = res['views'].get('form', {}).get('toolbar') or False
        list_toolbar = res['views'].get('list', {}).get('toolbar') or False

        remove_action = self.env['remove.action'].sudo().search([
            ('access_management_id.active', '=', True),
            ('access_management_id', 'in', self.env.user.access_management_ids.ids),
            ('model_id.model', '=', self._name)
        ])
        remove_action -= remove_action.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )

        if form_toolbar or list_toolbar:
            remove_server_action = remove_action.mapped('server_action_ids.action_id').ids
            remove_print_action = remove_action.mapped('report_action_ids.action_id').ids

        if form_toolbar:
            if res['views']['form']['toolbar'].get('action', False):
                action = [
                    rec for rec in res['views']['form']['toolbar']['action']
                    if rec.get('id', False) not in remove_server_action
                ]
                res['views']['form']['toolbar']['action'] = action
            if res['views']['form']['toolbar'].get('print', False):
                prints = [
                    rec for rec in res['views']['form']['toolbar']['print']
                    if rec.get('id', False) not in remove_print_action
                ]
                res['views']['form']['toolbar']['print'] = prints

        # Odoo 19: 'tree' -> 'list'
        if list_toolbar:
            if res['views']['list']['toolbar'].get('action', False):
                action = [
                    rec for rec in res['views']['list']['toolbar']['action']
                    if rec.get('id', False) not in remove_server_action
                ]
                res['views']['list']['toolbar']['action'] = action
            if res['views']['list']['toolbar'].get('print', False):
                prints = [
                    rec for rec in res['views']['list']['toolbar']['print']
                    if rec.get('id', False) not in remove_print_action
                ]
                res['views']['list']['toolbar']['print'] = prints

        return res

    @api.model
    def load_views(self, views, options=None):
        actions_and_prints = []
        remove_action = self.env['remove.action'].sudo().search([
            ('access_management_id.active', '=', True),
            ('access_management_id', 'in', self.env.user.access_management_ids.ids),
            ('model_id.model', '=', self._name)
        ])
        remove_action -= remove_action.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )

        for access in remove_action:
            actions_and_prints = actions_and_prints + access.mapped('report_action_ids.action_id').ids
            actions_and_prints = actions_and_prints + access.mapped('server_action_ids.action_id').ids
            for view_data in access.view_data_ids:
                for view_data_list in views:
                    if view_data.techname == view_data_list[1]:
                        views.pop(views.index(view_data_list))

        res = super().load_views(views, options=options)

        if 'fields_views' in res.keys():
            # Odoo 19: 'tree' -> 'list'
            for view in ['list', 'form']:
                if view in res['fields_views'].keys():
                    if 'toolbar' in res['fields_views'][view].keys():
                        if 'print' in res['fields_views'][view]['toolbar'].keys():
                            prints = res['fields_views'][view]['toolbar']['print'][:]
                            for pri in prints:
                                if pri['id'] in actions_and_prints:
                                    res['fields_views'][view]['toolbar']['print'].remove(pri)
                        if 'action' in res['fields_views'][view]['toolbar'].keys():
                            action = res['fields_views'][view]['toolbar']['action'][:]
                            for act in action:
                                if act['id'] in actions_and_prints:
                                    res['fields_views'][view]['toolbar']['action'].remove(act)
        return res

    def _get_access_management_domain_record(self, model=False):
        records = None
        try:
            if model:
                self.env.cr.execute(
                    "SELECT id FROM ir_model WHERE model = %s",
                    (model,)
                )
                row = self.env.cr.fetchone()
                model_numeric_id = row[0] if row else False

                if model_numeric_id and isinstance(model_numeric_id, int) and self.env.user:
                    self.env.cr.execute("""
                        SELECT dm.id
                        FROM access_domain_ah AS dm
                        WHERE dm.model_id = %s
                        AND dm.access_management_id IN (
                            SELECT am.id
                            FROM access_management AS am
                            WHERE am.active = 't'
                            AND am.id IN (
                                SELECT amusr.access_management_id
                                FROM access_management_users_rel_ah AS amusr
                                WHERE amusr.user_id = %s
                            )
                        )
                    """, [model_numeric_id, self.env.user.id])
                    records = self.env['access.domain.ah'].sudo().browse(
                        row[0] for row in self.env.cr.fetchall()
                    )
        except Exception:
            pass
        return records

    def _check_access_management_right(self, mode=False, records=False):
        access_flag = False
        access_rule = None
        length = len(records.sudo()) if records.sudo() else 0
        partner_ids = self.env['res.users'].sudo().search([]).mapped("partner_id.id")
        partner_domain = ['|', ('id', 'in', partner_ids)]

        for record in records.sudo():
            if mode == 'create' and record.create_right:
                access_flag = True
                break
            elif mode in ['write', 'unlink']:
                access = False
                if mode == 'unlink':
                    access = record.delete_right
                elif mode == 'write':
                    access = record.write_right

                domain_list = []
                if self.sudo()._name == "res.partner":
                    domain_list += partner_domain

                dom = safe_eval(record.domain) if record.domain else []
                if dom:
                    dom = expression.normalize_domain(dom)
                    model_name = self._name
                    if isinstance(dom, list):
                        for dom_tuple in dom:
                            if isinstance(dom_tuple, tuple):
                                left_value = dom_tuple[0]
                                operator_value = dom_tuple[1]
                                right_value = dom_tuple[2]
                                left_value_split_list = left_value.split('.')
                                model_string = model_name
                                left_user = False
                                left_company = False

                                for field in left_value_split_list:
                                    left_user = False
                                    left_company = False
                                    model_obj = self.env[model_string]
                                    field_type = model_obj.fields_get()[field]['type']
                                    if field_type in ['many2one', 'many2many', 'one2many']:
                                        field_relation = model_obj.fields_get()[field]['relation']
                                        model_string = field_relation
                                        if model_string == 'res.users':
                                            left_user = True
                                        if model_string == 'res.company':
                                            left_company = True

                                if left_user:
                                    if operator_value in ['in', 'not in']:
                                        if isinstance(right_value, list) and 0 in right_value:
                                            zero_index = right_value.index(0)
                                            right_value[zero_index] = self.env.user.id

                                if left_company:
                                    if operator_value in ['in', 'not in']:
                                        if isinstance(right_value, list) and 0 in right_value:
                                            zero_index = right_value.index(0)
                                            right_value[zero_index] = self.env.company.id

                                if operator_value == 'date_filter':
                                    domain_list += prepare_domain_v2(dom_tuple)
                                else:
                                    domain_list.append(dom_tuple)
                            else:
                                domain_list.append(dom_tuple)

                search_domain = domain_list
                if 'active' in self._fields:
                    search_domain = ['|', ('active', '=', False), ('active', '=', True)] + search_domain
                record_ids = self.search(search_domain)

                if self in record_ids and access:
                    access_flag = access
                    break
            access_rule = record.access_management_id.name

        return {'access_flag': access_flag, 'access_rule': access_rule}

    def _display_access_management_error(self, mode=None, rule=None):
        if mode and rule:
            msg_heads = {
                'unlink': _(
                    "Due to access management rule,\nYou are not allowed to delete record '%(record)s' from (%(document_model)s) model.",
                    record=self.display_name, document_model=self._name),
                'write': _(
                    "Due to access management rule,\nYou are not allowed to edit record '%(record)s' from (%(document_model)s) model.",
                    record=self.display_name, document_model=self._name),
                'create': _(
                    "Due to access management rule,\nYou are not allowed to create records from (%(document_model)s) model.",
                    document_model=self.display_name),
            }
            operation_error = msg_heads[mode]
            resolution_info = _("Check Applied Rule on Access Management:\n %(access_name)s", access_name=rule)
            msg = """{operation_error}

{resolution_info}""".format(operation_error=operation_error, resolution_info=resolution_info)
            raise AccessError(msg)

    def unlink(self):
        value = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'uninstall_simplify_access_management')], limit=1
        ).value
        if not value:
            for rec in self:
                if rec._name:
                    access_domain_ah_ids = rec._get_access_management_domain_record(model=rec._name)
                    if access_domain_ah_ids:
                        access_domain_ah_ids = access_domain_ah_ids.filtered(
                            lambda line: self.env.company in line.access_management_id.company_ids
                        )
                    if access_domain_ah_ids:
                        flag = rec._check_access_management_right(mode='unlink', records=access_domain_ah_ids)
                        if not flag['access_flag']:
                            rec._display_access_management_error(mode='unlink', rule=flag['access_rule'])
        return super().unlink()

    def write(self, vals):
        value = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'uninstall_simplify_access_management')], limit=1
        ).value
        if not value:
            for rec in self:
                if rec._name:
                    access_domain_ah_ids = rec._get_access_management_domain_record(model=rec._name)
                    if access_domain_ah_ids:
                        access_domain_ah_ids = access_domain_ah_ids.filtered(
                            lambda line: self.env.company in line.access_management_id.company_ids
                        )
                    if access_domain_ah_ids:
                        flag = rec._check_access_management_right(mode='write', records=access_domain_ah_ids)
                        if not flag['access_flag']:
                            rec._display_access_management_error(mode='write', rule=flag['access_rule'])
        return super().write(vals)

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        access_management_obj = self.env['access.management']

        readonly_access_id = access_management_obj.sudo().search([
            ('company_ids', 'in', self.env.company.id),
            ('active', '=', True),
            ('user_ids', 'in', self.env.user.id),
            ('readonly', '=', True)
        ])

        access_recs = self.env['access.domain.ah'].sudo().search([
            ('access_management_id.user_ids', 'in', self.env.user.id),
            ('access_management_id.active', '=', True),
            ('model_id.model', '=', self._name)
        ])
        access_recs -= access_recs.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )

        access_model_recs = self.env['remove.action'].sudo().search([
            ('access_management_id.user_ids', 'in', self.env.user.id),
            ('access_management_id.active', '=', True),
            ('model_id.model', '=', self._name)
        ])
        access_model_recs -= access_model_recs.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )

        if view_type == 'form':
            access_management_id = access_management_obj.sudo().search([
                ('active', '=', True),
                ('user_ids', 'in', self.env.user.id),
                ('hide_chatter', '=', True)
            ], limit=1)

            if access_management_id and access_management_id.is_apply_on_without_company:
                for div in arch.xpath
