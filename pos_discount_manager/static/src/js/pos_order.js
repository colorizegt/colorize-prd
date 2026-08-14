/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);

        json.discount_manager_id = this.discount_manager_id || false;
        json.discount_manager_name = this.discount_manager_name || false;

        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);

        this.discount_manager_id = json.discount_manager_id || false;
        this.discount_manager_name = json.discount_manager_name || false;
    },

    set_discount_manager(employee) {
        if (employee) {
            this.discount_manager_id = employee.id;
            this.discount_manager_name = employee.name;
        } else {
            this.discount_manager_id = false;
            this.discount_manager_name = false;
        }
    },

    get_discount_manager() {
        return {
            id: this.discount_manager_id || false,
            name: this.discount_manager_name || false,
        };
    },
});
