# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
from odoo.tools.sql import column_exists, rename_column


def migrate(cr, version):
    if column_exists(cr, 'pos_config', 'fel_commercial_name'):
        rename_column(cr, 'pos_config', 'fel_commercial_name', 'fel_gt_commercial_name')

    if column_exists(cr, 'pos_config', 'fel_address'):
        rename_column(cr, 'pos_config', 'fel_address', 'fel_gt_address')

    if column_exists(cr, 'pos_config', 'fel_zip_code'):
        rename_column(cr, 'pos_config', 'fel_zip_code', 'fel_gt_zip_code')

    if column_exists(cr, 'pos_config', 'fel_department'):
        rename_column(cr, 'pos_config', 'fel_department', 'fel_gt_department')

    if column_exists(cr, 'pos_config', 'fel_township'):
        rename_column(cr, 'pos_config', 'fel_township', 'fel_gt_township')

    if column_exists(cr, 'pos_config', 'fel_certifier'):
        rename_column(cr, 'pos_config', 'fel_certifier', 'fel_gt_certifier')

    if column_exists(cr, 'pos_config', 'fel_active'):
        rename_column(cr, 'pos_config', 'fel_active', 'fel_gt_active')

    if column_exists(cr, 'pos_config', 'contingency_fel_active'):
        rename_column(cr, 'pos_config', 'contingency_fel_active', 'fel_gt_contingency_active')

    if column_exists(cr, 'pos_config', 'phrases_fel'):
        rename_column(cr, 'pos_config', 'phrases_fel', 'fel_gt_phrases')

    if column_exists(cr, 'pos_config', 'fel_contingency_start_range'):
        rename_column(cr, 'pos_config', 'fel_contingency_start_range', 'fel_gt_contingency_start_range')

    if column_exists(cr, 'pos_config', 'fel_contingency_end_range'):
        rename_column(cr, 'pos_config', 'fel_contingency_end_range', 'fel_gt_contingency_end_range')

    if column_exists(cr, 'pos_config', 'fel_contingency_actual_number'):
        rename_column(cr, 'pos_config', 'fel_contingency_actual_number', 'fel_gt_contingency_actual_number')

    if column_exists(cr, 'pos_config', 'auto_check_invoice'):
        rename_column(cr, 'pos_config', 'auto_check_invoice', 'fel_gt_auto_check_invoice')

    if column_exists(cr, 'pos_config', 'disable_download_invoice_pdf'):
        rename_column(cr, 'pos_config', 'disable_download_invoice_pdf', 'fel_gt_disable_download_invoice_pdf')

    if column_exists(cr, 'pos_config', 'default_customer'):
        rename_column(cr, 'pos_config', 'default_customer', 'fel_gt_default_customer')

    if column_exists(cr, 'pos_config', 'show_qrcode'):
        rename_column(cr, 'pos_config', 'show_qrcode', 'fel_gt_show_qrcode')

    if column_exists(cr, 'pos_config', 'size_qr_logo'):
        rename_column(cr, 'pos_config', 'size_qr_logo', 'fel_gt_size_qr_logo')

    if column_exists(cr, 'pos_config', 'show_fel_logo'):
        rename_column(cr, 'pos_config', 'show_fel_logo', 'fel_gt_show_fel_logo')

    if column_exists(cr, 'pos_config', 'show_logo'):
        rename_column(cr, 'pos_config', 'show_logo', 'fel_gt_show_logo')

    if column_exists(cr, 'pos_config', 'show_pdv_name'):
        rename_column(cr, 'pos_config', 'show_pdv_name', 'fel_gt_show_pdv_name')

    if column_exists(cr, 'pos_config', 'custom_logo'):
        rename_column(cr, 'pos_config', 'custom_logo', 'fel_gt_custom_logo')

    if column_exists(cr, 'pos_config', 'pos_custom_logo'):
        rename_column(cr, 'pos_config', 'pos_custom_logo', 'fel_gt_pos_custom_logo')

    if column_exists(cr, 'pos_config', 'cancel_fel_stock_picking'):
        rename_column(cr, 'pos_config', 'cancel_fel_stock_picking', 'fel_gt_cancel_stock_picking')

    if column_exists(cr, 'pos_config', 'cancel_fel_payment'):
        rename_column(cr, 'pos_config', 'cancel_fel_payment', 'fel_gt_cancel_payment')

    if column_exists(cr, 'pos_config', 'cancel_fel_order'):
        rename_column(cr, 'pos_config', 'cancel_fel_order', 'fel_gt_cancel_order')

    if column_exists(cr, 'pos_config', 'allow_open_cash_d'):
        rename_column(cr, 'pos_config', 'allow_open_cash_d', 'fel_gt_allow_open_cash_d')

    if column_exists(cr, 'pos_config', 'hide_product_info'):
        rename_column(cr, 'pos_config', 'hide_product_info', 'fel_gt_hide_product_info')

    if column_exists(cr, 'pos_config', 'show_stock_info'):
        rename_column(cr, 'pos_config', 'show_stock_info', 'fel_gt_show_stock_info')

    if column_exists(cr, 'pos_config', 'manage_stock_stock_info'):
        rename_column(cr, 'pos_config', 'manage_stock_stock_info', 'fel_gt_manage_stock_info')
    
    if column_exists(cr, 'pos_order', 'dte_invoice'):
        rename_column(cr, 'pos_order', 'dte_invoice', 'fel_gt_dte_invoice')

    if column_exists(cr, 'pos_order', 'uuid_invoice'):
        rename_column(cr, 'pos_order', 'uuid_invoice', 'fel_gt_uuid_invoice')

    if column_exists(cr, 'pos_order', 'serie_invoice'):
        rename_column(cr, 'pos_order', 'serie_invoice', 'fel_gt_serie_invoice')

    if column_exists(cr, 'pos_order', 'fel_cancel_motive'):
        rename_column(cr, 'pos_order', 'fel_cancel_motive', 'fel_gt_cancel_motive')

    if column_exists(cr, 'pos_order', 'date_invoice'):
        rename_column(cr, 'pos_order', 'date_invoice', 'fel_gt_date_invoice')

    if column_exists(cr, 'pos_order', 'has_contingency'):
        rename_column(cr, 'pos_order', 'has_contingency', 'fel_gt_has_contingency')

    if column_exists(cr, 'pos_order', 'contingency_access_number'):
        rename_column(cr, 'pos_order', 'contingency_access_number', 'fel_gt_contingency_access_number')