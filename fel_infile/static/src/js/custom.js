odoo.define('pos_custom_buttons.ReceiptScreenButton', function(require) {
    'use strict';
       var rpc = require('web.rpc');
       const { Gui } = require('point_of_sale.Gui');
       const PosComponent = require('point_of_sale.PosComponent');
       const { posbus } = require('point_of_sale.utils');
       const { useListener } = require('web.custom_hooks');
       const Registries = require('point_of_sale.Registries');
       const ReceiptScreen = require('point_of_sale.ReceiptScreen');
        const CustomButtonReceiptScreen = (ReceiptScreen) =>
           class extends ReceiptScreen {
               constructor() {
                   super(...arguments);
               }
               IsCustomButton() {
                   window.alert("La factura en FEL no se encuentra generada por favor verifique"); 
               }
           };
       Registries.Component.extend(ReceiptScreen, CustomButtonReceiptScreen);
       return CustomButtonReceiptScreen;
    });