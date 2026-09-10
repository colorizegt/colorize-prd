from odoo import api, fields, models, tools, _
from odoo.addons.advanced_web_domain_widget.models.domain_prepare import prepare_domain_v2


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def domain_name_search(self, name='', args=None, operator='ilike', limit=100):
        res = self.sudo().name_search(name, args, operator, limit)
        return res

    @api.model
    def get_widget_count(self, args):
        domain_list = []
        for domain in args:
            if isinstance(domain, tuple) or isinstance(domain, list):
                domain_list += prepare_domain_v2(domain)
        return self.sudo().search_count(domain_list)
