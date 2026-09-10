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
from odoo.exceptions import ValidationError
from odoo import api, models, fields
import logging
import calendar
import datetime

class ReporteDiario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_diario'
    _description = 'Report Diario'
    
    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id) join account_move am on(am.id = l.move_id)'\
            "where a.id = %s and l.date < %s and am.state = 'posted' group by a.id, a.code, a.name,l.debit,l.credit", (cuenta,fecha_desde))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id) join account_move am on(am.id = l.move_id)'\
            "where a.id = %s and l.date < %s and am.state = 'posted' group by a.id, a.code, a.name,l.debit,l.credit", (cuenta,fecha_desde))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        fecha = fields.Date.from_string(fecha_desde)
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id) join account_move am on(am.id = l.move_id)'\
            "where a.id = %s and l.date < %s and l.date >= %s and am.state = 'posted' group by a.id, a.code, a.name,l.debit,l.credit", (cuenta,fecha_desde,fecha.strftime('%Y-1-1')))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id) join account_move am on(am.id = l.move_id)'\
            "where a.id = %s and l.date < %s and l.date >= %s and am.state = 'posted' group by a.id, a.code, a.name,l.debit,l.credit", (cuenta,fecha_desde,fecha.strftime('%Y-1-1')))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial
    
    def excel_lines(self, datos):
        totales = {}
        lineas = []
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0
        months_data = []
        daily_data = []
        transaction_data = []

        company = self.env['res.company'].browse(datos['company_id'][0])

        journals_to_exclude = company.journals_to_exclude
        journals_to_exclude_str = ','.join([str(x.id) for x in journals_to_exclude])
        
        accounts_str = ','.join([str(x) for x in datos['cuentas_id']])

        if datos['grouping_type'] == 'daily':
            total_debe = 0
            total_haber = 0
            if journals_to_exclude_str:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name 
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s and am.journal_id not in (%s)
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id), journals_to_exclude_str)
            else:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name   
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id))
            self.env.cr.execute(sql)
            move_line_ids = self.env.cr.dictfetchall()
            for line in move_line_ids:
                
                line_date = line['fecha']
                new_line = {
                        'descripcion': line['descripcion'] if line['descripcion'] else '-',
                        'fecha_movimiento': line['fecha'].strftime('%d/%m/%Y'),
                        'codigo': line['codigo_cuenta'],
                        'cuenta': self.env['account.account'].browse(line['cuenta_id']).name,
                        'poliza': line['poliza'],
                        'id': line['cuenta_id'],
                        'haber': line['haber'],                        
                        'debe': line['debe'],
                        'saldo_inicial': 0,
                        'name': line['name']
                    }

                data_found = False
                for daily_line in daily_data:
                    if daily_line['daily_date_obj'] == line_date:
                        data_found = True
                        daily_line['group_data'].append(new_line)
                        daily_line['daily_total_credit'] += new_line['haber']
                        daily_line['daily_total_debit'] += new_line['debe']
                
                if not data_found:
                    new_daily_data = []
                    new_daily_data.append(new_line)
                    date_label = str(line_date.day).zfill(2) + '/' + str(line_date.month).zfill(2) + '/' + str(line_date.year).zfill(4)
                    new_daily = {
                        'daily_date_obj': line_date,
                        'daily_date': date_label,
                        'group_data': new_daily_data,
                        'daily_total_credit': new_line['haber'],
                        'daily_total_debit': new_line['debe']
                    }
                    daily_data.append(new_daily)
                

            for daily_line in daily_data:
                total_haber += daily_line['daily_total_credit']
                total_debe += daily_line['daily_total_debit']
            totales = {
                'total_debe': total_debe,
                'total_haber': total_haber
            }
            
            return {'fechas': daily_data, 'totales': totales}
            
        elif datos['grouping_type'] == 'monthly':
            if journals_to_exclude_str:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name  
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s and am.journal_id not in (%s)
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id), journals_to_exclude_str)
            else:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name   
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id))
            self.env.cr.execute(sql)
            move_line_ids = self.env.cr.dictfetchall()
            total_debe = 0
            total_haber = 0
            for line in move_line_ids:
                number_month = int(line['fecha'].strftime('%m'))
                new_line = {
                        'descripcion': line['descripcion'] if line['descripcion'] else '-',
                        'fecha_movimiento': line['fecha'].strftime('%d/%m/%Y'),
                        'codigo': line['codigo_cuenta'],
                        'cuenta': self.env['account.account'].browse(line['cuenta_id']).name,
                        'poliza': line['poliza'],
                        'id': line['cuenta_id'],
                        'haber': line['haber'],                        
                        'debe': line['debe'],
                        'saldo_inicial': 0,
                        'name': line['name'],
                    }
                
                
                data_found = False
                
                for month_data in months_data:
                    if month_data['month_number'] == number_month:
                        data_found = True
                        month_data['group_data'].append(new_line)
                        month_data['month_total_credit'] += new_line['haber']
                        month_data['month_total_debit'] += new_line['debe']
                
                if not data_found:
                    new_month_data = []
                    new_month_data.append(new_line)
                    new_month = {
                        'month_number': number_month,
                        'month_name': self.get_month_name(number_month),
                        'group_data': new_month_data,
                        'month_total_credit': new_line['haber'],
                        'month_total_debit': new_line['debe']
                    }
                    months_data.append(new_month)
            
            total_debe = 0
            total_haber = 0
            for month_data in months_data:
                total_haber += month_data['month_total_credit']
                total_debe += month_data['month_total_debit']
            totales = {
                'total_debe': total_debe,
                'total_haber': total_haber
            }
            
            return {'meses': months_data, 'totales': totales}

        elif datos['grouping_type'] == 'transaction':
            if journals_to_exclude_str:
                sql = """
                    select 
                        aml.date as fecha_movimiento,
                        aml.move_id as id_movimiento,
                        aa.id as cuenta_id,
                        aa.code as codigo_cuenta,
                        aml.debit as debe,
                        aml.credit as haber,
                        am.name as poliza,
                        am.ref as referencia,
                        aa.name as cuenta,
                        aml.name as name
                    from
                        account_move_line aml 
                    inner join
                        account_move am on(am.id = aml.move_id)
                    inner join account_account aa on
                        (aml.account_id = aa.id)	
                    where
                        aml.date >= '%s'
                        and aml.date <= '%s'
                        and am.company_id = %s
                        and aml.account_id IN (%s)
                        and aml.journal_id not in (%s)
                        and am.state = 'posted'
                    order by 
                        aml.id
                """%(str(datos['fecha_desde']),str(datos['fecha_hasta']),str(company.id), accounts_str, journals_to_exclude_str)
            else:
                sql = """
                    select 
                        aml.date as fecha_movimiento,
                        aml.move_id as id_movimiento,
                        aa.id as cuenta_id,
                        aa.code as codigo_cuenta,
                        aml.debit as debe,
                        aml.credit as haber,
                        am.name as poliza,
                        am.ref as referencia,
                        aa.name as cuenta,
                        aml.name as name
                    from
                        account_move_line aml 
                    inner join
                        account_move am on(am.id = aml.move_id)
                    inner join account_account aa on
                        (aml.account_id = aa.id)	
                    where
                        aml.date >= '%s'
                        and aml.date <= '%s'
                        and am.company_id = %s
                        and aml.account_id IN (%s)
                        and am.state = 'posted'
                    order by 
                        aml.id
                """%(str(datos['fecha_desde']),str(datos['fecha_hasta']),str(company.id), accounts_str)
            self.env.cr.execute(sql)
            move_line_ids = {}
            
            for line in self.env.cr.dictfetchall():
                line_date = line['fecha_movimiento']
                new_line ={
                        'referencia': line['referencia'] if line['referencia'] else '-',
                        'fecha_movimiento': line['fecha_movimiento'].strftime('%d/%m/%Y'),
                        'id_movimiento': line['id_movimiento'],
                        'codigo': line['codigo_cuenta'],
                        'cuenta': self.env['account.account'].browse(line['cuenta_id']).name,
                        'poliza': line['poliza'],
                        'haber': line['haber'],
                        'debe': line['debe'],   
                        'name': line['name'],  
                    }

                data_found = False
                
                for transaction_line in transaction_data:
                    if transaction_line['move_id'] == new_line['id_movimiento']:
                        data_found = True
                        transaction_line['group_data'].append(new_line)
                        transaction_line['transaction_total_credit'] += new_line['haber']
                        transaction_line['transaction_total_debit'] += new_line['debe']
                
                if not data_found:
                    new_transaction_data = []
                    new_transaction_data.append(new_line)
                    date_label = str(line_date.day).zfill(2) + '/' + str(line_date.month).zfill(2) + '/' + str(line_date.year).zfill(4)
                    new_transaction = {
                        'move_id': new_line['id_movimiento'],
                        'transaction_date': date_label,
                        'poliza': new_line['poliza'],
                        'group_data': new_transaction_data,
                        'transaction_total_credit': new_line['haber'],
                        'transaction_total_debit': new_line['debe']
                    }
                    transaction_data.append(new_transaction)
                
            
            totales = {}
            total_debe = 0
            total_haber = 0
            for transaction_line in transaction_data:
                total_haber += transaction_line['transaction_total_credit']
                total_debe += transaction_line['transaction_total_debit']
                
            totales = {
                'total_debe': total_debe,
                'total_haber': total_haber
            }
            
            return {'move_line_ids': transaction_data, 'totales':totales}
    
    
    def lineas(self, datos):
        
        totales = {}
        lineas = []
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0
        meses = {}

        company = self.env['res.company'].browse(datos['company_id'][0])

        journals_to_exclude = company.journals_to_exclude
        journals_to_exclude_str = ','.join([str(x.id) for x in journals_to_exclude])
        
        accounts_str = ','.join([str(x) for x in datos['cuentas_id']])

        if datos['grouping_type'] == 'daily':
            fechas = {}
            subtotales = {}
            if journals_to_exclude_str:
                sql = """
                    select ml.date as fecha, aa.id as No_Cuenta, aa.id as cuenta, aa.code as codigo_cuenta, SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, ml.move_id as move_id, am.ref as descripcion, ml.name as name 
                    from account_move_line ml 
                    inner join account_account aa on(ml.account_id = aa.id) 
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s and am.journal_id not in (%s)
                    group by  ml.account_id, ml.name, aa.id, aa.code, ml.move_id, am.name, am.ref, ml.date
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id), journals_to_exclude_str)
            else:
                sql = """
                    select ml.date as fecha, aa.id as No_Cuenta, aa.id as cuenta, aa.code as codigo_cuenta, SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, ml.move_id as move_id, am.ref as descripcion, ml.name as name 
                    from account_move_line ml 
                    inner join account_account aa on(ml.account_id = aa.id) 
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s
                    group by  ml.account_id, ml.name, aa.id, aa.code, ml.move_id, am.name, am.ref, ml.date
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id))
            self.env.cr.execute(sql)
            move_line_ids = self.env.cr.dictfetchall()
            for line in move_line_ids:
                date = line['fecha'].strftime('%d/%m/%Y')
                new_line = {
                        'descripcion': line['descripcion'] if line['descripcion'] else '-',
                        'codigo_cuenta': line['codigo_cuenta'],
                        'fecha_movimiento': date,
                        'cuenta': self.env['account.account'].browse(line['cuenta']).name,
                        'poliza': line['poliza'],
                        'haber': line['haber'],
                        'debe': line['debe'],
                        'name': line['name'],
                    }
                
                if date in fechas:
                    fechas[date].append(new_line)
                else:
                    data_lines = []
                    data_lines.append(new_line)
                    fechas[date] = data_lines

            total_debe = 0
            total_haber = 0
            for date in fechas:
                subtotal_debe = 0
                subtotal_haber = 0
                for line in fechas[date]:
                    subtotal_debe += line['debe']
                    subtotal_haber += line['haber']
                subtotales[date] = {
                    'subtotal_debe': subtotal_debe,
                    'subtotal_haber': subtotal_haber
                }
                total_haber += subtotal_haber
                total_debe += subtotal_haber
            totales = {
                'total_debe': total_debe,
                'total_haber': total_haber
            }
            return {'fechas': fechas, 'subtotales': subtotales, 'totales': totales}
            
        elif datos['grouping_type'] == 'monthly':
            if journals_to_exclude_str:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name  
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s and am.journal_id not in (%s)
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id), journals_to_exclude_str)
            else:
                sql = """
                    select ml.date as fecha, aa.id as cuenta_id, aa.code as codigo_cuenta,SUM(ml.debit) as debe, SUM(ml.credit) as haber, am.name as poliza, aa.name as cuenta, am.ref as descripcion, ml.name as name  
                    from account_move_line ml inner join account_account aa on(ml.account_id = aa.id)  
                    inner join account_move am on(am.id = ml.move_id)  
                    where ml.date >= '%s' and ml.date <= '%s' and aa.id in (%s) and am.state = 'posted' and am.company_id = %s
                    group by  ml.account_id,ml.name, aa.id, aa.code, am.name, am.ref,ml.date 
                    order by ml.date, aa.id
                """%(datos['fecha_desde'], datos['fecha_hasta'], accounts_str, str(company.id))
            self.env.cr.execute(sql)
            move_line_ids = self.env.cr.dictfetchall()
            total_debe = 0
            total_haber = 0
            subtotales = {}
            for line in move_line_ids:
                new_line = {
                        'descripcion': line['descripcion'] if line['descripcion'] else '-',
                        'fecha_movimiento': line['fecha'].strftime('%d/%m/%Y'),
                        'codigo': line['codigo_cuenta'],
                        'cuenta': self.env['account.account'].browse(line['cuenta_id']).name,
                        'poliza': line['poliza'],
                        'id': line['cuenta_id'],
                        'haber': line['haber'],                        
                        'debe': line['debe'],
                        'saldo_inicial': 0,
                        'name': line['name'],
                    }
                number_month = int(line['fecha'].strftime('%m'))
                month = self.get_month_name(number_month)
                if month in meses:
                    meses[month].append(new_line)
                else:
                    data_lines = []
                    data_lines.append(new_line)
                    meses[month] = data_lines

            total_debe = 0
            total_haber = 0
            for date in meses:
                subtotal_debe = 0
                subtotal_haber = 0
                for line in meses[date]:
                    subtotal_debe += line['debe']
                    subtotal_haber += line['haber']
                subtotales[date] = {
                    'subtotal_debe': subtotal_debe,
                    'subtotal_haber': subtotal_haber
                }
                total_haber += subtotal_haber
                total_debe += subtotal_haber
            totales = {
                'total_debe': total_debe,
                'total_haber': total_haber
            }
            return {'meses': meses,'totales': totales, 'subtotales':subtotales }

        elif datos['grouping_type'] == 'transaction':
            if journals_to_exclude_str:
                sql = """
                    select 
                        aml.date as fecha_movimiento,
                        aml.move_id as id_movimiento,
                        aa.id as cuenta_id,
                        aa.code as codigo_cuenta,
                        aml.debit as debe,
                        aml.credit as haber,
                        am.name as poliza,
                        am.ref as referencia,
                        aa.name as cuenta,
                        aml.name as name
                    from
                        account_move_line aml 
                    inner join
                        account_move am on(am.id = aml.move_id)
                    inner join account_account aa on
                        (aml.account_id = aa.id)	
                    where
                        aml.date >= '%s'
                        and aml.date <= '%s'
                        and am.company_id = %s
                        and aml.journal_id not in (%s)
                        and am.state = 'posted'
                    order by 
                        aml.id
                """%(str(datos['fecha_desde']),str(datos['fecha_hasta']),str(company.id),journals_to_exclude_str)
            else:
                sql = """
                    select 
                        aml.date as fecha_movimiento,
                        aml.move_id as id_movimiento,
                        aa.id as cuenta_id,
                        aa.code as codigo_cuenta,
                        aml.debit as debe,
                        aml.credit as haber,
                        am.name as poliza,
                        am.ref as referencia,
                        aa.name as cuenta,
                        aml.name as name
                    from
                        account_move_line aml 
                    inner join
                        account_move am on(am.id = aml.move_id)
                    inner join account_account aa on
                        (aml.account_id = aa.id)	
                    where
                        aml.date >= '%s'
                        and aml.date <= '%s'
                        and am.company_id = %s
                        and am.state = 'posted'
                    order by 
                        aml.id
                """%(str(datos['fecha_desde']),str(datos['fecha_hasta']),str(company.id))
            self.env.cr.execute(sql)
            move_line_ids = {} 
            
            for linea in self.env.cr.dictfetchall():
                nueva_linea ={
                        'referencia': linea['referencia'] if linea['referencia'] else '-',
                        'fecha_movimiento': linea['fecha_movimiento'].strftime('%d/%m/%Y'),
                        'id_movimiento': linea['id_movimiento'],
                        'codigo': linea['codigo_cuenta'],
                        'cuenta': self.env['account.account'].browse(linea['cuenta_id']).name,
                        'poliza': linea['poliza'],
                        'haber': linea['haber'],
                        'debe': linea['debe'], 
                        'name': linea['name'],  
                    }

                if str(linea['poliza']) in move_line_ids:
                    move_line_ids[str(linea['poliza'])].append(nueva_linea)
                else:
                    lineas = []
                    lineas.append(nueva_linea)
                    move_line_ids[str(linea['poliza'])] = lineas
            
            subtotales = {}
            totales = {}
            total_debe = 0
            total_haber = 0
            for move in move_line_ids:
                subtotal_debe = 0
                subtotal_haber = 0
                
                for line in move_line_ids[str(move)]:
                    subtotal_haber += abs(line['haber'])
                    subtotal_debe += abs(line['debe'])
                
                total_haber += abs(subtotal_haber)
                total_debe += abs(subtotal_debe)
                subtotales[str(move)] = {
                    'subtotal_haber': subtotal_haber,
                    'subtotal_debe': subtotal_debe
                }

            totales['total_haber'] = round(total_haber,2)
            totales['total_debe'] = round(total_debe, 2)
            return {'move_line_ids':move_line_ids, 'subtotales': subtotales, 'totales':totales}
            
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
        
        fecha_inicio = str(tmp_inicio[2])+"/"+str(tmp_inicio[1]+"/"+str(tmp_inicio[0]))
        fecha_final = str(tmp_final[2])+"/"+str(tmp_final[1]+"/"+str(tmp_final[0]))
        company = self.env['res.company'].browse(data['company_id'][0])
        data['fecha_inicio'] = fecha_inicio
        data['fecha_final'] = fecha_final
        data['anio_inicio'] = str(tmp_inicio[0])
        data['anio_final'] = str(tmp_final[0])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'lineas': self.lineas,
            'company_id': company,
        }