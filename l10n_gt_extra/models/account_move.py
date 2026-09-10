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

from odoo import api, models, sql_db, fields, _, Command
from decimal import Decimal, ROUND_HALF_UP
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
import logging
from datetime import datetime

class AccountMove(models.Model):
    _inherit = 'account.move'

    nota_debito = fields.Boolean(string="Nota de debito")

    def impuesto_global(self):
        impuestos = self.env['l10n_gt_extra.impuestos'].search([['active','=',True],['tipo','=','compra']])
        impuestos_valores = []
        diferencia  = 0
        suma_impuesto = 0
        impuesto_total = 0
        rango_final_anterior = 0
        for rango in impuestos.rangos_ids:
            if self.amount_untaxed > rango.rango_final and diferencia == 0:
                diferencia = self.amount_untaxed - rango.rango_final
                impuesto_individual = rango.rango_final * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
            elif self.amount_untaxed <= rango.rango_final and diferencia == 0 and rango_final_anterior == 0:
                impuesto_individual = self.amount_untaxed * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                rango_final_anterior = rango.rango_final
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
            elif diferencia > 0:
                impuesto_individual = diferencia * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
        impuesto_total = 0
        self.update({'amount_tax': suma_impuesto, 'amount_total': impuesto_total + self.amount_untaxed})
        account_invoice_tax = self.env['account.invoice.tax']

        for impuesto in impuestos_valores:
            account_invoice_tax.create({'invoice_id': self.id,'tax_id':impuesto['impuesto_id'],'name': impuesto['nombre'],'account_id': impuesto['account_id'],'amount':impuesto['total'] })
        return True

    tax_withholding_isr = fields.Selection(
        [
            ('quarter_witholding', 'Sujeto a Pagos Trimestrales'),
            ('definitive_withholding', 'Sujeto a Retención Definitiva'),
            ('small_taxpayer_withholding',
             'P.C. No genera Devolución de Crédito Fiscal')
        ], string="Regimen Retención ISR", default="quarter_witholding"
    )
    tax_withholding_price = fields.Float(string='Monto de retención')
    tax_withholding_iva = fields.Selection(
        [
            ('no_witholding', 'No es agente rentenedor de IVA'),
            ('export', 'Exportadores'),
            ('decree_28_89', 'Beneficiarios del Decreto 28-89'),
            ('public_sector', 'Sector Público'),
            ('credit_cards_companies', 'Operadores de Tarjetas de Crédito y/o Débito'),
            ('special_taxpayer', 'Contribuyente Especiales'),
            ('special_taxpayer_export', 'Contribuyente Especial y Exportador'),
            ('others', 'Otros Agentes de Retención'),
            ('iva_forgiveness', 'Exención de IVA')
        ], string='Regimen Retención IVA', default=lambda self: self._set_initial_values())
    isr_withold_amount = fields.Monetary(string='Retención ISR', store=True)
    tax_withold_amount = fields.Monetary(string='Retención ISR 2', store=True)
    tax_withholding_amount_isr = fields.Monetary(string='Retención ISR Monto', store=True)
    iva_withold_amount = fields.Monetary(string='Retención/Exención IVA', store=True)
    tax_withholding_amount_iva = fields.Monetary(string='Retención/Exención IVA Monto', store=True)
    taxes_withold_calculated = fields.Boolean(string='Retenciónes y Exenciónes Calculadas')
    isr_withold_exclude_calculated = fields.Boolean(string='No Calcular Retención ISR')
    iva_withold_exclude_calculated = fields.Boolean(string='No Calcular Retención/Exención IVA')

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Tipo de Gasto", default="compra", compute='_compute_gt_move_type', store=True)
    
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción', related="journal_id.facturas_por_rangos")

    user_country_id = fields.Char(string="UserCountry", default=lambda self: self.env.company.country_id.code)

    type_invoice = fields.Selection(
        [
            ('FACT', 'Factura Normal'),
            ('FESP', 'Factura Especial'),
            ('FCAM', 'Factura Cambiaria'),
            ('FEXP', 'Factura Cambiaria Exp.'),
            ('NDEB', 'Nota de Débito'),
            ('NABN', 'Nota de Abono'),
            ('NCRE', 'Nota de Crédito'),
            ('RECI', 'Recibo'),
        ], string='Tipo de factura', default='FACT')

    ref_analytic_line_ids = fields.One2many('account.analytic.line', 'id', string='Analytic lines', compute="get_analytic_lines")
    show_analytic_lines = fields.Boolean(compute="get_show_analytic_lines", store=False)
    provider_invoice_serial = fields.Char(string="Factura serie", copy=False)
    provider_invoice_number = fields.Char(string="Factura número", copy=False)
    belongs_to_bank_statement = fields.Boolean(string="Pertenece a extracto bancario")
    is_service_invoice = fields.Boolean(string='Factura de Servicio(s)')

    amount_total_with_withold = fields.Monetary(string='Total c/ retenciones', compute='_calculate_amount_total_with_withold')

    not_include_sat_report = fields.Boolean(string="No Incluir en Reportes SAT")

    @api.depends('amount_total_in_currency_signed','iva_withold_amount','isr_withold_amount')
    def _calculate_amount_total_with_withold(self):
        for rec in self:
            if rec.move_type in ('in_invoice', 'out_refund', 'out_invoice', 'in_refund'):
                rec.amount_total_with_withold = abs(rec.amount_total_in_currency_signed) + rec.iva_withold_amount + rec.isr_withold_amount
            else:
                rec.amount_total_with_withold = rec.amount_total_in_currency_signed

    @api.onchange('isr_withold_exclude_calculated')
    def _onchange_isr_withold_exclude_calculated(self):
        if self.isr_withold_exclude_calculated:
            self.remove_isr_withold_lines()
        else:
            self._compute_amount()

    @api.onchange('iva_withold_exclude_calculated')
    def _onchange_iva_withold_exclude_calculated(self):
        if self.iva_withold_exclude_calculated:
            self.remove_iva_withold_lines()
        else:
            self._compute_amount()
    
    @api.constrains('provider_invoice_serial', 'provider_invoice_number')
    def _validate_unique_serial_invoice_number(self):
        if self.provider_invoice_serial and self.provider_invoice_number:
            invoice_data = self.search([
                ('provider_invoice_serial', '=', self.provider_invoice_serial), 
                ('provider_invoice_number', '=', self.provider_invoice_number), 
                ('partner_id', '=', self.partner_id.id),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ('posted','draft')),
                ('move_type', '=', 'in_invoice')
            ])
            if len(invoice_data) > 1:
                raise ValidationError("Ya existe una factura de proveedor creada con ese numero de serie y factura")
            else:
                if self.company_id.sale_report_invoice_number_field:
                    self.write({self.company_id.sale_report_invoice_number_field.name : self.provider_invoice_number})
                if self.company_id.sale_report_invoice_serie_field:
                    self.write({self.company_id.sale_report_invoice_serie_field.name : self.provider_invoice_serial})
    
    def check_isr_iva_lines(self):

        if not self.is_invoice(include_receipts=False) or self.company_id.ignore_tax_withholding:
            return True

        if not self.iva_withold_amount and not self.isr_withold_amount:
            return True

        company_id = self.company_id

        if not self.company_id.ignore_tax_withholding and self.partner_id:
            self.tax_withholding_isr = self._get_tax_withholding_isr()

            if self.move_type in ('out_invoice','out_refund'):
                self.tax_withholding_iva = self._get_company_iva_agent_type()
            elif self.move_type in ('in_invoice','in_refund'):
                self.tax_withholding_iva = company_id.tax_withholding_iva

        conversion_rate = self._get_conversion_rate()

        self._calculate_retention_iva(conversion_rate)
        self._calculate_retention_isr(conversion_rate)

        if not self.invoice_date:
            self.invoice_date = fields.Date.context_today(self)
        
        return True

    def _get_tax_withholding_isr(self):
        if self.partner_id.company_type == "company":
            return self.partner_id.tax_withholding_isr
        if self.partner_id.parent_id:
            return self.partner_id.parent_id.tax_withholding_isr
        return self.partner_id.tax_withholding_isr

    def _get_company_iva_agent_type(self):
        if self.partner_id.company_type == "company":
            return self.partner_id.tax_withholding_iva
        if self.partner_id.parent_id:
            return self.partner_id.parent_id.tax_withholding_iva
        return self.partner_id.tax_withholding_iva

    def _get_conversion_rate(self):
        if 'conversion_rate_ref' in self.env['account.move']._fields:
            return self.conversion_rate_ref
        return self.currency_id.with_context(date=self.invoice_date).rate

    def _calculate_retention_iva(self, conversion_rate):
        iva_retencion_account_id, iva_retencion_account_root_id, iva_aml_label = self._get_iva_accounts_and_label()
        if not self.iva_withold_exclude_calculated and self.iva_withold_amount > 0:
            self._update_or_create_iva_line(iva_retencion_account_id, iva_retencion_account_root_id, iva_aml_label, conversion_rate)

    def _calculate_retention_isr(self, conversion_rate):
        if not self.isr_withold_exclude_calculated and self.isr_withold_amount > 0:
            self._update_or_create_isr_line(conversion_rate)

    def _get_iva_accounts_and_label(self):
        if self.move_type in ('in_invoice','in_refund'):
            label = "Retención de IVA"
            account = self.company_id.iva_purchase_account_id
        else:
            label = "Exención de IVA"
            account = self.company_id.iva_sales_account_id

        if not account:
            raise ValidationError('Debe seleccionar el la cuenta a utilizar con retencion de IVA en compras')

        return account.id, account.root_id, label

    def _execute_sql(self, sql, params):
        with sql_db.db_connect(self._cr.dbname).cursor() as cr:
            cr.execute(sql, params)
            return cr.fetchall()

    def _update_or_create_iva_line(self, iva_retencion_account_id, iva_retencion_account_root_id, iva_aml_label, conversion_rate):
        iva_amount, iva_amount_currency, rate = self._calculate_amounts(self.iva_withold_amount, conversion_rate)
        operation_totals = self._get_operation_totals(self.move_type)
        self._process_existing_lines(
            account_id=iva_retencion_account_id, 
            label=iva_aml_label, 
            amount=iva_amount, 
            amount_currency=iva_amount_currency, 
            rate=rate, 
            operation_totals=operation_totals,
            is_iva=True
        )
        self._insert_new_line_if_needed(
            account_id=iva_retencion_account_id, 
            account_root_id=iva_retencion_account_root_id, 
            label=iva_aml_label, 
            amount=iva_amount, 
            amount_currency=iva_amount_currency,
        )

    def _update_or_create_isr_line(self, conversion_rate):
        isr_retencion_account_id, isr_retencion_account_root_id = self._get_isr_accounts()
        isr_amount, isr_amount_currency, rate = self._calculate_amounts(self.isr_withold_amount, conversion_rate)
        operation_totals = self._get_operation_totals(self.move_type)
        self._process_existing_lines(
            account_id=isr_retencion_account_id, 
            label='Retención de ISR', 
            amount=isr_amount, 
            amount_currency=isr_amount_currency, 
            rate=rate, 
            operation_totals=operation_totals,
            is_iva=False
        )
        self._insert_new_line_if_needed(
            account_id=isr_retencion_account_id, 
            account_root_id=isr_retencion_account_root_id, 
            label='Retención de ISR', 
            amount=isr_amount, 
            amount_currency=isr_amount_currency,
        )

    def _get_isr_accounts(self):
        if self.move_type in ('in_invoice','in_refund'):
            account = self.company_id.isr_purchase_account_id
        else:
            account = self.company_id.isr_sales_account_id

        if not account:
            raise ValidationError('Debe seleccionar la cuenta ISR en el diario de retención del ISR')

        return account.id, account.root_id

    def _calculate_amounts(self, amount, conversion_rate):
        amount_currency = amount
        rate = 1
        if self.currency_id.id != self.company_id.currency_id.id:
            rate = conversion_rate
            if not rate:
                rate = 1
            if rate > 1:
                rate = 1 / rate
            amount = amount / rate
        return amount, amount_currency, rate

    def _get_operation_totals(self, move_type):
        if move_type in ('in_invoice','out_refund'):
            field = 'debit'
        else:
            field = 'credit'

        sql = f"SELECT {field}, amount_currency FROM account_move_line WHERE move_id = %s and {field} > 0"
        params = (self.id,)
        results = self._execute_sql(sql, params)

        operation_total = sum(result[0] for result in results)  # assuming first column is debit or credit
        operation_currency_total = sum(result[1] for result in results)  # assuming second column is amount_currency

        return operation_total, operation_currency_total

    def _process_existing_lines(self, account_id, label, amount, amount_currency, rate, operation_totals, is_iva):
        sql = "SELECT id FROM account_move_line WHERE account_id = %s AND move_id = %s AND name = %s"
        params = (account_id, self.id, label)
        results = self._execute_sql(sql, params)

        if results:
            for result in results:
                if self.move_type in ('out_invoice','in_refund'):
                    sql = """UPDATE account_move_line SET 
                                price_unit = %s, debit = %s, amount_currency = %s, 
                                balance = %s, price_subtotal = %s, price_total = %s, 
                                write_uid = %s, write_date = %s 
                            WHERE id = %s"""
                    sql_params = (
                        amount, amount, amount_currency, amount, 
                        amount, amount, self.env.user.id, datetime.now(), result[0]
                    )
                else:
                    sql = """UPDATE account_move_line SET 
                                price_unit = %s, credit = %s, amount_currency = %s, 
                                balance = %s, price_subtotal = %s, amount_residual = %s, 
                                amount_residual_currency = %s, price_total = %s, 
                                write_uid = %s, write_date = %s 
                            WHERE id = %s"""
                    sql_params = (
                        amount * -1, amount, amount_currency * -1, amount * -1, 
                        amount * -1, amount * -1, amount_currency * -1, amount * -1, 
                        self.env.user.id, datetime.now(), result[0]
                    )
                self._cr.execute(sql, sql_params)
                self._cr.commit()
        else:
            self._update_partner_line(operation_totals, amount, amount_currency, is_iva, rate)

    def _update_partner_line(self, operation_totals, amount, amount_currency, is_iva, rate):
        for line in self.line_ids:
            if line.account_id.id == (self.partner_id.property_account_receivable_id.id if self.move_type in ('out_invoice','out_refund') else self.partner_id.property_account_payable_id.id):
                if is_iva:
                    other_amount, other_amount_currency, rate = self._calculate_amounts(self.isr_withold_amount, rate)
                else:
                    other_amount, other_amount_currency, rate = self._calculate_amounts(self.iva_withold_amount, rate)

                partner_amount = round(operation_totals[0] - amount - other_amount, 2)
                if self.move_type in ('out_invoice','in_refund'):
                    partner_amount_currency = abs(round(operation_totals[1] + amount_currency + other_amount_currency, 2))
                else:
                    partner_amount_currency = abs(round(operation_totals[1] - amount_currency - other_amount_currency, 2))

                if self.move_type in ('out_invoice','in_refund'):
                    sql = """UPDATE account_move_line SET 
                                price_unit = %s, debit = %s, amount_currency = %s, 
                                balance = %s, price_subtotal = %s, amount_residual = %s, 
                                amount_residual_currency = %s, price_total = %s, 
                                write_uid = %s, write_date = %s 
                            WHERE id = %s"""
                    sql_params = (
                        partner_amount * -1, partner_amount, partner_amount_currency, 
                        partner_amount, partner_amount * -1, partner_amount,
                        partner_amount_currency, partner_amount * -1,
                        self.env.user.id, datetime.now(), line.id
                    )
                else:
                    sql = """UPDATE account_move_line SET 
                                price_unit = %s, credit = %s, amount_currency = %s, 
                                balance = %s, price_subtotal = %s, amount_residual = %s, 
                                amount_residual_currency = %s, price_total = %s, 
                                write_uid = %s, write_date = %s 
                            WHERE id = %s"""
                    sql_params = (
                        partner_amount * -1, partner_amount, partner_amount_currency * -1, 
                        partner_amount * -1, partner_amount, partner_amount * -1, 
                        partner_amount_currency * -1, partner_amount * -1, 
                        self.env.user.id, datetime.now(), line.id
                    )

                self._cr.execute(sql, sql_params)
                self._cr.commit()
                self.env.invalidate_all()

    def _insert_new_line_if_needed(self, account_id, account_root_id, label, amount, amount_currency):
        for line in self.line_ids:
            if account_id == line.account_id.id and line.name == label:
                return
        move_date = self.date or datetime.now().date()
        sql = """INSERT INTO account_move_line (
                    move_id, move_name, date, parent_state, journal_id, company_id, company_currency_id, 
                    account_id, account_root_id, sequence, name, quantity, price_unit, discount, debit, 
                    credit, balance, amount_currency, price_subtotal, price_total, currency_id, partner_id, 
                    display_type, create_uid, create_date, write_uid, write_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )"""
        sign = 1
        if self.move_type in ('out_invoice','in_refund'):
            sign = -1

        sql_params = (
            self.id, self.name, move_date, self.state, self.journal_id.id, self.company_id.id, 
            self.company_id.currency_id.id, account_id, account_root_id.id, 
            "10", label, 1, amount * sign, 0, amount if sign == -1 else 0, amount if sign == 1 else 0, 
            amount * -sign, amount_currency * -sign, amount * sign, amount * sign, self.currency_id.id, 
            self.partner_id.id, 'tax', self.env.user.id, datetime.now(), self.env.user.id, datetime.now()
        )
        self._cr.execute(sql, sql_params)
        self._cr.commit()
        self.env.invalidate_all()

    def remove_isr_withold_lines(self):
        for rec in self:
            
            isr_retencion_account_id, isr_retencion_account_root_id = self._get_isr_accounts()

            sql = ""
            sql += "SELECT id"
            sql += " FROM account_move_line"
            sql += " WHERE account_id = %s" % (isr_retencion_account_id)
            sql += " AND move_id = %s AND name = '%s'" % (rec._origin.id, "Retención de ISR")
            
            cr_log = sql_db.db_connect(rec.env.cr.dbname).cursor()
            cr_log.execute(sql)

            for query_data in cr_log.dictfetchall():

                sql = ""
                sql += "UPDATE account_move_line"
                sql += " SET price_unit = %s," % (0)
                sql += " debit = %s," % (0)
                sql += " credit = %s," % (0)
                sql += " amount_currency = %s," % (0)
                sql += " balance = %s," % (0)
                sql += " price_subtotal = %s," % (0)
                sql += " amount_residual = %s," % (0)
                sql += " amount_residual_currency = %s," % (0)
                sql += " price_total = %s," % (0)
                sql += " display_type = 'product'," 
                sql += " write_uid = %s," % (rec.env.user.id)
                sql += " write_date = '%s'" % (datetime.now())
                sql += " WHERE id = %s" % (query_data['id'])

                rec._cr.execute(sql)
                rec._cr.commit()

                operation_total = 0
                operation_currency_total = 0
                self.env.invalidate_all()

                if rec.move_type in ('in_invoice','out_refund'):
                    sql = ""
                    sql += "SELECT debit, amount_currency"
                    sql += " FROM account_move_line"
                    sql += " WHERE debit > 0"
                    sql += " AND   move_id = %s" % (rec._origin.id)
                    
                    cr_total = sql_db.db_connect(rec.env.cr.dbname).cursor()
                    cr_total.execute(sql)
                    
                    for query_data in cr_total.dictfetchall():
                        operation_total += query_data['debit']
                        operation_currency_total += query_data['amount_currency']
                    
                    account_payable_id = rec.partner_id.property_account_payable_id.id if rec.move_type == 'in_invoice' else rec.partner_id.property_account_receivable_id.id

                    for line in rec._origin.line_ids:
                        if line.account_id.id == account_payable_id:
                            partner_amount = operation_total * -1
                            price_unit = partner_amount
                            credit = partner_amount
                            partner_amount_currency = operation_currency_total
                            amount_currency = partner_amount_currency * -1
                            balance = partner_amount
                            price_subtotal = partner_amount 
                            amount_residual = partner_amount
                            amount_residual_currency = amount_currency
                            price_total = partner_amount
                            
                            sql = ""
                            sql += "UPDATE account_move_line"
                            sql += " SET price_unit = %s," % (price_unit)
                            sql += " credit = %s," % (credit)
                            sql += " amount_currency = %s," % (amount_currency)
                            sql += " balance = %s," % (balance)
                            sql += " price_subtotal = %s," % (price_subtotal)
                            sql += " amount_residual = %s," % (amount_residual)
                            sql += " amount_residual_currency = %s," % (amount_residual_currency)
                            sql += " price_total = %s," % (price_total)
                            sql += " write_uid = %s," % (rec.env.user.id)
                            sql += " write_date = '%s'" % (datetime.now())
                            sql += " WHERE id = %s" % (line.id)
                            
                            rec._cr.execute(sql)
                            rec._cr.commit()
                            self.env.invalidate_all()

                        if line.balance == 0:
                            line.sudo().unlink()

                elif rec.move_type in ('out_invoice','in_refund'):
                    sql = ""
                    sql += "SELECT credit, amount_currency"
                    sql += " FROM account_move_line"
                    sql += " WHERE credit > 0"
                    sql += " AND   move_id = %s" % (rec._origin.id)
                    
                    cr_total = sql_db.db_connect(rec.env.cr.dbname).cursor()
                    cr_total.execute(sql)
                    
                    for query_data in cr_total.dictfetchall():
                        operation_total += query_data['credit']
                        operation_currency_total += query_data['amount_currency']

                    account_receivable_id = rec.partner_id.property_account_payable_id.id if rec.move_type == 'in_refund' else rec.partner_id.property_account_receivable_id.id

                    for line in rec._origin.line_ids:
                        if line.account_id.id == account_receivable_id:
                            partner_amount = operation_total
                            price_unit = partner_amount
                            debit = partner_amount
                            partner_amount_currency = operation_currency_total
                            amount_currency = partner_amount_currency * -1
                            balance = partner_amount
                            price_subtotal = partner_amount 
                            amount_residual = partner_amount
                            amount_residual_currency = amount_currency
                            price_total = partner_amount
                            
                            sql = ""
                            sql += "UPDATE account_move_line"
                            sql += " SET price_unit = %s," % (price_unit)
                            sql += " debit = %s," % (debit)
                            sql += " amount_currency = %s," % (amount_currency)
                            sql += " balance = %s," % (balance)
                            sql += " price_subtotal = %s," % (price_subtotal)
                            sql += " amount_residual = %s," % (amount_residual)
                            sql += " amount_residual_currency = %s," % (amount_residual_currency)
                            sql += " price_total = %s," % (price_total)
                            sql += " write_uid = %s," % (rec.env.user.id)
                            sql += " write_date = '%s'" % (datetime.now())
                            sql += " WHERE id = %s" % (line.id)
                            
                            rec._cr.execute(sql)
                            rec._cr.commit()
                            self.env.invalidate_all()

                        if line.balance == 0:
                            line.sudo().unlink()

            rec.write({'isr_withold_amount': 0,'tax_withholding_amount_isr':0,'isr_withold_exclude_calculated':True})

        return True

    def remove_iva_withold_lines(self):
        for rec in self:
            company_id = rec.company_id
            
            iva_retencion_account_id, iva_retencion_account_root_id, iva_aml_label = self._get_iva_accounts_and_label()

            sql = ""
            sql += "SELECT id"
            sql += " FROM account_move_line"
            sql += " WHERE account_id = %s" % (iva_retencion_account_id)
            sql += " AND   move_id = %s AND name = '%s'" % (rec._origin.id, iva_aml_label)
            
            cr_log = sql_db.db_connect(rec.env.cr.dbname).cursor()
            cr_log.execute(sql)

            for query_data in cr_log.dictfetchall():

                sql = ""
                sql += "UPDATE account_move_line"
                sql += " SET price_unit = %s," % (0)
                sql += " debit = %s," % (0)
                sql += " credit = %s," % (0)
                sql += " amount_currency = %s," % (0)
                sql += " balance = %s," % (0)
                sql += " price_subtotal = %s," % (0)
                sql += " amount_residual = %s," % (0)
                sql += " amount_residual_currency = %s," % (0)
                sql += " price_total = %s," % (0)
                sql += " display_type = 'product',"
                sql += " write_uid = %s," % (rec.env.user.id)
                sql += " write_date = '%s'" % (datetime.now())
                sql += " WHERE id = %s" % (query_data['id'])

                rec._cr.execute(sql)
                rec._cr.commit()

                operation_total = 0
                operation_currency_total = 0
                self.env.invalidate_all()

                if rec.move_type in ('in_invoice','out_refund'):
                    sql = ""
                    sql += "SELECT debit, amount_currency"
                    sql += " FROM account_move_line"
                    sql += " WHERE debit > 0"
                    sql += " AND   move_id = %s" % (rec._origin.id)
                    
                    cr_total = sql_db.db_connect(rec.env.cr.dbname).cursor()
                    cr_total.execute(sql)
                    
                    for query_data in cr_total.dictfetchall():
                        operation_total += query_data['debit']
                        operation_currency_total += query_data['amount_currency']

                    account_payable_id = rec.partner_id.property_account_payable_id.id if rec.move_type == 'in_invoice' else rec.partner_id.property_account_receivable_id.id

                    for line in rec._origin.line_ids:
                        if line.account_id.id == account_payable_id:
                            partner_amount = operation_total - rec.isr_withold_amount
                            price_unit = partner_amount 
                            credit = partner_amount
                            partner_amount_currency = operation_currency_total - rec.isr_withold_amount
                            amount_currency = partner_amount_currency 
                            balance = partner_amount
                            price_subtotal = partner_amount
                            amount_residual = partner_amount
                            amount_residual_currency = amount_currency
                            price_total = partner_amount
                            
                            sql = ""
                            sql += "UPDATE account_move_line"
                            sql += " SET price_unit = %s," % (price_unit)
                            sql += " credit = %s," % (credit)
                            sql += " amount_currency = %s," % (amount_currency)
                            sql += " balance = %s," % (balance)
                            sql += " amount_residual = %s," % (amount_residual)
                            sql += " amount_residual_currency = %s," % (amount_residual_currency)
                            sql += " price_subtotal = %s," % (price_subtotal)
                            sql += " price_total = %s," % (price_total)
                            sql += " write_uid = %s," % (rec.env.user.id)
                            sql += " write_date = '%s'" % (datetime.now())
                            sql += " WHERE id = %s" % (line.id)
                            
                            rec._cr.execute(sql)
                            rec._cr.commit()
                            self.env.invalidate_all()

                        if line.balance == 0:
                            line.sudo().unlink()

                elif rec.move_type in ('out_invoice','in_refund'):
                    sql = ""
                    sql += "SELECT credit, amount_currency"
                    sql += " FROM account_move_line"
                    sql += " WHERE credit > 0"
                    sql += " AND   move_id = %s" % (rec._origin.id)
                    
                    cr_total = sql_db.db_connect(rec.env.cr.dbname).cursor()
                    cr_total.execute(sql)
                    
                    for query_data in cr_total.dictfetchall():
                        operation_total += query_data['credit']
                        operation_currency_total += query_data['amount_currency']

                    account_receivable_id = rec.partner_id.property_account_payable_id.id if rec.move_type == 'in_refund' else rec.partner_id.property_account_receivable_id.id

                    for line in rec._origin.line_ids:
                        if line.account_id.id == account_receivable_id:
                            partner_amount = operation_total
                            price_unit = partner_amount * -1
                            debit = partner_amount
                            partner_amount_currency = operation_currency_total
                            amount_currency = partner_amount_currency  * -1
                            balance = partner_amount
                            price_subtotal = partner_amount * -1
                            amount_residual = partner_amount
                            amount_residual_currency = amount_currency
                            price_total = partner_amount * -1
                            
                            sql = ""
                            sql += "UPDATE account_move_line"
                            sql += " SET price_unit = %s," % (price_unit)
                            sql += " debit = %s," % (debit)
                            sql += " amount_currency = %s," % (amount_currency)
                            sql += " balance = %s," % (balance)
                            sql += " amount_residual = %s," % (amount_residual)
                            sql += " amount_residual_currency = %s," % (amount_residual_currency)
                            sql += " price_subtotal = %s," % (price_subtotal)
                            sql += " price_total = %s," % (price_total)
                            sql += " write_uid = %s," % (rec.env.user.id)
                            sql += " write_date = '%s'" % (datetime.now())
                            sql += " WHERE id = %s" % (line.id)
                            
                            rec._cr.execute(sql)
                            rec._cr.commit()
                            self.env.invalidate_all()

                        if line.balance == 0:
                            line.sudo().unlink()

            rec.write({'tax_withholding_amount_iva': 0,'iva_withold_amount':0,'iva_withold_exclude_calculated':True})

        return True

    def _post(self, soft=True):
        # Call the super method if soft is True or there are no records in self
        if soft or not self:
            return super(AccountMove, self)._post(soft)

        for rec in self:
            if rec.is_invoice(include_receipts=True):
                if rec.iva_withold_amount > 0 or rec.isr_withold_amount > 0:
                    rec.check_isr_iva_lines()
                rec.taxes_withold_calculated = True
            # Call the super method for each record in self
            res = super(AccountMove, self)._post(soft)
            return res

    def button_draft(self):
        for rec in self:
            rec.taxes_withold_calculated = False
        return super(AccountMove, self).button_draft()

    def get_show_analytic_lines(self):
        for rec in self:
            rec.show_analytic_lines = self.env.user.company_id.show_analytic_lines

    def get_analytic_lines(self):
        for rec in self:
            rec.ref_analytic_line_ids = False
            if rec.line_ids:
                rec.ref_analytic_line_ids = rec.line_ids.analytic_line_ids

    @api.onchange('type_invoice')
    def onchange_type_invoice(self):
        if 'fel_gt_invoice_type' in self.env['account.move']._fields:
            self.fel_gt_invoice_type = self.type_invoice

    @api.model
    def _set_initial_values(self):
        initial_iva_withhold = 'no_witholding'
        default_move_type = self.default_get(['move_type'])
        
        if default_move_type['move_type'] in ('out_invoice','in_refund'):
            if self.partner_id:
                if self.partner_id.company_type == "company":
                    initial_iva_withhold = self.partner_id.tax_withholding_iva
                else:
                    if self.partner_id.parent_id:
                        initial_iva_withhold = self.partner_id.parent_id.tax_withholding_iva
                    else:
                        initial_iva_withhold = self.partner_id.tax_withholding_iva
        if default_move_type['move_type'] in ('in_invoice','out_refund'):
            initial_iva_withhold = self.company_id.tax_withholding_iva
        return initial_iva_withhold
 
    @api.constrains('inicial_rango', 'final_rango')
    def _validar_rango(self):
        if self.diario_facturas_por_rangos:
            if int(self.final_rango) < int(self.inicial_rango):
                raise ValidationError('El número inicial del rango es mayor que el final.')
            cruzados = self.search([('serie_rango', '=', self.serie_rango), ('inicial_rango', '<=', self.inicial_rango), ('final_rango', '>=', self.inicial_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
            cruzados = self.search([('serie_rango', '=', self.serie_rango), ('inicial_rango', '<=', self.final_rango), ('final_rango', '>=', self.final_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
            cruzados = self.search([('serie_rango', '=', self.serie_rango), ('inicial_rango', '>=', self.inicial_rango), ('inicial_rango', '<=', self.final_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')

            self.name = "{}-{} al {}-{}".format(self.serie_rango, self.inicial_rango, self.serie_rango, self.final_rango)

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        response = super(AccountMove, self)._onchange_partner_id()
        company_iva_agent_type = self.company_id.tax_withholding_iva
        if self.partner_id:
            isr_withold_type = ""
            iva_withold_type = "no_witholding"

            if self.move_type in ('in_invoice','in_refund'):
                if self.partner_id.company_type == "company":
                    isr_withold_type = self.partner_id.tax_withholding_isr
                else:
                    if self.partner_id.parent_id:
                        isr_withold_type = self.partner_id.parent_id.tax_withholding_isr
                    else:
                        isr_withold_type = self.partner_id.tax_withholding_isr
            
            if self.move_type in ('out_invoice','out_refund'):
                isr_withold_type = self.company_id.tax_withholding_isr
                

            self.tax_withholding_isr = isr_withold_type

            if self.partner_id.tax_withholding_isr == "small_taxpayer_withholding" and self.move_type == 'in_invoice':

                for invoice_lines in self.invoice_line_ids:
                    invoice_lines.tax_ids = False

                move_lines = []
                for move_line in self.line_ids:
                    if not move_line.tax_line_id.id:
                        move_lines.append(move_line.id)

                self.line_ids = move_lines
            else:

                default_tax = False
                if self.move_type in ('out_invoice','out_refund'):
                    default_tax = self.company_id.account_purchase_tax_id
                if self.move_type in ('in_invoice','in_refund'):
                    default_tax = self.company_id.account_sale_tax_id

                for invoice_lines in self.invoice_line_ids:
                    if len(invoice_lines.tax_ids) == 0:
                        tax_ids = []
                        if not invoice_lines.product_id.product_tmpl_id.taxes_id.id:
                            tax_ids.append(default_tax.id)
                            invoice_lines.tax_ids = default_tax

                            for line in invoice_lines:
                                if not line.product_id or line.display_type in ('line_section', 'line_note'):
                                    continue
                                line.name = line._compute_name()
                                line.account_id = line._compute_account_id()
                                line.tax_ids = line._compute_tax_ids()
                                line.product_uom_id = line._compute_product_uom_id()
                                line.price_unit = line._compute_price_unit()
                        else:
                            if default_tax != False:
                                for tax in invoice_lines.product_id.product_tmpl_id.taxes_id:
                                    tax_ids.append(tax.id)
                            invoice_lines.tax_ids = tax_ids

            if not self.journal_id.is_receipt_journal:
                if self.move_type in ('out_invoice','out_refund'):
                    if self.partner_id.company_type == "company":
                        company_iva_agent_type = self.partner_id.tax_withholding_iva
                    else:
                        if self.partner_id.parent_id:
                            company_iva_agent_type = self.partner_id.parent_id.tax_withholding_iva
                        else:
                            company_iva_agent_type = self.partner_id.tax_withholding_iva

                    if company_iva_agent_type != 'no_witholding':
                        self.tax_withholding_iva = company_iva_agent_type
                        self.amount_total = self.amount_total + self.tax_withholding_amount_iva
                        self.tax_withholding_amount_iva = 0
                    else:
                        self.tax_withholding_iva = company_iva_agent_type

                # FACTURAS COMPRA
                if self.move_type in ('in_invoice','in_refund'):
                    company_iva_agent_type = self.company_id.tax_withholding_iva
                    if company_iva_agent_type != 'no_witholding':
                        self.tax_withholding_iva = company_iva_agent_type
                        self.amount_total = self.amount_total + self.tax_withholding_amount_iva
                        self.tax_withholding_amount_iva = 0
                    else:
                        self.tax_withholding_iva = company_iva_agent_type

        return response

    def _compute_base_line_taxes_gt_extra(self, base_line):
        move = base_line.move_id
        if move.is_invoice(include_receipts=True):
            handle_price_include = True
            sign = -1 if move.is_inbound() else 1
            quantity = base_line.quantity
            is_refund = move.move_type in ('out_refund', 'in_refund')
            price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
        else:
            handle_price_include = False
            quantity = 1.0
            tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
            is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
            price_unit_wo_discount = base_line.amount_currency

        return base_line.tax_ids._origin.compute_all(
            price_unit_wo_discount,
            currency=base_line.currency_id,
            quantity=quantity,
            product=base_line.product_id,
            partner=base_line.partner_id,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
            include_caba_tags=move.always_tax_exigible,
        )

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state',
        'partner_id',
    )
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()

        for move in self:
            if not move.is_invoice(include_receipts=False) or self.company_id.ignore_tax_withholding:
                continue

            move.isr_withold_amount = 0
            move.iva_withold_amount = 0
            if move.is_invoice(include_receipts=False):
                company_iva_agent_type = move._get_company_iva_agent_type()
                iva_withhold_amount = move._calculate_iva_withholding(company_iva_agent_type)
                move.tax_withholding_amount_iva = iva_withhold_amount
                move.iva_withold_amount = iva_withhold_amount

                sign = 1 if move.move_type in ['out_invoice', 'in_refund'] else -1

                if move.currency_id and move.currency_id != move.company_id.currency_id:
                    move.amount_total = sign * (move.amount_untaxed_signed + move.amount_tax_signed - move.tax_withholding_amount_isr - move.tax_withholding_amount_iva)

                isr_withold_type = move._get_isr_withold_type()
                if move.move_type in ('out_invoice','out_refund') and not move.iva_withold_exclude_calculated and not move.journal_id.is_receipt_journal:
                    move._calculate_out_invoice_withholding(isr_withold_type, company_iva_agent_type)
                
                if move.move_type in ('in_invoice','in_refund') and not move.iva_withold_exclude_calculated and not move.journal_id.is_receipt_journal:
                    move._calculate_in_invoice_withholding(isr_withold_type, company_iva_agent_type)

                if (isr_withold_type == 'definitive_withholding' and not move.journal_id.is_receipt_journal and move.partner_id.vat and move.partner_id.vat.upper() != "CF" and not move.isr_withold_exclude_calculated) or move.type_invoice == 'FESP':
                    move._calculate_isr_withholding()

                if not move.taxes_withold_calculated:
                    move._calculate_residual_amount()

            if not move.is_invoice(include_receipts=True):
                move.tax_withholding_amount_isr = 0
                move.tax_withholding_amount_iva = 0
                

    def _get_company_iva_agent_type(self):
        return self.company_id.tax_withholding_iva

    def _calculate_iva_withholding(self, iva_agent_type):
        iva_withhold_amount = 0
        for invoice_line in self.invoice_line_ids:
            if self._is_applicable_for_iva_withholding(invoice_line, iva_agent_type):
                iva_amount = self._calculate_iva_amount(invoice_line)
                iva_withhold_amount += iva_amount
        return iva_withhold_amount

    def _is_applicable_for_iva_withholding(self, invoice_line, iva_agent_type):
        if iva_agent_type == 'iva_forgiveness':
            return False
        return invoice_line.product_id.product_tmpl_id.categ_id.sat_iva_type_product in ['good_services', 'agriculture', 'not_agriculture']

    def _calculate_iva_amount(self, invoice_line):
        iva_amount = invoice_line.price_total - invoice_line.price_subtotal
        if 'fel_timbre_tax' in self.env['account.tax']._fields:
            timbre_tax_fel = any(tax.fel_timbre_tax for tax in invoice_line.tax_ids)
            if timbre_tax_fel:
                timbre_amount = invoice_line.price_total / 1.125 * 0.005
                iva_amount -= timbre_amount
        gas_tax = any(tax.sat_tax_type == 'gas' for tax in invoice_line.tax_ids)
        if gas_tax:
            for tax_line in invoice_line.tax_ids.filtered(lambda x : x.sat_tax_type == 'gas'):
                tax_amount = self._get_gas_amount(tax_line.sat_tax_gas_type)
                gas_tax_amount = invoice_line.quantity * tax_amount
                iva_amount -= gas_tax_amount
        if iva_amount <= 0:
            base_amount_gtq = invoice_line.price_total
            rate = 1
            if self.currency_id.id != self.company_id.currency_id.id:
                rate = self._get_conversion_rate()
                if not rate:
                    rate = 1
                elif rate > 1:
                    rate = 1 / rate
                rate = round(rate, 10)
                base_amount_gtq = invoice_line.price_total / rate
                base_amount_gtq /= 1.12
                base_amount_gtq = round(base_amount_gtq, 2)
                iva_amount = (invoice_line.price_total / rate) - base_amount_gtq
                iva_amount *= rate
            else:
                base_amount_gtq = invoice_line.price_total / rate
                base_amount_gtq /= 1.12
                base_amount_gtq = round(base_amount_gtq, 2)
                iva_amount = invoice_line.price_total - base_amount_gtq
        return iva_amount
    
    def _get_gas_amount(self, gas_type):
        if gas_type == 'super':
            return 4.7
        if gas_type == 'regular':
            return 4.6
        if gas_type == 'disel':
            return 1.3

    def _get_isr_withold_type(self):
        isr_withhold_type = ''
        if self.move_type in ('out_invoice','out_refund'):
            isr_withhold_type = self.company_id.tax_withholding_isr
        elif self.move_type in ('in_invoice','in_refund'):
            if not self.partner_id.parent_id:
                isr_withhold_type = self.partner_id.tax_withholding_isr
            elif self.partner_id.parent_id:
                isr_withhold_type = self.partner_id.parent_id.tax_withholding_isr
            else:
                isr_withhold_type = self.partner_id.tax_withholding_isr
        return isr_withhold_type
    
    def _calculate_iva_forgiveness_withholding(self):
        iva_withhold_amount = 0
        for invoice_line in self.invoice_line_ids:
            timbre_tax_fel = False
            if 'fel_timbre_tax' in self.env['account.tax']._fields:
                if invoice_line.tax_ids:
                    for tax in invoice_line.tax_ids:
                        if tax.fel_timbre_tax:
                            timbre_tax_fel = True
                            
            if invoice_line.product_id.product_tmpl_id.categ_id.sat_iva_type_product == 'good_services':
                iva_amount = invoice_line.price_total - invoice_line.price_subtotal
                if not timbre_tax_fel:
                    iva_withhold_amount += iva_amount
                else:
                    timbre_amount = invoice_line.price_total / 1.125
                    timbre_amount = timbre_amount * 0.005
                    iva_amount = iva_amount - timbre_amount
                    iva_withhold_amount += iva_amount
        return iva_withhold_amount

    def _calculate_out_invoice_withholding(self, isr_withold_type, company_iva_agent_type):
        if self.partner_id.company_type == "company":
            partner_iva_agent_type = self.partner_id.tax_withholding_iva
        else:
            partner_iva_agent_type = self.partner_id.parent_id.tax_withholding_iva if self.partner_id.parent_id else self.partner_id.tax_withholding_iva
        
        if self.fiscal_position_id and self.fiscal_position_id.tax_withold:
            partner_iva_agent_type = 'iva_forgiveness'
        iva_withhold_amount = 0
        if partner_iva_agent_type == 'iva_forgiveness':
            iva_withhold_amount = self._calculate_iva_forgiveness_withholding()
        if partner_iva_agent_type != 'no_witholding' and company_iva_agent_type == 'no_witholding':
            iva_withhold_amount += self._calculate_other_iva_withholding(partner_iva_agent_type, isr_withold_type)
        self.iva_withold_amount = iva_withhold_amount
        self.amount_total -= iva_withhold_amount

    def _calculate_in_invoice_withholding(self, isr_withold_type, company_iva_agent_type):
        if self.partner_id.company_type == "company":
            partner_iva_agent_type = self.partner_id.tax_withholding_iva
        else:
            partner_iva_agent_type = self.partner_id.parent_id.tax_withholding_iva if self.partner_id.parent_id else self.partner_id.tax_withholding_iva
        iva_withhold_amount = 0
        if company_iva_agent_type != 'no_witholding' and partner_iva_agent_type == 'no_witholding':
            iva_withhold_amount = self._calculate_other_iva_withholding(company_iva_agent_type, isr_withold_type)
        self.iva_withold_amount = iva_withhold_amount
        self.amount_total -= iva_withhold_amount
        self.tax_withholding_amount_iva = iva_withhold_amount

    def _calculate_isr_withholding(self):
        base_amount_gtq = self.amount_untaxed
        rate = 1
        if self.currency_id.id != self.company_id.currency_id.id:
            rate = self._get_conversion_rate()
            if not rate:
                rate = 1
            elif rate > 1:
                rate = 1 / rate
            rate = round(rate, 10)
            base_amount_gtq = self.amount_untaxed / rate
        has_taxes = any(move_line.tax_line_id for move_line in self.line_ids)
        if not has_taxes:
            base_amount_gtq /= 1.12
            base_amount_gtq = round(base_amount_gtq, 2)
        isr_amount = 0
        if base_amount_gtq > 30000.00:
            base_amount_gtq -= 30000
            isr_amount = ((base_amount_gtq * 7) / 100.00) + 1500.00
            if self.currency_id.id != self.company_id.currency_id.id:
                isr_amount *= rate
            isr_amount = Decimal(isr_amount).quantize(Decimal('0.01'), ROUND_HALF_UP)
        elif 2500.00 <= base_amount_gtq <= 30000.00:
            isr_amount = ((base_amount_gtq * 5) / 100.00)
            if self.currency_id.id != self.company_id.currency_id.id:
                isr_amount *= rate
            isr_amount = Decimal(isr_amount).quantize(Decimal('0.01'), ROUND_HALF_UP)
        self.isr_withold_amount = isr_amount
        self.tax_withholding_amount_isr = isr_amount
        self.amount_total -= float(isr_amount)

    def _calculate_residual_amount(self):
        amount_residual_signed = self.amount_total_signed
        if self.currency_id.id != self.company_id.currency_id.id:
            rate = self._get_conversion_rate()
            if not rate:
                rate = 1
            if rate > 1:
                rate = 1 / rate
            rate = round(rate, 10)
            amount_residual_signed = self.amount_total_signed / rate
        if self.move_type in ('in_invoice','out_refund'):
            amount_residual_signed *= -1
        if self.iva_withold_amount > 0 or self.isr_withold_amount > 0:
            self.amount_residual = amount_residual_signed
            self.amount_residual_signed = self.amount_total_signed

    def _calculate_other_iva_withholding(self, iva_agent_type, isr_withold_type):
        iva_withhold_amount = 0
        base_amount = self._calculate_base_amount()
        for invoice_line in self.invoice_line_ids:
            if isr_withold_type == 'small_taxpayer_withholding' and base_amount >= 2500:
                iva_withhold_amount += self._calculate_small_taxpayer_withholding(invoice_line)
            elif self.type_invoice == 'FESP':
                iva_withhold_amount += self._calculate_special_invoice_withholding(invoice_line)
            else:
                if iva_agent_type == 'export' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_export_withholding(invoice_line)
                if iva_agent_type == 'decree_28_89' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_decree_28_89_withholding(invoice_line)
                if iva_agent_type == 'public_sector' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_public_sector_withholding(invoice_line)
                if iva_agent_type == 'credit_cards_companies' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_credit_cards_companies_withholding(invoice_line)
                if iva_agent_type == 'special_taxpayer' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_special_taxpayer_withholding(invoice_line)
                if iva_agent_type == 'others' and base_amount >= 2500:
                    iva_withhold_amount += self._calculate_others_withholding(invoice_line)
        return iva_withhold_amount

    def _calculate_base_amount(self):
        company_currency = self.company_id.currency_id
        has_foreign_currency = self.currency_id and self.currency_id != company_currency
        if not has_foreign_currency:
            return self.amount_total
        else:
            conversion_rate = self._get_conversion_rate()
            if not conversion_rate:
                conversion_rate = 1
            elif conversion_rate < 1:
                conversion_rate = 1 / conversion_rate
            conversion_rate = round(conversion_rate, 10)
        return self.amount_total * conversion_rate

    def _calculate_small_taxpayer_withholding(self, invoice_line):
        total_amount = invoice_line.price_total
        iva_amount = total_amount * 0.05
        return iva_amount

    def _calculate_special_invoice_withholding(self, invoice_line):
        iva_amount = invoice_line.price_total - invoice_line.price_subtotal
        return iva_amount

    def _calculate_export_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.65 if invoice_line.product_id.product_tmpl_id.categ_id.sat_iva_type_product == 'agriculture' else self._calculate_iva_amount(invoice_line) * 0.15

    def _calculate_decree_28_89_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.65

    def _calculate_public_sector_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.25

    def _calculate_credit_cards_companies_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.15 if invoice_line.product_id.product_tmpl_id.categ_id.sat_iva_type_product == 'payment_creditholders' else self._calculate_iva_amount(invoice_line) * 0.015

    def _calculate_special_taxpayer_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.15

    def _calculate_others_withholding(self, invoice_line):
        return self._calculate_iva_amount(invoice_line) * 0.15
    
    @api.depends('invoice_line_ids')
    def _compute_gt_move_type(self):
        is_compra = is_service = is_mix = is_import = is_gas = False

        if self.invoice_incoterm_id:
            is_import = True

        for line in self.invoice_line_ids:
            
            if any(tax.sat_tax_type == 'gas' for tax in line.tax_ids):
                if is_compra or is_service:
                    is_mix = True
                else:
                    is_gas = True
                continue

            product_type = line.product_id.type
            if product_type in ['product', 'consu']:
                if is_service or is_gas:
                    is_mix = True
                else:
                    is_compra = True
            elif product_type == 'service':
                if is_compra or is_gas:
                    is_mix = True
                else:
                    is_service = True

            if is_mix:
                break

        if is_mix:
            self.tipo_gasto = 'mixto'
        elif is_compra:
            self.tipo_gasto = 'compra'
        elif is_service:
            self.tipo_gasto = 'servicio'
        elif is_import:
            self.tipo_gasto = 'importacion'
        elif is_gas:
            self.tipo_gasto = 'combustible'

    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        res = super(AccountMove, self)._onchange_quick_edit_line_ids()
        self._compute_amount()
        return res