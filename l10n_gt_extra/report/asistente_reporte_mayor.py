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


class AsistenteReporteMayor(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_mayor'
    _description = 'Asistente Report Mayor'
        
    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')
        else:
            return self.env['account.account'].search([]).ids

    cuentas_id = fields.Many2many("account.account", string="Cuentas", required=True, default=_default_cuenta, domain="[('company_id','=',company_id)]")
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    agrupado_por_dia = fields.Boolean(string="Agrupado por dia", compute="_get_gouping_type")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    currency_id = fields.Many2one('res.currency',string="Moneda", default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)
    detailed_report = fields.Boolean(string="Reporte Detallado")
    
    all_accounts = fields.Boolean(string="Todas las cuentas")
    grouping_type = fields.Selection([
        ('monthly', 'Mensual'),
        ('daily','Diario')
    ],string="Tipo de Agrupación", default="monthly")

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'cuentas_id': [(5, 0, 0)], 'all_accounts': False})

    def _get_gouping_type(self):
        if self.grouping_type == 'daily':
            self.agrupado_por_dia = True
        else:
            self.agrupado_por_dia = False
    
    @api.onchange('all_accounts')
    def onchange_all_accounts(self):
        if self.all_accounts == True:
            for rec in self:
                account_data = self.env['account.account'].search([
                ])
                for account in account_data:
                    rec.cuentas_id = [(4, account.id)] 
        if self.all_accounts == False:
            for rec in self:
                rec.cuentas_id = False
    
    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_mayor',
             'form': self.read()[0],
             'company_id': self.company_id.id
        }
        return self.env.ref('l10n_gt_extra.action_reporte_mayor').report_action(self, data=data)
    
    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'l10n_gt_extra.asistente_reporte_mayor',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro Mayor',
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
        dict['detailed_report'] = data['detailed_report']
        dict['grouping_type'] = data['grouping_type']
        dict['company_id'] = data['company_id']
        res = self.env['report.l10n_gt_extra.reporte_mayor'].lineas(dict)

        sheet = workbook.add_worksheet('Libro Mayor')
        formato_fecha = workbook.add_format({'num_format': 'dd/mm/yy'})

        if data['detailed_report']:
            sheet.set_column('A1:A1', 5)
            sheet.set_column('B1:B1', 15)
            sheet.set_column('C1:C1', 15)
            sheet.set_column('D1:D1', 15)
            sheet.set_column('E1:E1', 15)
            sheet.set_column('F1:F1', 20)
            sheet.set_column('G1:G1', 25)
            sheet.set_column('H1:H1', 5)
        else:
            sheet.set_column('A1:A1', 5)
            sheet.set_column('B1:B1', 12)
            sheet.set_column('C1:C1', 30)
            sheet.set_column('D1:D1', 12)
            sheet.set_column('E1:E1', 12)
            sheet.set_column('F1:F1', 12)
            sheet.set_column('G1:G1', 12)
            sheet.set_column('H1:H1', 12)
            sheet.set_column('I1:I1', 5)

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
        data_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_left_border_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 0, 'left': 1, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_center_border_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'center', 'right': 0, 'left': 1, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        data_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter', 'num_format': '#,##0.00'})
        data_left_border_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 0, 'top': 0, 'bottom': 0, 'valign': 'vcenter'})
        top_border = workbook.add_format({'top': 1})
        top_border_right = workbook.add_format({'top': 1, 'font_size': data_font_size, 'align': 'right'})
        top_border_number_total = workbook.add_format({'top': 1, 'bold': False, 'num_format': '#,##0.00', 'font_size': data_font_size})
        total_report_label = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'left'})
        total_report = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'right'})
        folio_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom':1, 'valign': 'vcenter'})
        amount_format = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' ,'num_format': 'Q ###,##0.00','align': 'right'})
        date_format= workbook.add_format({ 'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center','num_format': 'dd/mm/yy', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' })
        title_labels_value_date = workbook.add_format({'font_name': 'Arial', 'font_size': title_label_font_size,  'bold': False, 'font_color': 'black', 'align': 'center','num_format': 'dd/mm/yy', 'valign': 'vcenter'})
        amount_format_bold = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' ,'num_format': 'Q ###,##0.00','align': 'right'})
        
        company_data = self.env['res.company'].browse(data['company_id'][0])

        sheet.merge_range('B2:C2', 'Nombre Fiscal: ', title_labels)
        sheet.merge_range('D2:H2', company_data.company_registry, title_labels_value)
        sheet.write('G2', 'Folio: ', title_labels)
        sheet.write('H2', data['folio_inicial'], title_labels_value)        
        sheet.merge_range('B3:C3', 'NIT: ', title_labels)
        sheet.merge_range('D3:F3', company_data.vat, title_labels_value)
        sheet.merge_range('B5:C5', 'Moneda: ', title_labels)
        sheet.merge_range('D5:H5', company_data.currency_id.currency_unit_label + ' ' + company_data.currency_id.name, title_labels_value)
        sheet.merge_range('B4:C4', 'Dirección: ', title_labels)
        sheet.merge_range('D4:H4', company_data.street, title_labels_value)
        # Title
        sheet.merge_range('B8:H8', 'LIBRO MAYOR', title_center)
        # Dates
        sheet.write('B10', 'Desde: ', title_labels)
        sheet.merge_range('C10:D10', data['fecha_desde'], title_labels_value_date)
        sheet.write('F10', 'Hasta: ', title_labels)
        sheet.merge_range('G10:H10', data['fecha_hasta'], title_labels_value_date)

        row_index = 12
        if data['detailed_report']:
            if data['agrupado_por_dia']:
                account_names = res['account_names']
                data_lines = res['data_lines']
                for account_id in data_lines:
                    account_ids = data_lines[account_id]
                    sheet.merge_range('B'+str(row_index)+':G'+str(row_index), 'Cuenta: '+account_names[account_id][0], header_center)
                    account_balance = account_names[account_id][1]
                    row_index += 1
                    num_dates = 0
                    for date in account_ids:
                        num_dates += 1
                        lines = account_ids[date]
                        sheet.merge_range('B'+str(row_index)+':G'+str(row_index), 'Fecha: '+str(date), header_center)
                        row_index += 1
                        sheet.write('B'+str(row_index), 'Fecha', header_center)
                        sheet.write('C'+str(row_index), 'Débito', header_center)
                        sheet.write('D'+str(row_index), 'Crédito', header_center)
                        sheet.write('E'+str(row_index), 'Saldo', header_center)
                        sheet.write('F'+str(row_index), 'Póliza', header_center)
                        sheet.write('G'+str(row_index), 'Descripción', header_center)
                        row_index += 1
                        num_lines = 0
                        opening_balance = account_names[account_id][1]
                        subtotal_balance = 0
                        subtotal_haber = 0
                        for line in lines:
                            num_lines += 1
                            if num_lines == 1 and num_dates <= len(account_ids):
                                sheet.merge_range('B'+str(row_index)+':D'+str(row_index), 'Saldo Inicial', header_center)
                                sheet.write('E'+str(row_index), account_balance, amount_format)
                                row_index += 1
                            sheet.write('B'+str(row_index), line['fecha_movimiento'], date_format)
                            sheet.write('C'+str(row_index), line['debe'], amount_format)
                            sheet.write('D'+str(row_index), line['haber'], amount_format)
                            sheet.write('E'+str(row_index), line['balance'], amount_format)
                            sheet.write('F'+str(row_index), str(line['poliza']), data_left)
                            sheet.write('G'+str(row_index), str(line['descripcion']), data_left)
                            row_index += 1
                            if len(lines) == num_lines:
                                sheet.write('B'+str(row_index), 'Total', header_center)
                                sheet.write('C'+str(row_index), res['subtotales'][account_id][date]['subtotal_debe'], amount_format_bold)
                                sheet.write('D'+str(row_index), res['subtotales'][account_id][date]['subtotal_haber'], amount_format_bold)
                                sheet.write('E'+str(row_index), line['balance'], amount_format_bold)
                                subtotal_balance += line['balance']
                                account_balance = line['balance']
                                row_index += 1

            else:
                account_names = res['account_names']
                account_ids = res['data_lines']
                for account_id in account_ids:
                    sheet.merge_range('B'+str(row_index)+':G'+str(row_index), 'Cuenta: '+account_names[account_id][0], header_center)
                    account_balance = account_names[account_id][1]
                    months = account_ids[account_id]
                    row_index += 1
                    num_months = 0
                    for month in months:
                        num_months += 1
                        
                        sheet.merge_range('B'+str(row_index)+':G'+str(row_index), 'Mes: '+str(month), header_center)
                        row_index += 1
                        sheet.write('B'+str(row_index), 'Fecha', header_center)
                        sheet.write('C'+str(row_index), 'Débito', header_center)
                        sheet.write('D'+str(row_index), 'Crédito', header_center)
                        sheet.write('E'+str(row_index), 'Saldo', header_center)
                        sheet.write('F'+str(row_index), 'Póliza', header_center)
                        sheet.write('G'+str(row_index), 'Descripción', header_center)
                        row_index += 1
                        num_lines = 0
                        opening_balance = account_names[account_id][1]
                        subtotal_balance = 0
                        subtotal_debe = 0
                        subtotal_haber = 0
                        for line in months[month]:
                            num_lines += 1
                            if num_lines == 1 and num_months <= len(months):
                                sheet.merge_range('B'+str(row_index)+':D'+str(row_index), 'Saldo Inicial', header_center)
                                sheet.write('E'+str(row_index), account_balance, amount_format)
                                row_index += 1
                            sheet.write('B'+str(row_index), line['fecha_movimiento'], date_format)
                            sheet.write('C'+str(row_index), line['debe'], amount_format)
                            subtotal_debe = subtotal_debe + line['debe']
                            sheet.write('D'+str(row_index), line['haber'], amount_format)
                            subtotal_haber = subtotal_haber + line['haber']
                            sheet.write('E'+str(row_index), line['balance'], amount_format)
                            sheet.write('F'+str(row_index), str(line['poliza']), data_left)
                            sheet.write('G'+str(row_index), str(line['descripcion']), data_left)
                            row_index += 1
                            if num_lines == len(months[month]):
                                sheet.write('B'+str(row_index), 'Total', header_center)
                                sheet.write('C'+str(row_index), subtotal_debe, amount_format_bold)
                                sheet.write('D'+str(row_index), subtotal_haber, amount_format_bold)
                                sheet.write('E'+str(row_index), line['balance'], amount_format_bold)
                                subtotal_balance += line['balance']
                                account_balance = line['balance']
                                row_index += 1
        else:
            lineas = res['lineas']
            if data['agrupado_por_dia']:
                
                sheet.write('B'+str(row_index), 'Codigo', header_center)
                sheet.write('C'+str(row_index), 'Cuenta', header_center)
                sheet.write('D'+str(row_index), 'Fecha', header_center)
                sheet.write('E'+str(row_index), 'Saldo Inicial', header_center)
                sheet.write('F'+str(row_index), 'Debe', header_center)
                sheet.write('G'+str(row_index), 'Haber', header_center)
                sheet.write('H'+str(row_index), 'Saldo Final', header_center)
                for cuenta in lineas:
                    if (cuenta['total_debe']+cuenta['total_haber']) != 0:
                        row_index += 1
                        sheet.write('B'+str(row_index), cuenta['codigo'], data_left)
                        sheet.write('C'+str(row_index), cuenta['cuenta'], data_left)
                        sheet.write('D'+str(row_index), '', data_left)
                        sheet.write('E'+str(row_index), cuenta['saldo_inicial'], amount_format)
                        sheet.write('F'+str(row_index), cuenta['total_debe'], amount_format)
                        sheet.write('G'+str(row_index), cuenta['total_haber'], amount_format)
                        sheet.write('H'+str(row_index), cuenta['saldo_final'], amount_format)
                        for fechas in cuenta['fechas']:
                            row_index += 1
                            sheet.write('D'+str(row_index), fechas['fecha'], date_format)
                            sheet.write('F'+str(row_index), fechas['debe'], amount_format)
                            sheet.write('G'+str(row_index), fechas['haber'], amount_format)
                        row_index += 1
            else:
                sheet.write('B'+str(row_index), 'Codigo', header_center)
                sheet.merge_range('C'+str(row_index)+':D'+str(row_index), 'Cuenta', header_center)
                sheet.write('E'+str(row_index), 'Saldo Inicial', header_center)
                sheet.write('F'+str(row_index), 'Debe', header_center)
                sheet.write('G'+str(row_index), 'Haber', header_center)
                sheet.write('H'+str(row_index), 'Saldo Final', header_center)

                for linea in lineas:
                    if (linea['debe']+linea['haber']) != 0:
                        row_index += 1

                        sheet.write('B'+str(row_index), linea['codigo'], data_left)
                        sheet.merge_range('C'+str(row_index)+':D'+str(row_index), linea['cuenta'], data_left)
                        sheet.write('E'+str(row_index), linea['saldo_inicial'], amount_format)
                        sheet.write('F'+str(row_index), linea['debe'], amount_format)
                        sheet.write('G'+str(row_index), linea['haber'], amount_format)
                        sheet.write('H'+str(row_index), linea['saldo_final'], amount_format)

            totales = res['totales']
            row_index += 1
            sheet.merge_range('B'+str(row_index)+':E'+str(row_index), 'Totales', total_report)
            sheet.write('F'+str(row_index), totales['debe'], total_report)
            sheet.write('G'+str(row_index), totales['haber'], total_report)

        sheet.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()