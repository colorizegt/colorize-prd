from odoo import http
from odoo.exceptions import UserError
from odoo.addons.web.controllers.export import Export as WebExport
from odoo.http import request


class Export(WebExport):

    def fields_get(self, model, *args, **kwargs):
        """Odoo 19: firma con *args/**kwargs para compatibilidad."""
        fields = super().fields_get(model, *args, **kwargs)

        invisible_field_ids = request.env['hide.field'].search([
            ('access_management_id.company_ids', 'in', request.env.company.id),
            ('model_id.model', '=', model),
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', request.env.user.id),
            ('invisible', '=', True)
        ])

        if not invisible_field_ids:
            return fields

        # Recopilar los nombres de campos a ocultar
        invisible_field_names = set()
        for invisible_field in invisible_field_ids:
            for field in invisible_field.field_id:
                if field.name:
                    invisible_field_names.add(field.name)

        # Eliminar los campos invisibles (excepto 'id')
        for field_name in list(fields.keys()):
            if field_name in invisible_field_names and field_name != 'id':
                del fields[field_name]

        return fields
