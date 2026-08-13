# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	state = fields.Selection(selection_add=([('waiting for approval', 'Waiting For Approval')]))
	email_id=fields.Many2one('res.users',string="Request to Approve")
	discount_approved=fields.Many2one('res.users',string="Discount Appoved By")

	def action_confirm(self):
		res = super(SaleOrder, self).action_confirm()
		order_line_id=self.env['sale.order.line'].search([],order="id desc",limit=1)
		if self.env.user.allow_discount != 0.00 and order_line_id.discount > self.env.user.allow_discount:
			template_id=self.env.ref('sale_order_discount_approval_app.discount_email_template_ids').id
			template=self.env['mail.template'].browse(template_id)
			template.send_mail(self.id,force_send=True)
			self.write({'state':'waiting for approval'})
		return res

	def cancel_order(self):
		self.write({'state':'cancel'})

	def button_approve(self):
		self.update({'discount_approved':self.env.user.id})
		self.write({'state':'sale'})






		
