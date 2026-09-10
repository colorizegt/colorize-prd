# -*- coding: utf-8 -*-

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

class L10nGtExtraCheckReport(models.TransientModel):
    _name = "l10n_gt_extra.check_report"
    _description = "Check Report"
    
    journal_id = fields.Many2many('account.journal', string='Diario', domain="[('type','=','bank'),('company_id','=',company_id)]")
    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')
    company_id = fields.Many2one('res.company', string="Compañia", required=True, default=lambda self: self.env.company.id)

    @api.onchange('company_id')
    def _company_onchange(self):
        self.write({'journal_id': [(5, 0, 0)]})

    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'l10n_gt_extra.check_report',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Reporte de Cheques',
                     },
            'report_type': 'l10n_gt_extra_xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Reporte de Cheques')
        sheet.set_column('A2:A2', 2)
        sheet.set_column('B2:B2', 4)
        sheet.set_column('C2:C2', 17)
        sheet.set_column('D2:D2', 15)
        sheet.set_column('E8:E8', 35)
        sheet.set_column('F2:F2', 22)
        sheet.set_column('G2:G2', 13)
        sheet.set_column('H2:H2', 11)
        sheet.set_column('I2:I2', 12)
        sheet.set_column('J2:J2', 25)
        sheet.set_row(1, 40)
        sheet.set_row(4, 35)
        sheet.freeze_panes(5, 0)
                
        titule_center = workbook.add_format({'font_name': 'Arial', 'font_size': 24, 'font_color': 'black', 'align': 'center'})
        sub_titule_center = workbook.add_format({'font_name': 'Arial', 'font_size': 16, 'font_color': 'black', 'align': 'center'})
        titule_center_u = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'font_color': 'black', 'align': 'center'})
        header_center = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        signal_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'bottom': 1, 'valign': 'vcenter'})
        data_left = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        data_left_black = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter'})
        data_right = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'right', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter', 'num_format': '###,##0.00'})
        data_right_clean = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'num_format': '###,##0.00'})
        data_right_black = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': 'black', 'align': 'right', 'valign': 'vcenter', 'num_format': '###,##0.00'})
        data_center = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'valign': 'vcenter'})
        
        date_range = ''
        date_from = False
        if data['date_from']:
            date_from = datetime.strptime(data['date_from'], '%Y-%m-%d')
        date_to = False
        if data['date_to']:
            date_to = datetime.strptime(data['date_to'], '%Y-%m-%d')

        if date_from and date_to:
            date_range = 'Desde: ' + str(date_from.strftime('%d/%m/%Y')) + ' Hasta: ' + str(date_to.strftime('%d/%m/%Y'))
        elif date_from and not date_to:
            date_range = 'Desde: ' + str(date_from.strftime('%d/%m/%Y'))
        elif not date_from and date_to:
            date_range = ' Hasta: ' + str(date_to.strftime('%d/%m/%Y'))
        
        company_data = self.env['res.company'].browse(data['company_id'][0])
            
        sheet.merge_range('B2:J2', company_data.name, titule_center)
        sheet.merge_range('B3:J3', 'Reporte de Cheques', sub_titule_center)
        sheet.merge_range('B4:J4', date_range, sub_titule_center)
        
        sheet.write('B5', 'No.', header_center)
        sheet.write('C5', 'Número de Cheque', header_center)
        sheet.write('D5', 'Fecha', header_center)
        sheet.write('E5', 'Cliente/Proveedor', header_center)
        sheet.write('F5', 'Diario', header_center)
        sheet.write('G5', 'Fecha anulación', header_center)
        sheet.write('H5', 'Moneda', header_center)
        sheet.write('I5', 'Importe', header_center)
        sheet.write('J5', 'Memo', header_center)
        if data['journal_id']:
            journal_ids = data['journal_id']
        else:
            journal_ids = self.env['account.journal'].search([])
        data_payment = self.sudo().env['account.payment'].search([('date','<=', date_to),('date','>=', date_from),('journal_id','in', journal_ids),('state','in',('posted','cancel')),('check_number','!=',False),('company_id','=',company_data.id)])
        
        sequence = 0; y = 6
        for payment in data_payment:
            sequence += 1
            sheet.write('B'+str(y), sequence, data_center)
            sheet.write('C'+str(y), payment.check_number, data_left)
            sheet.write('D'+str(y), str(payment.date.strftime('%d/%m/%Y')), data_center)
            if payment.printed_check_name:
                sheet.write('E'+str(y), payment.printed_check_name, data_left)
            else:
                sheet.write('E'+str(y), payment.partner_id.name, data_left)
            sheet.write('F'+str(y), payment.journal_id.name, data_left) 

            if payment.discarded_date or payment.state == 'cancel':
                discarded_date = payment.discarded_date
                if not discarded_date:
                    discarded_date = self.get_last_cancel_date(payment)
                if not discarded_date:
                    discarded_date = payment.date
                sheet.write('G'+str(y), str(discarded_date.strftime('%d/%m/%Y')), data_center)
            else:
                sheet.write('G'+str(y), '', data_left)
            sheet.write('H'+str(y), payment.currency_id.name, data_center)
            sheet.write('I'+str(y), str(payment.currency_id.symbol) + ' ' + str(round(payment.amount,2)), data_right)
            sheet.write('J'+str(y), payment.ref if payment.ref else '', data_left)
            y += 1
        data_currency = self.env['res.currency'].search([('active','=',True)])
        for currency in data_currency:
            amount_currency = 0
            for paymt in data_payment:
                if paymt.currency_id.id == currency.id:
                    amount_currency += paymt.amount
            if amount_currency > 0:
                y += 1
                sheet.write('H'+str(y), 'Importe Total ' + str(currency.symbol), data_left_black)
                sheet.write('I'+str(y), str(currency.symbol) + ' ' +str(round(amount_currency,2)), data_right_black)
        y += 4
        sheet.write('C'+str(y), 'Hecho por:', data_right_clean)
        sheet.write('D'+str(y), '', signal_data)
        sheet.write('F'+str(y), 'Autorizado por:', data_right_clean)
        sheet.merge_range('G'+str(y)+':H'+str(y), '', signal_data)

        sheet.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_last_cancel_date(self, payment):
        tracking_values = payment.message_ids.mapped('tracking_value_ids')
        cancel_tracking_values = [t for t in tracking_values if t.field_id.name == 'state' and t.new_value_char in ('Cancelado','Cancel')]
        
        if cancel_tracking_values:
            # Ordenar por fecha de creación y obtener el último
            last_cancel_date = max(cancel_tracking_values, key=lambda t: t.create_date).create_date
            return last_cancel_date
        return None