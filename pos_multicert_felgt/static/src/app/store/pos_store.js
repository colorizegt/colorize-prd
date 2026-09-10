/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {

    constructor(obj) {
        super.PosStore(...arguments);
        this.fel_gt_next_contingency_access_number = "";
    },

    async _processData(loadedData) {
        await super._processData(...arguments);
        this.fel_gt_phrases = loadedData['fel_gt.tools.phrases'];
        this.get_current_fel_gt_contingency_access_number();
    },

    get_current_fel_gt_contingency_access_number(){
        if (this.config.fel_gt_contingency_actual_number >= this.config.fel_gt_contingency_start_range && this.config.fel_gt_contingency_actual_number <= this.config.fel_gt_contingency_end_range) {
            return this.set_fel_gt_next_contingency_access_number(Math.trunc(this.config.fel_gt_contingency_actual_number)); 
        } else {
            return this.set_fel_gt_next_contingency_access_number(1);
        }
        
    },

    set_fel_gt_next_contingency_access_number(fel_gt_next_contingency_access_number){
        this.fel_gt_next_contingency_access_number = fel_gt_next_contingency_access_number || "";
    },

    get_fel_gt_next_contingency_access_number(){
        return this.fel_gt_next_contingency_access_number;
    },

    getReceiptHeaderData() {
        return {
            ...super.getReceiptHeaderData(...arguments),
            show_logo: this.config.fel_gt_show_logo,
            custom_logo: this.config.fel_gt_custom_logo,
            pos_custom_logo: this.config.id,
        };
    },

    get order_product_qty() {
        let orderProductQty = {};
        let order_list = this.get_order_list();
        for (let i = 0; i < order_list.length; i++) {
            const order = order_list[i];
            const orderlines = order.get_orderlines();
            for (let j = 0; j < orderlines.length; j++) {
                const orderLine = orderlines[j];
                if (orderLine.product) {
                    const productId = orderLine.product.id;
                    const quantity = orderLine.quantity;

                    if (!orderProductQty[productId]) {
                        orderProductQty[productId] = 0;
                    }
                    orderProductQty[productId] += quantity;
                }
            }
        }
        return orderProductQty;
    },

    openCashbox() {
        this.hardwareProxy.openCashbox();
    },

    isGuatemalanCompany() {
        return this.company.country?.code == "GT";
    },
    
});
