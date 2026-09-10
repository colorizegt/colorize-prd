/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/utils/input_popups/error_popup";

patch(PaymentScreen.prototype, {
    /**
     * Odoo 19: Validamos el descuento antes de proceder al pago.
     * Si el descuento excede el límite del empleado, solicitamos
     * aprobación del manager mediante PIN.
     */
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        const orderlines = order.getOrderlines();
        
        // Calcular el descuento total aplicado
        let totalDiscount = 0;
        let maxDiscountLimit = 0;
        
        for (const line of orderlines) {
            if (line.discount) {
                totalDiscount += line.discount;
            }
        }
        
        // Obtener el límite del empleado actual
        const cashier = order.getCashier();
        if (cashier && cashier.user_id) {
            const employee = this.pos.getEmployeeDiscountLimit(cashier.user_id[0]);
            maxDiscountLimit = employee;
        }
        
        // Si el descuento excede el límite, solicitamos aprobación
        if (totalDiscount > maxDiscountLimit && maxDiscountLimit > 0) {
            const { confirmed, payload: pin } = await this.env.services.popup.add(
                NumberPopup,
                {
                    title: _t("Manager Approval Required"),
                    body: _t(
                        "The discount applied (%s%%) exceeds your limit (%s%%). " +
                        "Please enter the manager PIN to authorize.",
                        totalDiscount,
                        maxDiscountLimit
                    ),
                }
            );
            
            if (!confirmed) {
                return;
            }
            
            // Validar el PIN con el backend
            const manager = await this.pos.validateDiscountManagerPin(pin);
            
            if (!manager) {
                await this.env.services.popup.add(ErrorPopup, {
                    title: _t("Invalid PIN"),
                    body: _t("The PIN entered is incorrect or the manager is not authorized."),
                });
                return;
            }
            
            // Guardar la autorización en la orden
            order.discount_authorized = true;
            order.discount_manager_id = manager.id;
            order.discount_authorized_at = new Date().toISOString();
        }
        
        return super.validateOrder(...arguments);
    },
});
