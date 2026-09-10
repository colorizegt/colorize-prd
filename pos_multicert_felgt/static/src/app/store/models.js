/** @odoo-module */

import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { evaluateExpr, evaluateBooleanExpr } from "@web/core/py_js/py";
import {
    formatDateTime,
} from "@web/core/l10n/dates";
const { DateTime } = luxon;

patch(Order.prototype, {
    constructor(obj, options) {
        super.Order(...arguments);
        this.fel_gt_dte_invoice = this.fel_gt_dte_invoice || null;
        this.fel_gt_uuid_invoice = this.fel_gt_uuid_invoice || null;
        this.fel_gt_serie_invoice = this.fel_gt_serie_invoice || null;
        this.fel_gt_date_invoice = this.fel_gt_date_invoice || null;
        this.fel_gt_has_contingency = this.fel_gt_has_contingency || false;
        this.fel_gt_contingency_access_number = this.fel_gt_contingency_access_number || null;
        this.fel_gt_invoice_type = this.fel_gt_invoice_type || null;
    },

    set_fel_gt_has_contingency(fel_gt_has_contingency){
        this.fel_gt_has_contingency = fel_gt_has_contingency || false;
    },

    get_fel_gt_has_contingency(){
        return this.fel_gt_has_contingency;
    },

    set_fel_gt_contingency_access_number(fel_gt_contingency_access_number){
        this.fel_gt_contingency_access_number = fel_gt_contingency_access_number || '';
    },

    get_fel_gt_contingency_access_number(){
        return this.fel_gt_contingency_access_number;
    },

    set_fel_gt_dte_invoice(fel_gt_dte_invoice) {
        this.fel_gt_dte_invoice = fel_gt_dte_invoice || '';
    },

    set_fel_gt_uuid_invoice(fel_gt_uuid_invoice) {
        this.fel_gt_uuid_invoice = fel_gt_uuid_invoice || '';
    },

    set_fel_gt_serie_invoice(fel_gt_serie_invoice) {
        this.fel_gt_serie_invoice = fel_gt_serie_invoice || '';
    },

    set_fel_gt_date_invoice(fel_gt_date_invoice) {
        this.fel_gt_date_invoice = fel_gt_date_invoice || '';
    },

    set_fel_gt_invoice_type(fel_gt_invoice_type) {
        this.fel_gt_invoice_type = fel_gt_invoice_type || '';
    },

    get_fel_gt_dte_invoice() {
        return this.fel_gt_dte_invoice;
    },

    get_fel_gt_uuid_invoice() {
        return this.fel_gt_uuid_invoice;
    },

    get_fel_gt_serie_invoice() {
        return this.fel_gt_serie_invoice;
    },

    get_fel_gt_date_invoice() {
        return this.fel_gt_date_invoice;
    },

    get_fel_gt_invoice_type() {
        return this.fel_gt_invoice_type;
    },

    get_fel_gt_invoice_type_text(fel_gt_invoice_type) {
        if (fel_gt_invoice_type === 'FACT') {
            if (this.pos.config.fel_gt_small_taxpayer_withholding) {
                return 'Factura Electrónica Pequeño Contribuyente';
            } else {
                return 'Factura Electrónica';
            }
        } else if (fel_gt_invoice_type === 'FCAM') {
            if (this.pos.config.fel_gt_small_taxpayer_withholding) {
                return 'Factura Cambiaria Pequeño Contribuyente';
            } else {
                return 'Factura Electrónica Cambiaria';
            }
        } else if (fel_gt_invoice_type === 'FEXP') {
            return 'Factura Electrónica Cambiaria de Exportación';
        } else if (fel_gt_invoice_type === 'FESP') {
            return 'Factura Especial Electrónica';
        } else if (fel_gt_invoice_type === 'NDEB') {
            return 'Nota de Débito';
        } else if (fel_gt_invoice_type === 'RECI') {
            return 'Recibo';
        } else if (fel_gt_invoice_type === 'NABN') {
            return 'Nota de Abono';
        } else {
            return 'Nota de Crédito';
        }
    },

    partner_validated(){
        var validation = true;

        var client = this.get_partner();
        if (!client) {
            return false
        }
        var client_vat = "";
        var tax_id_label = "";
        if (client.vat != undefined && client.vat) {
            client_vat = client.vat.toUpperCase();
            tax_id_label = "NIT";
        }
        if (client.vat == '') {
            if (client.fel_gt_dpi_number != undefined && client.fel_gt_dpi_number != false) {
                client_vat = client.fel_gt_dpi_number;
                tax_id_label = "DPI";
            } else {
                if (client.fel_gt_passport_number != undefined && client.fel_gt_passport_number != false) {
                    client_vat = client.fel_gt_passport_number;
                    tax_id_label = "Pasaporte";
                }
            }
        } else if (client.vat == 'CF') {
            if (client.fel_gt_dpi_number != undefined && client.fel_gt_dpi_number != false) {
                client_vat = client.fel_gt_dpi_number;
                tax_id_label = "DPI";
            } else {
                if (client.fel_gt_passport_number != undefined && client.fel_gt_passport_number != false) {
                    client_vat = client.fel_gt_passport_number;
                    tax_id_label = "Pasaporte";
                }
            }
        }

        if (tax_id_label === 'NIT' && client.vat === 'CF' && this.get_total_with_tax() >= 2500){
            validation = false;
        }

        return validation
    },

    getHasNegativePrice() {
        for (const line of this.get_orderlines()) {
            var subtotal = line.price * line.quantity;
            if (subtotal < 0) {
                return true;
            }
        }
        return false;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.fel_gt_has_contingency = this.fel_gt_has_contingency;
        json.fel_gt_contingency_access_number = this.fel_gt_contingency_access_number;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.fel_gt_dte_invoice = json.fel_gt_dte_invoice;
        this.fel_gt_uuid_invoice = json.fel_gt_uuid_invoice;
        this.fel_gt_serie_invoice = json.fel_gt_serie_invoice;
        this.fel_gt_date_invoice = json.fel_gt_date_invoice;
        this.fel_gt_has_contingency = json.fel_gt_has_contingency;
        this.fel_gt_contingency_access_number = json.fel_gt_contingency_access_number;
    },

    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.fel_gt_active = this.pos.config.fel_gt_active;

        if (!this.pos.config.fel_gt_active) {
            return json;
        }

        //Company Data
        var company = this.pos.company;
        json.company = company;
        
        //Partner Data
        var client = this.get_partner();
        var client_vat = "";
        var tax_id_label = "";

        if (client.vat != undefined && client.vat) {
            client_vat = client.vat.toUpperCase();
            tax_id_label = "NIT";
        }
        if (client.vat == '') {
            if (client.fel_gt_dpi_number != undefined && client.fel_gt_dpi_number != false) {
                client_vat = client.fel_gt_dpi_number;
                tax_id_label = "DPI";
            } else {
                if (client.fel_gt_passport_number != undefined && client.fel_gt_passport_number != false) {
                    client_vat = client.fel_gt_passport_number;
                    tax_id_label = "Pasaporte";
                }
            }
        } else if (client.vat == 'CF') {
            if (client.fel_gt_dpi_number != undefined && client.fel_gt_dpi_number != false) {
                client_vat = client.fel_gt_dpi_number;
                tax_id_label = "DPI";
            } else {
                if (client.fel_gt_passport_number != undefined && client.fel_gt_passport_number != false) {
                    client_vat = client.fel_gt_passport_number;
                    tax_id_label = "Pasaporte";
                }
            }
        }

        json.client = client;
        json.tax_id_label = tax_id_label;
        json.client_vat = client_vat;
        

        //FEL DATA
        json.street_invoice = this.pos.config.fel_gt_address;
        json.fel_gt_township_and_department = this.pos.config.fel_gt_township + ' , ' + this.pos.config.fel_gt_department;
        json.fel_gt_commercial_name = this.pos.config.fel_gt_commercial_name;
        json.fel_gt_certifier = this.pos.config.fel_gt_certifier;
        json.fel_gt_phrases = JSON.parse(JSON.stringify(this.pos.fel_gt_phrases));
        

        var fel_gt_date_invoice = this.get_fel_gt_date_invoice();

        if (fel_gt_date_invoice) {
            var objectDate = new Date(fel_gt_date_invoice);
        } else {
            var objectDate = new Date();
        }

        objectDate.toLocaleString('es', { timeZone: 'America/Guatemala' })
        let day = objectDate.getDate();
        let month = objectDate.getMonth() + 1;
        let year = objectDate.getFullYear();

        let format2 = day + "/" + month + "/" + year;
        
        json.fel_gt_invoice_type_text = this.get_fel_gt_invoice_type_text(this.get_fel_gt_invoice_type());
        json.fel_gt_certifier = this.pos.config.fel_gt_certifier;
        json.fel_gt_phrases = JSON.parse(JSON.stringify(this.pos.fel_gt_phrases));

        var invoice_url = ''
        if (this.fel_gt_has_contingency) {
            invoice_url = "https://felpub.c.sat.gob.gt/verificador-web/publico/vistas/verificacionDte.jsf?tipo=contingencia&numero="+this.fel_gt_contingency_access_number.toString()+"&emisor="+company.vat.toString()+"&receptor="+client_vat.toString()+"&monto="+this.get_total_with_tax().toString()
        } else {
            if (this.pos.config.fel_gt_certifier == 'infile') {
                invoice_url = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid=" + this.fel_gt_uuid_invoice;
            } else {
                invoice_url = "https://felpub.c.sat.gob.gt/verificador-web/publico/vistas/verificacionDte.jsf?tipo=autorizacion&numero="+this.fel_gt_uuid_invoice+"&emisor="+company.vat.toString()+"&receptor="+client_vat.toString()+"&monto="+this.get_total_with_tax().toString();
            }
        }
        json.fel_gt_date_invoice = format2;
        json.datetime_invoice ||= formatDateTime(luxon.DateTime.now());
        json.fel_gt_has_contingency = this.get_fel_gt_has_contingency();
        json.fel_gt_contingency_access_number = Math.trunc(this.get_fel_gt_contingency_access_number());
        json.fel_gt_dte_invoice = this.get_fel_gt_dte_invoice();
        json.fel_gt_uuid_invoice = this.get_fel_gt_uuid_invoice();
        json.fel_gt_serie_invoice = this.get_fel_gt_serie_invoice();

        const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();

        var size_qr = 130;
        if (this.pos.config.size_qr_logo > 0){
            size_qr = this.pos.config.size_qr_logo;
        }
        else {
            if (this.pos.config.fel_gt_certifier == 'infile') {
                size_qr = 110;
            }
        }

        const fel_gt_qr_code_svg = new XMLSerializer().serializeToString(
            codeWriter.write(invoice_url, size_qr, size_qr)
        );
        json.fel_gt_qr_code = "data:image/svg+xml;base64," + window.btoa(fel_gt_qr_code_svg);

        json.other_discounts = this.getHasNegativePrice();

        //POS CONFIG OPTIONS
        json.show_qrcode = this.pos.config.show_qrcode;
        json.show_fel_logo = this.pos.config.show_fel_logo;
        json.custom_logo = this.pos.config.custom_logo;
        json.show_pdv_name = this.pos.config.show_pdv_name;

        json.name_config = this.pos.config.name;
        
        return json;
    },
    
});

patch(Orderline.prototype, {
    getDisplayData() {
        let productName = this.get_full_product_name();
        if (this.product.default_code) {
            productName = '['+this.product.default_code+'] ' + this.get_full_product_name();
        }
        return {
            ...super.getDisplayData(),
            productName: productName,
        };
    },

    get_all_prices(qty = this.get_quantity()){
        if (!this.pos.config.fel_gt_active) {
            return super.get_all_prices(...arguments);
        }
        var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        var taxtotal = 0;

        var product =  this.get_product();
        var taxes_ids = this.tax_ids || product.taxes_id;
        taxes_ids = taxes_ids.filter((t) => t in this.pos.taxes_by_id);
        var taxdetail = {};
        var product_taxes = this.pos.get_taxes_after_fp(taxes_ids, this.order.fiscal_position);

        var all_taxes = this.compute_all(product_taxes, price_unit, qty, this.pos.currency.rounding);
        var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), qty, this.pos.currency.rounding);
        all_taxes.taxes.forEach(function (tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = {
                amount: tax.amount,
                base: tax.base,
            };
        });
        for ( let tax of product_taxes ){
            if (tax.amount_type == 'code'){
                let formula = tax.python_compute.split("=") && tax.python_compute.split("=").length > 1 && tax.python_compute.split("=")[1] || {};
                var result = evaluateExpr(formula, {
                    product: {'standard_price': product.standard_price},
                    price_unit: price_unit,
                    quantity: this.get_quantity(),
                    base_price: price_unit,
                })
                taxtotal += result * this.get_quantity();
                if (taxtotal > 0){
                    taxdetail[tax.id] = {
                        amount : taxtotal
                    } ;
                } else {
                    taxdetail[tax.id] = {
                        amount : 0
                    } ;
                }
            }
        }

        var extra_to_price = 0;
        if (taxtotal < 0){
            extra_to_price = Math.abs(taxtotal);
            taxtotal = 0;
        }

        var priceWithTax = all_taxes.total_included;
        if (taxtotal == 0){
            priceWithTax = all_taxes_before_discount.total_included;
        }

        return {
            "priceWithTax": priceWithTax,
            "priceWithoutTax": all_taxes.total_excluded-extra_to_price,
            "priceSumTaxVoid": all_taxes.total_void,
            "priceWithTaxBeforeDiscount": all_taxes_before_discount.total_included,
            "priceWithoutTaxBeforeDiscount": all_taxes_before_discount.total_excluded,
            "tax": taxtotal,
            "taxDetails": taxdetail,
            "tax_percentages": product_taxes.map((tax) => tax.amount),
        };
    }
})
