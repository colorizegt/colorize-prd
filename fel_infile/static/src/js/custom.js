odoo.define('fel_infile.ReceiptScreenButton', function(require) {
    'use strict';

    const rpc = require('web.rpc');
    const Registries = require('point_of_sale.Registries');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');

    const CustomButtonReceiptScreen = (OriginalReceiptScreen) =>
        class extends OriginalReceiptScreen {
            async IsCustomButton() {
                try {
                    const order = this.env.pos.get_order();
                    if (!order) {
                        this.showPopup('ErrorPopup', {
                            title: 'Error',
                            body: 'No hay una orden seleccionada'
                        });
                        return;
                    }

                    const result = await rpc.query({
                        model: 'account.move',
                        method: 'get_pdf_fel',
                        args: [[], order.name]
                    });

                    if (result) {
                        // Abrir el PDF en una nueva ventana
                        const win = window.open(
                            result,
                            'popUpWindow',
                            'height=1000,width=800,left=100,top=10,resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=no,directories=no,status=yes'
                        );
                        if (!win) {
                            this.showPopup('ErrorPopup', {
                                title: 'Error',
                                body: 'El navegador bloqueó la apertura de la ventana. Por favor, permite ventanas emergentes para este sitio.'
                            });
                        }
                    } else {
                        this.showPopup('ErrorPopup', {
                            title: 'Error',
                            body: 'La factura FEL no se encuentra generada. Por favor verifique.'
                        });
                    }
                } catch (error) {
                    console.error('Error al obtener PDF FEL:', error);
                    this.showPopup('ErrorPopup', {
                        title: 'Error',
                        body: 'Ocurrió un error al obtener el PDF de la factura FEL.'
                    });
                }
            }
        };

    Registries.Component.extend(ReceiptScreen, CustomButtonReceiptScreen);

    return CustomButtonReceiptScreen;
});
