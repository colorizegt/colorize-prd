from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    tipo_gasto = fields.Selection([
        ("mixto", "Mixto"), 
        ("compra", "Compra/Bien"), 
        ("servicio", "Servicio"), 
        ("importacion", "Importación/Exportación"), 
        ("combustible", "Combustible")
    ], string="Tipo de Gasto", default="mixto")
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(
        string="Las facturas se ingresan por rango", 
        help="Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción",
        related="journal_id.facturas_por_rangos"
    )
    nota_debito = fields.Boolean(string="Nota de debito")

    def suma_impuesto(self, impuestos_ids):
        suma_monto = 0
        for impuesto in impuestos_ids:
            suma_monto += impuesto.amount
        return suma_monto

    def impuesto_global(self):
        """Calcula impuestos globales para compras"""
        impuestos = self.env['l10n_gt_extra.impuestos'].search([
            ['active', '=', True],
            ['tipo', '=', 'compra']
        ])
        impuestos_valores = []
        diferencia = 0
        suma_impuesto = 0
        impuesto_total = 0
        rango_final_anterior = 0
        
        for rango in impuestos.rangos_ids:
            if self.amount_untaxed > rango.rango_final and diferencia == 0:
                diferencia = self.amount_untaxed - rango.rango_final
                impuesto_individual = rango.rango_final * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({
                    'nombre': rango.impuestos_ids[0].name,
                    'impuesto_id': rango.impuestos_ids[0].id,
                    'account_id': rango.impuestos_ids[0].account_id.id,
                    'total': impuesto_individual
                })
            elif self.amount_untaxed <= rango.rango_final and diferencia == 0 and rango_final_anterior == 0:
                impuesto_individual = self.amount_untaxed * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                rango_final_anterior = rango.rango_final
                impuestos_valores.append({
                    'nombre': rango.impuestos_ids[0].name,
                    'impuesto_id': rango.impuestos_ids[0].id,
                    'account_id': rango.impuestos_ids[0].account_id.id,
                    'total': impuesto_individual
                })
            elif diferencia > 0:
                impuesto_individual = diferencia * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({
                    'nombre': rango.impuestos_ids[0].name,
                    'impuesto_id': rango.impuestos_ids[0].id,
                    'account_id': rango.impuestos_ids[0].account_id.id,
                    'total': impuesto_individual
                })
                
        impuesto_total = 0
        self.update({
            'amount_tax': suma_impuesto, 
            'amount_total': impuesto_total + self.amount_untaxed
        })
        
        # Crear líneas de impuestos en la factura
        for impuesto in impuestos_valores:
            # Crear línea de impuesto usando el modelo account.move.line
            self._create_tax_line(impuesto)
            
        return True

    def _create_tax_line(self, impuesto_data):
        """Crea una línea de impuesto en la factura (v19)"""
        tax_line_vals = {
            'move_id': self.id,
            'tax_ids': [(4, impuesto_data['impuesto_id'])],
            'account_id': impuesto_data['account_id'],
            'name': impuesto_data['nombre'],
            'amount': impuesto_data['total'],
            'tax_line_id': impuesto_data['impuesto_id'],
        }
        self.env['account.move.line'].create(tax_line_vals)

    @api.constrains('inicial_rango', 'final_rango')
    def _validar_rango(self):
        for factura in self:
            if factura.diario_facturas_por_rangos:
                if int(factura.final_rango) < int(factura.inicial_rango):
                    raise ValidationError('El número inicial del rango es mayor que el final.')
                    
                cruzados = factura.search([
                    ('serie_rango', '=', factura.serie_rango),
                    ('inicial_rango', '<=', factura.inicial_rango),
                    ('final_rango', '>=', factura.inicial_rango)
                ])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
                    
                cruzados = self.search([
                    ('serie_rango', '=', factura.serie_rango),
                    ('inicial_rango', '<=', factura.final_rango),
                    ('final_rango', '>=', factura.final_rango)
                ])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
                    
                cruzados = self.search([
                    ('serie_rango', '=', factura.serie_rango),
                    ('inicial_rango', '>=', factura.inicial_rango),
                    ('inicial_rango', '<=', factura.final_rango)
                ])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')

                self.name = "{}-{} al {}-{}".format(
                    factura.serie_rango, 
                    factura.inicial_rango, 
                    factura.serie_rango, 
                    factura.final_rango
                )


class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)
    anulado = fields.Boolean('Anulado')
    fecha_anulacion = fields.Date('Fecha anulación')

    def cancel(self):
        for rec in self:
            rec.write({'numero_viejo': rec.name})
        return super(AccountPayment, self).cancel()

    def anular(self):
        """Anula un pago generando un asiento de reverso"""
        for rec in self:
            move = self.env['account.move']
            
            # Obtener el asiento relacionado (v19)
            if rec.move_id:
                move = rec.move_id
            else:
                continue
                
            # Cancelar el asiento original
            move.button_cancel()
            
            # Limpiar líneas del asiento
            for line in move.line_ids:
                line.remove_move_reconcile()
                line.write({'debit': 0, 'credit': 0, 'amount_currency': 0})
            
            # Publicar el asiento cancelado
            move.post()
            
            rec.anulado = True
            rec.fecha_anulacion = fields.Date.context_today(self)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento')
    facturas_por_rangos = fields.Boolean(
        string='Las facturas se ingresan por rango',
        help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción'
    )
    usar_referencia = fields.Boolean(
        string='Usar referencia para libro de ventas',
        help='El número de la factura se ingresa en Referencia/Descripción'
    )
