/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConnectionLostError, RPCError } from "@web/core/network/rpc_service";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.pos.config.fel_gt_auto_check_invoice) {
            this.currentOrder.set_to_invoice(true);
        }
        if (this.pos.config.fel_gt_default_customer && !this.currentOrder.get_partner()) {
            this.currentOrder.set_partner(this.pos.db.get_partner_by_id(this.pos.config.fel_gt_default_customer[0]));
        }
    },
    
    //@override
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        if (this.pos.config.fel_gt_active) {
            if (!order.get_partner()) {
                this.popup.add(ErrorPopup, {
                    title: _t('AGREGAR CLIENTE'),
                    body: _t("No se pueden emitir facturas sin haber establecido un cliente en la venta."),
                });
                return;
            }
            if (!order.partner_validated()) {
                this.popup.add(ErrorPopup, {
                    title: _t('ERROR DE CLIENTE'),
                    body: _t("No se pueden emitir facturas con un monto mayor a Q 2,500.00 a un NIT CF. Debe ingresar el DPI o número de pasaporte, en caso ser extranjero."),
                });
                return;
            }
            if (this.pos.synch.status === "connected") {
                try {
                    const result = await this.orm.call("pos.config", "get_current_fel_gt_access_number", [this.pos.config.id]);
                    this.pos.get_order().set_fel_gt_has_contingency(false);
                    this.pos.set_fel_gt_next_contingency_access_number(Math.trunc(result));
                } catch (error) {
                    let checkContingency = this._handleFelGtOfflineContingency();
                    if (!checkContingency) {
                        this._handleFelGtError(error);
                        return;
                    }
                }
            } else {
                if (!this._handleFelGtOfflineContingency()) return;
            }
        }
        
        return super.validateOrder(...arguments);
    },

    async _finalizeValidation() {
        if (!this.pos.config.fel_gt_active) {
            await super._finalizeValidation(...arguments);
        } else {
            try {
                if (this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) {
                    this.hardwareProxy.openCashbox();
                }

                this.currentOrder.date_order = luxon.DateTime.now();
                for (const line of this.paymentLines) {
                    if (line.amount === 0) {
                        this.currentOrder.remove_paymentline(line);
                    }
                }
                this.currentOrder.finalized = true;

                // 1. Save order to server.
                this.env.services.ui.block();
                const syncOrderResult = await this.pos.push_single_order(this.currentOrder);
                this.env.services.ui.unblock();

                if (syncOrderResult instanceof ConnectionLostError) {
                    this.pos.showScreen(this.nextScreen);
                    return;
                } else if (!syncOrderResult) {
                    return;
                }
            
                // 2. Invoice.
                if (!this.pos.config.fel_gt_disable_download_invoice_pdf && this.currentOrder.is_to_invoice()) {
                    if (syncOrderResult[0]?.account_move) {
                        await this.report.doAction("account.account_invoices", [
                            syncOrderResult[0].account_move,
                        ]);
                    } else {
                        throw {
                            code: 401,
                            message: "Backend Invoice",
                            data: { order: this.currentOrder },
                        };
                    }
                }

                // 2.1 Get FEL Data
                if (this.pos.config.fel_gt_active && !this.currentOrder.get_fel_gt_has_contingency()) {
                    try {
                        const savedOrder = await this.orm.searchRead(
                            "pos.order",
                            [["id", "=", syncOrderResult[0].id]],
                            ["name","fel_gt_dte_invoice","fel_gt_uuid_invoice","fel_gt_serie_invoice","fel_gt_has_contingency","fel_gt_contingency_access_number","fel_gt_date_invoice","fel_gt_invoice_type"]
                        );
                        this.currentOrder.set_fel_gt_dte_invoice(savedOrder[0].fel_gt_dte_invoice);
                        this.currentOrder.set_fel_gt_uuid_invoice(savedOrder[0].fel_gt_uuid_invoice);
                        this.currentOrder.set_fel_gt_serie_invoice(savedOrder[0].fel_gt_serie_invoice);
                        this.currentOrder.set_fel_gt_date_invoice(savedOrder[0].fel_gt_date_invoice);
                        this.currentOrder.set_fel_gt_has_contingency(savedOrder[0].fel_gt_has_contingency);
                        this.currentOrder.set_fel_gt_contingency_access_number(savedOrder[0].fel_gt_contingency_access_number);
                        this.currentOrder.set_fel_gt_invoice_type(savedOrder[0].fel_gt_invoice_type);
                    } catch (error) {
                        this._handleFelGtError(error);
                        return;
                    }
                }

                // 3. Post process.
                if (
                    syncOrderResult &&
                    syncOrderResult.length > 0 &&
                    this.currentOrder.wait_for_push_order()
                ) {
                    await this.postPushOrderResolve(syncOrderResult.map((res) => res.id));
                }
                
                await this.afterOrderValidation(!!syncOrderResult && syncOrderResult.length > 0);
            } catch (error) {
                if (this.currentOrder.get_fel_gt_has_contingency()) {
                    this.env.services.ui.unblock();
                    this.pos.showScreen(this.nextScreen);
                    return;
                } else {
                    this._handleFelGtError(error);
                }
            }
        }
    },

    _handleFelGtError(error) {
        let errorMessage = _t('Se produjo un error en el servidor de Odoo. Por favor, contacte a su administrador.');

        if (error instanceof RPCError) {
            if (error.data && error.data.message) {
                errorMessage = error.data.message;
            } else if (error.message) {
                errorMessage = error.message;
            }
        }

        this.popup.add(ErrorPopup, {
            title: _t('ERROR DE FEL'),
            body: errorMessage,
        });

        this.env.services.ui.unblock();
    },

    _handleFelGtOfflineContingency() {
        console.log("handleFelGtOfflineContingency");
        if (this.pos.config.fel_gt_contingency_active) {
            if (this.pos.fel_gt_next_contingency_access_number <= this.pos.config.fel_gt_contingency_end_range) {
                console.log("Contingency Access Number: ", this.pos.fel_gt_next_contingency_access_number);
                this.pos.get_order().set_fel_gt_has_contingency(true);
                this.pos.get_order().set_fel_gt_contingency_access_number(Math.trunc(this.pos.fel_gt_next_contingency_access_number));
                this.pos.set_fel_gt_next_contingency_access_number(Math.trunc(this.pos.fel_gt_next_contingency_access_number + 1));
            } else {
                this.popup.add(ErrorPopup, {
                    title: _t('ERROR DE VALIDACIÓN DE NUMERO DE CONTINGENCIA'),
                    body: _t('Llegó al límite de números habilitados, por favor contacte al administrador del sistema.'),
                });
                return false;
            }
        } else {
            this.popup.add(ErrorPopup, {
                title: _t('ERROR DE VALIDACIÓN DE FACTURACIÓN'),
                body: _t('Debe estar en línea para poder continuar, ya que no tiene la contingencia activa.'),
            });
            return false;
        }
        return true;
    },

    shouldDownloadInvoice() {
        if (!this.pos.config.fel_gt_active) {
            super.shouldDownloadInvoice(...arguments);
        } else {
            return !this.pos.config.fel_gt_disable_download_invoice_pdf;
        }
    },

    async afterOrderValidation(suggestToSync = true) {
        const orderlines = this.currentOrder.get_orderlines();
        for (let j = 0; j < orderlines.length; j++) {
            const orderLine = orderlines[j];
            if (orderLine.product) {
                orderLine.product.available_stock -= orderLine.quantity;
                orderLine.product.on_hand_stock -= orderLine.quantity;
            }
        }
        return await super.afterOrderValidation(...arguments);
    },
});
