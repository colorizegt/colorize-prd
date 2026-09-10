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
from datetime import datetime

class AsistenteReporteDiario(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_diario'
    _description = 'Asistente Report Diario'

    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')
        else:
            return self.env['account.account'].search([]).ids

    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)
    cuentas_id = fields.Many2many("account.account", string="Cuentas",required=True, default=_default_cuenta, domain="[('company_id','=',company_id)]")
    folio_inicial = fields.Integer(string="Folio Inicial",required=True, default=1)
    agrupado_por_dia = fields.Boolean(string="Agrupado por dia")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True,default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))

    currency_id = fields.Many2one('res.currency',string="Moneda", default=lambda self: self.env.company.currency_id.id)
    

    all_accounts = fields.Boolean(string="Todas las cuentas")
    grouping_type = fields.Selection([
        ('monthly', 'Mensual'),
        ('daily','Día'),
        ('transaction', 'Transacción')

    ],string="Tipo de Agrupación", default="monthly")

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'cuentas_id': [(5, 0, 0)], 'all_accounts': False})

    @api.onchange('all_accounts')
    def onchange_all_accounts(self):
        if self.all_accounts == True:
            for rec in self:
                account_data = self.env['account.account'].search([('company_id','=',self.company_id.id)])
                for account in account_data:
                    rec.cuentas_id = [(4, account.id)] 
        if self.all_accounts == False:
            for rec in self:
                rec.cuentas_id = False
            
    
    def print_report(self):
        form_data = []
        if self.read():
            form_data = self.read()[0]
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_diario',
             'form': form_data,
             'company_id': self.company_id
        }
        return self.env.ref('l10n_gt_extra.action_reporte_diario').report_action(self, data=data)
    
    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'l10n_gt_extra.asistente_reporte_diario',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro Diario',
                     },
            'report_type': 'l10n_gt_extra_xlsx'
        }
    
    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        dict = {}
        dict['fecha_hasta'] = data['fecha_hasta']
        dict['fecha_desde'] = data['fecha_desde']
        dict['agrupado_por_dia'] = data['agrupado_por_dia']
        dict['cuentas_id'] = data['cuentas_id']
        dict['grouping_type'] = data['grouping_type']
        dict['company_id'] = data['company_id']
        grouping_type = data['grouping_type']
        report_data = self.env['report.l10n_gt_extra.reporte_diario'].excel_lines(dict)

        company_data = self.env['res.company'].browse(data['company_id'][0])
        fecha_desde = datetime.strptime(data['fecha_desde'], '%Y-%m-%d')
        fecha_hasta = datetime.strptime(data['fecha_hasta'], '%Y-%m-%d')
        start_date_label = str(fecha_desde.day).zfill(2) + '/' + str(fecha_desde.month).zfill(2) + '/' + str(fecha_desde.year)
        end_date_label = str(fecha_hasta.day).zfill(2) + '/' + str(fecha_hasta.month).zfill(2) + '/' + str(fecha_hasta.year)
        
        
        sheet = workbook.add_worksheet('Libro Diario')
        sheet.set_column('A1:A1', 2)
        sheet.set_column('B1:B1', 12)
        sheet.set_column('C1:C1', 12)
        sheet.set_column('D1:D1', 12)
        sheet.set_column('E1:E1', 12)
        sheet.set_column('F1:F1', 12)
        sheet.set_column('G1:G1', 12)
        sheet.set_column('H1:H1', 12)
        sheet.set_column('I1:I1', 12)
        sheet.set_column('J1:J1', 12)
        sheet.set_column('K1:B1', 12)
        sheet.set_column('L1:L1', 12)
        sheet.set_column('M1:M1', 12)
        sheet.set_column('N1:N1', 12)
        sheet.set_column('O1:O1', 12)
        sheet.set_column('P1:P1', 12)
        sheet.set_column('Q1:Q1', 12)
        sheet.set_column('R1:R1', 12)
        sheet.set_column('S1:S1', 12)
        sheet.set_column('T1:T1', 2)
        sheet.set_default_row(14)
        
        title_label_font_size = 12
        title_center = workbook.add_format({'font_name': 'Arial', 'font_size': 16, 'font_color': 'black', 'align': 'center'})
        title_labels = workbook.add_format({'font_name': 'Arial', 'font_size': title_label_font_size,  'bold': True, 'font_color': 'black', 'align': 'right'})
        months_labels = workbook.add_format({'font_name': 'Arial', 'font_size': title_label_font_size,  'bold': True, 'font_color': 'black', 'align': 'left'})
        date_labels = workbook.add_format({'font_name': 'Arial', 'font_size': title_label_font_size,  'bold': True, 'font_color': 'black', 'align': 'right'})
        title_labels_value = workbook.add_format({'font_name': 'Arial', 'font_size': title_label_font_size,  'bold': False, 'font_color': 'black', 'align': 'left'})
        
        data_font_size = 10
        total_font_size = 11
        header_center = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        header_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})        
        header_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'right', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_center = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'center', 'right': 0, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 0, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_left_border_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 0, 'left': 1, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_center_border_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'center', 'right': 0, 'left': 1, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter', 'num_format': '#,##0.00'})
        data_left_border_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        top_border = workbook.add_format({'top': 1})
        top_border_right = workbook.add_format({'top': 1, 'font_size': data_font_size, 'align': 'right'})
        top_border_number_total = workbook.add_format({'top': 1, 'bold': False, 'num_format': '#,##0.00', 'font_size': data_font_size})
        total_report_label = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'left'})
        total_report = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'right'})
        folio_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom':0, 'valign': 'vcenter'})
        
        sheet.merge_range('B2:C2', 'Nombre Fiscal: ', title_labels)
        sheet.merge_range('D2:H2', company_data.company_registry, title_labels_value)
        sheet.write('P2', 'Folio: ', title_labels)
        sheet.write('Q2', data['folio_inicial'], title_labels_value)        
        sheet.merge_range('B3:C3', 'NIT: ', title_labels)
        sheet.merge_range('D3:H3', company_data.vat, title_labels_value)
        sheet.write('P3', 'Moneda: ', title_labels)
        sheet.merge_range('Q3:S3', company_data.currency_id.currency_unit_label + ' ' + company_data.currency_id.name, title_labels_value)
        sheet.merge_range('B4:C4', 'Dirección: ', title_labels)
        sheet.merge_range('D4:H4', company_data.street, title_labels_value)
        # Title
        sheet.merge_range('B7:S7', 'Libro Diario', title_center)
        # Dates
        sheet.write('B9', 'Desde: ', title_labels)
        sheet.merge_range('C9:D9', start_date_label, title_labels_value)
        sheet.write('E9', 'Hasta: ', title_labels)
        sheet.merge_range('F9:G9', end_date_label, title_labels_value)
        
        row_index = 11
        grouping_data = []
        index_name = ""
        index_total_credit = ""
        index_total_debit = ""
        if grouping_type == "monthly":
            grouping_data = report_data['meses']
            index_name = 'month_name'
            index_total_credit = 'month_total_credit'
            index_total_debit = 'month_total_debit'
        
        if grouping_type == "daily":
            grouping_data = report_data['fechas']
            index_name = 'daily_date'
            index_total_credit = 'daily_total_credit'
            index_total_debit = 'daily_total_debit'
            
        if grouping_type == "transaction":
            grouping_data = report_data['move_line_ids']
            index_name = 'poliza'
            index_total_credit = 'transaction_total_credit'
            index_total_debit = 'transaction_total_debit'
        
        if grouping_type == "transaction":
            count_page = 11
            folio = int(data['folio_inicial'])
            for group_data in grouping_data:
                #folio status
                if count_page >= 56:
                    folio += 1
                    temp_row = 0 
                    if count_page == 62:
                        temp_row -= 1
                    if count_page == 60:
                        temp_row += 1
                    if count_page == 59:
                        temp_row += 1 
                        temp_row += 1
                    if count_page == 58:
                        temp_row += 1
                        temp_row += 1                       
                        temp_row += 1
                    if count_page == 57:
                        temp_row += 1
                        temp_row += 1
                        temp_row += 1 
                        temp_row += 1
                    if count_page == 56:
                        temp_row += 1
                        temp_row += 1
                        temp_row += 1
                        temp_row += 1
                        temp_row += 1
                    row_index = row_index + temp_row
                    sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                    sheet.write('Q'+str(row_index), str(folio), folio_data)
                    row_index += 1
                    count_page = 2           
                    
                sheet.merge_range('B'+str(row_index)+':E'+str(row_index), 'Póliza:' + group_data[index_name], months_labels)                
                sheet.write('L'+str(row_index), 'Fecha: ', date_labels)
                sheet.write('M'+str(row_index), group_data['transaction_date'], months_labels)
                row_index += 1
                count_page += 1
                sheet.merge_range('B'+str(row_index)+':C'+str(row_index), 'Fecha', header_center)
                sheet.merge_range('D'+str(row_index)+':E'+str(row_index), 'Código', header_left)
                sheet.merge_range('F'+str(row_index)+':H'+str(row_index), 'Cuenta', header_left)
                sheet.merge_range('I'+str(row_index)+':K'+str(row_index), 'Descripcion', header_left)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), 'Debe', header_right)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), 'Haber', header_right)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), 'Referencia bancaria', header_left)                
                row_index += 1
                count_page += 1
                
                for line_data in  group_data['group_data']:
                    sheet.merge_range('B'+str(row_index)+':C'+str(row_index), line_data['fecha_movimiento'], data_center_border_left)
                    sheet.merge_range('D'+str(row_index)+':E'+str(row_index), line_data['codigo'], data_left)
                    sheet.merge_range('F'+str(row_index)+':H'+str(row_index), str(line_data['cuenta']), data_left)
                    sheet.merge_range('I'+str(row_index)+':K'+str(row_index), line_data['name'], data_right)
                    sheet.merge_range('L'+str(row_index)+':M'+str(row_index), line_data['debe'], data_right)
                    sheet.merge_range('N'+str(row_index)+':O'+str(row_index), line_data['haber'], data_right)
                    sheet.merge_range('P'+str(row_index)+':S'+str(row_index), line_data['referencia'], data_left_border_right)                
                    row_index += 1
                    count_page += 1
                
                sheet.merge_range('B'+str(row_index)+':C'+str(row_index), '', top_border)
                sheet.merge_range('D'+str(row_index)+':E'+str(row_index), '', top_border)
                sheet.merge_range('F'+str(row_index)+':K'+str(row_index), 'Total: ', top_border_right)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), group_data[index_total_debit], top_border_number_total)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), group_data[index_total_credit], top_border_number_total)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), '', top_border)                
                
                row_index += 2
                count_page += 2
            
            sheet.merge_range('F'+str(row_index)+':H'+str(row_index), 'Totales: ', total_report)
            sheet.merge_range('I'+str(row_index)+':J'+str(row_index), report_data['totales']['total_debe'], total_report)
            sheet.merge_range('K'+str(row_index)+':L'+str(row_index), report_data['totales']['total_haber'], total_report)
                
        if grouping_type == "monthly":
            
            for group_data in grouping_data:
                sheet.merge_range('B'+str(row_index)+':E'+str(row_index), group_data[index_name], months_labels)
                row_index += 1
                sheet.write('B'+str(row_index), 'Fecha', header_center)
                sheet.write('C'+str(row_index), 'Código', header_left)
                sheet.merge_range('D'+str(row_index)+':F'+str(row_index), 'Cuenta', header_left)
                sheet.merge_range('G'+str(row_index)+':I'+str(row_index), 'Descripcion', header_left)
                sheet.merge_range('J'+str(row_index)+':K'+str(row_index), 'Debe', header_right)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), 'Haber', header_right)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), 'No. Póliza', header_left)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), 'Referencia bancaria', header_left)                
                row_index += 1
                count_page = 12
                folio = int(data['folio_inicial']) + 1
                for line_data in  group_data['group_data']:
                    sheet.write('B'+str(row_index), line_data['fecha_movimiento'], data_center_border_left)
                    sheet.write('C'+str(row_index), line_data['codigo'], data_left)
                    sheet.merge_range('D'+str(row_index)+':F'+str(row_index), line_data['cuenta'], data_left)
                    sheet.merge_range('G'+str(row_index)+':I'+str(row_index), line_data['name'], data_right)
                    sheet.merge_range('J'+str(row_index)+':K'+str(row_index), line_data['debe'], data_right)
                    sheet.merge_range('L'+str(row_index)+':M'+str(row_index), line_data['haber'], data_right)
                    sheet.merge_range('N'+str(row_index)+':O'+str(row_index), line_data['poliza'], data_left)
                    sheet.merge_range('P'+str(row_index)+':S'+str(row_index), line_data['descripcion'], data_left_border_right)
                    row_index += 1
                    count_page += 1
                    if count_page == 60:
                        row_index += 1
                        sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                        sheet.write('Q'+str(row_index), str(folio), folio_data)
                        folio += 1
                        row_index += 1
                        count_page = 2
                sheet.write('B'+str(row_index), '', top_border)
                sheet.write('C'+str(row_index), '', top_border)
                sheet.merge_range('D'+str(row_index)+':I'+str(row_index), 'Total: ', top_border_right)
                sheet.merge_range('J'+str(row_index)+':K'+str(row_index), group_data[index_total_debit], top_border_number_total)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), group_data[index_total_credit], top_border_number_total)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), '', top_border)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), '', top_border)                
                row_index += 2
            sheet.merge_range('D'+str(row_index)+':I'+str(row_index), 'Totales: ', total_report)
            sheet.merge_range('J'+str(row_index)+':K'+str(row_index), report_data['totales']['total_debe'], total_report)
            sheet.merge_range('L'+str(row_index)+':M'+str(row_index), report_data['totales']['total_haber'], total_report)
            
        if grouping_type == "daily":
            count_page = 12
            folio = int(data['folio_inicial']) + 1
            for group_data in grouping_data:
                sheet.merge_range('B'+str(row_index)+':E'+str(row_index), group_data[index_name], months_labels)
                row_index += 1
                count_page += 1
                if count_page == 60:
                    row_index += 2
                    sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                    sheet.write('Q'+str(row_index), str(folio), folio_data)
                    folio += 1
                    row_index += 1
                    count_page = 3
                sheet.write('B'+str(row_index), 'Fecha', header_center)
                sheet.write('C'+str(row_index), 'Código', header_left)
                sheet.merge_range('D'+str(row_index)+':F'+str(row_index), 'Cuenta', header_left)
                sheet.merge_range('G'+str(row_index)+':I'+str(row_index), 'Descripcion', header_left)
                sheet.merge_range('J'+str(row_index)+':K'+str(row_index), 'Debe', header_right)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), 'Haber', header_right)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), 'No. Póliza', header_left)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), 'Referencia bancaria', header_left) 
                row_index += 1
                count_page += 1
                if count_page == 60:
                    row_index += 2
                    sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                    sheet.write('Q'+str(row_index), str(folio), folio_data)
                    folio += 1
                    row_index += 1
                    count_page = 3
                for line_data in  group_data['group_data']:
                    sheet.write('B'+str(row_index), line_data['fecha_movimiento'], data_center_border_left)
                    sheet.write('C'+str(row_index), line_data['codigo'], data_left)
                    sheet.merge_range('D'+str(row_index)+':F'+str(row_index), line_data['cuenta'], data_left)
                    sheet.merge_range('G'+str(row_index)+':I'+str(row_index), line_data['name'], data_right)
                    sheet.merge_range('J'+str(row_index)+':K'+str(row_index), line_data['debe'], data_right)
                    sheet.merge_range('L'+str(row_index)+':M'+str(row_index), line_data['haber'], data_right)
                    sheet.merge_range('N'+str(row_index)+':O'+str(row_index), line_data['poliza'], data_left)
                    sheet.merge_range('P'+str(row_index)+':S'+str(row_index), line_data['descripcion'], data_left_border_right)                
                    row_index += 1
                    count_page += 1
                    if count_page == 60:
                        row_index += 2
                        sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                        sheet.write('Q'+str(row_index), str(folio), folio_data)
                        folio += 1
                        row_index += 1
                        count_page = 3
                sheet.write('B'+str(row_index), '', top_border)
                sheet.write('C'+str(row_index), '', top_border)
                sheet.merge_range('D'+str(row_index)+':I'+str(row_index), 'Total: ', top_border_right)
                sheet.merge_range('J'+str(row_index)+':K'+str(row_index), group_data[index_total_debit], top_border_number_total)
                sheet.merge_range('L'+str(row_index)+':M'+str(row_index), group_data[index_total_credit], top_border_number_total)
                sheet.merge_range('N'+str(row_index)+':O'+str(row_index), '', top_border)
                sheet.merge_range('P'+str(row_index)+':S'+str(row_index), '', top_border)
                row_index += 1
                count_page += 1
                if count_page == 60:
                    row_index += 2
                    sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                    sheet.write('Q'+str(row_index), str(folio), folio_data)
                    folio += 1
                    row_index += 1
                    count_page = 3
                row_index += 1
                count_page += 1
                if count_page == 60:
                    row_index += 2
                    sheet.write('P'+str(row_index), 'Folio: ', folio_data)
                    sheet.write('Q'+str(row_index), str(folio), folio_data)
                    folio += 1
                    row_index += 1
                    count_page = 3
                
            sheet.merge_range('D'+str(row_index)+':I'+str(row_index), 'Totales: ', total_report)
            sheet.merge_range('J'+str(row_index)+':K'+str(row_index), report_data['totales']['total_debe'], total_report)
            sheet.merge_range('L'+str(row_index)+':M'+str(row_index), report_data['totales']['total_haber'], total_report)
            
        sheet.set_paper(1)
        sheet.set_landscape()
        list_row = []
        for x in range(60, row_index, 60):
            list_row.append(x)
        sheet.set_v_pagebreaks([16])
        sheet.set_h_pagebreaks(list_row)
        sheet.set_print_scale(110)
        sheet.center_horizontally()

        sheet.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()