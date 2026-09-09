from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime
import base64
from lxml import etree
import requests
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    pdf_fel = fields.Char('PDF FEL', copy=False)

    def _post(self, soft=True):
        """Post del asiento con certificación FEL"""
        # Primero certificar si es necesario
        if self._certificar():
            return super(AccountMove, self)._post(soft)
        return super(AccountMove, self)._post(soft)

    def get_pdf_fel(self, pos_reference):
        """Obtiene el PDF de la factura FEL desde POS"""
        rec_pos = self.env['pos.order'].search([
            ('pos_reference', '=', pos_reference)
        ])

        if rec_pos and rec_pos[0].account_move:
            rec_account = rec_pos[0].account_move
            return rec_account.pdf_fel
        return False

    def post(self):
        """Post del asiento con certificación FEL"""
        if self._certificar():
            return super(AccountMove, self).post()
        return super(AccountMove, self).post()

    def _certificar(self):
        """Certifica la factura con el servicio de Infile"""
        for factura in self:
            # Verificar si requiere certificación
            if not hasattr(factura, 'requiere_certificacion') or not factura.requiere_certificacion():
                continue

            self.ensure_one()

            if factura.error_pre_validacion():
                return False

            # Generar DTE
            dte = factura.dte_documento()
            _logger.info("DTE generado: %s", dte)

            xmls = etree.tostring(dte, encoding="UTF-8")
            xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
            xmls_base64 = base64.b64encode(xmls)
            _logger.info("XML generado para firma")

            # Firmar el documento
            headers = {"Content-Type": "application/json"}
            data = {
                "llave": factura.company_id.token_firma_fel,
                "archivo": xmls_base64.decode("utf-8"),
                "codigo": factura.company_id.vat.replace('-', ''),
                "alias": factura.company_id.usuario_fel,
            }

            try:
                r = requests.post(
                    'https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml',
                    json=data,
                    headers=headers,
                    timeout=30
                )
                _logger.info("Respuesta de firma: %s", r.text)
                firma_json = r.json()

                if firma_json.get("resultado"):
                    # Certificar el documento
                    headers = {
                        "USUARIO": factura.company_id.usuario_fel,
                        "LLAVE": factura.company_id.clave_fel,
                        "IDENTIFICADOR": factura.journal_id.code + str(factura.id),
                        "Content-Type": "application/json",
                    }
                    data = {
                        "nit_emisor": factura.company_id.vat.replace('-', ''),
                        "correo_copia": factura.company_id.email or '',
                        "xml_dte": firma_json.get("archivo", ""),
                    }

                    r = requests.post(
                        "https://certificador.feel.com.gt/fel/certificacion/v2/dte/",
                        json=data,
                        headers=headers,
                        timeout=30
                    )
                    _logger.info("Respuesta de certificación: %s", r.json())
                    certificacion_json = r.json()

                    if certificacion_json.get("resultado"):
                        # Actualizar la factura con los datos de certificación
                        factura.firma_fel = certificacion_json.get("uuid", "")
                        factura.ref = str(certificacion_json.get("serie", "")) + "-" + str(certificacion_json.get("numero", ""))
                        factura.serie_fel = certificacion_json.get("serie", "")
                        factura.numero_fel = certificacion_json.get("numero", "")
                        factura.documento_xml_fel = xmls_base64
                        factura.resultado_xml_fel = certificacion_json.get("xml_certificado", "")
                        factura.pdf_fel = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid=" + certificacion_json.get("uuid", "")
                        factura.certificador_fel = "infile"
                    else:
                        # Manejar errores de certificación
                        error_msg = certificacion_json.get("descripcion_errores", "Error desconocido")
                        if hasattr(factura, 'error_certificador'):
                            factura.error_certificador(str(error_msg))
                        else:
                            _logger.error("Error en certificación: %s", error_msg)
                        return False
                else:
                    # Manejar errores de firma
                    error_msg = firma_json.get("mensaje", "Error en firma")
                    if hasattr(factura, 'error_certificador'):
                        factura.error_certificador(str(error_msg))
                    else:
                        _logger.error("Error en firma: %s", error_msg)
                    return False

            except requests.exceptions.RequestException as e:
                error_msg = f"Error de conexión con Infile: {str(e)}"
                if hasattr(factura, 'error_certificador'):
                    factura.error_certificador(error_msg)
                else:
                    _logger.error(error_msg)
                return False
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                if hasattr(factura, 'error_certificador'):
                    factura.error_certificador(error_msg)
                else:
                    _logger.error(error_msg)
                return False

        return True

    def button_cancel(self):
        """Cancela la factura y notifica a Infile si fue certificada"""
        result = super(AccountMove, self).button_cancel()

        for factura in self:
            if not hasattr(factura, 'requiere_certificacion') or not factura.requiere_certificacion():
                continue

            if factura.firma_fel:
                # Generar documento de anulación
                dte = factura.dte_anulacion()

                xmls = etree.tostring(dte, encoding="UTF-8")
                xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
                xmls_base64 = base64.b64encode(xmls)

                # Firmar anulación
                headers = {"Content-Type": "application/json"}
                data = {
                    "llave": factura.company_id.token_firma_fel,
                    "archivo": xmls_base64.decode("utf-8"),
                    "codigo": factura.company_id.vat.replace('-', ''),
                    "alias": factura.company_id.usuario_fel,
                    "es_anulacion": "S",
                }

                try:
                    r = requests.post(
                        'https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml',
                        json=data,
                        headers=headers,
                        timeout=30
                    )
                    _logger.info("Respuesta de firma anulación: %s", r.text)
                    firma_json = r.json()

                    if firma_json.get("resultado"):
                        # Enviar anulación al certificador
                        headers = {
                            "USUARIO": factura.company_id.usuario_fel,
                            "LLAVE": factura.company_id.clave_fel,
                            "IDENTIFICADOR": factura.journal_id.code + str(factura.id),
                            "Content-Type": "application/json",
                        }
                        data = {
                            "nit_emisor": factura.company_id.vat.replace('-', ''),
                            "correo_copia": factura.company_id.email or '',
                            "xml_dte": firma_json.get("archivo", ""),
                        }

                        r = requests.post(
                            "https://certificador.feel.com.gt/fel/anulacion/v2/dte/",
                            json=data,
                            headers=headers,
                            timeout=30
                        )
                        _logger.info("Respuesta de anulación: %s", r.text)
                        certificacion_json = r.json()

                        if not certificacion_json.get("resultado"):
                            raise UserError(str(certificacion_json.get("descripcion_errores", "Error en anulación")))
                    else:
                        raise UserError(firma_json.get("mensaje", "Error en firma de anulación"))

                except requests.exceptions.RequestException as e:
                    raise UserError(f"Error de conexión con Infile: {str(e)}")
                except Exception as e:
                    raise UserError(f"Error en anulación: {str(e)}")

        return result


class AccountJournal(models.Model):
    _inherit = "account.journal"
    # No se agregan campos adicionales en esta versión


class ResCompany(models.Model):
    _inherit = "res.company"

    usuario_fel = fields.Char('Usuario FEL')
    clave_fel = fields.Char('Clave FEL')
    token_firma_fel = fields.Char('Token Firma FEL')
