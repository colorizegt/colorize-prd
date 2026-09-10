from odoo.tools.sql import column_exists, rename_column
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if column_exists(cr, 'res_partner', 'buyer_code'):
        rename_column(cr, 'res_partner', 'buyer_code', 'fel_gt_buyer_code')
    if column_exists(cr, 'res_partner', 'invoice_currency'):
        rename_column(cr, 'res_partner', 'invoice_currency', 'fel_gt_invoice_currency')
    if column_exists(cr, 'res_partner', 'dpi_number'):
        rename_column(cr, 'res_partner', 'dpi_number', 'fel_gt_dpi_number')
    if column_exists(cr, 'res_partner', 'passport_number'):
        rename_column(cr, 'res_partner', 'passport_number', 'fel_gt_passport_number')
    if column_exists(cr, 'res_partner', 'consignatary_name'):
        rename_column(cr, 'res_partner', 'consignatary_name', 'fel_gt_consignatary_name')
    if column_exists(cr, 'res_partner', 'consignatary_code'):
        rename_column(cr, 'res_partner', 'consignatary_code', 'fel_gt_consignatary_code')
    if column_exists(cr, 'res_partner', 'consignatary_address'):
        rename_column(cr, 'res_partner', 'consignatary_address', 'fel_gt_consignatary_address')
    if column_exists(cr, 'res_partner', 'buyer_name'):
        rename_column(cr, 'res_partner', 'buyer_name', 'fel_gt_buyer_name')
    if column_exists(cr, 'res_partner', 'buyer_address'):
        rename_column(cr, 'res_partner', 'buyer_address', 'fel_gt_buyer_address')
    if column_exists(cr, 'res_partner', 'exporter_name'):
        rename_column(cr, 'res_partner', 'exporter_name', 'fel_gt_exporter_name')
    if column_exists(cr, 'res_partner', 'exporter_code'):
        rename_column(cr, 'res_partner', 'exporter_code', 'fel_gt_exporter_code')
    if column_exists(cr, 'res_partner', 'currency_from_invoice'):
        rename_column(cr, 'res_partner', 'currency_from_invoice', 'fel_gt_currency_from_invoice')

    _logger.info("Migration completed successfully.")
