/** @odoo-module **/

import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";

patch(PartnerDetailsEdit.prototype, {
    setup(){
        const res = super.setup(...arguments);
        if (!this.pos.isGuatemalanCompany()) {
            return res;
        }

        this.changes.fel_gt_dpi_number = this.props.partner.fel_gt_dpi_number;
        this.changes.fel_gt_passport_number = this.props.partner.fel_gt_passport_number;

    }
});
