# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from xml.etree.ElementTree import fromstring
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import timedelta
import dateutil.parser

import base64
from odoo.modules import get_module_resource

standard_template = [
    ('bold', 'Bold'),    
    ('classic', 'Classic'),
    ('corporate', 'Corporate'),
    ('morden', 'Morden'),
    ('polished', 'Polished'),
    ('vintage', 'Vintage'),
]

template = {
    'vintage': {
        'theme_color': '#000000',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#000000',
    },
    'bold': {
        'theme_color': '#32a860',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#32a860',
    },
    'morden': {
        'theme_color': '#007aff',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#007aff',
    },
    'polished': {
        'theme_color': '#007aff',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#007aff',
    },
    'corporate': {
        'theme_color': '#bfbcbb',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#bfbcbb',
    },
    'classic': {
        'theme_color': '#a24689',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#a24689',
    },
}

class ResCompany(models.Model):
    _inherit = "res.company"

    fel_gt_certifier = fields.Selection([
        ('infile', 'InFile'),
        ('g4s', 'G4S'),
        ('guatefacturas', 'Guatefacturas'),
        ('megaprint', 'Megaprint'),
        ('digifact', 'Digifact'),
        ], string='Certificador a utilizar - FEL GT', default='infile')

    fel_gt_currency_from_invoice = fields.Boolean(string="Seleccionar moneda de facturación en base a diario - FEL GT", default=True)
    fel_gt_invoice_currency = fields.Many2one('res.currency', string="Moneda de facturación - FEL GT")
    fel_gt_move_name = fields.Boolean(string="Nombre del Documento Establecido por FEL - FEL GT")
    fel_gt_default_code_divider = fields.Char(string="Separador de referencia interna - FEL GT")
    
    fel_gt_invoice_line_name = fields.Selection([
        ('product', 'Nombre de producto'),
        ('description', 'Descripcion')
    ], string="Descripcion de producto de factura - FEL GT", default="description")

    fel_gt_price_tax_rounding = fields.Integer(string="Número decimales de redondeo - FEL GT", help="Ingrese el número de decimales de redondeo que desea aplicar a los precios e impuestos")
    fel_gt_resolution_date = fields.Char(string="Fecha de resolución - FEL GT", help="Ingrese la fecha de resolución en caso de aplicar")
    fel_gt_resolution_number = fields.Char(string="Número de resolución - FEL GT", help="Ingrese el número de resolución en caso de aplicar")
    fel_gt_publish_onerror = fields.Boolean(string="Publicar asiento con errores SAT - FEL GT", help="Permite publicar los asientos contables aun cuando existan errores en la validación FEL en SAT")
    fel_gt_establishment_code = fields.Char(string="Código Establecimiento - FEL GT")
    fel_gt_small_taxpayer_withholding = fields.Boolean(string="Pequeño Contribuyente - FEL GT")
    fel_gt_old_tax_regime = fields.Boolean(string="Nota de crédito rebajando régimen antiguo - FEL GT")
    

    # INFILE
    fel_gt_infile_user = fields.Char(string="Usuario INFILE (Alias/Prefijo) - FEL GT", help="Ingrese el usuario proporcionado por INFILE.")
    fel_gt_infile_cert_method = fields.Selection([
        ('direct', 'Directo'),
        ('signature', 'Firma/Certificación')
    ], string="Método de Certificación - FEL GT", default="direct", help="Seleccione el método de Certificación de INFILE.")
    fel_gt_infile_xml_url_direct = fields.Char(string="URL Directo INFILE - FEL GT", help="Ingrese la URL para la firma de método directo.")
    fel_gt_infile_xml_key_signature = fields.Char(string="Llave Firma INFILE (Token) - FEL GT", help="Ingrese la llave para la firma.")
    fel_gt_infile_xml_url_signature = fields.Char(string="URL Firma INFILE - FEL GT", help="Ingrese la URL para la firma.")
    fel_gt_infile_key_certificate = fields.Char(string="Llave Certificación INFILE (Llave) - FEL GT", help="Ingrese la llave para la certificación.")
    fel_gt_infile_url_certificate = fields.Char(string="URL Certificación INFILE - FEL GT", help="Ingrese la URL para la certificación.")
    fel_gt_infile_url_anulation = fields.Char(string="URL Anulación INFILE - FEL GT", help="Ingrese la URL para la anulación de facturas.")

    # G4S
    fel_gt_g4s_requestor = fields.Char(string="Requestor G4S - FEL GT", help="Ingrese el requestor proporcionado por G4S.")
    fel_gt_g4s_user = fields.Char(string="Usuario G4S - FEL GT", help="Ingrese la url para la firma de G4S.")
    fel_gt_g4s_xml_url_signature = fields.Char(string="URL G4S - FEL GT", help="Ingrese el usuario proporcionado por G4S.")

    # GUATEFACTURAS
    fel_gt_guatefacturas_user = fields.Char(string="Usuario Guatefacturas - FEL GT", help="Ingrese el usuario proporcionado por Guatefacturas.")
    fel_gt_guatefacturas_password = fields.Char(string="Contraseña Guatefacturas - FEL GT", help="Ingrese la contraseña proporcionado por Guatefacturas.")
    fel_gt_guatefacturas_auth_user = fields.Char(string="Usuario HTTP Autenticación - FEL GT", help="Ingrese el usuario de Autenticación HTTP proporcionado por Guatefacturas.")
    fel_gt_guatefacturas_auth_password = fields.Char(string="Contraseña HTTP Autenticación - FEL GT", help="Ingrese la contraseña de Autenticación HTTP proporcionado por Guatefacturas.")
    fel_gt_guatefacturas_xml_url_signature = fields.Char(string="URL Firma Guatefacturas - FEL GT", help="Ingrese la URL para la firma proporcionada por Guatefacturas.")

    #MEGAPRINT
    fel_gt_megaprint_user = fields.Char(string="Usuario MegaPrint - FEL GT", help="Ingrese el Usuario proporcionado por MegaPrint.")
    fel_gt_megaprint_apikey = fields.Char(string="Apikey MegaPrint - FEL GT", help="Ingrese el ApiKey proporcionado por MegaPrint.")
    fel_gt_megaprint_token = fields.Char(string="Token MegaPrint - FEL GT",  help="Aqui podra Observar el Token Generado por MegaPrint")
    fel_gt_megaprint_url_token = fields.Char(string="URL Token MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api solicitarToken proporcionado por MegaPrint.")
    fel_gt_megaprint_token_expiry_date = fields.Datetime(string="Vigencia Token MegaPrint - FEL GT")
    fel_gt_megaprint_xml_url_verify = fields.Char(string="URL Verificar MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api verificarDocumento proporcionado por MegaPrint.")
    fel_gt_megaprint_xml_url_signature = fields.Char(string="URL Firma MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api solicitaFirma proporcionado por MegaPrint.")
    fel_gt_megaprint_xml_url_registry = fields.Char(string="URL Registrar MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api registrarDocumentoXML proporcionado por MegaPrint.")
    fel_gt_megaprint_xml_url_cancel = fields.Char(string="URL Anular MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api anularDocumentoXML proporcionado por MegaPrint.")
    fel_gt_megaprint_xml_url_pdf = fields.Char(string="URL PDF MegaPrint - FEL GT", help="Ingrese la URL para el consumo del Api retornarPDF proporcionado por MegaPrint.")

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
            self.env.cr.commit()
            return token
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
    fel_gt_digifact_user = fields.Char(string="Usuario Digifact - FEL GT", help="Ingrese el Usuario proporcionado por Digifact.")
    fel_gt_digifact_password = fields.Char(string="Contraseña Digifact - FEL GT", help="Ingrese el Password proporcionado por Digifact.")
    fel_gt_digifact_url_token = fields.Char(string="URL Token Digifact - FEL GT", help="Ingrese la URL para el consumo del Api solicitarToken proporcionado por Digifact.")
    fel_gt_digifact_token_expiry_date = fields.Datetime(string="Vigencia Token Digifact - FEL GT", help="Aqui podra Observar La Vigencia del Token Generado por Digifact.")
    fel_gt_digifact_token = fields.Char(string="Token Digifact - FEL GT", help="Aqui podra Observar el Token Generado por Digifact")
    fel_gt_digifact_api_xml_url_signature = fields.Char(string="URL Firma Digifact - FEL GT", help="Ingrese la URL para el consumo del Api solicitaFirma proporcionado por Digifact.")
    fel_gt_digifact_api_pdf_url_signature = fields.Char(string="URL PDF Digifact - FEL GT", help="Ingrese la URL para el consumo del Api GetDocument proporcionado por Digifact.")
    fel_gt_digifact_url_token_nuc = fields.Char(string="URL Token NUC Digifact - FEL GT", help="Ingrese la URL para el consumo del Token NUC proporcionado por Digifact.")
    fel_gt_digifact_token_nuc_expiry_date = fields.Datetime(string="Vigencia Token NUC Digifact - FEL GT", help="Aqui podra Observar La Vigencia del Token NUC Generado por Digifact.")
    fel_gt_digifact_token_nuc = fields.Char(string="Token NUC Digifact - FEL GT", help="Aqui podra Observar el Token NUC Generado por Digifact")

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
                "Username": 'GT.'+self.vat.replace('-','').zfill(12)+'.'+self.fel_gt_digifact_user,
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
            self.sudo().write({'fel_gt_digifact_token_nuc': token, 'fel_gt_digifact_token_nuc_expiry_date':gt_time})
            self.env.cr.commit()
            return token
        else:
            raise ValidationError('Ha ocurrido un error al intentar obtener un token.')
        

    #INVOICE TEMPLATES

    @api.model
    def fel_gt_default_report_template(self):
        fel_ir_rule_id = self.env['ir.rule'].search([('name', '=', 'res_partner: portal/public: read access on my commercial partner')])
        if fel_ir_rule_id:
            fel_ir_rule_id.unlink()
        fel_report_obj = self.env['ir.actions.report']
        fel_report_id = fel_report_obj.search([('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if fel_report_id:
            fel_report_id = fel_report_id[0]
        else:
            fel_report_id = fel_report_obj.search([('model', '=', 'account.move')])[0]
        return fel_report_id

    @api.depends('partner_id')
    def fel_gt_default_report_template1(self):
        fel_report_obj = self.env['ir.actions.report']
        fel_report_id = fel_report_obj.search([('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if fel_report_id:
            fel_report_id = fel_report_id[0]
        else:
            fel_report_id = fel_report_obj.search([('model', '=', 'account.move')])[0]
        if self.fel_gt_report_template_id and self.fel_gt_report_template_id.id < fel_report_id.id:
            self.write({'fel_gt_report_template_id': fel_report_id and fel_report_id.id or False})
        self.fel_gt_report_template_id1 = fel_report_id and fel_report_id.id or False

    @api.model
    def fel_gt_get_default_image(self, is_company, colorize=False):
        fel_img_path = get_module_resource('multicert_felgt', 'static/src/img', 'avatar.png')
        with open(fel_img_path, 'rb') as f:
            fel_image = f.read()
        return base64.b64encode(fel_image)

    def fel_gt_template_print1(self):       
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s?enable_editor' % ('multicert_felgt.report_demo_template_main', self.id),
        }

    @api.onchange('fel_gt_standard_template')
    def fel_gt_onchange_sale_order(self):
        if self.fel_gt_standard_template:
            fel_template_value = template.get(str(self.fel_gt_standard_template))
            self.fel_gt_theme_color = fel_template_value.get('theme_color', '#000000')
            self.fel_gt_theme_text_color = fel_template_value.get('theme_text_color', '#FFFFFF')
            self.fel_gt_text_color = fel_template_value.get('text_color', '#000000')
            self.fel_gt_company_color = fel_template_value.get('company_color', '#000000')
            self.fel_gt_company_address_color = fel_template_value.get('company_address_color', '#000000')
            self.fel_gt_customer_color = fel_template_value.get('customer_color', '#000000')
            self.fel_gt_customer_address_color = fel_template_value.get('customer_address_color', '#000000')
            self.fel_gt_odd_party_color = fel_template_value.get('odd_party_color', '#000000')
            self.fel_gt_even_party_color = fel_template_value.get('even_party_color', '#000000')
            self.fel_gt_watermark_text_color = fel_template_value.get('watermark_text_color', '#000000')
        return

    def fel_gt_get_font(self):
        return self.env['fel_gt.tools.report_fonts'].search([('family', '=', 'Helvetica'), ('mode', '=', 'all')], limit=1)

    def fel_gt_act_discover_fonts(self):
        self.ensure_one()
        return self.env["fel_gt.tools.report_fonts"].font_scan()

    fel_gt_theme_color = fields.Char(string="Color Base de la Plantilla - FEL GT", required=True, help="Por favor, establece el color Hex para la plantilla.", default="#a24689")
    fel_gt_theme_text_color = fields.Char(string="Color del Texto de la Plantilla - FEL GT", required=True, help="Por favor, establece el color Hex para el texto de la plantilla.", default="#FFFFFF")
    fel_gt_text_color = fields.Char(string="Color del Texto General - FEL GT", required=True, help="Por favor, establece el color Hex para el texto general.", default="#000000")
    fel_gt_company_color = fields.Char(string="Color del Nombre de la Empresa - FEL GT", required=True, help="Por favor, establece el color Hex para el nombre de la empresa.", default="#6F8192")
    fel_gt_customer_color = fields.Char(string="Color del Nombre del Cliente - FEL GT", required=True, help="Por favor, establece el color Hex para el nombre del cliente.", default="#000000")
    fel_gt_company_address_color = fields.Char(string="Color de la Dirección de la Empresa - FEL GT", required=True, help="Por favor, establece el color Hex para la dirección de la empresa.", default="#6F8192")
    fel_gt_customer_address_color = fields.Char(string="Color de la Dirección del Cliente - FEL GT", required=True, help="Por favor, establece el color Hex para la dirección del cliente.", default="#000000")
    fel_gt_odd_party_color = fields.Char(string="Color de Paridad Impar de la Tabla - FEL GT", required=True, help="Por favor, establece el color Hex para la paridad impar de la tabla.", default="#FFFFFF")
    fel_gt_even_party_color = fields.Char(string="Color de Paridad Par de la Tabla - FEL GT", required=True, help="Por favor, establece el color Hex para la paridad par de la tabla.", default="#e6e8ed")
    fel_gt_report_template_id1 = fields.Many2one('ir.actions.report', string="Plantilla de Factura 1 - FEL GT", compute='fel_gt_default_report_template1', help="Por favor, selecciona la plantilla de informe para la factura", domain=[('model', '=', 'account.move')])
    fel_gt_report_template_id = fields.Many2one('ir.actions.report', string="Plantilla de Factura - FEL GT", default=fel_gt_default_report_template, help="Por favor, selecciona la plantilla de informe para la factura", domain=[('model', '=', 'account.move')])
    fel_gt_invoice_logo = fields.Binary("Logotipo del Informe - FEL GT", attachment=True, default=lambda self: self.fel_gt_get_default_image(False, True), help="Este campo contiene la imagen utilizada como logotipo para el informe de la plantilla de factura.")
    fel_gt_is_description = fields.Boolean(string="Mostrar Descripción del Producto - FEL GT", default=True, help="Por favor, márcalo si deseas mostrar la descripción del producto en el informe.")
    fel_gt_watermark_logo = fields.Binary("Logotipo de Marca de Agua del Informe - FEL GT", default=lambda self: self.fel_gt_get_default_image(False, True), help="Por favor, establece el logotipo de marca de agua para el informe.")
    fel_gt_is_company_bold = fields.Boolean(string="Mostrar Nombre de la Empresa en Negrita - FEL GT", default=False, help="Por favor, márcalo si deseas mostrar el nombre de la empresa en negrita.")
    fel_gt_is_customer_bold = fields.Boolean(string="Mostrar Nombre del Cliente en Negrita - FEL GT", default=False, help="Por favor, márcalo si deseas mostrar el nombre del cliente en negrita.")
    fel_gt_standard_template = fields.Selection(standard_template, string="Configuración Estándar de la Plantilla - FEL GT", required=True, default='bold', help="Por favor, selecciona tu configuración estándar de color para todas las plantillas.")
    fel_gt_add_product_image = fields.Boolean(string="Mostrar Imagen del Producto - FEL GT", default=False, help="Por favor, márcalo si deseas mostrar la imagen del producto.")
    fel_gt_image_max_width = fields.Integer(string="Imagen del Producto Max Ancho - FEL GT", default=64)
    fel_gt_image_max_height = fields.Integer(string="Imagen del Producto Max Alto - FEL GT", default=64)
    fel_gt_image_min_width = fields.Integer(string="Imagen del Producto Min Ancho - FEL GT", default=32)
    fel_gt_image_min_height = fields.Integer(string="Imagen del Producto Min Alto - FEL GT", default=32)
    fel_gt_add_amount_in_words = fields.Boolean(string="Mostrar Monto en Palabras - FEL GT", default=True, help="Por favor, desmárcalo si deseas ocultar el monto en palabras.")
    fel_gt_is_show_watermark = fields.Boolean(string="¿Mostrar Marca de Agua? - FEL GT", help="Por favor, márcalo si deseas mostrar la marca de agua.")
    fel_gt_watermark = fields.Selection(selection=[('logo', 'Logotipo'), ('text', 'Texto'), ('status', 'Estado')], required=True, string="Mostrar Marca de Agua - FEL GT", default='text', help='Podemos elegir la marca de agua para el PDF ya sea logotipo, texto o estado.')
    fel_gt_watermark_text = fields.Char(string="Texto de la Marca de Agua - FEL GT", default='WatermarkText', help="Por favor, introduce el texto de la marca de agua.")
    fel_gt_watermark_text_color = fields.Char(string="Color del Texto de la Marca de Agua - FEL GT", help="Por favor, establece el color Hex para el texto de la marca de agua.", default="#2b4e99")
    fel_gt_watermark_text_font_size = fields.Integer('Tamaño de Fuente del Texto de la Marca de Agua (em) - FEL GT', default=4, help="Por favor, establece el tamaño de fuente del texto de la marca de agua.")
    fel_gt_report_footer_selection = fields.Selection(selection=[('standard', 'Estándar'), ('multi_columns', 'Pie de Página con Múltiples Columnas')], default='standard', string="Seleccionar Pie de Página del Informe - FEL GT", help="Selecciona el estilo del pie de página si deseas mostrarlo en el informe.")
    fel_gt_font_id = fields.Many2one('fel_gt.tools.report_fonts', string="Fuente del Informe - FEL GT", default=lambda self: self.fel_gt_get_font(), domain=[('mode', 'in', ('Normal', 'Regular', 'all', 'Book'))],
                            help="Establece la fuente en el encabezado del informe, se utilizará como fuente predeterminada en los informes inteligentes de la empresa del usuario.")
    fel_gt_font_size = fields.Integer('Tamaño de Fuente del Informe (px) - FEL GT', default=12, required=True)
    fel_gt_is_show_signature = fields.Boolean(string='Mostrar Firma - FEL GT', default=False, help="Por favor, márcalo si deseas mostrar la firma en el PDF.")
    fel_gt_signature = fields.Binary(string="Firma - FEL GT", default=lambda self: self.fel_gt_get_default_image(False, True), help="Por favor, sube la imagen de la firma para mostrarla en el informe.")
    fel_gt_logo_footer = fields.Binary("Logotipo del Pie de Página del Informe - FEL GT", help="Por favor, establece el logotipo del pie de página para el informe.")
    fel_gt_is_show_notes = fields.Boolean(string="Mostrar Notas - FEL GT", default=False, help="Por favor, márcalo si deseas mostrar notas de facturas, ventas y compras en el PDF.")
    fel_gt_is_show_payment_notes = fields.Boolean(string="Mostrar Notas de Pago - FEL GT", default=False, help="Por favor, márcalo si deseas mostrar notas de pago en el PDF.")
    fel_gt_is_show_barcode = fields.Boolean(string='Mostrar Código de Barras del Informe - FEL GT', default=False, help="Por favor, márcalo si deseas mostrar el código de barras en el PDF.")
    fel_gt_qr_code = fields.Boolean(string='Mostrar QR FEL - FEL GT', default=False, help="Por favor, márcalo si deseas mostrar el código QR en el PDF.")
    fel_gt_logo = fields.Boolean(string='Mostrar Logo FEL - FEL GT', default=False, help="Por favor, márcalo si deseas mostrar el logo de FEL en el PDF.")
    fel_gt_invoice_tax_column = fields.Boolean(string="Mostrar Columna de Impuestos - FEL GT")
    fel_gt_invoice_discount_column = fields.Boolean(string="Mostrar Columna de Descuento - FEL GT")
    
    fel_gt_invoice_hide_payments = fields.Boolean(string="Ocultar Pagos - FEL GT")
    fel_gt_invoice_hide_payment_status = fields.Boolean(string="Ocultar Estado de Pago - FEL GT")

    fel_gt_invoice_show_customer_code = fields.Boolean(string="Mostrar Código Cliente - FEL GT")
    fel_gt_invoice_show_invoice_ref = fields.Boolean(string="Mostrar Nombre Factura Interna - FEL GT")
    fel_gt_invoice_show_origin_order_name = fields.Boolean(string="Mostrar Pedido Origen - FEL GT")
    fel_gt_invoice_show_origin_order_date = fields.Boolean(string="Mostrar Fecha Pedido Origen - FEL GT")
    fel_gt_invoice_show_invoice_date_due = fields.Boolean(string="Mostrar Fecha Vencimiento - FEL GT")

    fel_gt_use_as_default_template = fields.Boolean(string="Usar como Plantilla Predeterminada - FEL GT", help="Por favor, márcalo si deseas establecer esta plantilla como predeterminada para todas las facturas.")

    def fel_gt_action_view_report_extra_content(self):
        fel_action = self.env.ref('multicert_felgt.action_fel_report_extracontent').read()[0]
        fel_action['domain'] = [('company_id', '=', self.id)]
        return fel_action

    @api.constrains('fel_gt_font_size', 'fel_gt_watermark_text_font_size')
    def fel_gt_check_font_size(self):
        if self.fel_gt_watermark_text_font_size <= 0 or self.fel_gt_watermark_text_font_size > 10:
            raise ValidationError(
                _('Por favor, introduce un tamaño de fuente del texto de la marca de agua mayor que 0 y menor que 10, de lo contrario tu informe será muy masivo.'))
        if self.fel_gt_font_size <= 10 or self.fel_gt_font_size >= 25:
            raise ValidationError(
                _('Por favor, introduce un tamaño de fuente mayor que 10 y menor que 25, de lo contrario tu informe será muy masivo.'))
