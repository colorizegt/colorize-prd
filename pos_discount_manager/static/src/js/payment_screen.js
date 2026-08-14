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

        const employeeDiscountLimit = cashier?.limited_discount || 0;
        const employeeName = cashier?.name || "";

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

            console.log("=== POS DISCOUNT MANAGER DEBUG ===");
            console.log("Cashier:", cashier);
            console.log("Entered PIN:", payload);
            console.log("HR employees:", this.pos.hr_employee);

            console.log("=== POS DISCOUNT MANAGER DEBUG 2 ===");

            console.log(
                "HR employees length:",
                this.pos.hr_employee.length
            );

            this.pos.hr_employee.forEach((employee, index) => {
                console.log(
                    "EMPLOYEE",
                     index,
                    "ID:", employee.id,
                    "NAME:", employee.name,
                    "PIN:", employee.pin,
                    "PIN TYPE:", typeof employee.pin,
                    "DISCOUNT MANAGER:", employee.discount_manager,
                    "DISCOUNT MANAGER TYPE:", typeof employee.discount_manager,
                    "LIMIT:", employee.limited_discount
                        );
                });

console.log("Entered PIN:", payload);
console.log("Entered PIN TYPE:", typeof payload);
            const manager = this.pos.hr_employee.find(
                (employee) =>
                    employee.discount_manager === true &&
                    employee.pin &&
                    employee.pin === payload
            );

            console.log("Manager found:", manager);

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

        return await super._finalizeValidation(...arguments);
    },
});
