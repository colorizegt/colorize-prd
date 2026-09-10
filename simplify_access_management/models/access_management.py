from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.http import request


class AccessManagement(models.Model):
    _name = 'access.management'
    _description = "Access Management"

    name = fields.Char('Name')
    user_ids = fields.Many2many(
        'res.users', 'access_management_users_rel_ah',
        'access_management_id', 'user_id', 'Users'
    )

    readonly = fields.Boolean('Read-Only')
    active = fields.Boolean('Active', default=True)

    hide_menu_ids = fields.Many2many(
        'menu.item', 'access_management_menu_rel_ah',
        'access_management_id', 'menu_id', 'Hide Menu',
        help="The menu or submenu added on above list will be hidden from the defined users."
    )
    hide_field_ids = fields.One2many('hide.field', 'access_management_id', 'Hide Field', copy=True)
    remove_action_ids = fields.One2many('remove.action', 'access_management_id', 'Remove Action', copy=True)
    access_domain_ah_ids = fields.One2many('access.domain.ah', 'access_management_id', 'Access Domain', copy=True)
    hide_view_nodes_ids = fields.One2many('hide.view.nodes', 'access_management_id', 'Button/Tab Access', copy=True)

    self_module_menu_ids = fields.Many2many(
        'ir.ui.menu', 'access_management_ir_ui_self_module_menu',
        'access_management_id', 'menu_id', 'Self Module Menu',
        default=lambda self: self.env.ref('simplify_access_management.main_menu_simplify_access_management')
    )

    total_rules = fields.Integer('Access Rules', compute="_count_total_rules")

    # Chatter
    hide_chatter_ids = fields.One2many('hide.chatter', 'access_management_id', 'Hide Chatters', copy=True)
    hide_chatter = fields.Boolean('Hide Chatter', help="...")
    hide_send_mail = fields.Boolean('Hide Send Message', help="...")
    hide_log_notes = fields.Boolean('Hide Log Notes', help="...")
    hide_schedule_activity = fields.Boolean('Hide Schedule Activity', help="...")

    hide_export = fields.Boolean(help="...")
    hide_import = fields.Boolean(help="...")
    hide_spreadsheet = fields.Boolean()
    hide_add_property = fields.Boolean()
    disable_login = fields.Boolean('Disable Login', help="...")
    disable_debug_mode = fields.Boolean('Disable Developer Mode', help="...")

    # ⚠️ NO renombramos la tabla para evitar migración de datos
    # El typo 'comapnay' se mantiene para compatibilidad
    company_ids = fields.Many2many(
        'res.company', 'access_management_comapnay_rel',
        'access_management_id', 'company_id', 'Companies',
        default=lambda self: self.env.company
    )

    hide_filters_groups_ids = fields.One2many(
        'hide.filters.groups', 'access_management_id', 'Hide Filters/Group By', copy=True
    )
    is_apply_on_without_company = fields.Boolean(
        string="Apply Without Company", default=True,
        help="When 'Apply Without Company' is selected, the rules will be applied to every company."
    )

    def _count_total_rules(self):
        for rec in self:
            rule = 0
            rule = (rule + len(rec.hide_menu_ids) + len(rec.hide_field_ids)
                    + len(rec.remove_action_ids) + len(rec.access_domain_ah_ids)
                    + len(rec.hide_view_nodes_ids))
            rec.total_rules = rule

    def action_show_rules(self):
        pass

    def toggle_active_value(self):
        for record in self:
            record.write({'active': not record.active})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # Odoo 19: usar self.env.registry.clear_cache() en lugar de request.registry
        self.env.registry.clear_cache()
        for record in res:
            if record.readonly:
                for user in record.user_ids:
                    if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user can not be set as a read-only..!'))
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res

    def write(self, vals):
        res = super().write(vals)
        if self.readonly:
            for user in self.user_ids:
                if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                    raise UserError(_('Admin user can not be set as a read-only..!'))
        self.env.registry.clear_cache()
        return res

    def get_remove_options(self, model):
        restrict_export = self.env['access.management'].sudo().search([
            ('active', '=', True),
            ('user_ids', 'in', self.env.user.id),
            ('hide_export', '=', True),
            ('is_apply_on_without_company', '=', True)
        ], limit=1).id

        if not restrict_export:
            restrict_export = self.env['access.management'].sudo().search([
                ('active', '=', True),
                ('user_ids', 'in', self.env.user.id),
                ('hide_export', '=', True)
            ], limit=1)
            restrict_export = restrict_export.filtered(
                lambda x: x.is_apply_on_without_company or self.env.company.id in x.company_ids.ids
            )

        remove_action = self.env['remove.action'].sudo().search([
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', self.env.user.id),
            ('access_management_id', 'in', self.env.user.access_management_ids.ids),
            ('model_id.model', '=', model)
        ])
        remove_action -= remove_action.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )

        options = []
        added_export = False

        if restrict_export:
            options.append('export')
            added_export = True

        for action in remove_action:
            if not added_export and action.restrict_export:
                options.append('export')
            if action.restrict_archive_unarchive:
                options.append('archive')
                options.append('unarchive')
            if action.restrict_duplicate:
                options.append('duplicate')
        return options

    @api.model
    def get_chatter_hide_details(self, user_id, company_id, model=False):
        hide_send_mail = True
        hide_log_notes = True
        hide_schedule_activity = True

        access_ids = self.search([('user_ids', 'in', user_id), ('company_ids', 'in', company_id)])
        for access in access_ids:
            if access.hide_chatter:
                hide_send_mail = False
                hide_log_notes = False
                hide_schedule_activity = False
                break
            if access.hide_send_mail:
                hide_send_mail = False
            if access.hide_log_notes:
                hide_log_notes = False
            if access.hide_schedule_activity:
                hide_schedule_activity = False

        if model and (hide_send_mail or hide_log_notes or hide_schedule_activity):
            hide_ids = self.env['hide.chatter'].sudo().search([
                ('access_management_id.active', '=', True),
                ('access_management_id.user_ids', 'in', user_id),
                ('model_id.model', '=', model)
            ])
            hide_ids -= hide_ids.filtered(
                lambda x: not x.access_management_id.is_apply_on_without_company
                          and self.env.company.id not in x.access_management_id.company_ids.ids
            )

            if hide_ids:
                if hide_send_mail and hide_ids.filtered(lambda x: x.hide_send_mail):
                    hide_send_mail = False
                if hide_log_notes and hide_ids.filtered(lambda x: x.hide_log_notes):
                    hide_log_notes = False
                if hide_schedule_activity and hide_ids.filtered(lambda x: x.hide_schedule_activity):
                    hide_schedule_activity = False

        return {
            'hide_send_mail': hide_send_mail,
            'hide_log_notes': hide_log_notes,
            'hide_schedule_activity': hide_schedule_activity
        }

    def is_spread_sheet_available(self, action_model, action_id):
        model = self.env[action_model].sudo().browse(action_id).res_model
        if self.search([
            ('user_ids', 'in', self.env.user.id),
            ('company_ids', 'in', self.env.company.id),
            ('active', '=', True),
            ('hide_spreadsheet', '=', True)
        ]):
            return True
        restrict_spreadsheet = self.env['remove.action'].sudo().search([
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', self.env.user.id),
            ('model_id.model', '=', model),
            ('restrict_spreadsheet', '=', True)
        ])
        restrict_spreadsheet -= restrict_spreadsheet.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )
        if model and restrict_spreadsheet:
            return True
        return False

    def is_add_property_available(self, model):
        if self.search([
            ('user_ids', 'in', self.env.user.id),
            ('company_ids', 'in', self.env.company.id),
            ('active', '=', True),
            ('hide_add_property', '=', True)
        ]):
            return True
        return False

    def is_export_hide(self, model=False):
        am = self.search([
            ('user_ids', 'in', self.env.user.id),
            ('active', '=', True),
            ('hide_export', '=', True)
        ])
        if am.filtered(lambda x: x.is_apply_on_without_company or self.env.company.id in x.company_ids.ids):
            return True

        restrict_export = self.env['remove.action'].sudo().search([
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', self.env.user.id),
            ('model_id.model', '=', model),
            ('restrict_export', '=', True)
        ])
        restrict_export -= restrict_export.filtered(
            lambda x: not x.access_management_id.is_apply_on_without_company
                      and self.env.company.id not in x.access_management_id.company_ids.ids
        )
        if model and restrict_export:
            return True
        return False

    def get_hidden_field(self, model=False):
        if model:
            hidden_fields = []
            hide_field_obj = self.env['hide.field'].sudo()
            hide_fields = hide_field_obj.search([
                ('model_id.model', '=', model),
                ('access_management_id.active', '=', True),
                ('access_management_id.user_ids', 'in', self._uid),
                ('invisible', '=', True)
            ])
            hide_fields -= hide_fields.filtered(
                lambda x: not x.access_management_id.is_apply_on_without_company
                          and self.env.company.id not in x.access_management_id.company_ids.ids
            )
            for hide_field in hide_fields:
                for field in hide_field.field_id:
                    if field.name:
                        hidden_fields.append(field.name)
            return hidden_fields
        return []
