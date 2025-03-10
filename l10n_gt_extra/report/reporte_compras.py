# -*- coding: utf-8 -*-
#################################################################################
# Author      : Rodrigo Contreras (<mrdc.tech>)
# Copyright(c): 2024
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, models, fields
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_compras'
    _description = 'Report Compras'

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['compra'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['servicio'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['importacion'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['combustible'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['small_taxpayer'] = {'compra': 0, 'servicio': 0, 'combustible': 0, 'importacion':0,'total': 0}
        totales['compras'] = {'bienes': 0}
        totales['total'] = 0
        totales['resumen'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['pequenio_contribuyente'] = 0

        journal_ids = [x for x in datos['diarios_id']]
        tax_ids = [x for x in datos['impuesto_id']]
        
        facturas = self.sudo().env['account.move'].search([
            ('state', 'in', ['draft', 'posted']),
            ('journal_id', 'in', journal_ids),
            ('date', '<=', datos['fecha_hasta']),
            ('date', '>=', datos['fecha_desde']),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('company_id', '=', datos['company_id'][0]),
        ], order='invoice_date, payment_reference')

        lineas = []
        for f in facturas:

            proveedor = f.partner_id.name
            nit = f.partner_id.vat

            totales['num_facturas'] += 1

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                if 'conversion_rate_ref' in self.env['account.move']._fields:
                    if f.conversion_rate_ref > 0:
                        tipo_cambio = f.conversion_rate_ref
                else:
                    if f.amount_total_signed and f.amount_total_in_currency_signed:
                        tipo_cambio = abs(f.amount_total_signed / f.amount_total_in_currency_signed)
                    if not tipo_cambio or tipo_cambio == 1:
                        tipo_cambio = f.currency_id.with_context(date=f.invoice_date).rate

            tipo = 'FACT'
            if f.move_type != 'in_invoice':
                tipo = 'NC'
            if f.partner_id.pequenio_contribuyente:
                tipo += '_PEQ'
            if f.type_invoice == 'FESP':
                tipo = 'FES'
            if f.tipo_gasto == 'importacion':
                tipo = 'DA'
            if f.journal_id.is_receipt_journal == True:
                tipo = 'REC'

            linea = {
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.invoice_date,
                'serie': f.provider_invoice_serial or '',
                'numero': f.provider_invoice_number or '',
                'proveedor': proveedor,
                'nit': nit,
                'compra': 0,
                'compra_exento': 0,
                'servicio': 0,
                'servicio_exento': 0,
                'combustible': 0,
                'combustible_exento': 0,
                'importacion': 0,
                'importacion_exento': 0,
                'importacion_iva': 0,
                'compra_iva': 0,
                'servicio_iva': 0,
                'combustible_iva': 0,
                'small_taxpayer_amount': 0,
                'base': 0,
                'iva': 0,
                'subtotal_exento': 0,
                'total': 0
            }
            is_compra = False
            is_service = False
            is_mix = False
            is_import = False
            is_gas = False
            flag_gas = False
            signo = 1
            for linea_factura in f.invoice_line_ids:

                precio = (linea_factura.price_unit *
                        (1-(linea_factura.discount or 0.0)/100.0)) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1
                    signo = -1
                tipo_linea = f.tipo_gasto
                
                if linea_factura.product_id.product_tmpl_id.type == 'service':
                    tipo_linea = 'servicio'

                if linea_factura.tax_ids:
                    for tax in linea_factura.tax_ids:
                        if tax.sat_tax_type == 'gas':
                            if is_compra or is_service:
                                is_mix = True
                                flag_gas = True
                            else:
                                is_gas = True
                                flag_gas = True
                    if flag_gas:
                        flag_gas = False

                if f.tipo_gasto == 'mixto':

                    tipo_linea = 'compra'
                    if linea_factura.product_id:
                        if linea_factura.product_id.product_tmpl_id.type == 'service':
                            tipo_linea = 'servicio'
                    if is_gas:
                        tipo_linea = 'combustible'

                if f.tipo_gasto == 'combustible':
                    tipo_linea = 'combustible'

                r = linea_factura.tax_ids._origin.compute_all(precio, currency=f.currency_id, quantity=linea_factura.quantity, product=linea_factura.product_id, partner=f.partner_id)

                base_price = linea_factura.price_subtotal * signo
                if f.currency_id.id != f.company_id.currency_id.id:
                    base_price = linea_factura.price_subtotal * tipo_cambio
                linea['base'] += base_price
                totales[tipo_linea]['total'] += base_price

                if len(linea_factura.tax_ids) > 0:
                    linea[tipo_linea] += base_price
                    if tipo_linea == 'compra':
                        totales['compras']['bienes'] += base_price
                    totales[tipo_linea]['neto'] += base_price
                    totales['resumen']['neto'] += base_price
                    for i in r['taxes']:
                        if i['id'] in tax_ids:
                            linea['iva'] += i['amount']
                            linea[tipo_linea+'_iva'] += i['amount']
                            totales[tipo_linea]['iva'] += i['amount']
                            totales['resumen']['iva'] += i['amount']
                            totales[tipo_linea]['total'] += i['amount']
                        elif i['amount'] > 0:
                            if tipo_linea == 'combustible':
                                linea[tipo_linea+'_exento'] += i['amount']
                                linea['subtotal_exento'] += i['amount']
                                totales[tipo_linea]['exento'] += i['amount']
                                totales[tipo_linea]['total'] += i['amount']
                            else:
                                linea[tipo_linea+'_exento'] += i['amount']
                                totales[tipo_linea]['exento'] += i['amount']
                                totales[tipo_linea]['total'] += i['amount']
                                linea['subtotal_exento'] += i['amount']
                            totales['resumen']['exento'] += i['amount']
                else:

                    if f.partner_id.pequenio_contribuyente:
                        linea['small_taxpayer_amount'] += base_price
                        totales['small_taxpayer'][tipo_linea] += base_price
                        totales['small_taxpayer']["total"] += base_price
                        totales['pequenio_contribuyente'] += base_price
                    else:
                        linea['subtotal_exento'] += base_price
                        linea[tipo_linea+'_exento'] += base_price
                        totales[tipo_linea]['exento'] += base_price
                        totales['resumen']['exento'] += base_price
                        totales[tipo_linea]['total'] += base_price

                linea['total'] += precio * linea_factura.quantity
                totales['total'] += precio * linea_factura.quantity
                    
            lineas.append(linea)
        return {'lineas': lineas, 'totales': totales}
        
    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        company = self.env['res.company'].browse(data['company_id'])
        diario = self.env['account.journal'].browse(data['form']['diarios_id'][0])
        
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'company_id': company
        }