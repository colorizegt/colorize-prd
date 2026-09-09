from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    nombre_facturacion_fel = fields.Char('Nombre facturación FEL', copy=False)
