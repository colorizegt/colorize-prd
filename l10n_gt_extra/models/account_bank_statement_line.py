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

from odoo import api, models, _

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'
	
	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if 'ref' in vals and not 'payment_ref' in vals:
				vals['payment_ref'] = vals.get('ref')
			if not "partner_id" in vals:
				amount = vals.get('amount')
				payment_type = 'inbound'
				if amount < 0:
					payment_type = 'outbound'
				partner_lookup = self.env['account.payment'].search([
    				('ref', '=', vals.get('ref')),
    				('amount_company_currency_signed', '=', amount),
    				('state', '=', 'posted'),
    				('payment_type', '=', payment_type)], limit=1).partner_id
				if partner_lookup:
					vals['partner_id'] = partner_lookup.id
		return super(AccountBankStatementLine, self).create(vals_list)