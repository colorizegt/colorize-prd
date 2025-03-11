# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fel_gt_auto_check_invoice = fields.Boolean(related='pos_config_id.fel_gt_auto_check_invoice', readonly=False)
    fel_gt_disable_download_invoice_pdf = fields.Boolean(related='pos_config_id.fel_gt_disable_download_invoice_pdf', readonly=False)
    fel_gt_default_customer = fields.Many2one(related='pos_config_id.fel_gt_default_customer', readonly=False)

    fel_gt_show_qrcode = fields.Boolean(related='pos_config_id.fel_gt_show_qrcode', readonly=False)
    fel_gt_size_qr_logo = fields.Integer(related='pos_config_id.fel_gt_size_qr_logo', readonly=False, default=110)
    fel_gt_show_fel_logo = fields.Boolean(related='pos_config_id.fel_gt_show_fel_logo', readonly=False)
    fel_gt_show_logo = fields.Boolean(related='pos_config_id.fel_gt_show_logo', readonly=False)
    fel_gt_show_pdv_name = fields.Boolean(related='pos_config_id.fel_gt_show_pdv_name', readonly=False)

    fel_gt_custom_logo = fields.Boolean(related='pos_config_id.fel_gt_custom_logo', readonly=False)

    fel_gt_contingency_active = fields.Boolean(related='pos_config_id.fel_gt_contingency_active', readonly=False)
    
    fel_gt_contingency_start_range = fields.Float(related="pos_config_id.invoice_journal_id.fel_gt_contingency_start_range", digits=(9, 0), readonly=False)
    fel_gt_contingency_end_range = fields.Float(related="pos_config_id.invoice_journal_id.fel_gt_contingency_end_range", digits=(9, 0), readonly=False)
    fel_gt_contingency_actual_number = fields.Float(related="pos_config_id.invoice_journal_id.fel_gt_contingency_actual_number", digits=(9, 0), readonly=False)

    fel_gt_cancel_stock_picking = fields.Boolean(related='pos_config_id.fel_gt_cancel_stock_picking', readonly=False)
    fel_gt_cancel_payment = fields.Boolean(related='pos_config_id.fel_gt_cancel_payment', readonly=False)
    fel_gt_cancel_order = fields.Boolean(related='pos_config_id.fel_gt_cancel_order', readonly=False)

    fel_gt_allow_open_cash_d = fields.Boolean(related='pos_config_id.fel_gt_allow_open_cash_d', readonly=False)
    fel_gt_hide_product_info = fields.Boolean(related='pos_config_id.fel_gt_hide_product_info', readonly=False)
    fel_gt_show_stock_info = fields.Boolean(related='pos_config_id.fel_gt_show_stock_info', readonly=False)
    fel_gt_manage_stock_info = fields.Selection(related='pos_config_id.fel_gt_manage_stock_info', readonly=False)

    fel_gt_force_refund_payment = fields.Boolean(related='pos_config_id.fel_gt_force_refund_payment', readonly=False)

    fel_gt_active = fields.Boolean(string="Generación de Facturación electrónica", related="pos_config_id.invoice_journal_id.fel_gt_active")
