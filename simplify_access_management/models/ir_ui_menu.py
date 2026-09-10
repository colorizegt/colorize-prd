from odoo import fields, models, api, _
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        ids = super().search(args, offset=0, limit=None, order=order)
        user = self.env.user
        try:
            cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or self.env.company.id
            for menu_id in user.access_management_ids.filtered(
                lambda line: int(cids) in line.company_ids.ids
            ).mapped('hide_menu_ids.menu_id'):
                menu_id_rec = self.browse(menu_id)
                if menu_id_rec in ids:
                    ids = ids - menu_id_rec
            if offset:
                ids = ids[offset:]
            if limit:
                ids = ids[:limit]
        except Exception:
            pass
        return ids

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        menu_item_obj = self.env['menu.item'].sudo()
        for record in res:
            menu_item_obj.create({'name': record.display_name, 'menu_id': record.id})
        return res

    def unlink(self):
        menu_item_obj = self.env['menu.item'].sudo()
        for record in self:
            menu_item_obj.search([('menu_id', '=', record.id)]).unlink()
        return super().unlink()
