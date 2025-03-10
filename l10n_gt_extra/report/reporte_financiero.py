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
import time
import datetime
import logging


class ReporteFinanciero(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_financiero'
    _description = 'Report Financiero'
    

    def get_balance_result(self, account_ids, start_date, end_date, company_id, excluded_journals_ids=False):
        if excluded_journals_ids:
            sql = """
                SELECT sum(balance) as account_balance
                FROM account_move_line aml
                INNER JOIN account_account aa on(aml.account_id = aa.id)
                INNER JOIN account_move am on (aml.move_id = am.id)
                WHERE aa.id in (%s) AND am.company_id = %s
                AND aml.date >= '%s' AND aml.date <= '%s'
                AND aml.journal_id not in (%s)
                AND aml.parent_state = 'posted'
            """ % (str(account_ids), str(company_id), str(start_date), str(end_date), str(excluded_journals_ids))
            self.env.cr.execute(sql)
            balance = self.env.cr.dictfetchall()
        else:
            sql = """
                SELECT sum(balance) as account_balance
                FROM account_move_line aml
                INNER JOIN account_account aa on(aml.account_id = aa.id)
                INNER JOIN account_move am on (aml.move_id = am.id)
                WHERE aa.id in (%s) AND am.company_id = %s
                AND aml.date >= '%s' AND aml.date <= '%s'
                AND aml.parent_state = 'posted'
            """ % (str(account_ids), str(company_id), str(start_date), str(end_date))
            self.env.cr.execute(sql)
            balance = self.env.cr.dictfetchall()
        return balance[0]['account_balance']

    def get_balance_balance(self, account_ids, end_date, company_id, excluded_journals_ids=False):
        if excluded_journals_ids:
            sql = """
                SELECT sum(balance) as account_balance
                FROM account_move_line aml
                INNER JOIN account_account aa on(aml.account_id = aa.id)
                INNER JOIN account_move am on (aml.move_id = am.id)
                WHERE aa.id in (%s) AND am.company_id = %s
                AND aml.date <= '%s'
                AND aml.journal_id not in (%s)
                AND aml.parent_state = 'posted'
            """ % (str(account_ids), str(company_id), str(end_date), str(excluded_journals_ids))
            self.env.cr.execute(sql)
            balance = self.env.cr.dictfetchall()
        else:
            sql = """
                SELECT sum(balance) as account_balance
                FROM account_move_line aml
                INNER JOIN account_account aa on(aml.account_id = aa.id)
                INNER JOIN account_move am on (aml.move_id = am.id)
                WHERE aa.id in (%s) AND am.company_id = %s
                AND aml.date <= '%s'
                AND aml.parent_state = 'posted'
            """ % (str(account_ids), str(company_id), str(end_date))
            self.env.cr.execute(sql)
            balance = self.env.cr.dictfetchall()
        return balance[0]['account_balance']

    def get_month_name(self, month):
        if month== 1:
            return "Enero"
        elif month == 2:
            return "Febrero"
        elif month == 3:
            return "Marzo"
        elif month == 4:
            return "Abril"
        elif month == 5:
            return "Mayo"
        elif month == 6:
            return "Junio"
        elif month == 7:
            return "Julio"
        elif month == 8:
            return "Agosto"
        elif month == 9:
            return "Septiembre"
        elif month == 10:
            return "Octubre"
        elif month == 11:
            return "Noviembre"
        elif month == 12:
            return "Diciembre"

    def get_date_between(self, end_date, start_date=False):
        if start_date:
            tmp_start = start_date.split('-')
            tmp_end = end_date.split('-')
            date_between = str(tmp_start[2]) + ' de ' + str(self.get_month_name(int(tmp_start[1]))) 
            date_between += ' al ' + str(tmp_end[2]) + ' de ' + str(self.get_month_name(int(tmp_end[1]))) 
            date_between += ' de '+ str(number2text(str(tmp_end[0])))
        else:
            tmp_end = end_date.split('-')
            date_between = 'Al ' + str(tmp_end[2]) + ' de ' + str(self.get_month_name(int(tmp_end[1]))) 
            date_between += ' de '+ str(number2text(str(tmp_end[0])))

        return date_between

    def process_footer_phrase(self, footer_phrase, end_date, amount, report, start_date=False):

        if '{accountant_name}' in footer_phrase:
            footer_phrase = footer_phrase.replace("{accountant_name}", str(report.accountant_name))

        if '{legal_representative_name}' in footer_phrase:
            footer_phrase = footer_phrase.replace("{legal_representative_name}", str(report.legal_representative_name))

        if '{date_between}' in footer_phrase:
            if start_date:
                footer_phrase = footer_phrase.replace("{date_between}", self.get_date_between(end_date,start_date))
            else:
                footer_phrase = footer_phrase.replace("{date_between}", self.get_date_between(end_date))

        if '{amount}' in footer_phrase:
            footer_phrase = footer_phrase.replace("{amount}", str(report.company_id.currency_id.symbol)+'. '+str(round(amount,2)))

        if '{amount_in_letters}' in footer_phrase:
            footer_phrase = footer_phrase.replace("{amount_in_letters}", str(number2text(round(amount,2), report.company_id.currency_id.currency_unit_label)))

        return footer_phrase

    def sections(self, data):
        sections = []
        report_info = {}
        report = self.env['l10n_gt_extra.report_config'].search([('report_type','=',data['report_type'])], limit=1)

        tmp_start = data['start_date'].split('-')
        tmp_end = data['end_date'].split('-')

        if report.report_type == 'result':
            period = str(tmp_start[2])+"/"+str(tmp_start[1]+"/"+str(tmp_start[0])) + ' Al ' +str(tmp_end[2])+"/"+str(tmp_end[1]+"/"+str(tmp_end[0]))
        else:
            period = 'Al ' +str(tmp_end[2])+"/"+str(tmp_end[1]+"/"+str(tmp_end[0]))

        report_info = {
            'column_numbers': report.column_numbers,
            'accountant_name': report.accountant_name,
            'legal_representative_name': report.legal_representative_name,
            'period': period
        }

        for report_section in report.report_section_ids:
            journals_to_exclude_str = ','.join([str(x.id) for x in report_section.excluded_journal_ids])
            total_section = 0.0
            section_childs = []
            for line in report_section.lines_ids:
                balance = 0.0
                balance_subtotal = 0.0
                if line.account_ids:
                    accounts_str = ','.join([str(x.id) for x in line.account_ids])
                    if report.report_type == 'result':
                        get_balance_account = self.get_balance_result(accounts_str, data['start_date'], data['end_date'], report.company_id.id, journals_to_exclude_str)
                    else:
                        get_balance_account = self.get_balance_balance(accounts_str, data['end_date'], report.company_id.id, journals_to_exclude_str)
                    if get_balance_account:
                        balance += get_balance_account
                        total_section += get_balance_account
                if line.calculate_subtotal:
                    codes_to_sum = line.codes_to_sum.split(',')
                    for child_line in codes_to_sum:
                        line_to_sum = self.env['l10n_gt_extra.report_config.section.lines'].search([('code','=',child_line),('section_id','=',report_section.id)], limit=1)
                        if line_to_sum:
                            if line_to_sum.account_ids:
                                accounts_str = ','.join([str(x.id) for x in line_to_sum.account_ids])
                                if report.report_type == 'result':
                                    get_balance_child_account = self.get_balance_result(accounts_str, data['start_date'], data['end_date'], report.company_id.id, journals_to_exclude_str)
                                else:
                                    get_balance_child_account = self.get_balance_balance(accounts_str, data['end_date'], report.company_id.id, journals_to_exclude_str)
                                if get_balance_child_account:
                                    balance_subtotal += get_balance_child_account
                                    if get_balance_account:
                                        balance_subtotal += get_balance_account
                new_line = {
                        'name': line.name,
                        'first_column': round(abs(balance),2) if line.column_number == 'first_column' else 0,
                        'second_column': round(abs(balance),2) if line.column_number == 'second_column' else 0,
                        'total_column': round(abs(balance),2) if line.column_number == 'total_column' else round(abs(balance_subtotal),2),
                    }
                section_childs.append(new_line)
            other_sections_total = 0.0
            if report_section.codes_to_sum:
                codes_to_sum = report_section.codes_to_sum.split(',')
                for parent_section in codes_to_sum:
                    section_to_sum = self.env['l10n_gt_extra.report_config.section'].search([('code','=',parent_section)], limit=1)
                    for other_section_line in section_to_sum.lines_ids:
                        if other_section_line.account_ids:
                            accounts_str = ','.join([str(x.id) for x in other_section_line.account_ids])
                            if report.report_type == 'result':
                                get_balance_section = self.get_balance_result(accounts_str, data['start_date'], data['end_date'], report.company_id.id, journals_to_exclude_str)
                            else:
                                get_balance_section = self.get_balance_balance(accounts_str, data['end_date'], report.company_id.id, journals_to_exclude_str)
                            if get_balance_section:
                                other_sections_total += get_balance_section
            new_line = {
                    'section_name': report_section.name if not report_section.not_show_name else False,
                    'total_name': report_section.total_name,
                    'total_column': round(abs(total_section+other_sections_total),2),
                    'section_childs': section_childs,
                    'section_header': report_section.section_header or False,
                    'not_show_totals': report_section.not_show_totals or False,
                }
            sections.append(new_line)

        if report.report_type == 'result':
            report_info['footer_phrase'] = self.process_footer_phrase(report.footer_phrase, data['end_date'], abs(total_section+other_sections_total), report, data['start_date'])
        else:
            report_info['footer_phrase'] = self.process_footer_phrase(report.footer_phrase, data['end_date'], abs(total_section+other_sections_total), report)

        return {'sections': sections, 'report_info': report_info}

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        data = data['form']
        tmp_start_date = data['start_date'].split('-')
        tmp_end_date = data['end_date'].split('-')
        data['start_year'] = str(tmp_start_date[0])
        data['end_year'] = str(tmp_end_date[0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'sections': self.sections,
            'company_id': self.env.company
        }


def number2text(number_in, currency_name=False):
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
    if currency_name:
        converted += currency_name
    if int(number_dec) != 0:
        converted += ' CON ' + number_dec + " centavos "
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