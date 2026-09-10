# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError
from xml.etree.ElementTree import fromstring
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import timedelta
import dateutil.parser


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fel_gt_certifier = fields.Selection(string='Certificador a utilizar', related="company_id.fel_gt_certifier", readonly=False)

    fel_gt_currency_from_invoice = fields.Boolean(string="Seleccionar moneda de facturación a factura", related="company_id.fel_gt_currency_from_invoice", readonly=False)
    fel_gt_invoice_currency = fields.Many2one('res.currency', related="company_id.fel_gt_invoice_currency", string="Moneda de facturación", readonly=False)
    fel_gt_move_name = fields.Boolean(string="Nombre del Documento Establecido por FEL", related="company_id.fel_gt_move_name", readonly=False)
    fel_gt_default_code_divider = fields.Char(string="Separador de referencia interna", related="company_id.fel_gt_default_code_divider", readonly=False)
    fel_gt_invoice_line_name = fields.Selection(string="Descripcion de producto de factura", related="company_id.fel_gt_invoice_line_name", readonly=False)
    fel_gt_price_tax_rounding = fields.Integer(string="Número decimales de redondeo", related="company_id.fel_gt_price_tax_rounding", readonly=False)
    fel_gt_publish_onerror = fields.Boolean(string="Publicar asiento con errores SAT", related="company_id.fel_gt_publish_onerror", readonly=False)
    fel_gt_establishment_code = fields.Char(string="Código Establecimiento", related="company_id.fel_gt_establishment_code", readonly=False)
    fel_gt_invoice_discount_column = fields.Boolean(string="Mostrar Columna de Descuento", related="company_id.fel_gt_invoice_discount_column", readonly=False)
    
    # INFILE
    fel_gt_infile_user = fields.Char(string="Usuario INFILE (Alias/Prefijo)", related="company_id.fel_gt_infile_user", readonly=False)
    fel_gt_infile_cert_method = fields.Selection(string="Método de Certificación", related="company_id.fel_gt_infile_cert_method", readonly=False)
    fel_gt_infile_xml_url_direct = fields.Char(string="URL Directo INFILE", related="company_id.fel_gt_infile_xml_url_direct", readonly=False)
    fel_gt_infile_xml_key_signature = fields.Char(string="Llave Firma INFILE (Token)", related="company_id.fel_gt_infile_xml_key_signature", readonly=False)
    fel_gt_infile_xml_url_signature = fields.Char(string="URL Firma INFILE", related="company_id.fel_gt_infile_xml_url_signature", readonly=False)
    fel_gt_infile_key_certificate = fields.Char(string="Llave Certificación INFILE (Llave)", related="company_id.fel_gt_infile_key_certificate", readonly=False)
    fel_gt_infile_url_certificate = fields.Char(string="URL Certificación INFILE", related="company_id.fel_gt_infile_url_certificate", readonly=False)
    fel_gt_infile_url_anulation = fields.Char(string="URL Anulación INFILE", related="company_id.fel_gt_infile_url_anulation", readonly=False)

    #G4S
    fel_gt_g4s_requestor = fields.Char(string="Requestor G4S", related="company_id.fel_gt_g4s_requestor", readonly=False)
    fel_gt_g4s_user = fields.Char(string="Usuario G4S", related="company_id.fel_gt_g4s_user", readonly=False)
    fel_gt_g4s_xml_url_signature = fields.Char(string="URL G4S", related="company_id.fel_gt_g4s_xml_url_signature", readonly=False)

    # GUATEFACTURAS
    fel_gt_guatefacturas_user = fields.Char(string="Usuario Guatefacturas", related="company_id.fel_gt_guatefacturas_user", readonly=False)
    fel_gt_guatefacturas_password = fields.Char(string="Contraseña Guatefacturas", related="company_id.fel_gt_guatefacturas_password", readonly=False)
    fel_gt_guatefacturas_auth_user = fields.Char(string="Usuario HTTP Autenticación", related="company_id.fel_gt_guatefacturas_auth_user", readonly=False)
    fel_gt_guatefacturas_auth_password = fields.Char(string="Contraseña HTTP Autenticación", related="company_id.fel_gt_guatefacturas_auth_password", readonly=False)
    fel_gt_guatefacturas_xml_url_signature = fields.Char(string="URL Firma Guatefacturas", related="company_id.fel_gt_guatefacturas_xml_url_signature", readonly=False)

    #MEGAPRINT
    fel_gt_megaprint_user = fields.Char(string="Usuario MegaPrint", related="company_id.fel_gt_megaprint_user", readonly=False)
    fel_gt_megaprint_apikey = fields.Char(string="Apikey MegaPrint", related="company_id.fel_gt_megaprint_apikey", readonly=False)
    fel_gt_megaprint_xml_url_signature = fields.Char(string="URL Firma MegaPrint", related="company_id.fel_gt_megaprint_xml_url_signature", readonly=False)
    fel_gt_megaprint_xml_url_verify = fields.Char(string="URL Verificar MegaPrint", related="company_id.fel_gt_megaprint_xml_url_verify", readonly=False)
    fel_gt_megaprint_xml_url_registry = fields.Char(string="URL Registrar MegaPrint", related="company_id.fel_gt_megaprint_xml_url_registry", readonly=False)
    fel_gt_megaprint_xml_url_cancel = fields.Char(string="URL Anular MegaPrint", related="company_id.fel_gt_megaprint_xml_url_cancel", readonly=False)
    fel_gt_megaprint_xml_url_pdf = fields.Char(string="URL PDF MegaPrint", related="company_id.fel_gt_megaprint_xml_url_pdf", readonly=False)
    fel_gt_megaprint_url_token = fields.Char(string="URL Token MegaPrint", related="company_id.fel_gt_megaprint_url_token", readonly=False)
    fel_gt_megaprint_token = fields.Char(string="Token MegaPrint", related="company_id.fel_gt_megaprint_token")
    fel_gt_megaprint_token_expiry_date = fields.Datetime(string="Vigencia Token MegaPrint", related="company_id.fel_gt_megaprint_token_expiry_date")

    def generate_megaprint_token(self):
        url = self.fel_gt_megaprint_url_token
        xml_body = '''<?xml version="1.0" encoding="utf-8"?>
                <SolicitaTokenRequest>
                    <usuario>%s</usuario>
                    <apikey>%s</apikey>
                </SolicitaTokenRequest>
                ''' %(self.fel_gt_megaprint_user, self.fel_gt_megaprint_apikey)
        
        headers = {
        'Content-Type': 'application/xml'
        }
        try:
            response = requests.request("POST", url, headers=headers, data=xml_body)
            response_xml_as_string = response.text
            responseXml = fromstring(response_xml_as_string)
        except Exception as e:
            _logger.info('MEGAPRINT TOKEN REQUEST ERROR ' + str(e))
            raise ValidationError('MEGAPRINT TOKEN REQUEST ERROR ' + str(e))
        if responseXml.find('tipo_respuesta').text == '0':
            token = responseXml.find('token').text
            expiry_date = responseXml.find('vigencia').text
            dte_given_time = dateutil.parser.parse(expiry_date)
            timezone_gt_adjust = timedelta(hours=6)
            gt_time = dte_given_time + timezone_gt_adjust
            dte_timedate_format = "%Y-%m-%d %H:%M:%S"
            gt_time = gt_time.strftime(dte_timedate_format)
            self.sudo().write({'fel_gt_megaprint_token': token, 'fel_gt_megaprint_token_expiry_date':gt_time})
            self.env.company.sudo().write({'fel_gt_megaprint_token': token, 'fel_gt_megaprint_token_expiry_date':gt_time})
        else:
            try:
                code_error = responseXml.findall('.//{*}cod_error')[0].text
                desc_error = responseXml.findall('.//{*}desc_error')[0].text
                if desc_error and code_error:
                    _logger.info('MEGAPRINT TOKEN REQUEST ERROR: ' + code_error + ' - ' + desc_error)
                    message = "Ha ocurrido un error al intentar obtener un token. \n Error No: %s - %s" % (code_error, desc_error)
                    raise ValidationError(message)
                else:
                    raise ValidationError('Ha ocurrido un error al intentar obtener un token.')
            except:
                raise ValidationError('Ha ocurrido un error al intentar obtener un token.')


    #DIGIFACT
    fel_gt_digifact_user = fields.Char(string="Usuario Digifact", readonly=False, related="company_id.fel_gt_digifact_user")
    fel_gt_digifact_password = fields.Char(string="Contraseña Digifact", readonly=False, related="company_id.fel_gt_digifact_password")
    fel_gt_digifact_url_token = fields.Char(string="URL Token Digifact", readonly=False, related="company_id.fel_gt_digifact_url_token")
    fel_gt_digifact_token_expiry_date = fields.Datetime(string="Vigencia Token Digifact", readonly=False, related="company_id.fel_gt_digifact_token_expiry_date")
    fel_gt_digifact_token = fields.Char(string="Token Digifact", readonly=False, related="company_id.fel_gt_digifact_token")
    fel_gt_digifact_api_xml_url_signature = fields.Char(string="URL Firma Digifact", readonly=False, related="company_id.fel_gt_digifact_api_xml_url_signature")
    fel_gt_digifact_api_pdf_url_signature = fields.Char(string="URL PDF Digifact", readonly=False, related="company_id.fel_gt_digifact_api_pdf_url_signature")
    fel_gt_digifact_url_token_nuc = fields.Char(string="URL Token NUC Digifact", readonly=False, related="company_id.fel_gt_digifact_url_token_nuc")
    fel_gt_digifact_token_nuc_expiry_date = fields.Datetime(string="Vigencia Token NUC Digifact", readonly=False, related="company_id.fel_gt_digifact_token_nuc_expiry_date")
    fel_gt_digifact_token_nuc = fields.Char(string="Token NUC Digifact", readonly=False, related="company_id.fel_gt_digifact_token_nuc")

    def generate_digifact_token(self):
        url = self.fel_gt_digifact_url_token
        
        headers = { "Content-Type": "application/json" }
        data = {
                "Username": 'GT.'+self.company_id.vat.replace('-','').zfill(12)+'.'+self.fel_gt_digifact_user,
                "Password": self.fel_gt_digifact_password,
            }
        try:
            response = requests.post(url, json=data, headers=headers)
            token_json = response.json()
        except Exception as e:
            _logger.info('DIGIFACT TOKEN REQUEST ERROR ' + str(e))
            raise ValidationError('DIGIFACT TOKEN REQUEST ERROR ' + str(e))
        if "Token" in token_json:
            token = token_json["Token"]
            expiry_date = token_json["expira_en"]
            dte_given_time = dateutil.parser.parse(expiry_date)
            timezone_gt_adjust = timedelta(hours=6)
            gt_time = dte_given_time + timezone_gt_adjust
            dte_timedate_format = "%Y-%m-%d %H:%M:%S"
            gt_time = gt_time.strftime(dte_timedate_format)
            self.sudo().write({'fel_gt_digifact_token': token, 'fel_gt_digifact_token_expiry_date':gt_time})
            self.env.cr.commit()
            return token
        else:
            raise ValidationError('Ha ocurrido un error al intentar obtener un token.')
        
    def generate_digifact_token_nuc(self):
        url = self.fel_gt_digifact_url_token_nuc
        
        headers = { "Content-Type": "application/json" }
        data = {
                "Username": 'GT.'+self.company_id.vat.replace('-','').zfill(12)+'.'+self.company_id.fel_gt_digifact_user,
                "Password": self.company_id.fel_gt_digifact_password,
            }
        try:
            response = requests.post(url, json=data, headers=headers)
            token_json = response.json()
        except Exception as e:
            _logger.info('DIGIFACT TOKEN REQUEST ERROR ' + str(e))
            raise ValidationError('DIGIFACT TOKEN REQUEST ERROR ' + str(e))
        if "Token" in token_json:
            token = token_json["Token"]
            expiry_date = token_json["expira_en"]
            dte_given_time = dateutil.parser.parse(expiry_date)
            timezone_gt_adjust = timedelta(hours=6)
            gt_time = dte_given_time + timezone_gt_adjust
            dte_timedate_format = "%Y-%m-%d %H:%M:%S"
            gt_time = gt_time.strftime(dte_timedate_format)
            self.sudo().write({'fel_gt_digifact_token_nuc': token, 'fel_gt_digifact_token_nuc_expiry_date':gt_time})
            self.env.cr.commit()
            return token
        else:
            raise ValidationError('Ha ocurrido un error al intentar obtener un token.')
