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


class ReporteInventario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_inventario'
    _description = 'Report Inventario'
    
    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.journal_id not in ('+journals_to_exclude_str+') and l.parent_state = %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,'posted'))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.parent_state = %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,'posted'))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde, journals_to_exclude_str=False):
        saldo_inicial = 0
        fecha = fields.Date.from_string(fecha_desde)
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.date >= %s and l.journal_id not in ('+journals_to_exclude_str+') and l.parent_state = %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,fecha.strftime('%Y-1-1'),'posted'))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
            'from account_move_line l join account_account a on(l.account_id = a.id)'\
            'where a.id = %s and l.date < %s and l.date >= %s and l.parent_state = %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,fecha.strftime('%Y-1-1'),'posted'))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def lineas(self, datos):
        totales = {}
        lineas_resumidas = {}
        lineas=[]
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0
        fecha_desde = datos['fecha_hasta']
        date_format = '%Y-%m-%d'
        date_obj = datetime.datetime.strptime(fecha_desde, date_format)

        fecha_desde =  str(date_obj.strftime("%Y") + '-' + '01' + '-' + '01')

        company = self.env['res.company'].browse(datos['company_id'][0])

        journals_to_exclude = company.journals_to_exclude
        journals_to_exclude_str = ','.join([str(x.id) for x in journals_to_exclude])

        accounts_str = ','.join([str(x) for x in datos['cuentas_id']])
        if journals_to_exclude_str:
            self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, sum(l.debit) as debe, sum(l.credit) as haber ' \
                'from account_move_line l join account_account a on(l.account_id = a.id)' \
                'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s and l.journal_id not in ('+journals_to_exclude_str+') and l.parent_state = %s group by a.id, a.code, a.name ORDER BY a.code',
            (company.id, fecha_desde, datos['fecha_hasta'],'posted'))
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.id as cuenta, sum(l.debit) as debe, sum(l.credit) as haber ' \
                'from account_move_line l join account_account a on(l.account_id = a.id)' \
                'where a.id in ('+accounts_str+') and l.company_id = %s and l.date >= %s and l.date <= %s and l.parent_state = %s group by a.id, a.code, a.name ORDER BY a.code',
            (company.id, fecha_desde, datos['fecha_hasta'],'posted'))

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
            l['saldo_inicial'] += self.retornar_saldo_inicial_inicio_anio(l['id'], fecha_desde, journals_to_exclude_str)
            l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
            totales['saldo_inicial'] += l['saldo_inicial']
            totales['saldo_final'] += l['saldo_final']

        return {'lineas': lineas,'totales': totales }

    def fecha_desde(self):
        fecha_desde = ''
        fecha_desde =  str(datetime.date.today().strftime("%Y") + '-' + '01' + '-' + '01')
        return fecha_desde

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        company = self.env['res.company'].browse(data['company_id'])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'fecha_desde': self.fecha_desde,
            'company_id': company
        }