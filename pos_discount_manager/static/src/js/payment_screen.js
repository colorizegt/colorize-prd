/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);

        this.orm = useService("orm");
    },

    async _finalizeValidation() {
        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();
        const cashier = this.pos.get_cashier();

        const employeeDiscountLimit = cashier?.limited_discount || 0;
        const employeeName = cashier?.name || "";

        // Check whether any order line exceeds the cashier's limit.
        const discountExceeded = orderlines.some(
            (line) => line.discount > employeeDiscountLimit
        );

        if (discountExceeded) {
            console.log("=== POS DISCOUNT MANAGER DEBUG ===");
            console.log("Cashier:", cashier);
            console.log(
                "Cashier discount limit:",
                employeeDiscountLimit
            );

            const { confirmed, payload } = await this.popup.add(
                NumberPopup,
                {
                    title: _t(
                        employeeName +
                        ", your discount is over the limit.\n" +
                        "Enter Manager PIN for Approval"
                    ),
                    isPassword: true,
                }
            );

            if (!confirmed) {
                return false;
            }

            console.log("Entered PIN:", payload);

            try {
                const valid = await this.orm.call(
                    "hr.employee",
                    "validate_discount_manager_pin",
                    [payload]
                );

                console.log(
                    "Manager PIN validation result:",
                    valid
                );

                if (!valid) {
                    await this.popup.add(ErrorPopup, {
                        title: _t("Manager Restricted Your Discount"),
                        body: _t(
                            employeeName +
                            ", the Manager PIN is incorrect."
                        ),
                    });

                    return false;
                }

                console.log("Manager PIN accepted.");

            } catch (error) {
                console.error(
                    "Error validating manager PIN:",
                    error
                );

                await this.popup.add(ErrorPopup, {
                    title: _t("Authorization Error"),
                    body: _t(
                        "The manager PIN could not be validated."
                    ),
                });

                return false;
            }
        }

        this.currentOrder.finalized = true;

        await super._finalizeValidation(...arguments);
    },
});
