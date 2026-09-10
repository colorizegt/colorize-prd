# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class IrModel(models.Model):
    _inherit = 'ir.model'

    abstract = fields.Boolean('Abstract', readonly=True)

    @api.depends('name', 'model')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()
        for model in self:
            model.display_name = "{} ({})".format(model.name, model.model)


class IrModelField(models.Model):
    _inherit = 'ir.model.fields'

    @api.depends('field_description', 'name', 'model_id.model')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()
        for field in self:
            field.display_name = "{} => {} ({})".format(
                field.field_description, field.name, field.model_id.model
            )


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.depends('name', 'model')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()
        for view in self:
            view.display_name = "{} ({})".format(view.name, view.model)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def _button_immediate_function(self, function):
        res = super()._button_immediate_function(function)
        if function.__name__ in ['button_install', 'button_upgrade']:
            for record in self.env['ir.model'].search([]):
                try:
                    record.abstract = self.env[record.model]._abstract
                except Exception:
                    record.abstract = False
        return res
