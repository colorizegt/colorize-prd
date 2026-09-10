# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    fel_gt_buyer_code = fields.Char(string="Código Comprador")
    fel_gt_invoice_currency = fields.Many2one('res.currency', string="Moneda de facturación")
    fel_gt_dpi_number = fields.Char(string="DPI")
    fel_gt_passport_number = fields.Char(string="Pasaporte")
    
    fel_gt_is_foreign = fields.Boolean(string="Es Extranjero", default=False)
    fel_gt_consignatary_name = fields.Char(string="Nombre Consignatario")
    fel_gt_consignatary_code = fields.Char(string="Código Consignatario")
    fel_gt_consignatary_address = fields.Char(string="Dirección Consignatario")
    fel_gt_buyer_name = fields.Char(string="Nombre Comprador")
    fel_gt_buyer_address = fields.Char(string="Dirección del Comprador")
    fel_gt_exporter_name = fields.Char(string="Nombre del Exportador")
    fel_gt_exporter_code = fields.Char(string="Código del Exportador")

    fel_gt_currency_from_invoice = fields.Boolean(string="Moneda de facturación en base al documento", default=False)

    fel_gt_vat = fields.Char(string="NIT Contacto")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'parent_id' in vals:
                if vals['parent_id']:
                    parent = self.browse(vals['parent_id'])
                    vals['fel_gt_dpi_number'] = parent.fel_gt_dpi_number
                    vals['fel_gt_invoice_currency'] = parent.fel_gt_invoice_currency.id if parent.fel_gt_invoice_currency else False
                    vals['fel_gt_buyer_code'] = parent.fel_gt_buyer_code
                    vals['fel_gt_is_foreign'] = parent.fel_gt_is_foreign
                    vals['fel_gt_consignatary_name'] = parent.fel_gt_consignatary_name
                    vals['fel_gt_consignatary_code'] = parent.fel_gt_consignatary_code
                    vals['fel_gt_consignatary_address'] = parent.fel_gt_consignatary_address
                    vals['fel_gt_buyer_name'] = parent.fel_gt_buyer_name
                    vals['fel_gt_buyer_address'] = parent.fel_gt_buyer_address
                    vals['fel_gt_exporter_name'] = parent.fel_gt_exporter_name
                    vals['fel_gt_exporter_code'] = parent.fel_gt_exporter_code
                    vals['fel_gt_currency_from_invoice'] = parent.fel_gt_currency_from_invoice
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for record in self:
            if record.child_ids:
                update_vals = {}
                if 'fel_gt_dpi_number' in vals:
                    update_vals['fel_gt_dpi_number'] = vals['fel_gt_dpi_number']
                if 'fel_gt_invoice_currency' in vals:
                    update_vals['fel_gt_invoice_currency'] = vals['fel_gt_invoice_currency']
                if 'fel_gt_buyer_code' in vals:
                    update_vals['fel_gt_buyer_code'] = vals['fel_gt_buyer_code']
                if 'fel_gt_is_foreign' in vals:
                    update_vals['fel_gt_is_foreign'] = vals['fel_gt_is_foreign']
                if 'fel_gt_consignatary_name' in vals:
                    update_vals['fel_gt_consignatary_name'] = vals['fel_gt_consignatary_name']
                if 'fel_gt_consignatary_code' in vals:
                    update_vals['fel_gt_consignatary_code'] = vals['fel_gt_consignatary_code']
                if 'fel_gt_consignatary_address' in vals:
                    update_vals['fel_gt_consignatary_address'] = vals['fel_gt_consignatary_address']
                if 'fel_gt_buyer_name' in vals:
                    update_vals['fel_gt_buyer_name'] = vals['fel_gt_buyer_name']
                if 'fel_gt_buyer_address' in vals:
                    update_vals['fel_gt_buyer_address'] = vals['fel_gt_buyer_address']
                if 'fel_gt_exporter_name' in vals:
                    update_vals['fel_gt_exporter_name'] = vals['fel_gt_exporter_name']
                if 'fel_gt_exporter_code' in vals:
                    update_vals['fel_gt_exporter_code'] = vals['fel_gt_exporter_code']
                if 'fel_gt_currency_from_invoice' in vals:
                    update_vals['fel_gt_currency_from_invoice'] = vals['fel_gt_currency_from_invoice']
                if update_vals:
                    record.child_ids.write(update_vals)
        return res

    @api.onchange('fel_gt_is_foreign')
    def _get_fel_gt_export_information(self):
        if self.fel_gt_is_foreign:
            self.fel_gt_consignatary_name = self.name
            self.fel_gt_consignatary_address = str(self.street if self.street else " ") + " " + str(self.street2 if self.street2 else " ")
            self.fel_gt_buyer_name = self.name
            self.fel_gt_buyer_address = str(self.street if self.street else " ") + " " +str(self.street2 if self.street2 else " ")
            self.fel_gt_exporter_name = ""
            self.fel_gt_exporter_code = ""

    @api.depends('vat', 'company_id', 'company_registry', 'fel_gt_dpi_number', 'fel_gt_passport_number')
    def _compute_same_vat_partner_id(self):
        for partner in self:
            partner_id = partner._origin.id
            Partner = self.with_context(active_test=False).sudo()
            domain = [
                ('vat', '=', partner.vat),
            ]
            if partner.company_id:
                domain += [('company_id', 'in', [False, partner.company_id.id])]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            if partner.fel_gt_dpi_number:
                domain += [('fel_gt_dpi_number', '=', partner.fel_gt_dpi_number)]
            if partner.fel_gt_passport_number:
                domain += [('fel_gt_passport_number', '=', partner.fel_gt_passport_number)]
            should_check_vat = partner.vat and len(partner.vat) != 1
            partner.same_vat_partner_id = should_check_vat and not partner.parent_id and Partner.search(domain, limit=1)
            
            domain = [
                ('company_registry', '=', partner.company_registry),
                ('company_id', 'in', [False, partner.company_id.id]),
            ]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            partner.same_company_registry_partner_id = bool(partner.company_registry) and not partner.parent_id and Partner.search(domain, limit=1)

    @api.model
    def _default_report_template(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        return report_id

    def _default_fel_gt_report_template1(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search(
            [('model', '=', 'account.move'), ('report_name', '=', 'multicert_felgt.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search([('model', '=', 'account.move')])[0]
        if self.fel_gt_report_template_id and self.fel_gt_report_template_id.id < report_id.id:
            self.write({'fel_gt_report_template_id': report_id and report_id.id or False})
        self.fel_gt_report_template_id1 = report_id and report_id.id or False

    fel_gt_report_template_id1 = fields.Many2one('ir.actions.report', string="Plantilla de Factura1", compute='_default_fel_gt_report_template1', help="Seleccione una plantilla para su factura FEL.", domain=[('model', '=', 'account.move')])
    fel_gt_report_template_id = fields.Many2one('ir.actions.report', string="Plantilla de Factura", help="Seleccione una plantilla para su factura FEL.", domain=[('model', '=', 'account.move')])
