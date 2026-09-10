from odoo.tools.sql import column_exists, rename_column
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):

    if column_exists(cr, 'account_journal', 'phrases_fel'):
        rename_column(cr, 'account_journal', 'phrases_fel', 'fel_gt_phrases')

    if column_exists(cr, 'account_journal', 'fel_certifier'):
        rename_column(cr, 'account_journal', 'fel_certifier', 'fel_gt_certifier')
    
    if column_exists(cr, 'account_journal', 'fel_active'):
        rename_column(cr, 'account_journal', 'fel_active', 'fel_gt_active')
    
    if column_exists(cr, 'account_journal', 'fel_establishment_code'):
        rename_column(cr, 'account_journal', 'fel_establishment_code', 'fel_gt_establishment_code')
    
    if column_exists(cr, 'account_journal', 'fel_address'):
        rename_column(cr, 'account_journal', 'fel_address', 'fel_gt_address')
    
    if column_exists(cr, 'account_journal', 'fel_commercial_name'):
        rename_column(cr, 'account_journal', 'fel_commercial_name', 'fel_gt_commercial_name')
    
    if column_exists(cr, 'account_journal', 'fel_zip_code'):
        rename_column(cr, 'account_journal', 'fel_zip_code', 'fel_gt_zip_code')
    
    if column_exists(cr, 'account_journal', 'fel_department'):
        rename_column(cr, 'account_journal', 'fel_department', 'fel_gt_department')
    
    if column_exists(cr, 'account_journal', 'fel_township'):
        rename_column(cr, 'account_journal', 'fel_township', 'fel_gt_township')
    
    if column_exists(cr, 'account_journal', 'fel_phrases'):
        rename_column(cr, 'account_journal', 'fel_phrases', 'fel_gt_phrases')
    
    if column_exists(cr, 'account_journal', 'is_receipt_journal'):
        rename_column(cr, 'account_journal', 'is_receipt_journal', 'fel_gt_is_receipt_journal')
    
    if column_exists(cr, 'account_journal', 'fel_has_contingency'):
        rename_column(cr, 'account_journal', 'fel_has_contingency', 'fel_gt_has_contingency')
    
    if column_exists(cr, 'account_journal', 'fel_contingency_start_range'):
        rename_column(cr, 'account_journal', 'fel_contingency_start_range', 'fel_gt_contingency_start_range')
    
    if column_exists(cr, 'account_journal', 'fel_contingency_end_range'):
        rename_column(cr, 'account_journal', 'fel_contingency_end_range', 'fel_gt_contingency_end_range')
    
    if column_exists(cr, 'account_journal', 'fel_contingency_actual_number'):
        rename_column(cr, 'account_journal', 'fel_contingency_actual_number', 'fel_gt_contingency_actual_number')
    
    if column_exists(cr, 'account_journal', 'custom_logo'):
        rename_column(cr, 'account_journal', 'custom_logo', 'fel_gt_custom_logo')
    
    if column_exists(cr, 'account_journal', 'invoice_custom_logo'):
        rename_column(cr, 'account_journal', 'invoice_custom_logo', 'fel_gt_invoice_custom_logo')

    
    
        

    

    