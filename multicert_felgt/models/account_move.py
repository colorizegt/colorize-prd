# -*- coding: utf-8 -*-

'''
1. Factura Cambiaria: Crear una factura normal y dar click en otra pestaña, seleccionar tipo de factura, seleccionar factura cambiaria y validar.
2. Factura cambiaria Exp: Crear una factura normal y dar click en otra pestaña, seleccionar tipo de factura, seleccionar factura cambiaria Exp. (El cliente no debe de tener nit solo debe de aparecer CF, dentro del cliente hay un campo que se llama Código comprador, hay que llenarlo)
3. Factura especial: Crear una factura normal y dar click en otra pestaña, seleccionar tipo de factura, seleccionar factura especial y llenar el monto de retención, luego validar.
4. Nota de abono: La nota de abono se crea desde Rectificativas de cliente (Facturas rectificativas), la creas y le das click en otra pestaña y le das click en un check box que dice Nota de abono y validas.
 5. Nota de crédito rebajando régimen face: Esta se crea una factura rectificativa a partir de una factura normal, antes de validar la factura rectificativa dar click en otra pestaña y click en el check box nota de crédito rebajando régimen anterior, luego validar.
 6. Nota de débito: Se presiona el botón de Nota de débito sobre una factura FEL publicada y esta genera una nueva factura FEL tipo de documento Nota de débito enlazada a la anterior.
'''
from odoo import api, models, sql_db, fields, _, tools
from odoo import tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero

import xml.etree.cElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from lxml import etree

from datetime import date, datetime, timedelta
import dateutil.parser
from dateutil.tz import gettz

import zeep
from zeep.transports import Transport
import requests
from requests.auth import HTTPBasicAuth 
from requests import Session

import json
import base64
from random import randint
import re
import html
import uuid as UD
import decimal

from xml.dom.minidom import parseString

import logging

_logger = logging.getLogger(__name__)


# VALIDATIONS CONSTANTS
RAISE_VALIDATION_COMPANY_REGISTRY = "Por favor ingrese el registro fiscal de la empresa emisora."
RAISE_VALIDATION_COMPANY_EMAIL = "Por favor ingrese el correo electrónico de la empresa emisora."
RAISE_VALIDATION_COMPANY_VAT = "Por favor ingrese el número de NIT de la empresa emisora."
RAISE_VALIDATION_COMPANY_STREET = "Por favor ingrese la dirección de la empresa emisora."
RAISE_VALIDATION_INVOICE_DATE_DUE = "Por favor ingrese la fecha de vencimiento de la factura."
RAISE_VALIDATION_INVOICE_PARTNER_NAME = "Por favor ingrese un nombre para el receptor de la factura."
RAISE_VALIDATION_UUID_CANCEL = "La factura debe tener un número de serie para poder ser cancelada."
RAISE_VALIDATION_PARTNER_BUYER_CODE = "Por favor ingresar el código de comprador del receptor de la factura."
RAISE_VALIDATION_COMPANY_CONSIGNATARY_CODE = "Por favor ingresar el código de consignatario de la empresa emisora."
RAISE_VALIDATION_COMPANY_EXPORTER_CODE = "Por favor ingresar el código de exportador de la empresa emisora."
RAISE_VALIDATION_PARTNER_ADDRESS = "Por favor ingresar la dirección del comprador"
RAISE_VALIDATION_SOURCE_UUID = "Por favor ingresar el UUID de Origen"

xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
xmlns_cancel = "http://www.sat.gob.gt/dte/fel/0.1.0"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
xmlns_ds = "http://www.w3.org/2000/09/xmldsig#"
schemaLocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
schemaLocation_cancel = "http://www.sat.gob.gt/dte/fel/0.1.0"
fesp_cno = "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0"
fexp_cna = "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0"
fexp_cno = "http://www.sat.gob.gt/fel/exportacion.xsd"
fcam_cno = "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0"
fexp_schemaLocation_complementos = "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0 GT_Complemento_Exportaciones-0.1.0.xsd"
note_schemaLocation_complementos = "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0 GT_Complemento_Referencia_Nota-0.1.0.xsd"
note_complemento_xmlns = "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"
notes_xsd = "http://www.sat.gob.gt/fel/notas.xsd"
fcam_schemaLocation_complementos = "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0 GT_Complemento_Cambiaria-0.1.0.xsd"


class AccountMove(models.Model):
    _inherit = 'account.move'

    fel_gt_uuid = fields.Char("Número de Autorización", readonly=True, copy=False)
    fel_gt_uuid_original = fields.Char("Número de Autorización Origen", readonly=True)
    fel_gt_uuid_internal = fields.Char("Número de Autorización Interno", readonly=True, copy=False)

    fel_gt_serie = fields.Char("Serie", readonly=True, copy=False)
    fel_gt_serie_original = fields.Char("Serie Origen", readonly=True)

    fel_gt_dte_number = fields.Char("Número DTE", readonly=True, copy=False)
    fel_gt_dte_number_original = fields.Char("Número DTE Origen", readonly=True)

    fel_gt_dte_date = fields.Datetime("Fecha Autorización", readonly=True, copy=False)
    fel_gt_dte_issue_date_original = fields.Char("Fecha Emisión Origen", readonly=True, copy=False)
    fel_gt_dte_issue_date = fields.Char("Fecha Emisión", copy=False)

    fel_gt_total_in_letters = fields.Text("Total Letras", readonly=True, copy=False)
    fel_gt_withhold_amount = fields.Float(string="Retención", readonly=True, copy=False)

    def _get_default_fel_gt_invoice_type(self):
        if self.env.user.fel_gt_invoice_default_type:
            return self.env.user.fel_gt_invoice_default_type
        else:
            return 'FACT'

    fel_gt_default_invoice_type = fields.Char(default=_get_default_fel_gt_invoice_type)

    fel_gt_invoice_type = fields.Selection([
        ('none', 'Ninguno'),
        ('FACT', 'Factura Normal'),
        ('FESP', 'Factura Especial'),
        ('FCAM', 'Factura Cambiaria'),
        ('FEXP', 'Factura Cambiaria Exp.'),
        ('NDEB', 'Nota de Débito'),
        ('NABN', 'Nota de Abono'),
        ('NCRE', 'Nota de Crédito'),
        ('RECI', 'Recibo'),
    ], string='Tipo de Factura', default=_get_default_fel_gt_invoice_type, copy=False)

    @api.onchange('fel_gt_invoice_type')
    def onchange_fel_gt_invoice_type(self):
        if 'type_invoice' in self.env['account.move']._fields:
            self.type_invoice = self.fel_gt_invoice_type
    
    fel_gt_old_tax_regime = fields.Boolean(string="Nota de crédito rebajando régimen antiguo", readonly=True, related='company_id.fel_gt_old_tax_regime')

    fel_gt_document_type = fields.Selection([
        ('RECI', 'Recibo'),
        ('RDON', 'Recibo por Donacion'),
        ('RANT', 'Recibo Anticipo'),
    ], string='Tipo de Documento', default="RECI", copy=False)

    fel_gt_source_debit_note_id = fields.Many2one('account.move', string="ND Documento origen", copy=False)
    fel_gt_source_credit_note_id = fields.Many2one('account.move', string="NC Documento origen", copy=False)

    fel_gt_sat_ref_id = fields.Char(string="AcuseReciboSAT", copy=False)
    fel_gt_link = fields.Char(string="Documento FEL Certificador", compute="get_fel_gt_link")
    fel_gt_sat_link = fields.Char(string="Documento FEL SAT", compute="get_fel_gt_sat_link")
    
    fel_gt_certifier = fields.Selection(string='Certificador a utilizar', related="journal_id.fel_gt_certifier", readonly=False)
    fel_gt_active = fields.Boolean(string="Generación de Facturación Electrónica", related="journal_id.fel_gt_active")

    fel_gt_enable_cancel_bypass = fields.Boolean(default=False, string="Generación de FEL fallida")
    fel_gt_is_foreign = fields.Boolean(string="Cliente del Extranjero", related="partner_id.fel_gt_is_foreign")

    fel_gt_has_contingency = fields.Boolean(string="Factura en contingencia", copy=False)
    fel_gt_contingency_access_number = fields.Char(string="Número de acceso", copy=False)

    fel_gt_state = fields.Selection([
        ('pending', 'Sin certificar'),
        ('sat_validation_error', 'Error en datos FEL'),
        ('certified', 'Certificada'),
        ('contingency', 'Contingencia FEL'),
        ('cancel', 'Anulada FEL'),
        ], string='Estado certificación FEL', readonly=False, copy=False, default="pending")
    
    fel_gt_xml_fel_sent = fields.Binary('Documento xml FEL', copy=False)
    fel_gt_xml_fel_sent_name = fields.Char('Nombre archivo xml FEL', default='xml_fel_sent.xml', size=32, copy=False)
    
    fel_gt_xml_fel_certified = fields.Binary('Documento xml FEL certificado', copy=False)
    fel_gt_xml_fel_certified_name = fields.Char('Nombre archivo xml FEL certificado', default='xml_fel_certified.xml', size=32, copy=False)
    
    fel_gt_phrases = fields.Many2many('fel_gt.tools.phrases', string="Frases FEL")

    fel_gt_original_values = fields.Text(
        string="Original FEL Values",
        help="Stores the original values of the invoice lines for restoration."
    )

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.fel_gt_state == 'certified' and self.fel_gt_uuid:
            if self.company_id.fel_gt_use_as_default_template:
                return 'multicert_felgt.fel_gt_report_invoice'
            else:
                return 'multicert_felgt.fel_gt_report_invoice_document'
        return super()._get_name_invoice_report()

    @api.onchange('journal_id')
    def _onchange_fel_gt_journal_phrases(self):
        """Sets the phrases for the invoice using the selected journal."""
        for rec in self:
            if not rec.fel_gt_phrases:
                if rec.journal_id and rec.journal_id.fel_gt_active:
                    rec.fel_gt_phrases = rec.journal_id.fel_gt_phrases
                else:
                    rec.fel_gt_phrases = [(5, 0, 0)]
                    if rec.move_type == 'in_invoice':
                        rec.fel_gt_invoice_type = 'FACT'

    fel_gt_cancel_motive = fields.Char("Motivo de Cancelación", copy=False)

    @api.model
    def default_get(self, default_fields):
        """Sets the default values for the invoice."""
        values = super(AccountMove, self).default_get(default_fields)
        if values.get('move_type', False) == 'out_refund':
            values['fel_gt_invoice_type'] = 'NABN'
        if values.get('move_type', False) == 'in_invoice':
            values['fel_gt_invoice_type'] = 'FESP'
        self._onchange_fel_gt_journal_phrases()
        return values
            
    def fel_gt_action_debit_note(self):
        """Generates a debit note for the invoice."""
        for rec in self:

            ctx = self._context.copy()
            ctx.update({
                'default_fel_gt_source_debit_note_id': rec.id,
                'default_journal_id': rec.journal_id.id,
                'default_fel_gt_invoice_type': 'NDEB',
                'default_partner_id': rec.partner_id.id
            })

            view_id = self.env.ref('account.view_move_form').id
            return {
                'name': _('Create invoice/bill'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': self.env.ref('account.view_move_form').id,
                'context': ctx
            }

    def get_fel_gt_link(self):
        """Generates the link for the invoice using the selected certifier."""
        for rec in self:
            rec.fel_gt_link = ""
            if rec.is_invoice(include_receipts=True):
                fel_certifier = rec.env.company.fel_gt_certifier
                rec.fel_gt_link = ""      
                if fel_certifier == 'infile':
                    if rec.fel_gt_uuid:
                        rec.fel_gt_link = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid="+str(rec.fel_gt_uuid)
                    else:
                        rec.fel_gt_link = ""

    def get_fel_gt_sat_link(self):
        """Generates the SAT link for the invoice."""
        for rec in self:
            rec.fel_gt_sat_link = ""
            if rec.is_invoice(include_receipts=True):
                rec.fel_gt_sat_link = ""

                vat = self._get_fel_gt_receptor_vat_info()[0]

                if rec.fel_gt_uuid:
                    rec.fel_gt_sat_link = "https://felpub.c.sat.gob.gt/verificador-web/publico/vistas/verificacionDte.jsf?tipo=autorizacion&numero="+rec.fel_gt_uuid+"&emisor="+str(rec.company_id.vat.replace('-',''))+"&receptor="+str(vat)+"&monto="+str(rec.amount_total)
                if rec.fel_gt_contingency_access_number:
                    rec.fel_gt_sat_link = "https://felpub.c.sat.gob.gt/verificador-web/publico/vistas/verificacionDte.jsf?tipo=contingencia&numero="+rec.fel_gt_contingency_access_number+"&emisor="+str(rec.company_id.vat.replace('-',''))+"&receptor="+str(vat)+"&monto="+str(rec.amount_total)
    
    def generate_fel_gt_certifier_pdf(self):
        """Generates the PDF for the invoice using the selected certifier."""
        for rec in self:
            if rec.fel_gt_certifier == 'megaprint':
                return rec.generate_megaprint_pdf()
            elif rec.fel_gt_certifier == 'g4s':
                return rec.generate_g4s_pdf()
            elif rec.fel_gt_certifier == 'infile':
                return rec.generate_infile_pdf()
            elif rec.fel_gt_certifier == 'megaprint':
                return rec.generate_megaprint_pdf()
            elif rec.fel_gt_certifier == 'digifact':
                return rec.generate_digifact_pdf()
            else:
                return self.env.ref('account.account_invoices').report_action(self)

    def _create_fel_gt_attachment(self, name, pdf_content):
        """Creates an attachment for the invoice PDF."""
        attachment = self.env['ir.attachment'].sudo().create({
            'name': name,
            'mimetype': 'application/pdf',
            'res_model': 'account.move',
            'type': 'binary',
            'public': False,
            'datas': pdf_content,
            'res_id': self.id
        })
        return attachment

    def _get_fel_gt_action_for_attachment(self, attachment_id):
        """Returns the action to download the attachment."""
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment_id.id),
            'target': 'self',
            'nodestroy': False,
            'context': self._context,
        }

    def generate_infile_pdf(self):
        """Generates the PDF for the invoice using the Infile API."""
        try:
            file_url = f'https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid={self.fel_gt_uuid}'
            invoice_file = requests.get(file_url, timeout=10)
            invoice_file.raise_for_status()
            
            pdf_content = base64.b64encode(invoice_file.content)
            attachment = self._create_fel_gt_attachment('DTE-' + str(self.fel_gt_dte_number), pdf_content)

            return self._get_fel_gt_action_for_attachment(attachment)
        except requests.RequestException:
            return self.env.ref('account.account_invoices').report_action(self)

    def generate_megaprint_pdf(self):
        """Generates the PDF for the invoice using the Megaprint API."""
        try:
            token = self._get_megaprint_token()
            headers = {"Content-Type": "application/xml", "authorization": f"Bearer {token}"}
            data = f'<?xml version="1.0" encoding="UTF-8"?><RetornaPDFRequest><uuid>{self.fel_gt_uuid}</uuid></RetornaPDFRequest>'
            
            r = requests.post(self.company_id.fel_gt_megaprint_xml_url_pdf, data=data, headers=headers, timeout=10)
            r.raise_for_status()

            resultadoXML = etree.XML(r.content)
            if not resultadoXML.xpath("//listado_errores"):
                pdf_content = resultadoXML.xpath("//pdf")[0].text
                attachment = self._create_fel_gt_attachment('DTE-' + str(self.fel_gt_dte_number), pdf_content)
                return self._get_fel_gt_action_for_attachment(attachment)

        except (requests.RequestException, etree.XMLSyntaxError):
            return self.env.ref('account.account_invoices').report_action(self)

    def generate_digifact_pdf(self):
        """Generates the PDF for the invoice using the Digifact API."""
        try:
            token = self._get_digifact_token()
            api_url = self.company_id.fel_gt_digifact_api_pdf_url_signature
            headers = {"Authorization": token}
            params = {
                'TAXID': self.company_id.vat.replace('-', '').zfill(12),
                'FORMAT': 'PDF',
                'USERNAME': self.company_id.fel_gt_digifact_user,
                'AUTHNUMBER': self.fel_gt_uuid,
            }
            
            r = requests.get(api_url, params=params, headers=headers, verify=False, timeout=10)
            r.raise_for_status()
            
            pdf_json = r.json()
            if pdf_json['REQUEST_DATA'][0]['Respuesta'] == 1:
                pdf_content = pdf_json['RESPONSE'][0]['ResponseData3']
                attachment = self._create_fel_gt_attachment('DTE-' + str(self.fel_gt_dte_number), pdf_content)
                return self._get_fel_gt_action_for_attachment(attachment)

        except (requests.RequestException, KeyError, ValueError):
            return self.env.ref('account.account_invoices').report_action(self)

    def generate_g4s_pdf(self):
        """Generates the PDF for the invoice using the G4S API."""
        try:

            company_id = self.company_id
            client = zeep.Client(wsdl=f"{company_id.g4s_xml_url_signature}?wsdl")

            request_data = {
                'Requestor': company_id.g4s_requestor,
                'Transaction': 'GET_DOCUMENT',
                'Country': 'GT',
                'Entity': company_id.vat,
                'User': company_id.g4s_requestor,
                'UserName': company_id.g4s_user,
                'Data1': self.fel_gt_uuid,
                'Data2': '',
                'Data3': 'PDF'
            }
            
            service_response = client.service.RequestTransaction(**request_data)
            pdf_b64_data = service_response.get('ResponseData', {}).get('ResponseData3')
            
            if not pdf_b64_data or not pdf_b64_data.startswith('%PDF'):
                raise ValueError("Invalid PDF data")

            pdf_content = base64.b64decode(pdf_b64_data, validate=True)
            attachment = self._create_fel_gt_attachment('DTE-' + str(self.fel_gt_dte_number), pdf_content)
            return self._get_fel_gt_action_for_attachment(attachment)
        
        except (zeep.exceptions.Error, ValueError):
            return self.env.ref('account.account_invoices').report_action(self)


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Sets the default values for the invoice using the selected partner."""
        if self.is_invoice(include_receipts=True):
            if self.partner_id.fel_gt_invoice_currency:
                self.currency_id = self.partner_id.fel_gt_invoice_currency
            else:
                if self.journal_id.currency_id:
                    self.currency_id = self.journal_id.currency_id
                else:
                    self.currency_id = self.company_id.currency_id


    def _post(self, soft=True):
        """Post the journal entry of the move."""
        if soft or len(self) == 0:
            return super(AccountMove, self)._post(soft)

        for move in self:
            if not move.is_invoice(include_receipts=True):
                return super(AccountMove, self)._post(soft)
            
            if not move.journal_id.fel_gt_active:
                return super(AccountMove, self)._post(soft)

            if move.fel_gt_invoice_type in ['none', False]:
                raise UserError("Favor agregar el tipo de Factura, previo a validarla.")
            
            if move.fel_gt_has_contingency or move.journal_id.fel_gt_has_contingency:
                return move._handle_fel_gt_contingency(soft)
            
            invoice_response = super(AccountMove, self)._post(soft)
            currency_name, general_rounding = move._get_fel_gt_currency_and_rounding()

            if move.move_type == "in_invoice":
                move._handle_fel_gt_in_invoice(currency_name, general_rounding, move.journal_id.fel_gt_is_receipt_journal or move.fel_gt_invoice_type == 'RECI')
            
            elif move.move_type == "out_invoice":
                move._handle_fel_gt_out_invoice(currency_name, general_rounding, move.journal_id.fel_gt_is_receipt_journal or move.fel_gt_invoice_type == 'RECI')

            elif move.move_type == "out_refund":
                move._handle_fel_gt_out_refund()

            return invoice_response

    def _handle_fel_gt_contingency(self, soft):
        """Handles the contingency process for the invoice."""
        if not self.fel_gt_contingency_access_number:
            self.fel_gt_contingency_access_number = self.get_fel_gt_establishment_access_code()
        if self.company_id.fel_gt_move_name:
            self.name = "DTE-" + str(self.fel_gt_contingency_access_number)
        self.write({'fel_gt_state': 'contingency'})
        return super(AccountMove, self)._post(soft)

    def _get_fel_gt_currency_and_rounding(self):
        """Returns the currency and rounding for the invoice."""
        currency_name = self.currency_id.currency_unit_label
        if self.company_id.fel_gt_invoice_currency and not self.company_id.fel_gt_currency_from_invoice and not self.partner_id.fel_gt_currency_from_invoice:
            currency_name = self.company_id.fel_gt_invoice_currency.currency_unit_label
        
        general_rounding = self.company_id.fel_gt_price_tax_rounding or 2
        return currency_name, general_rounding

    def _handle_fel_gt_in_invoice(self, currency_name, general_rounding, is_receipt):
        """Handles the invoice process for the invoice."""
        total = self._calculate_fel_total_withholdings(general_rounding)
        self.fel_gt_total_in_letters = str(number2text(total, currency_name))

        if not is_receipt:
            if self.fel_gt_invoice_type == 'FESP':
                self._process_fel_gt_invoice(self.fel_gt_invoice_type, 'Facturación Electrónica Especial')

    def _handle_fel_gt_out_invoice(self, currency_name, general_rounding, is_receipt):
        """Handles the invoice process for the invoice."""
        client_nit = self._get_fel_gt_receptor_vat_info()[0]
        
        self._validate_fel_out_invoice_nit(client_nit)
        
        total = self._calculate_fel_total_withholdings(general_rounding)
        self.fel_gt_total_in_letters = str(number2text(total, currency_name))            
        
        if is_receipt:
            self._process_fel_gt_receipt()
        else:
            self._process_fel_gt_out_invoice_by_type()

    def _validate_fel_out_invoice_nit(self, client_nit):
        """Validates the NIT for the invoice."""
        if client_nit in ["CF", "C/F"] and self.amount_total > 2500:
            if not self.partner_id.fel_gt_dpi_number and not self.partner_id.fel_gt_passport_number:
                raise UserError('No se pueden emitir facturas con un monto mayor a Q 2,500.00 a un NIT CF. Debe ingresar el DPI o número de pasaporte, en caso ser extranjero.')

    def _calculate_fel_total_withholdings(self, general_rounding):
        """Calculates the total for the invoice with withholdings."""
        total = self.amount_total
        if 'isr_withold_amount' in self.env['account.move']._fields:
            total += self.isr_withold_amount
        if 'iva_withold_amount' in self.env['account.move']._fields:
            total += self.iva_withold_amount
        return round(total, general_rounding)

    def _process_fel_gt_invoice(self, invoice_type, doc_type):
        """Processes the invoice for the invoice."""
        fel_certifier = self.company_id.fel_gt_certifier
        xml_data = self._xml_standard_fel_gt_maker(fel_certifier, type=invoice_type)
        uuid, serie, dte_number, dte_date, sat_ref_id = self.send_data_api(xml_data, 'fel', doc_type, fel_certifier)
        message = _(f"{self._fel_gt_invoice_name()}: Serie %s  Número %s") % (serie, dte_number)
        self._finalize_fel_gt_invoice(uuid, serie, dte_number, dte_date, sat_ref_id, message)

    def _fel_gt_invoice_name(self):
        """Returns the name for the invoice."""
        if self.fel_gt_invoice_type == 'FACT':
            if self.company_id.fel_gt_small_taxpayer_withholding:
                return 'Factura Electrónica Pequeño Contribuyente'
            else:
                return 'Factura Electrónica'
        elif self.fel_gt_invoice_type == 'FCAM':
            if self.company_id.fel_gt_small_taxpayer_withholding:
                return 'Factura Cambiaria Pequeño Contribuyente'
            else:
                return 'Factura Electrónica Cambiaria'
        elif self.fel_gt_invoice_type == 'FEXP':
            return 'Factura Electrónica Cambiaria de Exportación'
        elif self.fel_gt_invoice_type == 'FESP':
            return 'Factura Especial Electrónica'
        elif self.fel_gt_invoice_type == 'NDEB':
            return 'Nota de Débito'
        elif self.fel_gt_invoice_type == 'RECI':
            if self.fel_gt_document_type == 'RDON':
                return 'Recibo Donacion'
            elif self.fel_gt_document_type == 'RANT':
                return 'Recibo por Anticipo'
            else:
                return 'Recibo'
        elif self.fel_gt_invoice_type == 'NABN':
            return 'Nota de Abono'
        else:
            return 'Nota de Crédito'

    def _process_fel_gt_out_invoice_by_type(self):
        """Processes the invoice for the invoice by type."""
        if self.fel_gt_invoice_type == 'FACT':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 1)
        elif self.fel_gt_invoice_type == 'FESP':
            raise UserError("Las facturas especiales FEL solo pueden ser emitidas desde la facturación de proveedores")
        elif self.fel_gt_invoice_type == 'FCAM':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 2)
        elif self.fel_gt_invoice_type == 'FEXP':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 1)
        elif self.fel_gt_invoice_type == 'NDEB':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 9)
        elif self.fel_gt_invoice_type == 'RECI':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 9)

    def _process_fel_gt_receipt(self):
        if self.fel_gt_document_type == 'RDON':
            self._process_fel_gt_invoice(self.fel_gt_document_type, 8)
        elif self.fel_gt_document_type == 'RANT':
            self._process_fel_gt_invoice(self.fel_gt_document_type, 8)
        else:
            self._process_fel_gt_invoice(self.fel_gt_document_type, 8)

    def _handle_fel_gt_out_refund(self):
        if self.fel_gt_invoice_type == 'NABN':
            self._process_fel_gt_invoice(self.fel_gt_invoice_type, 6)
        else:
            self._process_fel_gt_invoice('NCRE', 10)

    def _finalize_fel_gt_invoice(self, uuid, serie, dte_number, dte_date, sat_ref_id, message, cancel=False):
        """Finalizes the invoice for the invoice."""
        self.message_post(body=message)
        if not cancel:
            self.fel_gt_uuid = uuid
            self.fel_gt_serie = serie
            self.fel_gt_dte_number = dte_number
            self.fel_gt_sat_ref_id = sat_ref_id
        if not self.fel_gt_uuid_original:
            self.fel_gt_uuid_original = uuid
            self.fel_gt_dte_issue_date_original = self.fel_gt_dte_issue_date
            self.fel_gt_serie_original = serie
            self.fel_gt_dte_number_original = dte_number
        if dte_date:
            self.fel_gt_dte_date = self._convert_fel_gt_dte_date(dte_date)
        if dte_number and self.company_id.fel_gt_move_name:
            self.name = f"DTE-{dte_number}"
        xml_name = f"DTE-{dte_number}.xml"
        xml_certified_name = f"CERTIFIED_{xml_name}"
        if not cancel:
            self.write({'fel_gt_state': 'certified', "fel_gt_xml_fel_sent_name": xml_name, "fel_gt_xml_fel_certified_name": xml_certified_name})
        else:
            self.write({'fel_gt_state': 'cancel', "fel_gt_xml_fel_sent_name": xml_name, "fel_gt_xml_fel_certified_name": xml_certified_name})
        
        self._restore_fel_gt_original_values()

    def _convert_fel_gt_dte_date(self, dte_date):
        """Converts the DTE date for the invoice."""
        dte_given_time = dateutil.parser.parse(dte_date)
        timezone_gt_adjust = timedelta(hours=6)
        gt_time = dte_given_time + timezone_gt_adjust
        return gt_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def button_draft(self):
        """Sets the invoice to draft state."""
        for move in self:
            if move.is_invoice():
                if move.state == 'cancel' and move.fel_gt_uuid:
                    raise UserError('La factura ya ha sido anulada en SAT, por lo que no puede ser retablecida a borrador, debera crear una nueva.')
        res = super(AccountMove, self).button_draft()
        return res


    def button_cancel(self):
        """Cancels the invoice."""
        for move in self:
            if move.is_invoice():
                if not move.journal_id.fel_gt_active:
                    return super(AccountMove, self).button_cancel()

                if self.fel_gt_state == 'certified':
                    if move.move_type in ["in_invoice", "out_invoice"] and not move.fel_gt_enable_cancel_bypass:
                        self.cancel_fel_gt_move()
                    elif move.move_type == "out_refund":
                        self.cancel_fel_gt_move()
        return super(AccountMove, self).button_cancel()
    

    def cancel_fel_gt_move(self):
        """Cancels the invoice in the FEL system."""
        fel_certifier = self.company_id.fel_gt_certifier
        if self.fel_gt_uuid:
            self.fel_gt_uuid_original = self.fel_gt_uuid
            xml_data = self._xml_cancel_standard_fel_maker(fel_certifier)
            uuid, serie, dte_number, dte_date, sat_ref_id = self.send_data_api(xml_data, 'cancel')
            message = _(f"{self._fel_gt_invoice_name()+' CANCELADA'}: Serie %s  Número %s") % (self.fel_gt_serie, self.fel_gt_dte_number)
            self._finalize_fel_gt_invoice(uuid, serie, dte_number, dte_date, sat_ref_id, message, cancel=True)

    def fel_gt_cancel(self, origin='accounting'):
        """Cancels the invoice in the FEL system."""
        for move in self:
            move_line_ids = move.sudo().mapped('line_ids')
            if move.is_invoice() and self.fel_gt_state == 'certified':
                move.cancel_fel_gt_move()

                pos_order = False
                
                if move.invoice_origin and origin == 'accounting':
                    is_pos_fel_installed = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'pos_multicert_felgt')], limit=1)
                    if is_pos_fel_installed:
                        pos_order = self.env['pos.order'].sudo().search(
                            [('name','=',move.invoice_origin)], limit=1
                        )
                        if pos_order:
                            pos_order.fel_gt_cancel(cancel_invoice=False)

                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.sudo().mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                
                payments = False
                if reconcile_lines:
                    payments = self.env['account.payment'].search(['|', ('invoice_line_ids.id', 'in', reconcile_lines.mapped(
                        'credit_move_id').ids), ('invoice_line_ids.id', 'in', reconcile_lines.mapped('debit_move_id').ids)])
                    reconcile_lines.sudo().unlink()

                if payments:
                    payment_ids = payments
                    if payment_ids.sudo().mapped('move_id').mapped('line_ids'):
                        payment_lines = payment_ids.sudo().mapped('move_id').mapped('line_ids')
                        reconcile_ids = payment_lines.sudo().mapped('id')

                        reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        
                        if reconcile_lines:
                            reconcile_lines.sudo().unlink()
                        move.mapped('line_ids.analytic_line_ids').sudo().unlink()

                if payments:
                    payment_ids = payments
                    payment_ids.sudo().mapped('move_id').write(
                        {'state': 'draft', 'name': '/'})

                    payment_ids.sudo().mapped('move_id').mapped(
                        'line_ids').sudo().write({'parent_state': 'draft'})
                    payment_ids.sudo().mapped('move_id').mapped('line_ids').sudo().unlink()
                    payment_ids.sudo().write({'state': 'cancel'})

                move_line_ids.sudo().write({'parent_state': 'draft'})
                move.sudo().write({'state': 'draft'})
                self.sudo().write({'state': 'cancel'})
                

    # FACTURA NORMAL GUATEFACTURA
    def set_data_for_invoice_guatefacturas(self, type_document=1):
        """Sets the data for the invoice using the Guatefacturas API."""
        company_vat = self.company_id.vat
        company_vat = re.sub(r'\ |\?|\.|\!|\/|\;|\:|\-', '', company_vat)
        company_vat = company_vat.upper()

        general_rounding = 2
        if self.company_id.fel_gt_price_tax_rounding > 0:
            general_rounding = self.company_id.fel_gt_price_tax_rounding
        
        line_code_divider = self.company_id.fel_gt_default_code_divider
        
        if self.partner_id.vat:
            vat = self.partner_id.vat
            vat = re.sub(r'\ |\?|\.|\!|\/|\;|\:|\-', '', vat)
            vat = vat.upper()
        else:
            vat = "CF"

        if type_document == 5:
            if not self.partner_id.fel_gt_dpi_number:
                raise ValidationError('Debe ingresar el número D.P.I. del proveedor')
            
            if not self.company_id.state_id:
                raise ValidationError('Debe indicar el departamento del emisión del documento')

            if not self.company_id.city:
                raise ValidationError('Debe indicar el municipio del emisión del documento')
        
        make_conversion = False
        conversion_rate = 1
        if self.company_id.fel_gt_invoice_currency and not self.company_id.fel_gt_currency_from_invoice:
            if self.currency_id != self.company_id.fel_gt_invoice_currency:
                if not self.invoice_date:
                    raise ValidationError('Debe seleccionar la fecha de la factura para asignar la tasa de conversión correcta')
                make_conversion = True
                account_move_fields = super(AccountMove, self).fields_get()
                if 'conversion_rate_ref' in account_move_fields:
                    conversion_rate = self.conversion_rate_ref
                else:
                    conversion_rate = self.currency_id.with_context(date=self.invoice_date).rate

        fecha_emision = datetime.now(gettz("America/Guatemala")).__format__('%d/%m/%Y')
        last_5_days = date.today() - timedelta(5)
        if not self.invoice_date:
            fecha_emision = datetime.now(gettz("America/Guatemala")).__format__('%d/%m/%Y')
        else:
            fecha_emision = self.invoice_date.__format__('%d/%m/%Y')
        currency_code = "GTQ"

        self.fel_gt_dte_issue_date = fecha_emision
        
        invoice_lines = self.invoice_line_ids
        
        BienOServicio = "B"
        for line in invoice_lines:
            if line.product_id.type == 'product':
                BienOServicio = "B"
                continue
            if line.product_id.type == 'service':
                BienOServicio = "S"
        
        DocElectronico = Element('DocElectronico')
        Encabezado = SubElement(DocElectronico, 'Encabezado')
        Receptor = SubElement(Encabezado, 'Receptor')
        
        if type_document == 5:
                NITReceptor = SubElement(Receptor, 'NITVendedor')
                NITReceptor.text = str(vat)
                
                Nombre = SubElement(Receptor, 'Nombre')
                Nombre.text = self.partner_id.name
                
                Direccion = SubElement(Receptor, 'Direccion')
                Direccion.text = self.partner_id.street or "Ciudad"
        else:
            NITReceptor = SubElement(Receptor, 'NITReceptor')
            NITReceptor.text = str(vat)
            
            Nombre = SubElement(Receptor, 'Nombre')
            Nombre.text = self.partner_id.name
            
            Direccion = SubElement(Receptor, 'Direccion')
            Direccion.text = self.partner_id.street or "Ciudad"

        InfoDoc = SubElement(Encabezado, 'InfoDoc')
        
        TipoVenta = SubElement(InfoDoc, 'TipoVenta')
        TipoVenta.text = BienOServicio
        
        DestinoVenta = SubElement(InfoDoc, 'DestinoVenta')
        DestinoVenta.text = "1"
        
        Fecha = SubElement(InfoDoc, 'Fecha')
        Fecha.text = fecha_emision
        
        currency_fel_id = 1
        if currency_code == 'USD':
            currency_fel_id = 2
            
        Moneda = SubElement(InfoDoc, 'Moneda')
        Moneda.text = str(currency_fel_id)
        
        if type_document == 5:
            Tasa_Cambio = SubElement(InfoDoc, 'Tasa_Cambio')
            Tasa_Cambio.text = str(conversion_rate)
        else:
            Tasa = SubElement(InfoDoc, 'Tasa')
            Tasa.text = str(conversion_rate)
        
        if type_document == 5:
            TipoDocIdentificacion = SubElement(InfoDoc, 'TipoDocIdentificacion')
            TipoDocIdentificacion.text = str(2)
            
            NumeroIdentificacion = SubElement(InfoDoc, 'NumeroIdentificacion')
            NumeroIdentificacion.text = str(self.partner_id.fel_gt_dpi_number)
            
            PaisEmision = SubElement(InfoDoc, 'PaisEmision')
            PaisEmision.text = str(1)
            
            DepartamentoEmision = SubElement(InfoDoc, 'DepartamentoEmision')
            department_id = departments_mapping(self.company_id.state_id.name.upper())
            DepartamentoEmision.text = department_id
            
            MunicipioEmision = SubElement(InfoDoc, 'MunicipioEmision')
            township_id = townships_mapping(self.company_id.city, department_id)
            MunicipioEmision.text = township_id
        
        Referencia = SubElement(InfoDoc, 'Referencia')
        odoo_reference = str(self.journal_id.code)+str(self.id)
        Referencia.text = odoo_reference
        
        if type_document == 5:
            PorcISR = SubElement(InfoDoc, 'PorcISR')
            PorcISR.text = str(0.05)
        
        NumeroAcceso = SubElement(InfoDoc, 'NumeroAcceso')
        #NumeroAcceso.text = "1"
        if int(float(self.fel_gt_contingency_access_number)) > 0:
            NumeroAcceso.text = str(int(float(self.fel_gt_contingency_access_number)))
        else:
            NumeroAcceso.text = ""
        
        """
        NOTA: PENDIENTE DE VALIDAR RECUPERACION DE DATOS
        """
        
        SerieAdmin = SubElement(InfoDoc, 'SerieAdmin')
        #SerieAdmin.text = "DTE-"+ str(self.id)
        SerieAdmin.text = ""
        
        NumeroAdmin = SubElement(InfoDoc, 'NumeroAdmin')
        #NumeroAdmin.text = str(self.id)
        NumeroAdmin.text = ""
        
        Reversion = SubElement(InfoDoc, 'Reversion')
        Reversion.text = "N"
        
        Totales = SubElement(Encabezado, 'Totales')
        
        #Get totals and details from invoice line
        invoice_line = self.invoice_line_ids
        invoice_counter = 0
        price_tax_total = 0
        grand_total = 0
        timbre_tax_fel = False
        has_one_timbre_tax_fel = False
        # Variables para manejo de timbre de prensa
        total_iva = 0
        total_timbre = 0
        
        product_details = []
        # Precio Bruto
        gross_price = 0
        total_discounts = 0
        other_taxes_total = 0
        
        # Facturas Especiales
        isr_especial_total = 0
        iva_especial_total = 0

        other_discount = 0
        extra_discount = 0
        cant_lines = len(invoice_line.filtered(lambda r: r.display_type == 'product'))
        # LineasFacturaDescuento
        for line in invoice_line.filtered(lambda r: r.price_unit < 0):
            other_discount += abs(line.quantity * line.price_unit)
            cant_lines -= 1

        if other_discount > 0 and cant_lines > 0:
            other_discount = other_discount / cant_lines

        net = 0
        iva = 0
        # LineasFactura
        for line in invoice_line.filtered(lambda r: r.price_unit > 0).sorted(key=lambda x: x.price_total):
            if line.display_type == 'product':
                invoice_counter += 1
                
                BienOServicio = "B"
                if line.product_id.type == 'service':
                    BienOServicio = "S"

                timbre_tax_fel = False
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.fel_gt_timbre_tax:
                            timbre_tax_fel = True
                            has_one_timbre_tax_fel = True

                if line.tax_ids:
                    tax = "IVA"

                
                else:
                    if type_document != 6:
                        raise UserError(_("Las líneas de Factura deben de llevar impuesto (IVA)."))
                
                # ------------------------------
                # --- CHECK INOVICE CURRENCY ---
                # ------------------------------

                line_price_unit = line.price_unit
                line_price = line.quantity * line.price_unit
                line_price_total = line.price_total
                line_price_subtotal = line.price_subtotal
                price_tax = line_price_total - line_price_subtotal

                # Variables para manejo de timbre de prensa --- CIG
                iva_amount = 0
                timbre_amount = 0
                iva_timbre_total = 0

                if timbre_tax_fel:
                    line_price_unit = line.price_unit / 1.125
                    timbre_unit = round(line_price_unit, general_rounding) * 0.005
                    line_price_unit = line.price_unit - round(timbre_unit, general_rounding)
                    line_price = line.quantity * round(line_price_unit, general_rounding)

                    monto_gravable = round(line_price, general_rounding) / 1.12
                    base_line = round(line_price, general_rounding) / 1.12
                    iva_amount = round(base_line, general_rounding) * 0.12
                    timbre_amount = round(base_line, general_rounding) * 0.005

                    total_iva += iva_amount
                    total_timbre += timbre_amount
                    iva_timbre_total = line_price + timbre_amount

                tax_amount = 0
                if make_conversion:
                    set_conversion_data = {
                        "line": line,
                        "conversion_rate": conversion_rate
                    }
                    get_conversion_data = conversion_rate_manager(self, "line", set_conversion_data)

                    line_price_unit = get_conversion_data['line_price_unit']
                    line_price = get_conversion_data['line_price']
                    line_price_total = get_conversion_data['line_price_total']
                    line_price_subtotal = get_conversion_data['line_price_subtotal']
                    price_tax = get_conversion_data['price_tax']
                    grand_total += line_price_total

                line_price = round(line_price, general_rounding)            
                line_gross_price = round(line_price_unit * line.quantity, general_rounding)
                gross_price += line_gross_price
                product_description = line.product_id.name
                line_code_divider = self.company_id.fel_gt_default_code_divider
                
                if line_code_divider:
                    if line.product_id.default_code:
                        product_description = line.product_id.default_code + line_code_divider + line.product_id.name
                    else:
                        product_description = line.product_id.name
                else:
                    product_description = line.product_id.name
                
                iva_line_amount = 0
                other_taxes = 0
                if timbre_tax_fel:
                    iva_line_amount = iva_amount
                    other_taxes = timbre_amount
                    price_tax_total = price_tax_total + iva_amount
                    price_tax_total = price_tax_total + timbre_amount
                else:
                    iva_line_amount = round(price_tax, general_rounding)
                    price_tax_total = price_tax_total + price_tax
                    if has_one_timbre_tax_fel:
                        total_iva += price_tax
                line_discount = round(((line.discount * (line.quantity * line_price_unit))/100)+other_discount+extra_discount, general_rounding)
                if line_discount > line_gross_price:
                    extra_discount += (line_discount - line_gross_price)/(cant_lines-invoice_counter)
                    line_discount = line_gross_price
                total_discounts += line_discount
                other_taxes_total += other_taxes
                impBruto = line_price_unit * line.quantity
                product_id = line.product_id.id
                isr_amount = 0
                if type_document == 6:
                    line_net = round((line_gross_price-line_discount), general_rounding)
                    line_iva = 0
                else:
                    line_net = round((line_gross_price-line_discount)/1.12, general_rounding)
                    line_iva = round(line_gross_price-line_net-line_discount, general_rounding)
                net += line_net
                iva += line_iva
                
                if type_document == 5:
                    product_id = 1
                    isr_amount = line.price_unit * line.quantity /1.12 *0.05
                    isr_amount = round(isr_amount, general_rounding)
                    iva_line_amount = line.price_unit * line.quantity / 1.12
                    iva_line_amount = iva_line_amount * 0.12
                    iva_line_amount = round(iva_line_amount, general_rounding)
                    isr_especial_total += isr_amount
                    iva_especial_total += iva_line_amount
                    line_price_total = line_gross_price
                product_detail = {
                    "Producto": str(product_id),
                    "Descripcion": str(product_description),
                    "Medida": "1",
                    "Cantidad": str(line.quantity),
                    "Precio": str(line_price_unit),
                    "PorcDesc": str(dropzeros(round((line_discount*100)/line_gross_price, 4))),
                    "ImpBruto": str(line_gross_price),
                    "ImpDescuento": str(dropzeros(line_discount)),
                    "ImpExento": str(dropzeros(line_net)) if type_document == 6 else "0",
                    "ImpOtros": str(dropzeros(other_taxes)),
                    "ImpNeto": str(dropzeros(line_net)) if type_document != 6 else "0",
                    "ImpIsr": str(isr_amount),
                    "ImpIva": str(dropzeros(line_iva)),
                    "ImpTotal": str(dropzeros(round(line_net+line_iva, general_rounding))),
                    "TipoVentaDet": BienOServicio                
                }
                product_details.append(product_detail)
        
        Bruto = SubElement(Totales, 'Bruto')
        Bruto.text = str(gross_price)
        
        Descuento = SubElement(Totales, 'Descuento')
        Descuento.text = str(dropzeros(total_discounts))
        
        Exento = SubElement(Totales, 'Exento')
        Exento.text = str(dropzeros(round(net, general_rounding))) if type_document == 6 else "0"
        
        Otros = SubElement(Totales, 'Otros')
        Otros.text = str(dropzeros(other_taxes_total))
        
        Neto = SubElement(Totales, 'Neto')
        Neto.text = str(dropzeros(round(net, general_rounding))) if type_document != 6 else "0"
        
        invoice_total = self.amount_untaxed
        
        if type_document == 5:
            Isr = SubElement(Totales, 'Isr')
            invoice_total += isr_especial_total
            Isr.text = str(isr_especial_total)
        else:
            
            Isr = SubElement(Totales, 'Isr')
            if 'isr_withold_amount' in self.env['account.move']._fields:
                invoice_total += self.isr_withold_amount
                Isr.text = str(dropzeros(self.isr_withold_amount))
            else:
                Isr.text = str(dropzeros(0))
        
        if type_document == 5:
            Iva = SubElement(Totales, 'Iva')
            invoice_total += iva_especial_total
            Iva.text = str(round(iva_especial_total, general_rounding))
        else:
            if has_one_timbre_tax_fel:        
                Iva = SubElement(Totales, 'Iva')
                invoice_total += total_iva
                Iva.text = str(round(dropzeros(total_iva), general_rounding))
            else:
                Iva = SubElement(Totales, 'Iva')
                invoice_total += price_tax_total
                Iva.text = str(round(dropzeros(iva), general_rounding))

        if type_document == 5:
            Total = SubElement(Totales, 'Total')
            Total.text = str(gross_price)
        else:
            if (invoice_total == 0):
                invoice_total = self.amount_total
            Total = SubElement(Totales, 'Total')
            Total.text = str(round(dropzeros(invoice_total), general_rounding))
        
        if type_document != 5:
            DatosAdicionales = SubElement(Encabezado, 'DatosAdicionales')
            if type_document == 2:
                AbonosFacturaCambiaria = SubElement(Encabezado, 'AbonosFacturaCambiaria')
                
                Abono = SubElement(AbonosFacturaCambiaria, 'Abono')
                
                NumeroAbono = SubElement(Abono, 'NumeroAbono')
                NumeroAbono.text = str("1")
                
                date_due = self.invoice_date_due
                formato2 = "%Y%m%d"
                date_due = date_due.strftime(formato2)
                
                FechaVencimiento = SubElement(Abono, 'FechaVencimiento')
                FechaVencimiento.text = str(date_due)
                
                MontoAbono = SubElement(Abono, 'MontoAbono')
                MontoAbono.text = str(round(self.amount_total, general_rounding))
                
        
        Detalles = SubElement(DocElectronico, 'Detalles')
        
        
        for product in product_details:
            Productos = SubElement(Detalles, 'Productos')
            Producto = SubElement(Productos, 'Producto')
            Producto.text = product['Producto']
            
            Descripcion = SubElement(Productos, 'Descripcion')
            Descripcion.text = product['Descripcion']
            
            Medida = SubElement(Productos, 'Medida')
            Medida.text = product['Medida']
            
            Cantidad = SubElement(Productos, 'Cantidad')
            Cantidad.text = product['Cantidad']
            
            Precio = SubElement(Productos, 'Precio')
            Precio.text = product['Precio']
            
            PorcDesc = SubElement(Productos, 'PorcDesc')
            PorcDesc.text = product['PorcDesc']
            
            ImpBruto = SubElement(Productos, 'ImpBruto')
            ImpBruto.text = product['ImpBruto']
            
            ImpDescuento = SubElement(Productos, 'ImpDescuento')
            ImpDescuento.text = product['ImpDescuento']
            
            ImpExento = SubElement(Productos, 'ImpExento')
            ImpExento.text = product['ImpExento']
                        
            ImpOtros = SubElement(Productos, 'ImpOtros')
            ImpOtros.text = product['ImpOtros']
            
            ImpNeto = SubElement(Productos, 'ImpNeto')
            ImpNeto.text = product['ImpNeto']
            
            ImpIsr = SubElement(Productos, 'ImpIsr')
            ImpIsr.text = product['ImpIsr']
            
            ImpIva = SubElement(Productos, 'ImpIva')
            ImpIva.text = product['ImpIva']
            
            ImpTotal = SubElement(Productos, 'ImpTotal')
            ImpTotal.text = product['ImpTotal']
            
            if type_document != 5:
            
                TipoVentaDet = SubElement(Productos, 'TipoVentaDet')
                TipoVentaDet.text = product['TipoVentaDet']
                
                DatosAdicionalesProd = SubElement(Productos, 'DatosAdicionalesProd')
                #DatosAdicionalesProd.text = product['DatosAdicionalesProd']

        if type_document != 5:
            DocAsociados = SubElement(Detalles, 'DocAsociados')
            
            DASerie = SubElement(DocAsociados, 'DASerie')
            if type_document == 10 or type_document == 6:
                DASerie.text = self.fel_gt_serie_original
            elif type_document == 9:
                DASerie.text = self.fel_gt_source_debit_note_id.serie_original
            else:
                DASerie.text = ""
            
            DAPreimpreso = SubElement(DocAsociados, 'DAPreimpreso')
            if type_document == 10 or type_document == 6:
                DAPreimpreso.text = self.fel_gt_dte_number_original
            elif type_document == 9:
                DAPreimpreso.text = self.fel_gt_source_debit_note_id.fel_gt_dte_number_original
            else:
                DAPreimpreso.text = ""
        
        xml_content = tostring(DocElectronico)
        date_due = self.invoice_date_due
        date_due_format = "%d-%m-%Y"
        date_due = date_due.strftime(date_due_format)
        
        _logger.info('FEL CONTENT ' + str(xml_content))

        store_sent_xml(self, xml_content, vat, date_due, 'guatefacturas')
        
        return xml_content


    def _check_fel_gt_neccesary_fields(self):
        """Check if the necessary fields are filled."""
        # Validation for required company fields
        required_company_fields = [
            ('company_registry', RAISE_VALIDATION_COMPANY_REGISTRY),
            ('email', RAISE_VALIDATION_COMPANY_EMAIL),
            ('vat', RAISE_VALIDATION_COMPANY_VAT),
            ('street', RAISE_VALIDATION_COMPANY_STREET)
        ]
        for field, error in required_company_fields:
            if not getattr(self.company_id, field):
                raise UserError(error)

        # Validation for invoice fields
        if not self.invoice_date_due:
            raise UserError(RAISE_VALIDATION_INVOICE_DATE_DUE)
        if not self.partner_id.name.strip():
            raise UserError(RAISE_VALIDATION_INVOICE_PARTNER_NAME)
        

    def _get_fel_gt_conversion_rate(self):
        """Calculate and return the appropriate conversion rate."""
        make_conversion = False
        conversion_rate = 1
        currency_code = "GTQ"

        if self.company_id.fel_gt_invoice_currency and not self.company_id.fel_gt_currency_from_invoice and not self.partner_id.fel_gt_currency_from_invoice:
            if self.currency_id != self.company_id.fel_gt_invoice_currency:
                if not self.invoice_date:
                    raise ValidationError('Debe seleccionar la fecha de la factura para asignar la tasa de conversión correcta')
                make_conversion = True

        if self.currency_id != self.company_id.fel_gt_invoice_currency:
            if 'conversion_rate_ref' in self.env['account.move']._fields:
                conversion_rate = self.conversion_rate_ref
            else:
                conversion_rate = self.currency_id.with_context(date=self.invoice_date).rate

        if self.company_id.fel_gt_currency_from_invoice or self.partner_id.fel_gt_currency_from_invoice:
            currency_code = self.currency_id.name
        else:
            if self.partner_id.fel_gt_currency_from_invoice:
                self.partner_id.fel_gt_invoice_currency.name
            else:
                currency_code = self.company_id.fel_gt_invoice_currency.name

        general_rounding = 2
        if self.company_id.fel_gt_price_tax_rounding > 0:
            general_rounding = self.company_id.fel_gt_price_tax_rounding

        return conversion_rate, make_conversion, currency_code, general_rounding
    

    def _get_fel_gt_issue_date(self):
        """Get the emission date in the correct format."""

        current_time = datetime.now(gettz("America/Guatemala"))
        if not self.invoice_date:
            return current_time.__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        if current_time.date() != self.invoice_date:
            return self.invoice_date.__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        
        return current_time.__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        

    def _get_fel_gt_establishment_info(self):
        """Retrieve the establishment info."""

        establishment_code = self.company_id.fel_gt_establishment_code
        if self.journal_id.fel_gt_establishment_code:
            establishment_code = self.journal_id.fel_gt_establishment_code
        
        commercial_name = self.company_id.name
        if self.journal_id.fel_gt_commercial_name:
            commercial_name = self.journal_id.fel_gt_commercial_name
        
        fel_address = self.get_fel_gt_company_address()
        if self.journal_id.fel_gt_address:
            fel_address = self.journal_id.fel_gt_address
        
        fel_zip_code = self.company_id.zip
        if self.journal_id.fel_gt_zip_code:
            fel_zip_code = self.journal_id.fel_gt_zip_code
        
        fel_township = self.company_id.city
        if self.journal_id.fel_gt_township:
            fel_township = self.journal_id.fel_gt_township
        
        fel_department = self.company_id.state_id.name
        if self.journal_id.fel_gt_department:
            fel_department = self.journal_id.fel_gt_department

        fel_company_name = self.company_id.name
        if self.company_id.company_registry:
            fel_company_name = self.company_id.company_registry
        
        fel_company_email = ''
        if self.company_id.email:
            fel_company_email = self.company_id.email

        return establishment_code, commercial_name, fel_address, fel_zip_code, fel_township, fel_department, fel_company_name, fel_company_email
    

    def _get_fel_gt_invoice_type(self):
        """Retrieve the invoice type."""
        fel_affiliation = "GEN"
        if self.company_id.fel_gt_small_taxpayer_withholding:
            fel_affiliation = "PEQ"
        if self.fel_gt_invoice_type in ['RECI','FEXP','NABN'] and not self.amount_tax_signed:
            fel_affiliation = "EXE"
        return fel_affiliation
        

    def _get_fel_gt_receptor_vat_info(self):
        """Retrieve and process the VAT information for the receptor."""
        for rec in self:
            vat = 'CF'
            has_dpi = has_passport = False
            name = rec.partner_id.name
            
            if rec.partner_id.fel_gt_vat:
                vat = rec.partner_id.fel_gt_vat
                name = rec.partner_id.name
            elif rec.partner_id.parent_id:
                vat = rec.partner_id.parent_id.vat
                name = rec.partner_id.parent_id.name
            elif rec.partner_id.vat:
                vat = rec.partner_id.vat

            vat = re.sub(r'[\s\?\.\/\;\:\-]', '', vat.upper())

            if not vat and (rec.partner_id.fel_gt_passport_number or rec.partner_id.fel_gt_dpi_number):
                if rec.partner_id.fel_gt_passport_number:
                    vat = rec.partner_id.fel_gt_passport_number
                    has_passport = True
                else:
                    vat = rec.partner_id.fel_gt_dpi_number
                    has_dpi = True
            elif vat == "CF":
                if rec.partner_id.fel_gt_passport_number:
                    vat = rec.partner_id.fel_gt_passport_number
                    has_passport = True
                elif rec.partner_id.fel_gt_dpi_number:
                    vat = rec.partner_id.fel_gt_dpi_number
                    has_dpi = True

            return vat, name, has_dpi, has_passport
        

    def _set_fel_gt_address_fields(self, xml_element, address, zip_code, township, department):
        """Set the XML address fields."""
        ET.SubElement(xml_element, f"{{{xmlns}}}Direccion").text = address or "Ciudad"
        ET.SubElement(xml_element, f"{{{xmlns}}}CodigoPostal").text = zip_code or "01009"
        ET.SubElement(xml_element, f"{{{xmlns}}}Municipio").text = township or "Guatemala"
        ET.SubElement(xml_element, f"{{{xmlns}}}Departamento").text = department or "Guatemala"
        ET.SubElement(xml_element, f"{{{xmlns}}}Pais").text = self.company_id.country_id.code or "GT"


    def _set_fel_gt_phrases(self, xml_data_emision, xmlns):
        """Handle the phrases"""
        if self.fel_gt_invoice_type != 'NABN':
            if self.fel_gt_phrases:
                xml_frases = ET.SubElement(xml_data_emision, f"{{{xmlns}}}Frases")

            if self.fel_gt_phrases:
                self._add_fel_gt_phrases_to_xml(xml_frases, self.fel_gt_phrases)


    def _add_fel_gt_phrases_to_xml(self, xml_frases, phrases):
        """Add phrases to the XML."""
        for phrase in phrases:
            if self.company_id.fel_gt_resolution_number and self.company_id.fel_gt_resolution_date:
                ET.SubElement(xml_frases, f"{{{xmlns}}}Frase", CodigoEscenario=str(phrase.scenario_code), 
                            TipoFrase=str(phrase.phrase_type), NumeroResolucion=self.company_id.fel_gt_resolution_number, 
                            FechaResolucion=self.company_id.fel_gt_resolution_date)
            else:
                ET.SubElement(xml_frases, f"{{{xmlns}}}Frase", CodigoEscenario=str(phrase.scenario_code), 
                            TipoFrase=str(phrase.phrase_type))
                
    def _apply_fel_gt_discount_lines(self):
        """Apply the extra discount lines to the invoice lines, saving original values for restoration."""
        
        self.fel_gt_original_values = json.dumps({
            line.id: {
                'price_unit': line.price_unit,
                'discount': line.discount,
                'name': line.name
            }
            for line in self.invoice_line_ids
        })

        total_discount_price = 0
        total_positive_price = 0
        updated_line_values = []

        for line in self.invoice_line_ids:
            if line.price_total > 0:
                total_positive_price += line.price_unit * line.quantity
            elif line.price_total < 0:
                total_discount_price += abs(line.price_total)
                updated_line_values.append([1, line.id, {'price_unit': 0}])

        if total_discount_price > 0:
            remaining_discount = total_discount_price
            precision_rounding = self.currency_id.rounding
            precision_digits = self.env['decimal.precision'].precision_get('Product Price')
            discount_in_price = self.journal_id.fel_gt_discount_in_price

            for line in self.invoice_line_ids:
                if line.price_total > 0:
                    discount = (total_discount_price / total_positive_price) * 100 + line.discount
                    if discount_in_price:
                        new_price = (line.price_unit * (100 - discount) / 100)
                        new_total_price = tools.float_round(new_price * line.quantity, precision_rounding=precision_rounding, rounding_method='DOWN')
                        discounted_amount = line.price_total - new_total_price
                        discounted_amount = min(discounted_amount, remaining_discount)
                        remaining_discount -= discounted_amount
                        discounted_price = tools.float_round((line.price_total - discounted_amount) / line.quantity, precision_digits=precision_digits)
                        updated_line_values.append([1, line.id, {'price_unit': discounted_price, 'discount': 0}])
                    else:
                        updated_line_values.append([1, line.id, {'discount': discount}])

            self.with_context(skip_invoice_sync=False, skip_readonly_check=True).write({'invoice_line_ids': updated_line_values})

        return True
    
    def _restore_fel_gt_original_values(self):
        """Restore the original values of the invoice lines."""
        if self.fel_gt_original_values:
            try:
                original_values = json.loads(self.fel_gt_original_values)
            except json.JSONDecodeError:
                original_values = {}

            updated_line_values = [
                [1, int(line_id), {
                    'price_unit': original['price_unit'],
                    'discount': original['discount'],
                    'name': original['name']
                }]
                for line_id, original in original_values.items()
            ]
            
            self.with_context(skip_invoice_sync=False, skip_readonly_check=True).write({'invoice_line_ids': updated_line_values})
            
            self.fel_gt_original_values = False

        return True

    def _set_fel_gt_items(self, xml_data_emision, xmlns, general_rounding, make_conversion, conversion_rate):
        """Set the items in the XML."""
        xml_items = ET.SubElement(xml_data_emision, "{" + xmlns + "}Items")

        line_code_divider = self.company_id.fel_gt_default_code_divider
        invoice_counter = 0
        grand_total = 0
        price_tax_total = 0
        total_iva = 0

        fel_taxes = {
            "IVA": 0,
            "PETROLEO": 0,
            "TURISMO HOSPEDAJE": 0,
            "TURISMO PASAJES": 0,
            "TIMBRE DE PRENSA": 0,
            "BOMBEROS": 0,
            "TASA MUNICIPAL": 0,
        }

        self._apply_fel_gt_discount_lines()
        
        for line in self.invoice_line_ids.filtered(lambda x: x.display_type == 'product' and x.price_unit > 0 and x.quantity > 0):

            invoice_counter += 1

            BienOServicio = "B"
            if line.product_id.type == 'service':
                BienOServicio = "S"

            xml_item = ET.SubElement(xml_items, "{" + xmlns + "}Item", BienOServicio=BienOServicio, NumeroLinea=str(invoice_counter))

            if not self.company_id.fel_gt_small_taxpayer_withholding and not line.tax_ids and self.fel_gt_invoice_type not in ['NABN','FEXP','RECI']:
                if self.fiscal_position_id:
                    if not self.fiscal_position_id.fel_gt_tax_withold:
                        raise UserError(_("Las líneas de Factura deben de llevar impuesto (IVA)."))
                else:
                    raise UserError(_("Las líneas de Factura deben de llevar impuesto (IVA)."))

            line_price_unit = line.price_unit
            line_price = line.quantity * line.price_unit
            
            line_price_total = line.price_total
            line_price_subtotal = line.price_subtotal
            if self.fel_gt_invoice_type == 'FESP':
                price_tax = line.price_subtotal * 0.12
                total_iva += price_tax
                line_price_total = line.price_subtotal + price_tax
            else:
                price_tax = line_price_total - line_price_subtotal
                total_iva += price_tax

            if make_conversion:
                set_conversion_data = {
                    "line": line,
                    "conversion_rate": conversion_rate
                }
                get_conversion_data = conversion_rate_manager(self, "line", set_conversion_data, general_rounding)
                
                line_price_unit = get_conversion_data['line_price_unit']
                line_price = get_conversion_data['line_price']
                line_price_total = get_conversion_data['line_price_total']
                line_price_subtotal = get_conversion_data['line_price_subtotal']
                price_tax = get_conversion_data['price_tax']
                
            line_price = round(line_price, general_rounding)

            ET.SubElement(xml_item, "{" + xmlns + "}Cantidad").text = str(round(line.quantity,4))
            ET.SubElement(xml_item, "{" + xmlns + "}UnidadMedida").text = line.product_uom_id.name.upper()[0:3] if line.product_uom_id else 'UND'
            
            line_description = line.product_id.name
            if self.company_id.fel_gt_invoice_line_name == 'description':
                line_description = line.name

            if not line_description:
                line_description = "Linea No. " + str(invoice_counter)
            
            discount = round((line.discount * (line.quantity * line_price_unit))/100, general_rounding)

            if line.product_id.default_code and line_code_divider:
                ET.SubElement(xml_item, "{" + xmlns + "}Descripcion").text = line.product_id.default_code + line_code_divider + line_description
            else:
                ET.SubElement(xml_item, "{" + xmlns + "}Descripcion").text = line_description
                
            price_unit_element = ET.SubElement(xml_item, "{" + xmlns + "}PrecioUnitario")
            price_unit_element.text = str(round(line_price_unit, general_rounding))
            price_element = ET.SubElement(xml_item, "{" + xmlns + "}Precio")
            price_element.text = str(round(line_price, general_rounding))
            ET.SubElement(xml_item, "{" + xmlns + "}Descuento").text = str(discount)

            if (line.tax_ids and line_price != line_price_subtotal) or (line.tax_ids and line_price < 0.1):
                xml_impuestos = ET.SubElement(xml_item, "{" + xmlns + "}Impuestos")
                hotel_tax = False
                hotel_total = 0.0
                if self.fel_gt_invoice_type != 'FESP':
                    for tax in line.tax_ids:
                        tax_name = tax.fel_gt_tax
                
                        xml_impuesto = ET.SubElement(xml_impuestos, "{" + xmlns + "}Impuesto")
                        
                        if tax_name == 'IVA':
                            base = line.price_unit * line.quantity if line.discount == 0 else line.price_subtotal
                            price_tax = tax._compute_amount(base, line.price_unit, line.quantity, line.product_id, self.partner_id) if line.discount == 0 else base * tax.amount / 100
                        else:
                            price_tax = tax._compute_amount(line.price_subtotal, line.price_unit, line.quantity, line.product_id, self.partner_id)
                    
                        ET.SubElement(xml_impuesto, "{" + xmlns + "}NombreCorto").text = tax_name
                        if tax_name == 'PETROLEO':
                            if tax.fel_gt_idp_tax_type == 'regular':
                                ET.SubElement(xml_impuesto, "dte:CodigoUnidadGravable").text = "2"
                            elif tax.fel_gt_idp_tax_type == 'disel':
                                ET.SubElement(xml_impuesto, "dte:CodigoUnidadGravable").text = "4"
                            else:
                                ET.SubElement(xml_impuesto, "dte:CodigoUnidadGravable").text = "1"
                            ET.SubElement(xml_impuesto, "dte:CantidadUnidadesGravables").text = str(line.quantity)
                        else:
                            ET.SubElement(xml_impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "1" if self.fel_gt_invoice_type != 'FEXP' else "2"
                            ET.SubElement(xml_impuesto, "dte:MontoGravable").text = str(round(line_price_subtotal, general_rounding))
                        price_tax = round(price_tax, general_rounding)
                        split_num = str(price_tax).split('.')
                        if int(split_num[1]) > 0:
                            decimal = str(split_num[1])
                            if len(decimal) > 2:
                                if int(decimal[2]) == 5:
                                    price_tax += 0.001

                        ET.SubElement(xml_impuesto, "{" + xmlns + "}MontoImpuesto").text = str(round(price_tax, general_rounding))
                        fel_taxes[tax_name] += price_tax

                        hotel_total += price_tax
                        if tax_name == "TURISMO HOSPEDAJE":
                            hotel_tax = True
                    
                    if hotel_tax:
                        new_unit_price = round(line_price_subtotal * 1.12, general_rounding)
                        price_unit_element.text = str(round(new_unit_price / line.quantity, general_rounding))
                        price_element.text = str(new_unit_price)
                        line_price_total = round(hotel_total + line_price_subtotal, general_rounding)

                    ET.SubElement(xml_item, "{" + xmlns + "}Total").text = str(round(line_price_total, general_rounding))
                    grand_total += round(line_price_total, general_rounding)
                    price_tax_total += price_tax
            
                else:
                    xml_impuesto = ET.SubElement(xml_impuestos, "{" + xmlns + "}Impuesto")
                    ET.SubElement(xml_impuesto, "{" + xmlns + "}NombreCorto").text = "IVA"
                    ET.SubElement(xml_impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
                    ET.SubElement(xml_impuesto, "{" + xmlns + "}MontoGravable").text = str(round(line_price_subtotal, general_rounding))
                    ET.SubElement(xml_impuesto, "{" + xmlns + "}MontoImpuesto").text = str(round(price_tax, general_rounding))
                    ET.SubElement(xml_item, "{" + xmlns + "}Total").text = str(round(line_price_total, general_rounding))
                    grand_total += round(line_price_total, general_rounding)
                    price_tax_total = price_tax_total + price_tax
                    fel_taxes["IVA"] += price_tax

            elif not self.company_id.fel_gt_small_taxpayer_withholding and self.fel_gt_invoice_type != 'NABN':
                xml_impuestos = ET.SubElement(xml_item, "{" + xmlns + "}Impuestos")
                xml_impuesto = ET.SubElement(xml_impuestos, "{" + xmlns + "}Impuesto")
                
                ET.SubElement(xml_impuesto, "{" + xmlns + "}NombreCorto").text = "IVA"
                ET.SubElement(xml_impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "2"
                ET.SubElement(xml_impuesto, "{" + xmlns + "}MontoGravable").text = str(round(line.price_subtotal, general_rounding))
                ET.SubElement(xml_impuesto, "{" + xmlns + "}MontoImpuesto").text = "0.00"
                ET.SubElement(xml_item, "{" + xmlns + "}Total").text = str(round(line_price_total, general_rounding))
                grand_total += round(line_price_total, general_rounding)
            
            elif not line.tax_ids:
                ET.SubElement(xml_item, "{" + xmlns + "}Total").text = str(round(line_price_total, general_rounding))
                grand_total += round(line_price_total, general_rounding)
                price_tax_total += price_tax

        return grand_total, fel_taxes, price_tax_total, total_iva


    def _set_fel_gt_totals(self, xml_data_emision, xmlns, fel_taxes, general_rounding, grand_total):
        """Handle the totals section of the XML."""
        xml_totales = ET.SubElement(xml_data_emision, f"{{{xmlns}}}Totales")

        if not self.company_id.fel_gt_small_taxpayer_withholding and self.fel_gt_invoice_type not in ['NABN','RECI']:
            xml_total_impuestos = ET.SubElement(xml_totales, f"{{{xmlns}}}TotalImpuestos")
            self._add_fel_gt_total_taxes_to_xml(xml_total_impuestos, fel_taxes, general_rounding)

        ET.SubElement(xml_totales, f"{{{xmlns}}}GranTotal").text = str(round(grand_total, general_rounding))


    def _add_fel_gt_total_taxes_to_xml(self, xml_total_impuestos, fel_taxes, general_rounding):
        """Add the total taxes to the XML."""
        for tax_name, amount in fel_taxes.items():
            if amount > 0:
                ET.SubElement(xml_total_impuestos, f"{{{xmlns}}}TotalImpuesto", NombreCorto=tax_name, 
                            TotalMontoImpuesto=str(round(amount, general_rounding)))
        if not self.company_id.fel_gt_small_taxpayer_withholding and self.fel_gt_invoice_type == 'FEXP':
            ET.SubElement(xml_total_impuestos, f"{{{xmlns}}}TotalImpuesto", NombreCorto="IVA", 
                            TotalMontoImpuesto="0")

    def _set_fel_gt_complements(self, type, xml_data_emision, xmlns, fel_certifier, make_conversion, conversion_rate, general_rounding, grand_total, price_tax_total, total_iva):
        """Handle the complements section of the XML."""
        if type == 'FESP':
            
            fel_gt_withhold_amount = self.fel_gt_withhold_amount
            amount_untaxed = self.amount_untaxed
            invoice_base_amount = round(amount_untaxed - fel_gt_withhold_amount, general_rounding)
            if make_conversion:
                invoice_base_amount = grand_total - price_tax_total
                if conversion_rate > 1.0:
                    fel_gt_withhold_amount = fel_gt_withhold_amount * conversion_rate
                    amount_untaxed = amount_untaxed * conversion_rate
                else:
                    fel_gt_withhold_amount = fel_gt_withhold_amount / conversion_rate
                    amount_untaxed = amount_untaxed / conversion_rate

            isr_withold = 0
            isr_withold = invoice_base_amount * 0.05
            
            isr_withold = round(isr_withold, general_rounding)
            fel_gt_withhold_amount = isr_withold

            xml_complementos = ET.SubElement(xml_data_emision, "{" + xmlns + "}Complementos")
            if fel_certifier == 'megaprint' or fel_certifier == 'digifact':
                xml_complemento = ET.SubElement(xml_complementos, f"{{{xmlns}}}Complemento", IDComplemento=str(randint(1, 99999)), 
                                                NombreComplemento="FacturaEspecial", URIComplemento="FESP")
            else:
                xml_complemento = ET.SubElement(xml_complementos, f"{{{xmlns}}}Complemento", IDComplemento=str(randint(1, 99999)), 
                                                NombreComplemento="FacturaEspecial", URIComplemento="FESP", attrib={"{" + xsi + "}schemaLocation": note_schemaLocation_complementos})
            xml_retenciones = ET.SubElement(xml_complemento, "{" + fesp_cno + "}RetencionesFacturaEspecial", Version="1")
            ET.SubElement(xml_retenciones, "{" + fesp_cno + "}RetencionISR").text = str(fel_gt_withhold_amount)
            ET.SubElement(xml_retenciones, "{" + fesp_cno + "}RetencionIVA").text = str(round(total_iva, general_rounding))
            if make_conversion:
                ET.SubElement(xml_retenciones, "{" + fesp_cno + "}TotalMenosRetenciones").text = str(round(invoice_base_amount - fel_gt_withhold_amount, general_rounding))
            else:
                ET.SubElement(xml_retenciones, "{" + fesp_cno + "}TotalMenosRetenciones").text = str(round(amount_untaxed - fel_gt_withhold_amount, general_rounding))
        
        elif type == 'NDEB':

            debit_note_name = "Nota de debito " + str(self.fel_gt_source_debit_note_id.fel_gt_dte_number)
            dte_date = self.fel_gt_source_debit_note_id.fel_gt_dte_date
            if not dte_date:
                raise UserError('La factura no posee una fecha de DTE, si desea realizar cambios sobre la misma desactive la facturación electrónica en el diario asociado a la misma.')
            racion_de_6h = timedelta(hours=6)
            dte_date = dte_date - racion_de_6h
            date_format = "%Y-%m-%d"
            dte_date = dte_date.strftime(date_format)
            xml_complementos = ET.SubElement(xml_data_emision, "{" + xmlns + "}Complementos")
            if fel_certifier == 'megaprint':
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento=self.name, URIComplemento=notes_xsd)
            elif fel_certifier == 'digifact':
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento=self.name, URIComplemento='cno')
            else:
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento=self.name, URIComplemento=notes_xsd, attrib={"{" + xsi + "}schemaLocation": note_schemaLocation_complementos})
            ET.register_namespace('cno', note_complemento_xmlns)
            if not self.fel_gt_old_tax_regime:
                ET.SubElement(xml_complemento, "{" + note_complemento_xmlns + "}ReferenciasNota", FechaEmisionDocumentoOrigen=dte_date, MotivoAjuste=debit_note_name, NumeroAutorizacionDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_uuid), NumeroDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_dte_number), SerieDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_serie), Version="0.1")
            else:
                ET.SubElement(xml_complemento, "{" + note_complemento_xmlns + "}ReferenciasNota", FechaEmisionDocumentoOrigen=dte_date, RegimenAntiguo="Antiguo", MotivoAjuste=debit_note_name, NumeroAutorizacionDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_uuid), NumeroDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_dte_number), SerieDocumentoOrigen=str(self.fel_gt_source_debit_note_id.fel_gt_serie), Version="0.1")
        
        elif type == 'NCRE':
            source = self.fel_gt_source_credit_note_id
            if source and source.invoice_date:
                dte_date = source.invoice_date
            else:
                dte_date = self.env['account.move'].search([('fel_gt_uuid_original', '=', self.fel_gt_uuid_original),('state','=','posted'),('move_type','=','out_invoice')], limit=1).invoice_date
            if not dte_date:
                raise UserError('La factura no posee una fecha de DTE, si desea realizar cambios sobre la misma desactive la facturación electrónica en el diario asociado a la misma.')

            date_format = "%Y-%m-%d"
            dte_date = dte_date.strftime(date_format)
            xml_complementos = ET.SubElement(xml_data_emision, "{" + xmlns + "}Complementos")
            uuid_source = source.fel_gt_uuid if source else self.fel_gt_uuid_original
            dte_source = source.fel_gt_dte_number if source else self.fel_gt_dte_number_original
            serie_source = source.fel_gt_serie if source else self.fel_gt_serie_original
            if fel_certifier == 'megaprint':
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento=self.name, URIComplemento=notes_xsd)
            elif fel_certifier == 'digifact':
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", NombreComplemento='NCRE', URIComplemento='cno', attrib={"xsi:schemaLocation": note_schemaLocation_complementos, "xmlns:cno": note_complemento_xmlns})
            else:
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento=self.name, URIComplemento=notes_xsd, attrib={"{" + xsi + "}schemaLocation": note_schemaLocation_complementos})
            if fel_certifier != 'digifact':
                ET.register_namespace('cno', note_complemento_xmlns)
                ET.SubElement(xml_complemento, "{" + note_complemento_xmlns + "}ReferenciasNota", FechaEmisionDocumentoOrigen=dte_date, MotivoAjuste=self.name, NumeroAutorizacionDocumentoOrigen=str(uuid_source), NumeroDocumentoOrigen=str(dte_source), SerieDocumentoOrigen=str(serie_source), Version="0.1")
            else:
                ET.SubElement(xml_complemento, "cno:ReferenciasNota", FechaEmisionDocumentoOrigen=dte_date, MotivoAjuste=self.name, NumeroAutorizacionDocumentoOrigen=str(uuid_source), NumeroDocumentoOrigen=str(dte_source), SerieDocumentoOrigen=str(serie_source), Version="0.1")

        elif type == 'FEXP':

            date_due = self.invoice_date_due
            formato2 = "%Y-%m-%d"
            date_due = date_due.strftime(formato2)

            xml_complementos = ET.SubElement(xml_data_emision, "{" + xmlns + "}Complementos")
            xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento="Exportacion", URIComplemento=fexp_cno)
            if fel_certifier == 'megaprint' or fel_certifier == 'digifact':
                xml_retenciones_secondary = ET.SubElement(xml_complemento, "{" + fexp_cna + "}Exportacion", Version="1")
            else:
                xml_retenciones_secondary = ET.SubElement(xml_complemento, "{" + fexp_cna + "}Exportacion", Version="1", attrib={"{" + xsi + "}schemaLocation": fexp_schemaLocation_complementos})
            ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}NombreConsignatarioODestinatario").text = self.partner_id.fel_gt_consignatary_name
            ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}DireccionConsignatarioODestinatario").text = self.partner_id.fel_gt_consignatary_address

            if self.partner_id.fel_gt_consignatary_code:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}CodigoConsignatarioODestinatario").text = self.partner_id.fel_gt_consignatary_code
            if self.partner_id.name:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}NombreComprador").text = self.partner_id.name
            if self.partner_id.fel_gt_buyer_address:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}DireccionComprador").text = self.partner_id.fel_gt_buyer_address
            if self.partner_id.fel_gt_buyer_code:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}CodigoComprador").text = self.partner_id.fel_gt_buyer_code
            if self.partner_id.ref:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}OtraReferencia").text = self.partner_id.ref
            if self.invoice_incoterm_id.code:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}INCOTERM").text = self.invoice_incoterm_id.code
            if self.partner_id.fel_gt_exporter_name:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}NombreExportador").text = self.partner_id.fel_gt_exporter_name
            if self.partner_id.fel_gt_exporter_code:
                ET.SubElement(xml_retenciones_secondary, "{" + fexp_cna + "}CodigoExportador").text = self.partner_id.fel_gt_exporter_code
        
        elif type == 'FCAM':
            date_due = self.invoice_date_due
            formato2 = "%Y-%m-%d"
            date_due = date_due.strftime(formato2)
            xml_complementos = ET.SubElement(xml_data_emision, "{" + xmlns + "}Complementos")
            if fel_certifier == 'megaprint' or fel_certifier == 'digifact':
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento="AbonosFacturaCambiaria", URIComplemento="FCAM")
            else:
                xml_complemento = ET.SubElement(xml_complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1, 99999)), NombreComplemento="AbonosFacturaCambiaria", URIComplemento="FCAM", attrib={"{" + xsi + "}schemaLocation": fcam_schemaLocation_complementos})
            xml_retenciones = ET.SubElement(xml_complemento, "{" + fcam_cno + "}AbonosFacturaCambiaria", Version="1")
            xml_abono = ET.SubElement(xml_retenciones, "{" + fcam_cno + "}Abono")
            ET.SubElement(xml_abono, "{" + fcam_cno + "}NumeroAbono").text = "1"
            ET.SubElement(xml_abono, "{" + fcam_cno + "}FechaVencimiento").text = date_due
            ET.SubElement(xml_abono, "{" + fcam_cno + "}MontoAbono").text = str(round(self.amount_total, general_rounding))


    def _set_fel_gt_addenda(self, xml_doc, xmlns, fel_certifier, conversion_rate, issue_date):
        """Handle the addenda section of the XML."""
        if not (self.journal_id.fel_gt_addendum_active or fel_certifier == 'digifact' or (fel_certifier == 'infile' and self.company_id.fel_gt_infile_cert_method == 'direct')):
            return
        
        date_format = "%d-%m-%Y"
            
        xml_adenda = ET.SubElement(xml_doc, f"{{{xmlns}}}Adenda")

        if fel_certifier == 'digifact':
            self._add_fel_gt_digifact_addenda(xml_adenda, issue_date)
        elif fel_certifier == 'infile' and self.company_id.fel_gt_infile_cert_method == 'direct':
            ET.SubElement(xml_adenda, "Documento").text = f"{self.journal_id.code}-{self.id}"
        
        if self.journal_id.fel_gt_addendum_internal_serie:
            ET.SubElement(xml_adenda, "serie").text = self.journal_id.code

        if self.journal_id.fel_gt_addendum_internal_number:
            ET.SubElement(xml_adenda, "numero").text = self.name

        if self.journal_id.fel_gt_addendum_partner_ref and self.partner_id.ref:
            ET.SubElement(xml_adenda, "cliente").text = self.partner_id.ref

        if self.journal_id.fel_gt_addendum_credit:
            ET.SubElement(xml_adenda, "credito").text = ''

        if self.journal_id.fel_gt_addendum_order and self.invoice_origin:
            ET.SubElement(xml_adenda, "pedido").text = self.invoice_origin
        
        if self.journal_id.fel_gt_addendum_comercial and self.invoice_user_id:
            ET.SubElement(xml_adenda, "vendedor").text = self.invoice_user_id.name

        if self.journal_id.fel_gt_addendum_payment_date and self.invoice_date_due:
            ET.SubElement(xml_adenda, "fecha_pago").text = self.invoice_date_due.strftime(date_format)
        
        if self.journal_id.fel_gt_addendum_currency_rate:
            ET.SubElement(xml_adenda, "tasadecambio").text = str(1 * conversion_rate if conversion_rate > 1.0 else 1 / conversion_rate)

        if self.fel_gt_invoice_type == 'NABN':
            date_due = self.invoice_date_due
            date_due = date_due.strftime(date_format)
            if fel_certifier != 'digifact':
                ET.SubElement(xml_adenda, "FechaVencimiento").text = date_due


    def _add_fel_gt_digifact_addenda(self, xml_adenda, fecha_emision):
        """Add specific addenda for Digifact."""
        informacion_comercial = ET.SubElement(xml_adenda, "dtecomm:Informacion_COMERCIAL", 
                                            attrib={"xmlns:dtecomm": "https://www.digifact.com.gt/dtecomm", "xsi:schemaLocation": "https://www.digifact.com.gt/dtecomm"})

        informacion_adicional = ET.SubElement(informacion_comercial, "dtecomm:InformacionAdicional", attrib={"Version": "7.1234654163"})
        codigo_firma = f"{self.journal_id.code}{self.id}"
        ET.SubElement(informacion_adicional, "dtecomm:REFERENCIA_INTERNA").text = codigo_firma
        ET.SubElement(informacion_adicional, "dtecomm:FECHA_REFERENCIA").text = fecha_emision
        ET.SubElement(informacion_adicional, "dtecomm:VALIDAR_REFERENCIA_INTERNA").text = 'VALIDAR'

        informacion_adicional_extra = ET.SubElement(informacion_adicional, "dtecomm:INFORMACION_ADICIONAL")
        ET.SubElement(informacion_adicional_extra, "dtecomm:Detalle", attrib={"Data": 'VALOR1', "Value": f"{self.journal_id.code}-{self.id}"})


    def _format_fel_gt_xml_content(self, xml_content):
        """Format the XML content for storage and sending."""
        search_string = "ns0"
        string_replace = "dte"
        xml_content = xml_content.decode('utf_8')
        xml_content = xml_content.replace(search_string, string_replace)
        return xml_content.encode('utf_8')
    

    def _store_fel_gt_sent_xml(self, xml_content, vat, date_due, fel_certifier):
        """Store the sent XML data."""
        raw_binary_data = base64.b64encode(b" " + xml_content)
        self.fel_gt_xml_fel_sent = raw_binary_data
        self.fel_gt_xml_fel_sent_name = "fel_xml.xml"
        store_sent_xml(self, xml_content, vat, date_due, fel_certifier)


    def _xml_standard_fel_gt_maker(self, fel_certifier, type='FACT'):
        """Create the standard FEL XML."""
        
        self._check_fel_gt_neccesary_fields()

        version = "0.1"
        
        root_attrib = {
            "Version": version,
            f"{{{xsi}}}schemaLocation": schemaLocation,
        }
        xml_root = ET.Element(f"{{{xmlns}}}GTDocumento", **root_attrib)

        if fel_certifier in ['g4s', 'megaprint']:
            xml_root = ET.Element(f"{{{xmlns}}}GTDocumento", Version=version)
        elif fel_certifier == 'digifact':
            xml_root = ET.Element(f"{{{xmlns}}}GTDocumento", {"xmlns:xsi": xsi, "Version": version})
        elif fel_certifier == 'infile' and self.company_id.fel_gt_infile_cert_method == 'direct':
            xml_root.set("xmlns:ds", xmlns_ds)

        fel_type = type
        if type == 'FESP':
            ET.register_namespace('cfe', fesp_cno)
        elif type == 'FEXP':
            ET.register_namespace('cex', fexp_cna)
            fel_type = 'FACT'
        elif type == 'FCAM':
            ET.register_namespace('cfc', fcam_cno)
        

        xml_doc = ET.SubElement(xml_root, f"{{{xmlns}}}SAT", ClaseDocumento="dte")
        xml_dte = ET.SubElement(xml_doc, f"{{{xmlns}}}DTE", ID="DatosCertificados")
        xml_data_emision = ET.SubElement(xml_dte, f"{{{xmlns}}}DatosEmision", ID="DatosEmision")

        company_vat = re.sub(r'[\s\?\.\/\;\:\-]', '', self.company_id.vat.upper())

        conversion_rate, make_conversion, currency_code, general_rounding = self._get_fel_gt_conversion_rate()

        issue_date = self._get_fel_gt_issue_date()
        self.fel_gt_dte_issue_date = issue_date

        general_data = ET.SubElement(xml_data_emision, f"{{{xmlns}}}DatosGenerales", 
                                        CodigoMoneda=currency_code, 
                                        FechaHoraEmision=issue_date, Tipo=fel_type)
        
        if int(float(self.fel_gt_contingency_access_number)) > 0:
            general_data.set("NumeroAcceso", str(int(float(self.fel_gt_contingency_access_number))))

        if type == 'FEXP':
            general_data.set("Exp", "SI")

        establishment_code, commercial_name, fel_address, fel_zip_code, fel_township, fel_department, fel_company_name, fel_company_email = self._get_fel_gt_establishment_info()

        fel_affiliation = self._get_fel_gt_invoice_type()

        xml_emisor = ET.SubElement(xml_data_emision, f"{{{xmlns}}}Emisor", AfiliacionIVA=fel_affiliation,
                                CodigoEstablecimiento=establishment_code, CorreoEmisor=fel_company_email,
                                NITEmisor=company_vat, NombreComercial=commercial_name,
                                NombreEmisor=fel_company_name)
        xml_emisor_address = ET.SubElement(xml_emisor, f"{{{xmlns}}}DireccionEmisor")
        self._set_fel_gt_address_fields(xml_emisor_address, fel_address, fel_zip_code, fel_township, fel_department)

        vat, name, has_dpi, has_passport = self._get_fel_gt_receptor_vat_info()

        xml_receptor = ET.SubElement(xml_data_emision, f"{{{xmlns}}}Receptor", CorreoReceptor=self.partner_id.email or "", 
                                    IDReceptor=vat, NombreReceptor=name)
        if has_dpi:
            xml_receptor.set("TipoEspecial", "CUI")
        elif has_passport:
            xml_receptor.set("TipoEspecial", "EXT")

        xml_receptor_address = ET.SubElement(xml_receptor, f"{{{xmlns}}}DireccionReceptor")
        self._set_fel_gt_address_fields(xml_receptor_address, self.partner_id.street, self.partner_id.zip, 
                                self.partner_id.city, self.partner_id.state_id.name if self.partner_id.state_id else 'Guatemala')

        self._set_fel_gt_phrases(xml_data_emision, xmlns)

        grand_total, fel_taxes, price_tax_total, total_iva = self._set_fel_gt_items(xml_data_emision, xmlns, general_rounding, make_conversion, conversion_rate)

        self._set_fel_gt_totals(xml_data_emision, xmlns, fel_taxes, general_rounding, grand_total)

        self._set_fel_gt_complements(type, xml_data_emision, xmlns, fel_certifier, make_conversion, conversion_rate, general_rounding, grand_total, price_tax_total, total_iva)

        self._set_fel_gt_addenda(xml_doc, xmlns, fel_certifier, conversion_rate, issue_date)

        xml_content = ET.tostring(xml_root, encoding="UTF-8", method="xml")
        xml_content = self._format_fel_gt_xml_content(xml_content)
        
        self._store_fel_gt_sent_xml(xml_content, vat, self.invoice_date.strftime("%d-%m-%Y"), fel_certifier)

        _logger.info(f'FEL CONTENT {xml_content}')

        return xml_content
 

    def _get_fel_gt_cancel_issue_date(self):
        """Get the issue date for the cancelation XML."""
        if self.fel_gt_dte_issue_date_original:
            date_invoice = self.fel_gt_dte_issue_date_original
            return datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3], date_invoice
        else:
            date_invoice = self.fel_gt_dte_date or datetime.now()
            racion_de_6h = timedelta(hours=6)
            date_invoice = date_invoice - racion_de_6h
            invoice_date_format = "%Y-%m-%dT%H:%M:%S.%f"
            date_invoice = date_invoice.strftime(invoice_date_format)[:-3]
            return datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3], date_invoice

    
    # ANULACIÓN DE FACTURA
    def _xml_cancel_standard_fel_maker(self, fel_certifier):
        """Create the standard FEL XML for cancelation."""
        self._check_fel_gt_neccesary_fields()

        xml_root = ET.Element("{" + xmlns_cancel + "}GTAnulacionDocumento", Version="0.1", attrib={"{" + xsi + "}schemaLocation": schemaLocation_cancel})
        if fel_certifier == 'g4s' or fel_certifier == 'megaprint':
            xml_root = ET.Element("{" + xmlns_cancel + "}GTAnulacionDocumento", Version="0.1")
        elif fel_certifier == 'digifact':
            root_attrib = {
                "xmlns:xsi": xsi,
                "Version": "0.1",
            }
            xml_root = ET.Element("{" + xmlns_cancel + "}GTAnulacionDocumento", root_attrib)

        xml_doc = ET.SubElement(xml_root, "{" + xmlns_cancel + "}SAT")
        xml_dte = ET.SubElement(xml_doc, "{" + xmlns_cancel + "}AnulacionDTE", ID="DatosCertificados")

        date_due, date_invoice = self._get_fel_gt_cancel_issue_date()
        
        company_vat = re.sub(r'[\s\?\.\/\;\:\-]', '', self.company_id.vat.upper())

        vat = self._get_fel_gt_receptor_vat_info()[0]

        motive = 'Anulación'
        if self.fel_gt_cancel_motive:
            motive = self.fel_gt_cancel_motive
        
        ET.SubElement(xml_dte, "{" + xmlns_cancel + "}DatosGenerales", FechaEmisionDocumentoAnular=date_invoice, FechaHoraAnulacion=date_due, ID="DatosAnulacion", IDReceptor=vat, MotivoAnulacion=motive, NITEmisor=company_vat, NumeroDocumentoAAnular=str(self.fel_gt_uuid))
        
        xml_content = ET.tostring(xml_root, encoding="UTF-8", method='xml')
        search_string = "ns0"
        attribute_replace = "dte"
        ds_search_string = "xsi:ds"
        ds_replace_string = "xmlns:ds"
        xml_content = xml_content.decode('utf_8')
        xml_content = xml_content.replace(search_string, attribute_replace)
        xml_content = xml_content.replace(ds_search_string, ds_replace_string)
        xml_content = xml_content.encode('utf_8')
        
        _logger.info('FEL CONTENT ' + str(xml_content))
        store_sent_xml(self, xml_content, vat, date_due, fel_certifier)

        return xml_content
    

    def send_data_api(self, xml_data=None, type_document='fel', fel_type=1, fel_certifier='infile'):
        """Send the XML data to the API."""
        company_nit = self.company_id.vat.replace('-', '').zfill(12)
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        today_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if fel_certifier == 'guatefacturas':
            return self._handle_fel_gt_guatefacturas(xml_data, company_nit, type_document, fel_type, today_date)
        elif fel_certifier == 'infile':
            return self._handle_fel_gt_infile(xml_data, company_nit, type_document, fel_type, today_date)
        elif fel_certifier == 'g4s':
            return self._handle_fel_gt_g4s(xml_data, company_nit, type_document, fel_type, today_date)
        elif fel_certifier == 'megaprint':
            return self._handle_fel_gt_megaprint(xml_data, company_nit, type_document, fel_type, today_date)
        elif fel_certifier == 'digifact':
            return self._handle_fel_gt_digifact(xml_data, company_nit, type_document, fel_type, today_date)
        
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_guatefacturas(self, xml_data, company_nit, type_document, fel_type, today_date):
        """Handle the Guatefacturas API."""
        username = self.company_id.fel_gt_guatefacturas_user
        password = self.company_id.fel_gt_guatefacturas_password
        soap_username = self.company_id.fel_gt_guatefacturas_auth_user
        soap_password = self.company_id.fel_gt_guatefacturas_auth_password
        env_url = self.company_id.fel_gt_guatefacturas_xml_url_signature
        fel_establishment_code = self.journal_id.fel_gt_establishment_code or self.company_id.fel_gt_establishment_code

        try:
            session = Session()
            session.auth = HTTPBasicAuth(soap_username, soap_password)
            client = zeep.Client(wsdl=env_url, transport=Transport(session=session))
        except Exception as e:
            return self._handle_fel_gt_certificate_error(xml_data, str(e), 'CLIENT ZEEP', 'guatefacturas')

        if type_document == 'cancel':
            return self._guatefacturas_cancel_document(client, company_nit, username, password, today_date)
        else:
            return self._guatefacturas_generate_document(client, company_nit, fel_establishment_code, fel_type, username, password, xml_data, today_date)


    def _guatefacturas_cancel_document(self, client, company_nit, username, password, today_date):
        """Cancel the document in Guatefacturas."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        fecha_anulacion = datetime.now().strftime('%Y%m%d')

        try:
            service_response = client.service.anulaDocumento(username, password, company_nit, self.fel_gt_serie, self.fel_gt_dte_number, self.partner_id.vat, fecha_anulacion, "Anulación")
            xml_response = ET.ElementTree(ET.fromstring(str(service_response)))
            root = xml_response.getroot()

            for child in root:
                if child.tag == 'ESTADO' and child.text == "ANULADO":
                    uuid, serie, dte_number, dte_date = self.fel_gt_uuid, self.fel_gt_serie, self.fel_gt_dte_number, fecha_anulacion
        except Exception as e:
            return self._handle_fel_gt_certificate_error(service_response, str(e), 'FUNCTIONCALL', 'guatefacturas')

        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _guatefacturas_generate_document(self, client, company_nit, fel_establishment_code, fel_type, username, password, xml_data, today_date):
        """Generate the document in Guatefacturas."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""

        try:
            service_response = client.service.generaDocumento(username, password, company_nit, fel_establishment_code, fel_type, 1, 'D', xml_data)
            service_response = service_response.replace('<Resultado>', "").replace('</Resultado>', "")
        except Exception as e:
            return self._handle_fel_gt_certificate_error(service_response, str(e), 'FUNCTIONCALL', 'guatefacturas')

        if 'dte:NumeroAutorizacion' not in service_response:
            return self._handle_fel_gt_sat_validation_error(service_response, today_date)

        raw_binary_data = base64.b64encode(bytes(service_response, encoding='utf-8'))
        self.fel_gt_xml_fel_certified = raw_binary_data
        self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"

        xml_response = ET.ElementTree(ET.fromstring(str(service_response)))
        root = xml_response.getroot()

        for child in root:
            if child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}SAT':
                for sat_child in child:
                    if sat_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}DTE':
                        for dte_child in sat_child:
                            if dte_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}Certificacion':
                                for cert_child in dte_child:
                                    if cert_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}NumeroAutorizacion':
                                        uuid = cert_child.text
                                        serie = cert_child.attrib['Serie']
                                        dte_number = cert_child.attrib['Numero']
                                    if cert_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}FechaHoraCertificacion':
                                        dte_date = cert_child.text

        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_infile(self, xml_data, company_nit, type_document, fel_type, today_date):
        """Handle the Infile API."""
        infile_user = self.company_id.fel_gt_infile_user
        infile_xml_key_signature = self.company_id.fel_gt_infile_xml_key_signature
        infile_key_certificate = self.company_id.fel_gt_infile_key_certificate
        codigo_firma = f"{self.journal_id.code}-{self.id}"
        self.fel_gt_uuid_internal = codigo_firma

        if self.company_id.fel_gt_infile_cert_method == 'signature':
            return self._infile_signature_method(xml_data, infile_user, infile_xml_key_signature, infile_key_certificate, codigo_firma, type_document, today_date)
        else:
            return self._infile_direct_method(xml_data, infile_user, infile_xml_key_signature, infile_key_certificate, codigo_firma, today_date)


    def _infile_signature_method(self, XML, infile_user, infile_xml_key_signature, infile_key_certificate, codigo_firma, type_document, today_date):
        """Handle the Infile signature method."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        XML = base64.b64encode(XML)
        is_anullment = "N"
        if type_document == 'cancel':
            is_anullment = 'S'
        data_send = {
            'llave': infile_xml_key_signature,
            'archivo': XML,
            'codigo': codigo_firma,
            'alias': infile_user,
            'es_anulacion': is_anullment
        }
        infile_xml_url_signature = self.company_id.fel_gt_infile_xml_url_signature

        try:
            response = requests.post(infile_xml_url_signature, data=data_send)
            JSON_response_signature = response.json()
        except Exception as e:
            return self._handle_fel_gt_certificate_error(XML, str(e), 'URL REQUEST', 'infile')

        if not JSON_response_signature["resultado"]:
            message = f"Ha ocurrido un error al intentar firmar el documento. \n {JSON_response_signature['descripcion']}"
            raise ValidationError(message)

        xml_dte = JSON_response_signature["archivo"]
        payload = {
            'nit_emisor': self.company_id.vat,
            'correo_copia': self.company_id.email,
            'xml_dte': xml_dte,
        }
        identificador = f"{self.journal_id.code}{self.id}"
        headers = {
            'usuario': infile_user,
            'llave': infile_key_certificate,
            'content-type': "application/json",
            'identificador': identificador,
        }
        api_url = self.company_id.fel_gt_infile_url_certificate if type_document != 'cancel' else self.company_id.fel_gt_infile_url_anulation

        try:
            response = requests.post(api_url, data=json.dumps(payload), headers=headers)
            JSON_response_certificate = response.json()
        except Exception as e:
            return self._handle_fel_gt_certificate_error(XML, str(e), 'POST REQUEST', 'infile')

        if not JSON_response_certificate.get("uuid"):
            return self._handle_fel_gt_sat_validation_error(response.text, today_date)

        uuid = JSON_response_certificate["uuid"]
        serie = JSON_response_certificate["serie"]
        dte_number = JSON_response_certificate["numero"]
        dte_date = JSON_response_certificate["fecha"]
        if 'xml_certificado' in JSON_response_certificate:
            xml_content = base64.b64decode(JSON_response_certificate['xml_certificado'])
            raw_binary_data = base64.b64encode(b" "+xml_content)
            self.fel_gt_xml_fel_certified = raw_binary_data
            self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"
        
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _infile_direct_method(self, XML, infile_user, infile_xml_key_signature, infile_key_certificate, codigo_firma, today_date):
        """Handle the Infile direct method."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        infile_xml_url_direct = self.company_id.fel_gt_infile_xml_url_direct
        headers = {
            'UsuarioAPI': infile_user,
            'LlaveAPI': infile_key_certificate,
            'UsuarioFirma': infile_user,
            'Identificador': codigo_firma,
            'LlaveFirma': infile_xml_key_signature,
            'Content-Type': 'application/xml',
        }

        try:
            response = requests.post(infile_xml_url_direct, headers=headers, data=XML)
            JSON_response_signature = response.json()
        except Exception as e:
            return self._handle_fel_gt_certificate_error(XML, str(e), 'URL REQUEST', 'infile')

        if not JSON_response_signature["resultado"]:
            message = f"Ha ocurrido un error al intentar firmar el documento. \n {JSON_response_signature['descripcion']}"
            raise ValidationError(message)

        uuid = JSON_response_signature["uuid"]
        serie = JSON_response_signature["serie"]
        dte_number = JSON_response_signature["numero"]
        dte_date = JSON_response_signature["fecha"]
        if 'xml_certificado' in JSON_response_signature:
            xml_content = base64.b64decode(JSON_response_signature['xml_certificado'])
            raw_binary_data = base64.b64encode(b" "+xml_content)
            self.fel_gt_xml_fel_certified = raw_binary_data
            self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"
        
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_g4s(self, xml_data, company_nit, type_document, fel_type, today_date):
        """Handle the G4S API."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        requestor_id = self.company_id.fel_gt_g4s_requestor
        username = self.company_id.fel_gt_g4s_user
        env_url = self.company_id.fel_gt_g4s_xml_url_signature
        second_wsdl = f"{env_url}?wsdl"

        try:
            client = zeep.Client(wsdl=second_wsdl)
        except Exception as e:
            return self._handle_fel_gt_certificate_error(xml_data, str(e), 'CLIENT ZEEP', 'g4s')

        type_request = 'POST_DOCUMENT_SAT' if type_document != 'cancel' else 'VOID_DOCUMENT'
        data3 = f"{self.journal_id.code}{self.id}" if type_document != 'cancel' else 'XML'

        request_data = {
            'Requestor': requestor_id,
            'Transaction': 'SYSTEM_REQUEST',
            'Country': 'GT',
            'Entity': company_nit,
            'User': requestor_id,
            'UserName': username,
            'Data1': type_request,
            'Data2': xml_data,
            'Data3': data3
        }

        try:
            service_response = client.service.RequestTransaction(**request_data)
        except Exception as e:
            return self._handle_fel_gt_certificate_error(service_response, str(e), 'FUNCTIONCALL', 'g4s')

        if 'Response' in service_response and 'Code' in service_response['Response']:
            if service_response['Response']['Code'] != 1:
                return self._handle_fel_gt_sat_validation_error(service_response['Response']['Description'], today_date)
            
            if 'ResponseData' in service_response and 'ResponseData1' in service_response['ResponseData']:
                success_response = service_response['ResponseData']['ResponseData1']
                xml_content = base64.b64decode(success_response)
                xml_response = ET.ElementTree(ET.fromstring(xml_content))
                raw_binary_data = base64.b64encode(b" "+xml_content)
                self.fel_gt_xml_fel_certified = raw_binary_data
                self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"
                root = xml_response.getroot()

                if type_document == 'cancel':
                    uuid, serie, dte_number, dte_date = self.fel_gt_uuid, self.fel_gt_serie, self.fel_gt_dte_number, self.fel_gt_dte_date
                else:
                    for child in root:
                        if child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}SAT':
                            for sat_child in child:
                                if sat_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}DTE':
                                    for dte_child in sat_child:
                                        if dte_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}Certificacion':
                                            for cert_child in dte_child:
                                                if cert_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}NumeroAutorizacion':
                                                    uuid = cert_child.text
                                                    serie = cert_child.attrib['Serie']
                                                    dte_number = cert_child.attrib['Numero']
                                                if cert_child.tag == '{http://www.sat.gob.gt/dte/fel/0.2.0}FechaHoraCertificacion':
                                                    dte_date = cert_child.text
                                                    self.fel_gt_enable_cancel_bypass = False
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_megaprint(self, xml_data, company_nit, type_document, fel_type, today_date):
        """Handle the Megaprint API."""
        if datetime.now() > self.company_id.fel_gt_megaprint_token_expiry_date:
            token = self.company_id.fel_gt_generate_megaprint_token()
        else:
            token = self.company_id.fel_gt_megaprint_token

        request_id = self.fel_gt_uuid_internal or str(UD.uuid5(UD.NAMESPACE_OID, f"{self.journal_id.code}{self.id}")).upper()
        self.fel_gt_uuid_internal = request_id
        xml_sin_firma = xml_data.decode("utf-8")

        if type_document != 'cancel':
            return self._megaprint_verify_and_register_document(token, request_id, xml_sin_firma, today_date)
        else:
            return self._megaprint_cancel_document(token, request_id, xml_sin_firma, today_date)


    def _megaprint_verify_and_register_document(self, token, request_id, xml_sin_firma, today_date):
        """Verify and register the document in Megaprint."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        headers = {"Content-Type": "application/xml", "authorization": f"Bearer {token}"}
        data = f'<?xml version="1.0" encoding="UTF-8"?><VerificaDocumentoRequest id="{request_id}"></VerificaDocumentoRequest>'

        r = requests.post(self.company_id.fel_gt_megaprint_xml_url_verify, data=data.encode('UTF-8'), headers=headers)
        resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

        if resultadoXML.find('tipo_respuesta').text == '0':
            return self._megaprint_sign_and_register_document(token, headers, request_id, xml_sin_firma, today_date)
        else:
            if self.fel_gt_uuid:
                _logger.info(f"La factura ya ha sido validada en la SAT\n {r.text}.")
                uuid, serie, dte_number, dte_date = self.fel_gt_uuid, self.fel_gt_serie, self.fel_gt_dte_number, today_date
            else:
                return self._handle_fel_gt_sat_validation_error(r.text, today_date)
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _megaprint_sign_and_register_document(self, token, headers, request_id, xml_sin_firma, today_date):
        """Sign and register the document in Megaprint."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        data = f'<?xml version="1.0" encoding="UTF-8"?><FirmaDocumentoRequest id="{request_id}"><xml_dte><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>{xml_sin_firma}]]></xml_dte></FirmaDocumentoRequest>'
        r = requests.post(self.company_id.fel_gt_megaprint_xml_url_signature, headers=headers, data=data.encode('UTF-8'))
        resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

        if resultadoXML.find('tipo_respuesta').text == '0':
            xml_con_firma = resultadoXML.xpath("//xml_dte")[0].text
            headers = {"Content-Type": "application/xml", "authorization": f"Bearer {token}"}
            data = f'<?xml version="1.0" encoding="UTF-8"?><RegistraDocumentoXMLRequest id="{request_id}"><xml_dte><![CDATA[{xml_con_firma}]]></xml_dte></RegistraDocumentoXMLRequest>'
            r = requests.post(self.company_id.fel_gt_megaprint_xml_url_registry, data=data.encode('UTF-8'), headers=headers)
            resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

            if resultadoXML.find('tipo_respuesta').text == '0':
                xml_certificado = resultadoXML.xpath("//xml_dte")[0].text
                xml_certificado_root = etree.XML(bytes(xml_certificado, encoding='utf-8'))
                numero_autorizacion = xml_certificado_root.find(".//{http://www.sat.gob.gt/dte/fel/0.2.0}NumeroAutorizacion")
                uuid = numero_autorizacion.text
                serie = numero_autorizacion.get("Serie")
                dte_number = numero_autorizacion.get("Numero")
                dte_date = xml_certificado_root.find(".//{http://www.sat.gob.gt/dte/fel/0.2.0}FechaHoraCertificacion").text
                self.fel_gt_xml_fel_certified = base64.b64encode(bytes(xml_certificado, encoding='utf-8'))
                self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"
            else:
                return self._handle_fel_gt_sat_validation_error(r.text, today_date)
        else:
            return self._handle_fel_gt_sat_validation_error(r.text, today_date)

        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _megaprint_cancel_document(self, token, request_id, xml_sin_firma, today_date):
        """Cancel the document in Megaprint."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        headers = {"Content-Type": "application/xml", "authorization": f"Bearer {token}"}
        data = f'<?xml version="1.0" encoding="UTF-8"?><FirmaDocumentoRequest id="{request_id}"><xml_dte><![CDATA[{xml_sin_firma}]]></xml_dte></FirmaDocumentoRequest>'
        r = requests.post(self.company_id.fel_gt_megaprint_xml_url_signature, headers=headers, data=data.encode('UTF-8'))
        resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

        if len(resultadoXML.xpath("//xml_dte")) > 0:
            xml_con_firma = html.unescape(resultadoXML.xpath("//xml_dte")[0].text)
            headers = {"Content-Type": "application/xml", "authorization": f"Bearer {token}"}
            data = f'<?xml version="1.0" encoding="UTF-8"?><AnulaDocumentoXMLRequest id="{request_id}"><xml_dte><![CDATA[{xml_con_firma}]]></xml_dte></AnulaDocumentoXMLRequest>'
            r = requests.post(self.company_id.fel_gt_megaprint_xml_url_cancel, headers=headers, data=data.encode('UTF-8'))
            resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

            if len(resultadoXML.xpath("//listado_errores")) > 0:
                raise UserError(r.text)
            else:
                uuid, serie, dte_number, dte_date = self.fel_gt_uuid, self.fel_gt_serie, self.fel_gt_dte_number, today_date
        else:
            return self._handle_fel_gt_sat_validation_error(r.text, today_date)

        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_digifact(self, xml_data, company_nit, type_document, fel_type, today_date):
        """Handle the Digifact API."""
        uuid, serie, dte_number, dte_date, sat_ref_id = "", "", "", "", ""
        if datetime.now() > self.company_id.fel_gt_digifact_token_expiry_date:
            token = self.company_id.fel_gt_generate_digifact_token()
        else:
            token = self.company_id.fel_gt_digifact_token

        api_url = self.company_id.fel_gt_digifact_api_xml_url_signature
        headers = {
            "Content-Type": "application/xml",
            "Authorization": token,
        }
        params = {
            'NIT': company_nit,
            'FORMAT': 'XML',
            'USERNAME': self.company_id.fel_gt_digifact_user,
            'TIPO': 'CERTIFICATE_DTE_XML_TOSIGN' if type_document != 'cancel' else 'ANULAR_FEL_TOSIGN',
        }

        try:
            r = requests.post(api_url, params=params, data=xml_data, headers=headers, verify=False)
            certificacion_json = r.json()
        except Exception as e:
            return self._handle_fel_gt_certificate_error(xml_data, str(e), 'POST REQUEST', 'digifact')

        if certificacion_json["Codigo"] != 1:
            return self._handle_fel_gt_sat_validation_error(certificacion_json["ResponseDATA1"], today_date)

        xml_resultado = base64.b64decode(certificacion_json['ResponseDATA1'])
        dte_resultado = etree.XML(xml_resultado)
        numero_autorizacion = dte_resultado.xpath("//*[local-name() = 'NumeroAutorizacion']")[0]

        uuid = numero_autorizacion.text
        serie = numero_autorizacion.get("Serie")
        dte_number = numero_autorizacion.get("Numero")
        dte_date = dte_resultado.find(".//{http://www.sat.gob.gt/dte/fel/0.2.0}FechaHoraCertificacion").text
        self.fel_gt_xml_fel_certified = xml_resultado
        self.fel_gt_xml_fel_certified_name = "fel_xml_certified.xml"
        
        return uuid, serie, dte_number, dte_date, sat_ref_id


    def _handle_fel_gt_certificate_error(self, xml_data, error_message, context, fel_certifier):
        """Handle the certificate error."""
        _logger.info(f'CERFTICATE ERROR {error_message}')
        store_sent_xml(self, xml_data, f"CERFTICATE-{error_message}", context, fel_certifier)
        html_message = f'La factura no pudo ser enviada a la SAT y se ha colocado en contingencia (Error: {error_message})'
        self.message_post(body=html_message)
        self.fel_gt_has_contingency = True
        self.fel_gt_state = 'contingency'
        if not self.fel_gt_contingency_access_number:
            self.fel_gt_contingency_access_number = self.get_fel_gt_establishment_access_code()
        self.update_pos_order_contingency_data()
        return False, False, False, False, False


    def _handle_fel_gt_sat_validation_error(self, service_response, today_date):
        """Handle the SAT validation error."""
        _logger.info(f"La factura no pudo ser validada en la SAT\n Error: {service_response}.")
        html_message = f'<strong>Error Validación FEL</strong><br/> <strong>Detalle:</strong> {service_response}'
        self.fel_gt_state = 'sat_validation_error'
        self.fel_gt_enable_cancel_bypass = True
        self.message_post(body=html_message)
        if not self.company_id.fel_gt_publish_onerror:
            raise UserError(f"La factura no pudo ser validada en la SAT\n Error:{service_response}.")
        return False, False, False, today_date, False


    def get_fel_gt_company_address(self):
        """Get the company address."""
        street = self.company_id.street or "Ciudad"
        street2 = self.company_id.street2 or ""
        address = "%s %s"%(street, street2)

        return address

    def update_pos_order_contingency_data(self):
        """Update the POS order with the contingency data."""
        try:
            pos_order_data = self.env['pos.order'].search([('account_move', '=', self.id)])
            if pos_order_data:
                pos_order_data.write({'fel_gt_has_contingency': True, 'fel_gt_contingency_access_number': self.fel_gt_contingency_access_number})
        except Exception as e:
            return False

    def get_fel_gt_establishment_access_code(self):
        """Get the establishment access code."""
        self.ensure_one()
        return self.journal_id.get_fel_next_fel_gt_contingency_number()
    
    def process_fel_gt_contigency(self):
        """Process the FEL contingency."""
        if self.fel_gt_invoice_type in ['none', False]:
            raise UserError("Favor agregar el tipo de Factura, previo a validarla.")
        
        currency_name, general_rounding = self._get_fel_gt_currency_and_rounding()

        if self.move_type == "in_invoice":
            self._handle_fel_gt_in_invoice(currency_name, general_rounding, self.journal_id.fel_gt_is_receipt_journal or self.fel_gt_invoice_type == 'RECI')
        
        elif self.move_type == "out_invoice":
            self._handle_fel_gt_out_invoice(currency_name, general_rounding, self.journal_id.fel_gt_is_receipt_journal or self.fel_gt_invoice_type == 'RECI')

        elif self.move_type == "out_refund":
            self._handle_fel_gt_out_refund()

    def process_fel_gt_all_contigency(self):
        """Process all the FEL contingency."""
        contingency_invoices = self.env['account.move'].search([
            ('fel_gt_state', '=', 'contingency'),
            ('fel_gt_has_contingency', '=', True)
        ])
        for invoice in contingency_invoices:
            if invoice.fel_gt_contingency_access_number:
                invoice.process_fel_gt_contigency()
    
    
    @api.onchange('partner_id', 'company_id')
    def _onchange_fel_partner_id(self):
        """Onchange the FEL partner ID."""
        result = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id and self.partner_id.fel_gt_report_template_id:
            self.fel_gt_report_template_id = self.partner_id.fel_gt_report_template_id.id or False
        return result

    @api.model
    def _default_report_template(self):
        """Get the default report template."""
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        return report_id

    @api.depends('partner_id')
    def _default_fel_gt_report_template1(self):
        """Get the default FEL report template."""
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        if self.fel_gt_report_template_id and self.fel_gt_report_template_id.id < report_id.id:
            self.write({'fel_gt_report_template_id': report_id and report_id.id or False})
        self.fel_gt_report_template_id = self.fel_gt_report_template_id or False
        self.fel_gt_report_template_id1 = report_id and report_id.id or False

    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        res = super(AccountMove, self).invoice_print()
        if self.fel_gt_report_template_id or self.partner_id and self.partner_id.fel_gt_report_template_id or self.company_id and self.company_id.fel_gt_report_template_id:
            report_id = self.fel_gt_report_template_id and self.fel_gt_report_template_id or self.partner_id and self.partner_id.fel_gt_report_template_id or self.company_id and self.company_id.fel_gt_report_template_id
            if report_id:
                report = report_id.report_action(self)
                return report
            else:
                return res
        return res

    def _get_fel_gt_street(self, partner):
        """Get the FEL street."""
        self.ensure_one()
        res = {}
        address = ''
        if partner.street:
            address = "%s" % (partner.street)
        if partner.street2:
            address += ", %s" % (partner.street2)
        if address:
            return address
        return False

    def _get_fel_gt_address_details(self, partner):
        """Get the FEL address details."""
        self.ensure_one()
        res = {}
        address = ''
        if partner.city:
            address = "%s" % (partner.city)
        if partner.state_id.name:
            address += ", %s" % (partner.state_id.name)
        if partner.zip:
            address += ", %s" % (partner.zip)
        if partner.country_id.name:
            address += ", %s" % (partner.country_id.name)
        if address:
            return address
        return False
    
    def _get_fel_gt_journal_details(self):
        """Get the FEL journal details."""
        self.ensure_one()
        res = {}
        address = ''
        if self.journal_id.fel_gt_address:
            address = "%s" % (self.journal_id.fel_gt_address)
        if self.journal_id.fel_gt_township:
            address += ", %s" % (self.journal_id.fel_gt_township)
        if self.journal_id.fel_gt_department:
            address += ", %s" % (self.journal_id.fel_gt_department)
        if self.journal_id.fel_gt_zip_code:
            address += ", %s" % (self.journal_id.fel_gt_zip_code)
        if address:
            return address
        return False

    def _get_fel_gt_partner_vat(self, partner):
        """Get the FEL partner VAT."""
        self.ensure_one()
        vat, name, has_dpi, has_passport = self._get_fel_gt_receptor_vat_info()
        vat_label = 'NIT'
        if has_dpi:
            vat_label = 'DPI'
        if has_passport:
            vat_label = 'PASAPORTE'
        return vat_label, vat

    def _get_fel_gt_origin_date(self, origin):
        """Get the FEL origin date."""
        self.ensure_one()
        try:
            if self.move_type in ('in_invoice', 'in_refund'):
                sale_obj = self.env['purchase.order']
            else:
                sale_obj = self.env['sale.order']
            lang = self.env.user.lang
            lang_obj = self.env['res.lang']
            ids = lang_obj.search([("code", "=", lang or 'en_US')])
            sale = sale_obj.search([('name', '=', origin)])
            if sale:
                timestamp = datetime.strptime(str(sale.date_order), tools.DEFAULT_SERVER_DATETIME_FORMAT)
                ts = fields.Datetime.context_timestamp(self, timestamp)
                n_date = ts.strftime(ids.date_format)
                if sale:
                    return n_date
            sale_obj = self.env['pos.order']
            sale = sale_obj.search([('name', '=', origin)])
            if sale:
                timestamp = datetime.strptime(str(sale.date_order), tools.DEFAULT_SERVER_DATETIME_FORMAT)
                ts = fields.Datetime.context_timestamp(self, timestamp)
                n_date = ts.strftime(ids.date_format)
                if sale:
                    return n_date
        except:
            return False
        return False

    def _get_fel_gt_invoice_date(self):
        """Get the FEL invoice date."""
        self.ensure_one()
        lang = self.env.user.lang
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        if self.invoice_date:
            timestamp = datetime.strptime(str(self.invoice_date), tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format)
            if self:
                return n_date
        return False

    def _get_fel_gt_invoice_due_date(self):
        """Get the FEL invoice due date."""
        self.ensure_one()
        lang = self.env.user.lang
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        if self.invoice_date_due:
            timestamp = datetime.strptime(str(self.invoice_date_due), tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format)
            if self:
                return n_date
        return False

    def _get_fel_gt_tax_amount(self, amount, payment=None):
        """Get the FEL tax amount."""
        self.ensure_one()
        res = {}
        currency = self.currency_id or self.company_id.currency_id
        res = formatLang(self.env, amount, currency_obj=currency)
        if payment != None:
            if self.move_type in ('out_invoice', 'in_refund'):
                amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
            elif self.move_type in ('in_invoice', 'out_refund'):
                amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
            # get the payment value in invoice currency
            if payment.currency_id and payment.currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, self.currency_id)
            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                return res
            res = formatLang(self.env, amount_to_show, currency_obj=currency)
        return res

    fel_gt_report_template_id1 = fields.Many2one('ir.actions.report', string="Plantilla Factura1", compute='_default_fel_gt_report_template1', help="Porfavor seleccione una Plantilla de Factura", domain=[('model', '=', 'account.move')])
    fel_gt_report_template_id = fields.Many2one('ir.actions.report', string="Plantilla Factura", help="Porfavor seleccione una Plantilla de Factura", domain=[('model', '=', 'account.move')])


def number2text(number_in, currency_name):
    converted = ''
    if type(number_in) != 'str':
        number = str(number_in)
    else:
        number = number_in

    number_str = number
    number_str = number_str.replace(',', '')
    try:
        number_int, number_dec = number_str.split(".")
    except ValueError:
        number_int = number_str
        number_dec = ""

    number_str = number_int.zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if(millones):
        if(millones == '001'):
            converted += 'UN MILLON '
        elif(int(millones) > 0):
            converted += '%sMILLONES ' % __convertNumber(millones)

    if(miles):
        if(miles == '001'):
            converted += 'MIL '
        elif(int(miles) > 0):
            converted += '%sMIL ' % __convertNumber(miles)
    if(cientos):
        if(cientos == '001'):
            converted += 'UN '
        elif(int(cientos) > 0):
            converted += '%s ' % __convertNumber(cientos)

    if number_dec == "":
        number_dec = "00"
    if (len(number_dec) < 2):
        number_dec += '0'

    converted += currency_name
    converted += ' CON ' + number_dec + "/100."
    return converted.title()

UNIDADES = (
    '',
    'UNO ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)
DECENAS = (
    'VEINTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)
CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)


def conversion_rate_manager(self, data_type, data, general_rounding=2):
    if data_type == 'line':
        line = data['line']
        line_price_unit = line.price_unit
        line_price = line.quantity * line.price_unit
        line_price_total = line.price_total
        line_price_subtotal = line.price_subtotal
        conversion_rate = data['conversion_rate']
        conversion_rate = 1 / conversion_rate
        tax_amount = 0
        if conversion_rate > 1.0:
            subtotal_conversion = 0
            subtotal_conversion = line.price_subtotal * conversion_rate
            if line.tax_ids:
                if line.tax_ids.amount_type == 'percent':
                    tax_amount = (line.tax_ids.amount * subtotal_conversion) / 100

            line_price = line_price * conversion_rate
            line_price_unit = line.price_unit * conversion_rate
            line_price_subtotal = line.price_subtotal * conversion_rate
            line_price_total = line.price_total * conversion_rate
            price_tax = tax_amount
            line_price_subtotal = line_price_total - price_tax

        else:
            subtotal_conversion = 0
            subtotal_conversion = line.price_subtotal / conversion_rate
            if line.tax_ids:
                if line.tax_ids.amount_type == 'percent':
                    tax_amount = (line.tax_ids.amount * subtotal_conversion) / 100

            line_price = line_price / conversion_rate
            line_price_unit = line.price_unit / conversion_rate
            line_price_subtotal = line.price_subtotal / conversion_rate
            line_price_total = line.price_total / conversion_rate
            price_tax = tax_amount
            line_price_subtotal = line_price_total - price_tax

        conversion_data = {
            "line_price": round(line_price, general_rounding),
            "line_price_unit": round(line_price_unit, general_rounding),
            "line_price_total": round(line_price_total, general_rounding),
            "line_price_subtotal": round(line_price_subtotal, general_rounding),
            "price_tax": round(price_tax, general_rounding)
        }

        return conversion_data

def store_sent_xml(self, xml_content, vat, date_due, certifier):

    sql = """
    INSERT INTO fel_gt_tools_log_xml_sent(
        name, data_content, certifier, 
        create_uid, create_date, write_uid, write_date
    )
    VALUES(%s, %s, %s, %s, %s, %s, %s)
    """
    
    cr_log = sql_db.db_connect(self.env.cr.dbname).cursor()
    name = f"{vat}-{self.company_id.vat}-{date_due}"
    final_xml = parseString(xml_content.decode('utf-8')).toprettyxml(indent="  ")
    
    params = [
        name, final_xml, certifier, 
        self.env.user.id, datetime.now(), 
        self.env.user.id, datetime.now()
    ]
    
    cr_log.execute(sql, params)
    cr_log.commit()

def dropzeros(number):
    mynum = decimal.Decimal(number).normalize()
    return mynum.__trunc__() if not mynum % 1 else float(mynum)

def __convertNumber(n):
    output = ''

    if(n == '100'):
        output = "CIEN"
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0])-1]

    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])

    return output

def departments_mapping(name):
    department = "1"
    switcher = {
        "GUATEMALA": "1",
        "EL PROGRESO": "2",
        "SACATEPEQUEZ": "3",
        "CHIMALTENANGO": "4",
        "ESCUINTLA": "5",
        "SANTA ROSA": "6",
        "SOLOLA": "7",
        "TOTONICAPAN": "8",
        "QUETZALTENANGO": "9",
        "SUCHITEPEQUEZ": "10",
        "RETALHULEU": "11",
        "SAN MARCOS": "12",
        "HUEHUETENANGO": "13",
        "QUICHE": "14",
        "BAJA VERAPAZ": "15",
        "ALTA VERAPAZ": "16",
        "PETEN": "17",
        "IZABAL": "18",
        "ZACAPA": "19",
        "CHIQUIMULA": "20",
        "JALAPA": "21",
        "JUTIAPA": "22",
        "BELICE": "23"
    }
    if switcher.get(name, ""):
        department = switcher.get(name, "")
    
    return department

def townships_mapping(name, department_id):
    township = "1"
    if department_id == 1:
        switcher = {
            "Guatemala": "1",
            "Santa Catarina Pinula": "2",
            "San Jose Pinula": "3",
            "San Jose del Golfo": "4",
            "Palencia": "5",
            "Chinautla": "6",
            "San Pedro Ayampuc": "7",
            "Mixco": "8",
            "San Pedro Sacatepequez": "9",
            "San Juan Sacatepequez": "10",
            "San Raymundo": "11",
            "Chuarrancho": "12",
            "Fraijanes": "13",
            "Amatitlan": "14",
            "Villa Nueva": "15",
            "Villa Canales": "16",
            "San Miguel Petapa": "17"
        }
        if switcher.get(name, ""):
            township = switcher.get(name, "")
    
    return township