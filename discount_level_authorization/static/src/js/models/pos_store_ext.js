/** @odoo-module **/
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    async setup(vals) {
        this.setDiscountReason(vals.discount_reason || false);
        this.setDiscountFile(vals.discount_reason_file || false);
        this.setDiscountFileName(vals.discount_reason_file_name || false);
        await super.setup(...arguments);
    },
    setDiscountReason(discount_reason) {
        if (discount_reason) {
            this.update({ discount_reason: discount_reason });
        } else {
            this.update({ discount_reason: false });
        }
    },
    setDiscountFile(discount_file) {
        if (discount_file) {
            this.update({ discount_reason_file: discount_file });
        } else {
            this.update({ discount_reason_file: false });
        }
    },
    setDiscountFileName(discount_file_name) {
        if (discount_file_name) {
            this.update({ discount_reason_file_name: discount_file_name });
        } else {
            this.update({ discount_reason_file_name: false });
        }
    }
});
