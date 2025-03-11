# -*- coding: utf-8 -*-

from odoo import fields, models


class FelGTLogXmlSent(models.Model):
    _name = "fel_gt.tools.log_xml_sent"
    _description = "Records the XML sent to the certifier log"

    name = fields.Char(string="Nombre",  required=True)
    data_content = fields.Char(string="Content")
    certifier = fields.Selection([
        ('infile', 'InFile'),
        ('g4s', 'G4S'),
        ('guatefacturas', 'Guatefacturas'),
        ('megaprint', 'Megaprint'),
        ('digifact', 'Digifact'),
        ], string='Certificador Utilizado')
    move_id = fields.Many2one('account.move', string='Factura')