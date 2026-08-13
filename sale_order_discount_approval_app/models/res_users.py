# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_discount=fields.Float(string="User Allow Discount")