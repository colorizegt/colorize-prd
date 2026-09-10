/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    /**
     * Odoo 19: Exportamos los datos de autorización de descuento
     * cuando la orden se envía al backend.
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        
        if (this.discount_authorized) {
            json.discount_authorized = this.discount_authorized;
            
            if (this.discount_manager_id) {
                json.discount_manager_id = this.discount_manager_id;
            }
            
            if (this.discount_authorized_at) {
                json.discount_authorized_at = this.discount_authorized_at;
            }
        }
        
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        
        if (json.discount_authorized) {
            this.discount_authorized = json.discount_authorized;
            this.discount_manager_id = json.discount_manager_id || false;
            this.discount_authorized_at = json.discount_authorized_at || false;
        }
    },
});
