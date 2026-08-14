/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    /**
     * Validate discount limits before finalizing the order.
     *
     * If any order line exceeds the cashier's discount limit,
     * an authorized manager PIN is required.
     */
    async _finalizeValidation() {
        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();

        const cashier = this.pos.get_cashier();

        const employeeDiscountLimit = cashier?.limited_discount || 0;
        const employeeName = cashier?.name || "";

        // Check whether any order line exceeds the cashier's discount limit.
        const discountExceeded = orderlines.some(
            (line) => line.discount > employeeDiscountLimit
        );

        if (discountExceeded) {
            const { confirmed, payload } = await this.popup.add(
                NumberPopup,
                {
                    title: _t(
                        `${employeeName}, your discount is over the limit.\n` +
                        "Manager PIN for Approval"
                    ),
                    isPassword: true,
                }
            );

            if (!confirmed) {
                return false;
            }

            /*
             * Find an employee who:
             * 1. Is authorized to approve discounts.
             * 2. Has a PIN configured.
             * 3. Entered the correct PIN.
             */
            const manager = this.pos.employees.find(
                (employee) =>
                    employee.discount_manager === true &&
                    employee.pin &&
                    employee.pin === payload
            );

            if (!manager) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Manager Approval Required"),
                    body: _t(
                        `${employeeName}, the Manager PIN is incorrect.`
                    ),
                });

                return false;
            }
        }

        /*
         * Continue with the normal Odoo POS validation process.
         */
        return await super._finalizeValidation(...arguments);
    },
});
