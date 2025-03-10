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


class AsistenteReporteBanco(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_banco'
    _description = 'Asistente de información para reporte de banco'

    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')[0]
        else:
            return None

    cuenta_bancaria_id = fields.Many2one("account.account", string="Cuenta", required=True, default=_default_cuenta, domain="[('company_id','=',company_id),('account_type','=','asset_cash')]")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'cuenta_bancaria_id': False})

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_banco',
             'form': self.read()[0],
             'company_id': self.company_id.id
        }
        return self.env.ref('l10n_gt_extra.action_reporte_banco').report_action(self, data=data)
    
    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'l10n_gt_extra.asistente_reporte_banco',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro de Banco',
                     },
            'report_type': 'l10n_gt_extra_xlsx'
        }
    
    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        dict = {}
        dict['fecha_hasta'] = data['fecha_hasta']
        dict['fecha_desde'] = data['fecha_desde']
        dict['cuenta_bancaria_id'] = data['cuenta_bancaria_id']
        dict['company_id'] = data['company_id']
        lines = self.env['report.l10n_gt_extra.reporte_banco'].lineas(dict)
        initial_balance = self.env['report.l10n_gt_extra.reporte_banco'].balance_inicial(dict)

        sheet = workbook.add_worksheet('Libro de Banco')
        formato_fecha = workbook.add_format({'num_format': 'dd/mm/yy'})

        sheet.set_column('A1:A1', 5)
        sheet.set_column('B1:B1', 12)
        sheet.set_column('C1:C1', 30)
        sheet.set_column('D1:D1', 30)
        sheet.set_column('E1:E1', 60)
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
        data_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'right', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter', 'num_format': '#,##0.00'})
        data_left_border_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'text_wrap': True, 'font_size': data_font_size, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        top_border = workbook.add_format({'top': 1})
        top_border_right = workbook.add_format({'top': 1, 'font_size': data_font_size, 'align': 'right'})
        top_border_number_total = workbook.add_format({'top': 1, 'bold': False, 'num_format': '#,##0.00', 'font_size': data_font_size})
        total_report_label = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'left'})
        total_report = workbook.add_format({'top': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': total_font_size, 'align': 'right'})
        folio_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 13, 'font_color': 'black', 'align': 'right', 'right': 0, 'left': 0, 'top': 0, 'bottom':1, 'valign': 'vcenter'})
        amount_format = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' ,'num_format': 'Q ###,##0.00','align': 'right'})
        date_format= workbook.add_format({ 'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center','num_format': 'dd/mm/yy', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter' })

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
        sheet.merge_range('B8:H8', 'LIBRO DE BANCO', title_center)
        # Dates
        sheet.merge_range('B10:H10', 'Registro del: '+str(data['fecha_desde'])+' al '+str(data['fecha_hasta']), title_labels_value)
        sheet.merge_range('B11:H11', 'Cuenta: '+str(data['cuenta_bancaria_id'][1]), title_labels_value)

        row_index = 13

        sheet.write('B'+str(row_index), 'Fecha', header_center)
        sheet.write('C'+str(row_index), 'Doc', header_center)
        sheet.write('D'+str(row_index), 'Nombre', header_center)
        sheet.write('E'+str(row_index), 'Concepto', header_center)
        sheet.write('F'+str(row_index), 'Crédito', header_center)
        sheet.write('G'+str(row_index), 'Débito', header_center)
        sheet.write('H'+str(row_index), 'Balance', header_center)

        row_index += 1

        sheet.merge_range('B'+str(row_index)+':G'+str(row_index), 'Saldo Inicial', data_right)
        balance = 0
        if 'balance_moneda' in initial_balance and initial_balance['balance_moneda']:
            balance = initial_balance['balance_moneda']
        elif 'balance' in initial_balance and initial_balance['balance']:
            balance = initial_balance['balance']
        sheet.write('H'+str(row_index), balance, amount_format)
        
        for line in lines:
            row_index += 1
            sheet.write('B'+str(row_index), line['fecha'], date_format)
            sheet.write('C'+str(row_index), line['documento'], data_left)
            sheet.write('D'+str(row_index), line['nombre'], data_left)
            sheet.write('E'+str(row_index), line['concepto'], data_left)
            sheet.write('F'+str(row_index), line['debito'], amount_format)
            sheet.write('G'+str(row_index), line['credito'], amount_format)
            sheet.write('H'+str(row_index), line['balance'], amount_format)

        sheet.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()