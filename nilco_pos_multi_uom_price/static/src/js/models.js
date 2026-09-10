/** @odoo-module */
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(Order.prototype, {
    set_orderline_options(orderline, options) {
        super.set_orderline_options(...arguments);
        if (options.product_uom_id !== undefined) {
            orderline.product_uom_id = options.product_uom_id;
        }
    }
});

patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        // Estandarizamos a formato [id, name]
        if (!this.product_uom_id) {
            const uom = this.product.uom_id;
            this.product_uom_id = Array.isArray(uom) ? uom : [uom[0], uom[1]];
        }
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (this.product_uom_id) {
            json.product_uom_id = Array.isArray(this.product_uom_id)
                ? this.product_uom_id[0]
                : this.product_uom_id.id || this.product_uom_id[0];
        }
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        if (json.product_uom_id && this.pos.units_by_id[json.product_uom_id]) {
            const uom = this.pos.units_by_id[json.product_uom_id];
            this.product_uom_id = [uom.id, uom.name];
        } else {
            this.product_uom_id = this.product.uom_id;
        }
    },

    set_uom(uom_id) {
        // Acepta tanto [id, name] como {0: id, 1: name} o un número
        if (Array.isArray(uom_id)) {
            this.product_uom_id = uom_id;
        } else if (typeof uom_id === 'object' && uom_id !== null) {
            this.product_uom_id = [uom_id[0] || uom_id.id, uom_id[1] || uom_id.name];
        } else {
            this.product_uom_id = [uom_id, ''];
        }
    },

    get_unit() {
        if (this.product_uom_id) {
            let unit_id = Array.isArray(this.product_uom_id) ? this.product_uom_id[0] : this.product_uom_id.id;
            if (!unit_id || !this.pos) {
                return undefined;
            }
            return this.pos.units_by_id[unit_id];
        }
        return this.product.get_unit();
    }
});

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.product_uom_price = loadedData['product.multi.uom.price'] || {};
    }
});
