/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

export class UOMButton extends Component {
    static template = "point_of_sale.UOMButton";

    setup() {
        super.setup();
    }

    get selectedOrderline() {
        return this.env.services.pos.getOrder()?.get_selected_orderline();
    }

    async onClick() {
        const line = this.selectedOrderline;
        if (!line) {
            return;
        }

        const pos = this.env.services.pos;
        const productTmplId = line.product.product_tmpl_id;
        const productUomPrices = pos.product_uom_price || {};

        const productKey = Object.keys(productUomPrices).find(
            key => key === String(productTmplId)
        );

        if (!productKey) {
            return;
        }

        const uomPrices = productUomPrices[productKey]?.uom_id;
        if (!uomPrices) {
            return;
        }

        const uomList = Object.values(uomPrices).map(uomPrice => ({
            id: uomPrice.id,
            label: uomPrice.name,
            isSelected: line.product_uom_id && line.product_uom_id[0] === uomPrice.id,
            item: uomPrice,
        }));

        const { confirmed, payload: selectedUOM } = await this.env.services.popup.add(
            SelectionPopup,
            {
                title: 'UOM',
                list: uomList,
            }
        );

        if (confirmed && selectedUOM) {
            line.set_uom([selectedUOM.id, selectedUOM.name]);
            line.set_unit_price(selectedUOM.price);
        }
    }
}

// En Odoo 19, se usa el registro de componentes
ProductScreen.addControlButton({
    component: UOMButton,
    condition: function () {
        return true;
    },
});
