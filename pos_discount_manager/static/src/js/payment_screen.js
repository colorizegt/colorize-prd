/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {

        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();

        const cashier = this.pos.get_cashier();
        const employee_dis = cashier.limited_discount || 0;
        const employee_name = cashier.name;

        let discount_exceeded = false;

        orderlines.forEach((orderline) => {
            if (orderline.discount > employee_dis) {
                discount_exceeded = true;
            }
        });

        // Discount is within the employee limit
        if (!discount_exceeded) {
            return await super._finalizeValidation(...arguments);
        }

        // Discount exceeds the employee limit
        const { confirmed, payload } = await this.popup.add(NumberPopup, {
            title: _t(
                employee_name +
                ", your discount is over the limit.\nManager PIN for Approval"
            ),
            isPassword: true,
        });

        if (!confirmed) {
            return false;
        }

        // Get employees authorized to approve discounts
        const managers = this.pos.hr_employee.filter(
            (employee) =>
                employee.discount_manager === true &&
                employee.pin
        );

        // Check PIN against all authorized managers
        const validManager = managers.find(
            (employee) => employee.pin === payload
        );

        if (!validManager) {
            await this.popup.add(ErrorPopup, {
                title: _t("Discount Approval"),
                body: _t(
                    employee_name +
                    ", the Manager PIN is incorrect."
                ),
            });

            return false;
        }

        // Manager approved the discount
        return await super._finalizeValidation(...arguments);
    },
});
