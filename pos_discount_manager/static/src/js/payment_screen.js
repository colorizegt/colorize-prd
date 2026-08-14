/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {

    /**
     * Validate the order and request manager approval
     * when the cashier exceeds their discount limit.
     */
    async _finalizeValidation() {

        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();
        const cashier = this.pos.get_cashier();

        const employeeDiscountLimit = cashier?.limited_discount || 0;
        const employeeName = cashier?.name || "";

        // Check if any order line exceeds the cashier's discount limit.
        const discountExceeded = orderlines.some(
            (line) => line.discount > employeeDiscountLimit
        );

        // No approval required.
        if (!discountExceeded) {
            await super._finalizeValidation(...arguments);
            return;
        }

        // Ask for manager PIN.
        const { confirmed, payload } = await this.popup.add(NumberPopup, {
            title: _t(
                "%s, your discount is over the limit.\nManager PIN required for approval.",
                employeeName
            ),
            isPassword: true,
        });

        if (!confirmed || !payload) {
            return false;
        }

        try {
            /*
             * Validate the manager PIN on the Odoo server.
             *
             * Odoo 17 hashes employee PINs before sending them
             * to the POS, therefore we must NOT compare the PIN
             * directly with employee.pin in JavaScript.
             */
            const validPin = await this.env.services.orm.call(
                "hr.employee",
                "validate_discount_manager_pin",
                [payload]
            );

            if (!validPin) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Manager Restricted Your Discount"),
                    body: _t(
                        "%s, the manager PIN is incorrect or the employee is not authorized to approve discounts.",
                        employeeName
                    ),
                });

                return false;
            }

            // Manager authorization successful.
            await super._finalizeValidation(...arguments);

        } catch (error) {

            console.error(
                "Error validating manager PIN:",
                error
            );

            await this.popup.add(ErrorPopup, {
                title: _t("Validation Error"),
                body: _t(
                    "An error occurred while validating the manager PIN. Please try again."
                ),
            });

            return false;
        }
    },
});
