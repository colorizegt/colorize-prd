# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fel_gt_certifier = fields.Selection([
        ('infile', 'InFile'),
        ('g4s', 'G4S'),
        ('guatefacturas', 'Guatefacturas'),
        ('megaprint', 'Megaprint'),
        ('digifact', 'Digifact'),
        ], string='Certificador a utilizar - FEL GT', compute="get_fel_gt_certifier", store=False)

    fel_gt_active = fields.Boolean(string="Generación de Facturación Electrónica - FEL GT")

    fel_gt_establishment_code = fields.Char(string="Código Establecimiento - FEL GT", help="Ingrese el código de establecimiento a utilizar")
    fel_gt_address = fields.Char(string="Dirección de facturación - FEL GT", default=lambda self: self.company_id.street)
    fel_gt_commercial_name = fields.Char(string="Nombre comercial - FEL GT", default=lambda self: self.company_id.name)
    fel_gt_zip_code = fields.Char(string="Código postal - FEL GT", default=lambda self: self.company_id.zip)
    fel_gt_department = fields.Char(string="Departamento - FEL GT", default=lambda self: self.company_id.state_id.name)
    fel_gt_township = fields.Char(string="Municipio - FEL GT", default=lambda self: self.company_id.city)

    fel_gt_phrases = fields.Many2many('fel_gt.tools.phrases', string="Frase - FEL GT")

    fel_gt_is_receipt_journal = fields.Boolean(string="¿Es recibo? - FEL GT")

    fel_gt_has_contingency = fields.Boolean(string="Activar contingencia manualmente - FEL GT")
    fel_gt_contingency_start_range = fields.Float("Número de Contingencia Actual Rango Inicial - FEL GT", digits=(9, 0))
    fel_gt_contingency_end_range = fields.Float("Número de Contingencia Actual Rango Final - FEL GT", digits=(9, 0))
    fel_gt_contingency_actual_number = fields.Float("Número de Contingencia Actual - FEL GT", digits=(9, 0))

    fel_gt_custom_logo = fields.Boolean(string="Logo Personalizado - FEL GT")
    fel_gt_invoice_custom_logo = fields.Binary(string='Logo - FEL GT')

    def get_fel_gt_certifier(self):
        fel_certifier = self.env.company.fel_gt_certifier
        self.fel_gt_certifier = fel_certifier

    def get_fel_next_fel_gt_contingency_number(self):
        self.ensure_one()
        temp_number = self.fel_gt_contingency_actual_number
        self.fel_gt_contingency_actual_number = temp_number + 1
        return temp_number
    

    
    fel_gt_addendum_internal_serie = fields.Boolean('Adenda Serie Interna - FEL GT')
    fel_gt_addendum_internal_number = fields.Boolean('Adenda Numero Interna - FEL GT')
    fel_gt_addendum_partner_ref = fields.Boolean('Adenda Referencia Contacto - FEL GT')
    fel_gt_addendum_credit = fields.Boolean('Adenda Crédito - FEL GT')
    fel_gt_addendum_order = fields.Boolean('Adenda Pedido - FEL GT')
    fel_gt_addendum_comercial = fields.Boolean('Adenda Comercial - FEL GT')
    fel_gt_addendum_payment_date = fields.Boolean('Adenda Fecha de Pago - FEL GT')
    fel_gt_addendum_currency_rate = fields.Boolean('Adenda Tipo de Cambio - FEL GT')

    fel_gt_discount_in_price = fields.Boolean('Descuento en Precio - FEL GT')

    fel_gt_addendum_active = fields.Boolean(
        string='Adenda Activa - FEL GT',
        compute='_compute_fel_gt_addendum_active',
        store=True
    )

    @api.depends(
        'fel_gt_addendum_internal_serie',
        'fel_gt_addendum_internal_number',
        'fel_gt_addendum_partner_ref',
        'fel_gt_addendum_credit',
        'fel_gt_addendum_order',
        'fel_gt_addendum_comercial',
        'fel_gt_addendum_payment_date',
        'fel_gt_addendum_currency_rate'
    )
    def _compute_fel_gt_addendum_active(self):
        for record in self:
            record.fel_gt_addendum_active = any([
                record.fel_gt_addendum_internal_serie,
                record.fel_gt_addendum_internal_number,
                record.fel_gt_addendum_partner_ref,
                record.fel_gt_addendum_credit,
                record.fel_gt_addendum_order,
                record.fel_gt_addendum_comercial,
                record.fel_gt_addendum_payment_date,
                record.fel_gt_addendum_currency_rate
            ])