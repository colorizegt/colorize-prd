from odoo import api, fields, models, tools, _
from odoo.addons.advanced_web_domain_widget.models.domain_prepare import prepare_domain_v2


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def domain_name_search(self, name='', args=None, operator='ilike', limit=100):
        """Odoo 19: name_search sigue existiendo con la misma firma básica."""
        return self.sudo().name_search(name, args, operator, limit)

    @api.model
    def get_widget_count(self, args):
        """Cuenta registros aplicando preparación de dominios."""
        domain_list = []
        for domain in args:
            if isinstance(domain, (tuple, list)):
                prepared = prepare_domain_v2(domain)
                if prepared:
                    domain_list += prepared
        return self.sudo().search_count(domain_list)
