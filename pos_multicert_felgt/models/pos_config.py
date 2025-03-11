# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"
    
    fel_gt_small_taxpayer_withholding = fields.Boolean(string="Pequeño Contribuyente", related="company_id.fel_gt_small_taxpayer_withholding")
    fel_gt_commercial_name = fields.Char(string="Nombre comercial", related="invoice_journal_id.fel_gt_commercial_name")
    fel_gt_address = fields.Char(string="Dirección de facturación", related="invoice_journal_id.fel_gt_address")
    fel_gt_zip_code = fields.Char(string="Código postal", related="invoice_journal_id.fel_gt_zip_code")
    fel_gt_department = fields.Char(string="Departamento", related="invoice_journal_id.fel_gt_department")
    fel_gt_township = fields.Char(string="Municipio", related="invoice_journal_id.fel_gt_township")
    fel_gt_certifier = fields.Selection(string='Certificador a utilizar', related="company_id.fel_gt_certifier")
    fel_gt_active = fields.Boolean(string="Generación de Facturación electrónica", related="invoice_journal_id.fel_gt_active")

    fel_gt_contingency_active = fields.Boolean(string="Habilitar Contigencia", default=True)
    fel_gt_phrases = fields.Many2many('fel_gt.tools.phrases', string="Frases FEL", related="invoice_journal_id.fel_gt_phrases")

    fel_gt_contingency_start_range = fields.Float(related="invoice_journal_id.fel_gt_contingency_start_range", digits=(9, 0))
    fel_gt_contingency_end_range = fields.Float(related="invoice_journal_id.fel_gt_contingency_end_range", digits=(9, 0))
    fel_gt_contingency_actual_number = fields.Float(related="invoice_journal_id.fel_gt_contingency_actual_number", digits=(9, 0))

    fel_gt_auto_check_invoice = fields.Boolean(string="Facturación Automatica")
    fel_gt_disable_download_invoice_pdf = fields.Boolean('Deshabilitar Descarga de PDF')
    fel_gt_default_customer = fields.Many2one('res.partner', string="Cliente por Defecto")

    fel_gt_show_qrcode = fields.Boolean(string="Mostrar Codigo QR")
    fel_gt_size_qr_logo = fields.Integer(string="Tamaño QR")
    fel_gt_show_fel_logo = fields.Boolean(string="Mostrar Logo de FEL")
    fel_gt_show_logo = fields.Boolean(string="Mostrar Logo")
    fel_gt_show_pdv_name = fields.Boolean(string="Mostrar Nombre de Punto de Venta")

    fel_gt_custom_logo = fields.Boolean(string="Logo Personalizado")
    fel_gt_pos_custom_logo = fields.Binary(string='Logo')

    fel_gt_cancel_stock_picking = fields.Boolean(string='Cancelar Movimiento de Inventario', default=True)
    fel_gt_cancel_payment = fields.Boolean(string='Cancelar Pago', default=True)
    fel_gt_cancel_order = fields.Boolean(string='Cancelar Orden', default=True)

    fel_gt_allow_open_cash_d = fields.Boolean(string='Habilitar Abrir Caja Registradora')
    fel_gt_hide_product_info = fields.Boolean(string='Ocultar Información de Producto en Punto de Venta')
    fel_gt_show_stock_info = fields.Boolean(string='Mostrar Stock en Punto de Venta')
    fel_gt_manage_stock_info = fields.Selection([('on_hand_qty', 'Cantidad en Mano'), ('available_qty', 'Cantidad Virtual'), ('both', 'Ambos')], string='Información de Stock', default='on_hand_qty')

    def get_current_fel_gt_access_number(self):
        self.ensure_one()
        return int(self.fel_gt_contingency_actual_number)

    fel_gt_force_refund_payment = fields.Boolean(string='Forzar Devolución hacia Pago Directamente', default=True)