from odoo.tools.sql import column_exists, rename_column
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE account_move
        SET fel_gt_invoice_type = CASE
            WHEN fel_gt_invoice_type = 'normal' THEN 'FACT'
            WHEN fel_gt_invoice_type = 'especial' THEN 'FESP'
            WHEN fel_gt_invoice_type = 'cambiaria' THEN 'FCAM'
            WHEN fel_gt_invoice_type = 'cambiaria_exp' THEN 'FEXP'
            WHEN fel_gt_invoice_type = 'nota_debito' THEN 'NDEB'
            WHEN fel_gt_invoice_type = 'nota_abono' THEN 'NABN'
            ELSE fel_gt_invoice_type
        END
        WHERE fel_gt_invoice_type IS NOT NULL;
    """)
    _logger.info("Updated %s account moves", cr.rowcount)

    cr.execute("""
        UPDATE res_users
        SET fel_gt_invoice_default_type = CASE
            WHEN fel_gt_invoice_default_type = 'normal' THEN 'FACT'
            WHEN fel_gt_invoice_default_type = 'especial' THEN 'FESP'
            WHEN fel_gt_invoice_default_type = 'cambiaria' THEN 'FCAM'
            WHEN fel_gt_invoice_default_type = 'cambiaria_exp' THEN 'FEXP'
            WHEN fel_gt_invoice_default_type = 'nota_debito' THEN 'NDEB'
            WHEN fel_gt_invoice_default_type = 'nota_abono' THEN 'NABN'
            ELSE fel_gt_invoice_default_type
        END
        WHERE fel_gt_invoice_default_type IS NOT NULL;
    """)
    _logger.info("Updated %s res users", cr.rowcount)

    if column_exists(cr, 'res_partner', 'is_foreign'):
        rename_column(cr, 'res_partner', 'is_foreign', 'fel_gt_is_foreign')

    if column_exists(cr, 'account_move', 'uuid'):
        rename_column(cr, 'account_move', 'uuid', 'fel_gt_uuid')

    if column_exists(cr, 'account_move', 'uuid_original'):
        rename_column(cr, 'account_move', 'uuid_original', 'fel_gt_uuid_original')

    if column_exists(cr, 'account_move', 'uuid_internal'):
        rename_column(cr, 'account_move', 'uuid_internal', 'fel_gt_uuid_internal')

    if column_exists(cr, 'account_move', 'serie'):
        rename_column(cr, 'account_move', 'serie', 'fel_gt_serie')

    if column_exists(cr, 'account_move', 'serie_original'):
        rename_column(cr, 'account_move', 'serie_original', 'fel_gt_serie_original')

    if column_exists(cr, 'account_move', 'dte_number'):
        rename_column(cr, 'account_move', 'dte_number', 'fel_gt_dte_number')

    if column_exists(cr, 'account_move', 'dte_number_original'):
        rename_column(cr, 'account_move', 'dte_number_original', 'fel_gt_dte_number_original')

    if column_exists(cr, 'account_move', 'dte_date'):
        rename_column(cr, 'account_move', 'dte_date', 'fel_gt_dte_date')

    if column_exists(cr, 'account_move', 'dte_issue_date_original'):
        rename_column(cr, 'account_move', 'dte_issue_date_original', 'fel_gt_dte_issue_date_original')

    if column_exists(cr, 'account_move', 'dte_issue_date'):
        rename_column(cr, 'account_move', 'dte_issue_date', 'fel_gt_dte_issue_date')

    if column_exists(cr, 'account_move', 'total_in_letters'):
        rename_column(cr, 'account_move', 'total_in_letters', 'fel_gt_total_in_letters')

    if column_exists(cr, 'account_move', 'is_foreign'):
        rename_column(cr, 'account_move', 'is_foreign', 'fel_gt_is_foreign')

    if column_exists(cr, 'account_move', 'has_contingency'):
        rename_column(cr, 'account_move', 'has_contingency', 'fel_gt_has_contingency')

    if column_exists(cr, 'account_move', 'contingency_access_number'):
        rename_column(cr, 'account_move', 'contingency_access_number', 'fel_gt_contingency_access_number')

    if column_exists(cr, 'account_move', 'contingency_state'):
        rename_column(cr, 'account_move', 'contingency_state', 'fel_gt_state')

    if column_exists(cr, 'account_move', 'xml_fel_sent'):
        rename_column(cr, 'account_move', 'xml_fel_sent', 'fel_gt_xml_fel_sent')

    if column_exists(cr, 'account_move', 'xml_fel_sent_name'):
        rename_column(cr, 'account_move', 'xml_fel_sent_name', 'fel_gt_xml_fel_sent_name')

    if column_exists(cr, 'account_move', 'xml_fel_certified'):
        rename_column(cr, 'account_move', 'xml_fel_certified', 'fel_gt_xml_fel_certified')

    if column_exists(cr, 'account_move', 'xml_fel_certified_name'):
        rename_column(cr, 'account_move', 'xml_fel_certified_name', 'fel_gt_xml_fel_certified_name')

    if column_exists(cr, 'account_move', 'phrases_fel'):
        rename_column(cr, 'account_move', 'phrases_fel', 'fel_gt_phrases')

    if column_exists(cr, 'account_move', 'cancel_motive'):
        rename_column(cr, 'account_move', 'cancel_motive', 'fel_gt_cancel_motive')

    
    
        

    

    