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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlwt
import base64
import io
import json
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AsistenteReporteVentas(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_ventas'
    _description = 'Asistente Report Ventas'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True, domain="[('type','in',['sale','sale_refund']),('company_id','=',company_id)]")
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True, domain="[('type_tax_use', '=', 'sale'),('company_id','=',company_id)]")
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    resumido = fields.Boolean(string="Resumido")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'diarios_id': [(5, 0, 0)], 'impuesto_id': False})

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_ventas',
             'form': self.read()[0],
             'company_id': self.company_id.id
        }
        return self.env.ref('l10n_gt_extra.action_reporte_ventas').report_action(self, data=data)
    
    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'l10n_gt_extra.asistente_reporte_ventas',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro de Ventas',
                     },
            'report_type': 'l10n_gt_extra_xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data_lines = self.env['report.l10n_gt_extra.reporte_ventas'].lineas(data)
        sheet = workbook.add_worksheet('Libro de Ventas')
        sheet.set_column('A2:A2', 1)
        sheet.set_column('B2:B2', 5)
        sheet.set_column('C2:C2', 15)
        sheet.set_column('D2:D2', 15)
        sheet.set_column('E8:E8', 15)
        sheet.set_column('F8:F8', 15)
        sheet.set_column('G2:G2', 13)
        sheet.set_column('H2:H2', 45)
        if data['resumido']:
            sheet.set_column('H2:H2', 13)
        #sheet.set_column('H2:H2', 13)
        sheet.set_column('I2:I2', 13)
        sheet.set_column('J2:J2', 13)
        sheet.set_column('K2:K2', 13)
        sheet.set_column('L2:L2', 13)
        sheet.set_column('M2:M2', 13)
        sheet.set_column('N2:N2', 13)
        sheet.set_column('O2:O2', 13)
        sheet.set_column('P2:P2', 1)
        sheet.set_row(1, 35)
        sheet.set_row(10, 35)
        sheet.freeze_panes(11, 0)


        title_center = workbook.add_format({'bold':True, 'font_name': 'Arial', 'font_size': 20, 'font_color': 'black', 'align': 'center'})
        title_left = workbook.add_format({'bold':True, 'font_name': 'Arial', 'font_size': 20, 'font_color': 'black', 'align': 'left'})
        subtitle_center = workbook.add_format({'font_name': 'Arial', 'font_size': 17, 'font_color': 'black', 'align': 'center','right': 1, 'left': 1, 'top': 1, 'bottom': 1})
        date_tile = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'font_color': 'black', 'align': 'left', 'bold': True})
        date_middle = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'font_color': 'black', 'align': 'center', 'bold': True})
        date_subtitle = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'font_color': 'black', 'align': 'right', 'num_format': 'dd/mm/yy'})
        subtitle_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        titule_center_u = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'font_color': 'black', 'align': 'center'})
        header_center = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'right', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_center = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_total = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        date_format= workbook.add_format({ 'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center','num_format': 'dd/mm/yy', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' })
        amount_format = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' ,'num_format': 'Q ###,##0.00','align': 'right'})
        folio_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom':1, 'valign': 'vcenter'})
        amount_format_bold = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' ,'num_format': 'Q ###,##0.00','align': 'right'})

        company_data = self.env['res.company'].browse(data['company_id'][0])

        sheet.merge_range('B3:O4', company_data.name, title_center)
        sheet.merge_range('B5:O6', 'NIT: '+company_data.vat, subtitle_center)
        sheet.merge_range('B7:O8', 'Registro de Libro de Ventas y Servicios', subtitle_center)

        sheet.merge_range('B9:C9', 'Registro del:', date_tile)
        sheet.write('D9', data['fecha_desde'], date_subtitle)
        sheet.write('E9', 'al', date_middle)
        sheet.write('F9', data['fecha_hasta'], date_subtitle)
        sheet.write('O9', 'Folio: ' + str(data['folio_inicial']), folio_data)

        sheet.merge_range('C10:F10', 'Documento', header_center)
        sheet.merge_range('G10:H10', 'Cliente', header_center)
        sheet.merge_range('I10:L10', 'Ventas', header_center)
        sheet.merge_range('M10:O10', 'Total', header_center)

        sheet.merge_range('B10:B11', 'No.', header_center)
        sheet.write('C11', 'Fecha', header_center)
        sheet.write('D11', 'Tipo', header_center)
        sheet.write('E11', 'Serie', header_center)
        sheet.write('F11', 'Número', header_center)
        if data['resumido']:
            sheet.merge_range('E11:F11', 'Rango Documentos', header_center)
        sheet.write('G11', 'NIT', header_center)
        sheet.write('H11', 'Nombre', header_center)
        sheet.write('I11', 'Exportaciones', header_center)
        sheet.write('J11', 'Bienes', header_center)
        sheet.write('K11', 'Servicios', header_center)
        sheet.write('L11', 'Exentas', header_center)
        sheet.write('M11', 'IVA', header_center)
        sheet.write('N11', 'Venta Neta', header_center)
        sheet.write('O11', 'Total', header_center)

        previous_establishment = ''
        row_number = 12
        line_counter = 1
        count_page = 12
        folio = data['folio_inicial'] + 1
        for line in data_lines['lineas']:
            if line['establecimiento'] != previous_establishment:
                if line_counter != 1:
                    sheet.merge_range('B'+str(row_number)+':H'+str(row_number), 'Total establecimiento', data_total)
                    sheet.write('I'+str(row_number), total_establishment['importacion'], amount_format_bold)
                    sheet.write('J'+str(row_number), total_establishment['compra'], amount_format_bold)
                    sheet.write('K'+str(row_number), total_establishment['servicio'], amount_format_bold)
                    sheet.write('L'+str(row_number), total_establishment['total_exento'], amount_format_bold)
                    sheet.write('M'+str(row_number), total_establishment['iva'], amount_format_bold)
                    sheet.write('N'+str(row_number), total_establishment['base'], amount_format_bold)
                    sheet.write('O'+str(row_number), total_establishment['total'], amount_format_bold)
                    row_number +=1
                total_establishment = {'importacion':0 , 'compra':0, 'servicio':0, 'total_exento':0, 'iva':0, 'base':0, 'total':0}
                if not data['resumido']:
                    sheet.merge_range('B'+str(row_number)+':O'+str(row_number), 'Establecimiento: '+str(line['establecimiento']), subtitle_center)
                else:
                    sheet.merge_range('B'+str(row_number)+':O'+str(row_number), 'Establecimiento: '+str(line['establecimiento'][0]), subtitle_center)
                row_number +=1
                previous_establishment = line['establecimiento']

            sheet.write('B'+str(row_number), line_counter, data_right)
            sheet.write('C'+str(row_number), line['fecha'], date_format)
            sheet.write('D'+str(row_number), line['tipo'], data_left)
            if not data['resumido']:
                sheet.write('E'+str(row_number), line['serie'] if line['serie'] else '', data_left)
                sheet.write('F'+str(row_number), line['numero'] if line['numero'] else '', data_left)
            else:
                sheet.merge_range('E'+str(row_number)+':F'+str(row_number), line['numero'] if line['numero'] else '', data_left)
            sheet.write('G'+str(row_number), line['nit'] if line['nit'] else "-", data_left)
            sheet.write('H'+str(row_number), line['cliente'], data_left)
            sheet.write('I'+str(row_number), line['importacion'], amount_format)
            sheet.write('J'+str(row_number), line['compra'], amount_format)
            sheet.write('K'+str(row_number), line['servicio'], amount_format)
            sheet.write('L'+str(row_number), line['total_extento'], amount_format)
            sheet.write('M'+str(row_number), line['iva'], amount_format)
            sheet.write('N'+str(row_number), line['base'], amount_format)
            sheet.write('O'+str(row_number), line['total'], amount_format)

            if line['estado'] != 'cancel':
                total_establishment['importacion'] += line['importacion']
                total_establishment['compra'] += line['compra']
                total_establishment['servicio'] += line['servicio']
                total_establishment['total_exento'] += line['total_extento']
                total_establishment['iva'] += line['iva']
                total_establishment['base'] += line['base']
                total_establishment['total'] += line['total']

            line_counter += 1
            row_number += 1
            count_page += 1
            if count_page == 60:
                row_number += 1
                sheet.write('O'+str(row_number), 'Folio: ' + str(folio), folio_data)
                folio += 1
                row_number += 1
                count_page = 2

        if data_lines['lineas']:
            sheet.merge_range('B'+str(row_number)+':H'+str(row_number), 'Total establecimiento', data_total)
            sheet.write('I'+str(row_number), total_establishment['importacion'], amount_format_bold)
            sheet.write('J'+str(row_number), total_establishment['compra'], amount_format_bold)
            sheet.write('K'+str(row_number), total_establishment['servicio'], amount_format_bold)
            sheet.write('L'+str(row_number), total_establishment['total_exento'], amount_format_bold)
            sheet.write('M'+str(row_number), total_establishment['iva'], amount_format_bold)
            sheet.write('N'+str(row_number), total_establishment['base'], amount_format_bold)
            sheet.write('O'+str(row_number), total_establishment['total'], amount_format_bold)
            row_number += 1

        sheet.merge_range('B'+str(row_number)+':H'+str(row_number), 'Totales', data_total)
        total_iva = data_lines['totales']['compra']['iva'] + data_lines['totales']['servicio']['iva']  + data_lines['totales']['importacion']['iva']
        total_exento = data_lines['totales']['servicio']['exento'] + data_lines['totales']['importacion']['exento'] + data_lines['totales']['compra']['exento']
        sheet.write('I'+str(row_number), data_lines['totales']['importacion']['neto'], amount_format_bold)
        sheet.write('J'+str(row_number), data_lines['totales']['compra']['neto'], amount_format_bold)
        sheet.write('K'+str(row_number), data_lines['totales']['servicio']['neto'], amount_format_bold)
        #sheet.write('L'+str(row_number), data_lines['totales']['combustible']['neto'], amount_format_bold)
        sheet.write('L'+str(row_number), total_exento, amount_format_bold)
        sheet.write('M'+str(row_number), total_iva, amount_format_bold)
        sheet.write('N'+str(row_number), data_lines['totales']['venta_neta'], amount_format_bold)
        sheet.write('O'+str(row_number), data_lines['totales']['compra']['total'] + data_lines['totales']['servicio']['total'] + data_lines['totales']['importacion']['total'], amount_format_bold)

        sheet.set_paper(1)
        sheet.set_landscape()
        sheet.print_area('A1:P'+str(row_number+1))
        list_row = []
        for x in range(60, row_number, 60):
            list_row.append(x)
        sheet.set_v_pagebreaks([16])
        sheet.set_h_pagebreaks(list_row)
        sheet.set_page_view()

        #####################
        # Hoja de Resumen   #
        #####################
        sheet2 = workbook.add_worksheet('Resumen')
        sheet2.merge_range('B3:E4', 'Resumen', title_left)

        sheet2.set_column('A2:A2', 1)
        sheet2.set_column('B2:B2', 15)
        sheet2.set_column('C2:C2', 12)
        sheet2.set_column('D2:D2', 12)
        sheet2.set_column('E8:E8', 12)
        sheet2.set_column('F2:F2', 12)
        sheet2.set_column('G2:G2', 12)

        sheet2.merge_range('B6:D6', 'Cantidad de Facturas:', data_left)
        sheet2.merge_range('B7:D7', 'Total Débito Fiscal:', data_left)
        sheet2.write('E6', data_lines['totales']['num_facturas'], data_right)
        sheet2.write('E7', data_lines['totales']['compra']['iva'] + data_lines['totales']['servicio']['iva'] + data_lines['totales']['importacion']['iva'], amount_format)

        #ENCABEZADO RESUMEN
        sheet2.write('B11', '', header_center)
        sheet2.write('C11', 'Exento', header_center)
        sheet2.write('D11', 'Neto', header_center)
        sheet2.write('E11', 'IVA', header_center)
        sheet2.write('F11', 'Total', header_center)

        #COMPRAS
        sheet2.write('B12', 'Bienes', subtitle_left)
        sheet2.write('C12', data_lines['totales']['compra']['exento'], amount_format)
        sheet2.write('D12', data_lines['totales']['compra']['neto'], amount_format)
        sheet2.write('E12', data_lines['totales']['compra']['iva'], amount_format)
        sheet2.write('F12', data_lines['totales']['compra']['total'], amount_format)

        #SERVICIOS
        sheet2.write('B13', 'Servicios', subtitle_left)
        sheet2.write('C13', data_lines['totales']['servicio']['exento'], amount_format)
        sheet2.write('D13', data_lines['totales']['servicio']['neto'], amount_format)
        sheet2.write('E13', data_lines['totales']['servicio']['iva'], amount_format)
        sheet2.write('F13', data_lines['totales']['servicio']['total'], amount_format)

        #IMPORTACIONES
        sheet2.write('B14', 'Exportaciones', subtitle_left)
        sheet2.write('C14', data_lines['totales']['importacion']['exento'], amount_format)
        sheet2.write('D14', data_lines['totales']['importacion']['neto'], amount_format)
        sheet2.write('E14', data_lines['totales']['importacion']['iva'], amount_format)
        sheet2.write('F14', data_lines['totales']['importacion']['total'], amount_format)

        #TOTALES
        total_exento = data_lines['totales']['compra']['exento'] + data_lines['totales']['servicio']['exento'] + data_lines['totales']['importacion']['exento']
        total_neto = data_lines['totales']['compra']['neto'] + data_lines['totales']['servicio']['neto'] + data_lines['totales']['importacion']['neto']
        total_iva = data_lines['totales']['compra']['iva'] + data_lines['totales']['servicio']['iva'] + data_lines['totales']['importacion']['iva']
        total = data_lines['totales']['compra']['total'] + data_lines['totales']['servicio']['total'] + data_lines['totales']['importacion']['total']
        sheet2.write('B15', 'Totales', subtitle_left)
        sheet2.write('C15', total_exento, amount_format)
        sheet2.write('D15', total_neto, amount_format)
        sheet2.write('E15', total_iva, amount_format)
        sheet2.write('F15', total, amount_format)

        #RESUMEN CONSTANCIAS
        sheet2.merge_range('B19:F19', 'Resumen Constancias', header_center)
        sheet2.write('B20', 'Cantidad', header_center)
        sheet2.merge_range('C20:E20', 'Tipo de Constancia', header_center)
        sheet2.write('F20', 'Total', header_center)
        sheet2.write('B21', data_lines['totales']['extension_iva']['cant'], data_right)
        sheet2.merge_range('C21:E21', 'Contancia de Extención de IVA', data_center)
        sheet2.write('F21', data_lines['totales']['extension_iva']['total'], amount_format)
        sheet2.write('B22', data_lines['totales']['retencion_iva']['cant'], data_right)
        sheet2.merge_range('C22:E22', 'Contancia de Retención de IVA', data_center)
        sheet2.write('F22', data_lines['totales']['retencion_iva']['total'], amount_format)

        sheet.hide_gridlines(2)
        sheet2.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()