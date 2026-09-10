from odoo.tools.sql import column_exists, rename_column
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if column_exists(cr, 'res_company', 'fel_certifier'):
        rename_column(cr, 'res_company', 'fel_certifier', 'fel_gt_certifier')
    if column_exists(cr, 'res_company', 'fel_currency_from_invoice'):
        rename_column(cr, 'res_company', 'fel_currency_from_invoice', 'fel_gt_currency_from_invoice')
    if column_exists(cr, 'res_company', 'fel_invoice_currency'):
        rename_column(cr, 'res_company', 'fel_invoice_currency', 'fel_gt_invoice_currency')
    if column_exists(cr, 'res_company', 'fel_move_name'):
        rename_column(cr, 'res_company', 'fel_move_name', 'fel_gt_move_name')
    if column_exists(cr, 'res_company', 'fel_default_code_divider'):
        rename_column(cr, 'res_company', 'fel_default_code_divider', 'fel_gt_default_code_divider')
    if column_exists(cr, 'res_company', 'fel_invoice_line_name'):
        rename_column(cr, 'res_company', 'fel_invoice_line_name', 'fel_gt_invoice_line_name')
    if column_exists(cr, 'res_company', 'fel_price_tax_rounding'):
        rename_column(cr, 'res_company', 'fel_price_tax_rounding', 'fel_gt_price_tax_rounding')
    if column_exists(cr, 'res_company', 'fel_resolution_date'):
        rename_column(cr, 'res_company', 'fel_resolution_date', 'fel_gt_resolution_date')
    if column_exists(cr, 'res_company', 'fel_resolution_number'):
        rename_column(cr, 'res_company', 'fel_resolution_number', 'fel_gt_resolution_number')
    if column_exists(cr, 'res_company', 'fel_publish_onerror'):
        rename_column(cr, 'res_company', 'fel_publish_onerror', 'fel_gt_publish_onerror')
    if column_exists(cr, 'res_company', 'fel_establishment_code'):
        rename_column(cr, 'res_company', 'fel_establishment_code', 'fel_gt_establishment_code')
    if column_exists(cr, 'res_company', 'fel_small_taxpayer_withholding'):
        rename_column(cr, 'res_company', 'fel_small_taxpayer_withholding', 'fel_gt_small_taxpayer_withholding')
    if column_exists(cr, 'res_company', 'fel_old_tax_regime'):
        rename_column(cr, 'res_company', 'fel_old_tax_regime', 'fel_gt_old_tax_regime')

    # INFILE
    if column_exists(cr, 'res_company', 'infile_user'):
        rename_column(cr, 'res_company', 'infile_user', 'fel_gt_infile_user')
    if column_exists(cr, 'res_company', 'infile_cert_method'):
        rename_column(cr, 'res_company', 'infile_cert_method', 'fel_gt_infile_cert_method')
    if column_exists(cr, 'res_company', 'infile_xml_url_direct'):
        rename_column(cr, 'res_company', 'infile_xml_url_direct', 'fel_gt_infile_xml_url_direct')
    if column_exists(cr, 'res_company', 'infile_xml_key_signature'):
        rename_column(cr, 'res_company', 'infile_xml_key_signature', 'fel_gt_infile_xml_key_signature')
    if column_exists(cr, 'res_company', 'infile_xml_url_signature'):
        rename_column(cr, 'res_company', 'infile_xml_url_signature', 'fel_gt_infile_xml_url_signature')
    if column_exists(cr, 'res_company', 'infile_key_certificate'):
        rename_column(cr, 'res_company', 'infile_key_certificate', 'fel_gt_infile_key_certificate')
    if column_exists(cr, 'res_company', 'infile_url_certificate'):
        rename_column(cr, 'res_company', 'infile_url_certificate', 'fel_gt_infile_url_certificate')
    if column_exists(cr, 'res_company', 'infile_url_anulation'):
        rename_column(cr, 'res_company', 'infile_url_anulation', 'fel_gt_infile_url_anulation')

    # G4S
    if column_exists(cr, 'res_company', 'g4s_requestor'):
        rename_column(cr, 'res_company', 'g4s_requestor', 'fel_gt_g4s_requestor')
    if column_exists(cr, 'res_company', 'g4s_user'):
        rename_column(cr, 'res_company', 'g4s_user', 'fel_gt_g4s_user')
    if column_exists(cr, 'res_company', 'g4s_xml_url_signature'):
        rename_column(cr, 'res_company', 'g4s_xml_url_signature', 'fel_gt_g4s_xml_url_signature')
    
    # GUATEFACTURAS
    if column_exists(cr, 'res_company', 'guatefacturas_user'):
        rename_column(cr, 'res_company', 'guatefacturas_user', 'fel_gt_guatefacturas_user')
    if column_exists(cr, 'res_company', 'guatefacturas_password'):
        rename_column(cr, 'res_company', 'guatefacturas_password', 'fel_gt_guatefacturas_password')
    if column_exists(cr, 'res_company', 'guatefacturas_auth_user'):
        rename_column(cr, 'res_company', 'guatefacturas_auth_user', 'fel_gt_guatefacturas_auth_user')
    if column_exists(cr, 'res_company', 'guatefacturas_auth_password'):
        rename_column(cr, 'res_company', 'guatefacturas_auth_password', 'fel_gt_guatefacturas_auth_password')
    if column_exists(cr, 'res_company', 'guatefacturas_xml_url_signature'):
        rename_column(cr, 'res_company', 'guatefacturas_xml_url_signature', 'fel_gt_guatefacturas_xml_url_signature')
    
    # MEGAPRINT
    if column_exists(cr, 'res_company', 'megaprint_user'):
        rename_column(cr, 'res_company', 'megaprint_user', 'fel_gt_megaprint_user')
    if column_exists(cr, 'res_company', 'megaprint_apikey'):
        rename_column(cr, 'res_company', 'megaprint_apikey', 'fel_gt_megaprint_apikey')
    if column_exists(cr, 'res_company', 'megaprint_token'):
        rename_column(cr, 'res_company', 'megaprint_token', 'fel_gt_megaprint_token')
    if column_exists(cr, 'res_company', 'megaprint_url_token'):
        rename_column(cr, 'res_company', 'megaprint_url_token', 'fel_gt_megaprint_url_token')
    if column_exists(cr, 'res_company', 'megaprint_token_expiry_date'):
        rename_column(cr, 'res_company', 'megaprint_token_expiry_date', 'fel_gt_megaprint_token_expiry_date')
    if column_exists(cr, 'res_company', 'megaprint_xml_url_verify'):
        rename_column(cr, 'res_company', 'megaprint_xml_url_verify', 'fel_gt_megaprint_xml_url_verify')
    if column_exists(cr, 'res_company', 'megaprint_xml_url_signature'):
        rename_column(cr, 'res_company', 'megaprint_xml_url_signature', 'fel_gt_megaprint_xml_url_signature')
    if column_exists(cr, 'res_company', 'megaprint_xml_url_registry'):
        rename_column(cr, 'res_company', 'megaprint_xml_url_registry', 'fel_gt_megaprint_xml_url_registry')
    if column_exists(cr, 'res_company', 'megaprint_xml_url_cancel'):
        rename_column(cr, 'res_company', 'megaprint_xml_url_cancel', 'fel_gt_megaprint_xml_url_cancel')
    if column_exists(cr, 'res_company', 'megaprint_xml_url_pdf'):
        rename_column(cr, 'res_company', 'megaprint_xml_url_pdf', 'fel_gt_megaprint_xml_url_pdf')

    # DIGIFACT
    if column_exists(cr, 'res_company', 'digifact_user'):
        rename_column(cr, 'res_company', 'digifact_user', 'fel_gt_digifact_user')
    if column_exists(cr, 'res_company', 'digifact_password'):
        rename_column(cr, 'res_company', 'digifact_password', 'fel_gt_digifact_password')
    if column_exists(cr, 'res_company', 'digifact_url_token'):
        rename_column(cr, 'res_company', 'digifact_url_token', 'fel_gt_digifact_url_token')
    if column_exists(cr, 'res_company', 'digifact_token_expiry_date'):
        rename_column(cr, 'res_company', 'digifact_token_expiry_date', 'fel_gt_digifact_token_expiry_date')
    if column_exists(cr, 'res_company', 'digifact_token'):
        rename_column(cr, 'res_company', 'digifact_token', 'fel_gt_digifact_token')
    if column_exists(cr, 'res_company', 'digifact_api_xml_url_signature'):
        rename_column(cr, 'res_company', 'digifact_api_xml_url_signature', 'fel_gt_digifact_api_xml_url_signature')
    if column_exists(cr, 'res_company', 'digifact_api_pdf_url_signature'):
        rename_column(cr, 'res_company', 'digifact_api_pdf_url_signature', 'fel_gt_digifact_api_pdf_url_signature')
    if column_exists(cr, 'res_company', 'digifact_url_token_nuc'):
        rename_column(cr, 'res_company', 'digifact_url_token_nuc', 'fel_gt_digifact_url_token_nuc')
    if column_exists(cr, 'res_company', 'digifact_token_nuc_expiry_date'):
        rename_column(cr, 'res_company', 'digifact_token_nuc_expiry_date', 'fel_gt_digifact_token_nuc_expiry_date')
    if column_exists(cr, 'res_company', 'digifact_token_nuc'):
        rename_column(cr, 'res_company', 'digifact_token_nuc', 'fel_gt_digifact_token_nuc')

    _logger.info("Migration completed successfully.")
