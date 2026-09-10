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
from typing import ValuesView
from odoo.exceptions import ValidationError
from odoo import api, models, fields
from datetime import date
import datetime
import calendar
import logging


class ReporteMayor(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_mayor'
    _description = 'Report Mayor'
    
    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.journal_id not in ('+journals_to_exclude_str+') group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        fecha = fields.Date.from_string(fecha_desde)
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.date >= %s and l.journal_id not in ('+journals_to_exclude_str+') group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,fecha.strftime('%Y-1-1')))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.date >= %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,fecha.strftime('%Y-1-1')))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def get_balance(self, account_id, company_id, date):
        sql = """
            SELECT sum(balance) as account_balance, sum(amount_currency) as amount_currency
            FROM account_move_line aml
            INNER JOIN account_move am on (aml.move_id = am.id)
            WHERE aml.account_id = %s AND am.company_id = %s
            AND aml.date < '%s'
            AND aml.parent_state = 'posted'
        """ % (str(account_id), str(company_id), str(date))
        self.env.cr.execute(sql)
        balance = self.env.cr.dictfetchall()

        return balance[0]
    
    def lineas(self, datos):
        totales = {}
        lineas_resumidas = {}
        lineas=[]
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0

        accounts_str = ','.join([str(x) for x in datos['cuentas_id']])
        company = self.env['res.company'].browse(datos['company_id'][0])

        journals_to_exclude = company.journals_to_exclude
        journals_to_exclude_str = ','.join([str(x.id) for x in journals_to_exclude])

        if datos['detailed_report']:
            credit_accounts = ('liability', 'equity', 'income')
            debit_accounts = ('asset', 'expense', 'off_balance')
            if journals_to_exclude_str:
                sql = """
                        select
                            ml.date as fecha_movimiento,
                            aa.internal_group as tipo_cuenta,
                            aa.id as cuenta_id,
                            aa.name as cuenta,
                            aa.code as codigo_cuenta,
                            ml.debit as debe,
                            ml.credit as haber,
                            am.name as poliza,
                            am.ref as descripcion

                        from
                            account_move_line ml
                        inner join account_account aa on
                            (ml.account_id = aa.id)
                        inner join account_move am on
                            (am.id = ml.move_id)
                        where
                            ml.date >= '%s'
                            and ml.date <= '%s'
                            and ml.journal_id not in (%s)
                            and aa.id in (%s)
                            and am.state = 'posted'
                            and am.company_id = %s
                        group by
                            aa.id,
                            aa.id,
                            aa.name,
                            aa.code,
                            ml.debit,
                            ml.credit,
                            am.name,
                            am.ref,
                            ml.date
                        order by
                            aa.id,
                            ml.date
                    """ % (datos['fecha_desde'], datos['fecha_hasta'], journals_to_exclude_str, accounts_str, str(company.id))
            else:
                sql = """
                        select
                            ml.date as fecha_movimiento,
                            aa.internal_group as tipo_cuenta,
                            aa.id as cuenta_id,
                            aa.name as cuenta,
                            aa.code as codigo_cuenta,
                            ml.debit as debe,
                            ml.credit as haber,
                            am.name as poliza,
                            am.ref as descripcion

                        from
                            account_move_line ml
                        inner join account_account aa on
                            (ml.account_id = aa.id)
                        inner join account_move am on
                            (am.id = ml.move_id)
                        where
                            ml.date >= '%s'
                            and ml.date <= '%s'
                            and aa.id in (%s)
                            and am.state = 'posted'
                            and am.company_id = %s
                        group by
                            aa.id,
                            aa.id,
                            aa.name,
                            aa.code,
                            ml.debit,
                            ml.credit,
                            am.name,
                            am.ref,
                            ml.date
                        order by
                            aa.id,
                            ml.date
                    """ % (datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id))
            self.env.cr.execute(sql)
            opening_balances = {}
            account_names = {}
            data_lines = {}
            if datos['grouping_type'] == 'daily':

                move_line_ids = self.env.cr.dictfetchall()

                for line in move_line_ids:

                    name_account = self.env['account.account'].browse(line['cuenta_id']).name

                    new_line = {
                        'descripcion': line['descripcion'] if line['descripcion'] else '-',
                        'fecha_movimiento': line['fecha_movimiento'],
                        'codigo_cuenta': line['codigo_cuenta'],
                        'cuenta_id': line['cuenta_id'],
                        'poliza': line['poliza'],
                        'cuenta': name_account,
                        'haber': line['haber'],
                        'debe': line['debe']
                    }

                    if not line['cuenta_id'] in account_names:
                        account_id = line['cuenta_id']
                        account_balance = self.get_balance(account_id, company.id, datos['fecha_desde'])
                        opening_balance = 0 if account_balance['account_balance'] is None else account_balance['account_balance']
                        opening_balances[line['cuenta_id']] = 0 if account_balance['account_balance'] is None else account_balance['account_balance']
                        account_names[account_id] = [name_account, opening_balance]
                    if line['tipo_cuenta'] in credit_accounts:
                        opening_balances[account_id] += line['haber']
                        opening_balances[account_id] -= line['debe']
                    elif line['tipo_cuenta'] in debit_accounts:
                        opening_balances[account_id] -= line['haber']
                        opening_balances[account_id] += line['debe']

                    new_line['balance'] = opening_balances[account_id]

                    if line['cuenta_id'] in data_lines:
                        account_id = line['cuenta_id']
                        if line['fecha_movimiento'] in data_lines[account_id]:
                            data_lines[account_id][line['fecha_movimiento']].append(new_line)
                        else:
                            line_ids = []
                            line_ids.append(new_line)
                            data_lines[account_id][line['fecha_movimiento']] = line_ids
                    else:
                        new_date = {}
                        line_ids = []
                        account_id = line['cuenta_id']
                        new_line['balance'] = opening_balances[account_id]
                        line_ids.append(new_line)

                        new_date[line['fecha_movimiento']] = line_ids
                        data_lines[line['cuenta_id']] = new_date

                total_debe = 0
                total_haber = 0
                subtotales = {}
                for account_id in data_lines:
                    account_ids = data_lines[account_id]
                    subtotales[account_id] = {}
                    for date in account_ids:
                        subtotal_debe = 0
                        subtotal_haber = 0
                        for line in account_ids[date]:
                            subtotal_debe += line['debe']
                            subtotal_haber += line['haber']
                        subtotales[account_id][date] = {
                            'subtotal_debe': subtotal_debe,
                            'subtotal_haber': subtotal_haber
                        }
                        total_haber += subtotal_haber
                        total_debe += subtotal_haber
                
                totales = {
                    'total_debe': total_debe,
                    'total_haber': total_haber
                }
                                
                return {'data_lines': data_lines, 'account_names': account_names, 'opening_balances': opening_balances, 'subtotales':subtotales, 'totales':totales}

            elif datos['grouping_type'] == 'monthly':
                
                move_line_ids = self.env.cr.dictfetchall()
                for line in move_line_ids:

                    name_account = self.env['account.account'].browse(line['cuenta_id']).name

                    new_line = {
                            #'saldo_inicial':  self.get_balance(line['cuenta_id'], datos['fecha_desde']),
                            'descripcion': line['descripcion'] if line['descripcion'] else '-',
                            'fecha_movimiento': line['fecha_movimiento'],
                            'codigo_cuenta': line['codigo_cuenta'],
                            'cuenta_id': line['cuenta_id'],
                            'poliza': line['poliza'],
                            'cuenta': name_account,
                            'haber': line['haber'],
                            'debe': line['debe']
                        }
                    month_number = int(line['fecha_movimiento'].strftime('%m'))
                    month = self.get_month_name(month_number)
                    
                    account_id = line['cuenta_id']
                    if not line['cuenta_id'] in account_names:
                        account_balance = self.get_balance(account_id, company.id, datos['fecha_desde'])
                        opening_balance = 0 if account_balance['account_balance'] is None else account_balance['account_balance']
                        opening_balances[account_id] = 0 if account_balance['account_balance'] is None else account_balance['account_balance']
                        account_names[account_id] = [name_account, opening_balance]

                    if line['tipo_cuenta'] in credit_accounts:
                        opening_balances[account_id] += line['haber']
                        opening_balances[account_id] -= line['debe']
                    elif line['tipo_cuenta'] in debit_accounts:
                        opening_balances[account_id] -= line['haber']
                        opening_balances[account_id] += line['debe']

                    new_line['balance'] = opening_balances[account_id]
                    if account_id in data_lines:
                        if month in data_lines[account_id]:
                            data_lines[account_id][month].append(new_line)
                        else:
                            month_data = []
                            month_data.append(new_line)
                            data_lines[account_id][month] = month_data
                    else:
                        new_month = {}
                        line_ids = []
                        line_ids.append(new_line)
                        new_month[month] = line_ids
                        data_lines[account_id] = new_month
                
                return {'data_lines': data_lines, 'account_names': account_names, 'opening_balances': opening_balances}
            
        else:
            if datos['agrupado_por_dia']:
                if journals_to_exclude_str:
                    self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, l.date as fecha, sum(l.debit) as debe, sum(l.credit) as haber ' \
                        'from account_move_line l join account_account a on(l.account_id = a.id)' \
                        'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s and l.journal_id not in ('+journals_to_exclude_str+') group by a.id, a.code, a.name, l.date ORDER BY a.code',
                    (company.id, datos['fecha_desde'], datos['fecha_hasta']))
                else:
                    self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, l.date as fecha, sum(l.debit) as debe, sum(l.credit) as haber ' \
                        'from account_move_line l join account_account a on(l.account_id = a.id)' \
                        'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s group by a.id, a.code, a.name, l.date ORDER BY a.code',
                    (company.id, datos['fecha_desde'], datos['fecha_hasta']))

                for r in self.env.cr.dictfetchall():
                    totales['debe'] += r['debe']
                    totales['haber'] += r['haber']
                    linea = {
                        'id': r['id'],
                        'fecha': r['fecha'],
                        'codigo': r['codigo'],
                        'cuenta': self.env['account.account'].browse(r['cuenta']).name,
                        'saldo_inicial': 0,
                        'debe': r['debe'],
                        'haber': r['haber'],
                        'saldo_final': 0,
                    }
                    lineas.append(linea)

                cuentas_agrupadas = {}
                llave = 'codigo'
                for l in lineas:
                    if l[llave] not in cuentas_agrupadas:
                        cuentas_agrupadas[l[llave]] = {
                            'codigo': l[llave],
                            'cuenta': l['cuenta'],
                            'saldo_inicial': 0,
                            'saldo_final': 0,
                            'fechas': [],
                            'total_debe': 0,
                            'total_haber': 0
                        }

                    cuentas_agrupadas[l[llave]]['saldo_inicial'] = self.retornar_saldo_inicial_inicio_anio(l['id'], datos['fecha_desde'], journals_to_exclude_str)
                    cuentas_agrupadas[l[llave]]['fechas'].append(l)

                for cuenta in cuentas_agrupadas.values():
                    for fecha in cuenta['fechas']:
                        cuenta['total_debe'] += fecha['debe']
                        cuenta['total_haber'] += fecha['haber']
                    cuenta['saldo_final'] += cuenta['saldo_inicial'] + cuenta['total_debe'] - cuenta['total_haber']

                lineas = cuentas_agrupadas.values()

                print(lineas)
            else:
                if journals_to_exclude_str:
                    self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, sum(l.debit) as debe, sum(l.credit) as haber ' \
                        'from account_move_line l join account_account a on(l.account_id = a.id)' \
                        'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s and l.journal_id not in ('+journals_to_exclude_str+') group by a.id, a.code, a.name ORDER BY a.code',
                    (company.id, datos['fecha_desde'], datos['fecha_hasta']))
                else:
                    self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, sum(l.debit) as debe, sum(l.credit) as haber ' \
                        'from account_move_line l join account_account a on(l.account_id = a.id)' \
                        'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s group by a.id, a.code, a.name ORDER BY a.code',
                    (company.id, datos['fecha_desde'], datos['fecha_hasta']))

                for r in self.env.cr.dictfetchall():
                    totales['debe'] += r['debe']
                    totales['haber'] += r['haber']
                    linea = {
                        'id': r['id'],
                        'codigo': r['codigo'],
                        'cuenta': self.env['account.account'].browse(r['cuenta']).name,
                        'saldo_inicial': 0,
                        'debe': r['debe'],
                        'haber': r['haber'],
                        'saldo_final': 0,
                    }
                    lineas.append(linea)

                for l in lineas:
                    l['saldo_inicial'] += self.retornar_saldo_inicial_todos_anios(l['id'], datos['fecha_desde'], journals_to_exclude_str)
                    l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                    totales['saldo_inicial'] += l['saldo_inicial']
                    totales['saldo_final'] += l['saldo_final']

            return {'lineas': lineas,'totales': totales }
            
    def get_month_name(self, month):
        switcher = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }
        return switcher.get(month, " - ")
        
    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        data = data['form']
        tmp_inicio = data['fecha_desde'].split('-')
        tmp_final = data['fecha_hasta'].split('-')

        fecha_inicio = str(tmp_inicio[2])+"/" + \
            str(tmp_inicio[1]+"/"+str(tmp_inicio[0]))
        fecha_final = str(tmp_final[2])+"/" + \
            str(tmp_final[1]+"/"+str(tmp_final[0]))
        data['fecha_inicio'] = fecha_inicio
        data['fecha_final'] = fecha_final
        data['anio_inicio'] = str(tmp_inicio[0])
        data['anio_final'] = str(tmp_final[0])

        company = self.env['res.company'].browse(data['company_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'lineas': self.lineas,
            'company_id': company
        }