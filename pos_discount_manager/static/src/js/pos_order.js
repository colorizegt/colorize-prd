/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models/order";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);

        json.discount_authorized = this.discount_authorized || false;
        json.discount_manager_id = this.discount_manager_id || false;

        return json;
    },

});
