
from odoo.addons.web.controllers.domain import Domain
from odoo import http, _


class Domain(Domain):

    @http.route('/web/domain/validate', type='json', auth="user")
    def validate(self, model, domain):
        result = super().validate(model, domain)
        if not result:
            # Odoo 19: domain puede ser una lista de tuplas/strings/dicts
            # Verificar de forma robusta si contiene 'date_filter'
            try:
                for dom in domain:
                    # Caso 1: dom es un string que contiene 'date_filter'
                    if isinstance(dom, str) and 'date_filter' in dom:
                        result = True
                        break
                    # Caso 2: dom es una tupla/lista donde el segundo elemento es 'date_filter'
                    if isinstance(dom, (tuple, list)) and len(dom) >= 2 and dom[1] == 'date_filter':
                        result = True
                        break
                    # Caso 3: dom es un dict (Odoo 19+ puede usar dicts)
                    if isinstance(dom, dict) and dom.get('operator') == 'date_filter':
                        result = True
                        break
            except (TypeError, IndexError):
                pass
        return result
