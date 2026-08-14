/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {

    setup() {
        super.setup(...arguments);

        this.discount_authorized = false;
        this.discount_manager_id = false;
        this.discount_manager_name = false;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);

        this.discount_authorized = json.discount_authorized || false;
        this.discount_manager_id = json.discount_manager_id || false;
        this.discount_manager_name = json.discount_manager_name || false;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);

        json.discount_authorized = this.discount_authorized || false;
        json.discount_manager_id = this.discount_manager_id || false;
        json.discount_manager_name = this.discount_manager_name || false;

        return json;
    },

});
