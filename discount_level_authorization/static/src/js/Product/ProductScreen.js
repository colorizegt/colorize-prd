/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { discountLogNote } from "../discount_log_note/discount_log_note";

patch(OrderSummary.prototype, {
   setup(){
   super.setup()
   this.notification = useService("notification");
   },
    async _setValue(val) {
        if (this.pos.numpadMode === 'discount') {
            const cashier = this.pos.getCashier();
            const discountValue = parseFloat(val);
            const discountPercentage = discountValue;
            const selectedLine = this.currentOrder.getSelectedOrderline();
            if (!selectedLine) return super._setValue(val);
            debugger;
            if (discountValue > cashier.allowed_discount_percentage) {
            // Manager approval flow
            // In Odoo 18, employees are stored in models["hr.employee"] which is a Proxy(Map)
            const employeeMap = this.pos.models["hr.employee"];
            if (!employeeMap) {
                await this.dialog.add(ErrorPopup, {
                    body: _t('Employee data not found. Please contact your administrator.'),
                });
                return;
            }

            // Extract all employees from the Map structure
            const employees = [];
            // Loop through the Map entries to collect all employees
            employeeMap.forEach((employee) => {
                employees.push(employee);
            });

            // Filter for managers - in Odoo 18 the role is stored in _role
            const managerList = employees
                .filter(employee => employee._role === "manager")
                .map(manager => ({
                    id: manager.id,
                    item: manager,
                    label: manager.name,
                }));

            // Check if we have any managers
            if (managerList.length === 0) {
                await this.dialog.add(ErrorPopup, {
                    body: _t('No managers found. Please contact your administrator.'),
                });
                return;
            }


            const managerResult = await makeAwaitable(this.dialog, SelectionPopup, {
                list: managerList,
                title: _t("Need Manager's Permission!"),
            });

            // if (!managerResult || !managerResult.confirmed) return;
            if (managerResult) {
                const pinResult = await makeAwaitable(this.dialog, NumberPopup, {
                    formatDisplayedValue: (x) => x.replace(/./g, "*"),
                    title: _t("Enter Manager PIN"),
                });

                // PIN validation - in Odoo 18 the pin is stored in _pin
                if(pinResult) {
                    if (Sha1.hash(pinResult) === managerResult._pin) {
                        this.notification.add(_t("Authenticated Successfully!"), {type: "info"});
                        this.pos.productScreen.setDiscount(selectedLine, discountValue, discountPercentage, false);
                    } else {
                        this.dialog.add(ErrorPopup, {
                            body: _t('Incorrect Password'),
                        });
                    }
                }


            }


            // if (!pinResult || !pinResult.confirmed) return;

        } else {
            this.pos.productScreen.setDiscount(selectedLine, discountValue, discountPercentage, false);
        }




            //////////////////////////////////////////////////////////////
            // Use the stored ProductScreen reference
            // if (this.pos.productScreen) {
            //     await this.pos.productScreen.applyDiscount(selectedLine, discountValue, false);
            // } else {
            //     console.error("ProductScreen reference not available");
            // }
            ///////////////////////////////////////////////////////////////
        } else {
            return super._setValue(val);
        }
    },
});



// Create a simple ErrorPopup using ConfirmationDialog
class ErrorPopup extends ConfirmationDialog {
    static defaultProps = {
        ...ConfirmationDialog.defaultProps,
        title: _t("Error"),
        cancel: null,
        cancelLabel: "",
    };
}

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        // this.pos = useService("pos");
        this.orm = useService("orm");
        this.notificationService = useService("notification");
        this.pos.productScreen = this;
    },
        destroy() {
        if (this.pos.productScreen === this) {
            this.pos.productScreen = null;
        }
        super.destroy(...arguments);
    },

    getDiscountPercentage(discount_value, total_value) {
        const discountPercentage = (discount_value / total_value) * 100;
        return parseFloat(discountPercentage.toFixed(2));
    },

    async onNumpadClick(buttonValue) {
        if (["quantity", "discount", "price"].includes(buttonValue)) {
            this.numberBuffer.capture();
            this.numberBuffer.reset();
            this.pos.numpadMode = buttonValue;
            const selectedOrder = this.pos.getOrder();
            const selectedLine = selectedOrder.getSelectedOrderline();
            if (selectedLine && buttonValue === 'discount') {
                let discount = await this.orm.searchRead('product.product', [['id', '=', selectedLine.product_id.id]], ['allow_discount'])
                // 1. Check if discount is allowed on product
                if (discount[0].allow_discount === 'no') {
                    await this.dialog.add(ErrorPopup, {
                        body: _t("Our pricing policy doesn't allow discount on this product"),
                    });
                    return;
                }

                // 2. Ask for discount type
//                const discountTypeResult = await this.dialog.add(ConfirmationDialog, {
//                    title: _t('Discount Type'),
//                    body: _t("Please select discount type:"),
//                    confirmLabel: _t('Amount'),
//                    cancelLabel: _t('Percentage'),
//                    confirm: () => this.opennumpad(selectedLine),
//                    cancel: () => this.numberBuffer.reset(),
//                });
//                if (discountTypeResult === undefined) return;
                this.dialog.add(discountLogNote, {
                    title: _t("Add Log Note"),
                    close: () => this.popup.close(),
                    selectedLine: selectedLine
                });
            }
            return;
        }
        this.numberBuffer.sendKey(buttonValue);
    },

    async opennumpad(selectedLine) {
        this.numberBuffer.reset();
        const inputNumber = await makeAwaitable(this.dialog, NumberPopup, {
            startingValue: selectedLine.getDiscount() || 10,
            title: _t("Set the new discount"),
        });
        if (!inputNumber) {
            return;
        }

        const discountValue = parseFloat(inputNumber);
        if (discountValue <= selectedLine.price_unit) {
            let discount_percentage = this.getDiscountPercentage(discountValue, selectedLine.price_unit);
            await this.applyDiscount(selectedLine, discountValue, true);
        } else {
            return await this.dialog.add(ErrorPopup, {
                body: _t('You can not set discount amount bigger than or equal price of item'),
            });
        }
    },


    async applyDiscount(selectedLine, discountValue, isAmountDiscount) {
        const cashier = this.pos.getCashier();
        let discountPercentage = isAmountDiscount ?
            this.getDiscountPercentage(discountValue, selectedLine.price_unit) :
            discountValue;

        // 3. Check if discount exceeds cashier's limit
        debugger;
        if (discountPercentage > cashier.allowed_discount_percentage) {
            // Manager approval flow
            // In Odoo 18, employees are stored in models["hr.employee"] which is a Proxy(Map)
            const employeeMap = this.pos.models["hr.employee"];
            if (!employeeMap) {
                await this.dialog.add(ErrorPopup, {
                    body: _t('Employee data not found. Please contact your administrator.'),
                });
                return;
            }

            // Extract all employees from the Map structure
            const employees = [];
            // Loop through the Map entries to collect all employees
            employeeMap.forEach((employee) => {
                employees.push(employee);
            });

            // Filter for managers - in Odoo 18 the role is stored in _role
            const managerList = employees
                .filter(employee => employee._role === "manager")
                .map(manager => ({
                    id: manager.id,
                    item: manager,
                    label: manager.name,
                }));

            // Check if we have any managers
            if (managerList.length === 0) {
                await this.dialog.add(ErrorPopup, {
                    body: _t('No managers found. Please contact your administrator.'),
                });
                return;
            }


            const managerResult = await makeAwaitable(this.dialog, SelectionPopup, {
                list: managerList,
                title: _t("Need Manager's Permission!"),
            });

            // if (!managerResult || !managerResult.confirmed) return;
            if (managerResult) {
                const pinResult = await makeAwaitable(this.dialog, NumberPopup, {
                    formatDisplayedValue: (x) => x.replace(/./g, "*"),
                    title: _t("Enter Manager PIN"),
                });

                // PIN validation - in Odoo 18 the pin is stored in _pin
                if(pinResult) {
                    if (Sha1.hash(pinResult) === managerResult._pin) {
                        this.notificationService.add(_t("Authenticated Successfully!"), {type: "info"});
                        this.setDiscount(selectedLine, discountValue, discountPercentage, isAmountDiscount);
                    } else {
                        this.dialog.add(ErrorPopup, {
                            body: _t('Incorrect Password'),
                        });
                    }
                }


            }


            // if (!pinResult || !pinResult.confirmed) return;

        } else {
            this.setDiscount(selectedLine, discountValue, discountPercentage, isAmountDiscount);
        }

        // Reset numpad mode
        this.pos.numpadMode = "quantity";
    },

    setDiscount(selectedLine, discountValue, discountPercentage, isAmountDiscount) {
        if (isAmountDiscount) {
            selectedLine.setDiscount(discountPercentage);
            selectedLine.discount_value = -discountValue;
            this.notificationService.add(
                _t('Discount applied: %s amount', discountValue.toFixed(2)),
                {type: "success"}
            );
        } else {
            selectedLine.setDiscount(discountValue);
            this.notificationService.add(
                _t('Discount applied: %s%', discountValue),
                {type: "success"}
            );
        }
    },

    async _setValue(val, ...args) {
        if (this.pos.numpadMode === 'discount' && args[0]?.key !== 'Backspace') {
            const discountValue = parseFloat(val);
            const selectedLine = this.currentOrder.getSelectedOrderline();

            if (!selectedLine) return super._setValue(val, ...args);

            // Handle percentage discount via numpad
            await this.applyDiscount(selectedLine, discountValue, false);
        } else {
            return super._setValue(val, ...args);
        }
    },

    async updateSelectedOrderline({buffer, key}) {
        const order = this.pos.getOrder();
        const selectedLine = order.getSelectedOrderline();

        // Handle tip modification restriction
        if (selectedLine && selectedLine.isTipLine() && this.pos.numpadMode !== "price") {
            this.numberBuffer.reset();
            if (key === "Backspace") {
                this._setValue("remove");
            } else {
                await this.dialog.add(ErrorPopup, {
                    body: _t("Tips cannot be modified directly. Please remove and re-add."),
                });
            }
            return;
        }

        // Handle combo item quantity restriction
        if (this.pos.numpadMode === "quantity" && selectedLine?.isPartOfCombo()) {
            if (key === "Backspace") {
                this._setValue("remove");
            } else {
                await this.dialog.add(ErrorPopup, {
                    body: _t("Combo items can only be deleted, not modified."),
                });
            }
            return;
        }

        // Handle quantity change restrictions
        if (selectedLine && this.pos.numpadMode === "quantity" && this.pos.disallowLineQuantityChange()) {
            const orderlines = order.orderlines;
            const lastId = orderlines.length > 0 && orderlines.at(-1).cid;
            const currentQuantity = selectedLine.getQuantity();

            if (selectedLine.noDecrease) {
                await this.dialog.add(ErrorPopup, {
                    body: _t("You are not authorized to decrease this quantity"),
                });
                return;
            }

            const parsedInput = buffer ? parseFloat(buffer) : 0;
            if (lastId !== selectedLine.cid || parsedInput < currentQuantity) {
                this._showDecreaseQuantityPopup();
            } else {
                this._setValue(buffer);
            }
            return;
        }

        // Default behavior
        const val = buffer === null ? "remove" : buffer;
        this._setValue(val, {key});
        if (val === "remove") {
            this.numberBuffer.reset();
            this.pos.numpadMode = "quantity";
        }
    }
});