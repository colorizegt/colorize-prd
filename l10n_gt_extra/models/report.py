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

class Report(models.Model):
    _inherit = "ir.actions.report"

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None, set_viewport_size=False):
        command_args = super(Report, self)._build_wkhtmltopdf_args(paperformat_id, landscape, specific_paperformat_args, set_viewport_size)
        if specific_paperformat_args and specific_paperformat_args.get('data-report-page-offset'):
            command_args.extend(['--page-offset', str(specific_paperformat_args['data-report-page-offset'])])
        return command_args
