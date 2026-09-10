/** @odoo-module */

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

patch(PosDB.prototype, {
    _partner_search_string(partner){
        var str =  partner.name || '';
        if(partner.barcode){
            str += '|' + partner.barcode;
        }
        if(partner.address){
            str += '|' + partner.address;
        }
        if(partner.phone){
            str += '|' + partner.phone.split(' ').join('');
        }
        if(partner.mobile){
            str += '|' + partner.mobile.split(' ').join('');
        }
        if(partner.email){
            str += '|' + partner.email;
        }
        if(partner.vat){
            str += '|' + partner.vat;
        }
        if(partner.fel_gt_dpi_number){
            str += '|' + partner.fel_gt_dpi_number;
        }
        if(partner.fel_gt_passport_number){
            str += '|' + partner.fel_gt_passport_number;
        }
        if(partner.parent_name){
            str += '|' + partner.parent_name;
        }
        str = '' + partner.id + ':' + str.replace(':', '').replace(/\n/g, ' ') + '\n';
        return str;
    },
});