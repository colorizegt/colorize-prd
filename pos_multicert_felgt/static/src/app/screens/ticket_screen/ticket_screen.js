/** @odoo-module */

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { TextAreaPopup } from "@point_of_sale/app/utils/input_popups/textarea_popup";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";
const { DateTime } = luxon;

patch(TicketScreen.prototype, {

    getNumerFelGt(order) {
        return order.get_fel_gt_dte_invoice();
    },
    getSerieFelGt(order) {
        return order.get_fel_gt_serie_invoice();
    },
    getUuidFelGt(order) {
        return order.get_fel_gt_uuid_invoice();
    },
    _getSearchFields() {
        const fields = super._getSearchFields(...arguments);

        if (!this.pos.config.fel_gt_active){
            return fields
        }

        fields.NUMERO_FEL = {
            repr: (order) => order.get_fel_gt_dte_invoice(),
            displayName: _t('Número FEL'),
            modelField: 'fel_gt_dte_invoice',
        };

        fields.SERIE_FEL = {
            repr: (order) => order.get_fel_gt_serie_invoice(),
            displayName: _t('Serie FEL'),
            modelField: 'fel_gt_serie_invoice',
        };

        fields.NUMERO_DE_AUTORIZACION_FEL = {
            repr: (order) => order.get_fel_gt_uuid_invoice(),
            displayName: _t('Número de Autorización FEL'),
            modelField: 'fel_gt_uuid_invoice',
        };
        return fields
    },
    _getOrderStates() {
        const states = super._getOrderStates(...arguments);
        states.set("CANCEL", {
            text: _t("Canceled"),
        });
        return states;
    },
    _getScreenToStatusMap() {
        return Object.assign(super._getScreenToStatusMap(...arguments), {
            PaymentScreen: "CANCEL",
        });
    },
    getFilteredOrderList() {
        if (this._state.ui.filter == "CANCEL") {
            return this._state.syncedOrders.toShow;
        }
        return super.getFilteredOrderList(...arguments);
    },
    async onFilterSelected(selectedFilter) {
        this._state.ui.filter = selectedFilter;
        if (this._state.ui.filter == "CANCEL") {
            await this._fetchCancelOrders();
        }
        return super.onFilterSelected(...arguments);
    },
    async _fetchCancelOrders() {
        if (!this.pos.config.fel_gt_active){
            return super._fetchCancelOrders(...arguments);
        }
        const domain = this._computeSyncedOrdersDomain();
        const limit = this._state.syncedOrders.nPerPage;
        const offset =
            (this._state.syncedOrders.currentPage - 1) * this._state.syncedOrders.nPerPage;
        const config_id = this.pos.config.id;
        const { ordersInfo, totalCount } = await this.orm.call(
            "pos.order",
            "search_cancel_order_ids",
            [],
            { config_id, domain, limit, offset }
        );
        const idsNotInCache = ordersInfo.filter(
            (orderInfo) => !(orderInfo[0] in this._state.syncedOrders.cache)
        );
        // If no cacheDate, then assume reasonable earlier date.
        const cacheDate = this._state.syncedOrders.cacheDate || DateTime.fromMillis(0);
        const idsNotUpToDate = ordersInfo.filter((orderInfo) => {
            return deserializeDateTime(orderInfo[1]) > cacheDate;
        });
        const idsToLoad = idsNotInCache.concat(idsNotUpToDate).map((info) => info[0]);
        if (idsToLoad.length > 0) {
            const fetchedOrders = await this.orm.call("pos.order", "export_for_ui", [idsToLoad]);
            // Check for missing products and partners and load them in the PoS
            await this.pos._loadMissingProducts(fetchedOrders);
            await this.pos._loadMissingPartners(fetchedOrders);
            // Cache these fetched orders so that next time, no need to fetch
            // them again, unless invalidated. See `_onInvoiceOrder`.
            fetchedOrders.forEach((order) => {
                this._state.syncedOrders.cache[order.id] = new Order(
                    { env: this.env },
                    { pos: this.pos, json: order }
                );
            });
            //Update the datetime indicator of the cache refresh
            this._state.syncedOrders.cacheDate = DateTime.local();
        }

        const ids = ordersInfo.map((info) => info[0]);
        this._state.syncedOrders.totalCount = totalCount;
        this._state.syncedOrders.toShow = ids.map((id) => this._state.syncedOrders.cache[id]);
    },
    showFelGtData() {
        return (this._state.ui.filter === "SYNCED" || this._state.ui.filter === "CANCEL") && this.pos.config.fel_gt_active && this.pos.isGuatemalanCompany();
    },
    showFelGtCancel() {
        return this._state.ui.filter === "SYNCED" && this.pos.get_cashier().fel_gt_cancel_in_pos && this.pos.config.fel_gt_active && this.pos.isGuatemalanCompany();
    },
    async cancelFELGT(order) {
        if (!this.pos.get_cashier().fel_gt_motive_cancel_in_pos){
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t("¿Esta seguro de Anular la Factura?"),
                body: _t(
                    "Esta operación estará cancelando la factura en SAT."
                ),
            });
            if (confirmed) {
                await this.orm.call("pos.order","fel_gt_pos_cancel",[,order.get_fel_gt_uuid_invoice()]);
                this.pos.ticket_screen_mobile_pane = "left";
                this.pos.closeScreen();
            }
        } else {
            const { confirmed, payload: inputMotive } = await this.popup.add(TextAreaPopup, {
                title: _t("¿Esta seguro de Anular la Factura?, favor ingrese el motivo de la anulación."),
            });
            if (confirmed) {
                await this.orm.call("pos.order","fel_gt_pos_cancel",[,order.get_fel_gt_uuid_invoice(),inputMotive]);
                this.pos.ticket_screen_mobile_pane = "left";
                this.pos.closeScreen();
            }
        }
    },

    /**
     * Select the lines from toRefundLines, as they can come from different orders.
     * Returns only details that:
     * - The quantity to refund is not zero
     * - Filtered by partner (optional)
     * - It's not yet linked to an active order (no destinationOrderUid)
     *
     * @param {Object} partner (optional)
     * @returns {Array} refundableDetails
     */
    _getRefundableDetails(partner) {
        if (!this.pos.config.fel_gt_force_refund_payment && this.pos.isGuatemalanCompany()){
            return super._getRefundableDetails(...arguments);
        }

        return Object.values(this.pos.toRefundLines).filter(
            ({ orderline, destinationOrderUid }) =>
                (partner ? orderline.orderPartnerId == partner.id : true) &&
                !destinationOrderUid
        );
    },

    async onDoRefund() {

        if (!this.pos.config.fel_gt_force_refund_payment && this.pos.isGuatemalanCompany()){
            return super.onDoRefund(...arguments);
        }

        const order = this.getSelectedOrder();

        if (order && this._doesOrderHaveSoleItem(order)) {
            if (!this._prepareAutoRefundOnOrder(order)) {
                // Don't proceed on refund if preparation returned false.
                return;
            }
        }

        if (!order) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return;
        }

        const partner = order.get_partner();

        const allToRefundDetails = this._getRefundableDetails(partner);

        if (allToRefundDetails.length == 0) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return;
        }

        

        const invoicedOrderIds = new Set(
            allToRefundDetails
                .filter(
                    (detail) =>
                        this._state.syncedOrders.cache[detail.orderline.orderBackendId]?.state ===
                        "invoiced"
                )
                .map((detail) => detail.orderline.orderBackendId)
        );

        if (invoicedOrderIds.size > 1) {
            this.popup.add(ErrorPopup, {
                title: _t("Multiple Invoiced Orders Selected"),
                body: _t(
                    "You have selected orderlines from multiple invoiced orders. To proceed refund, please select orderlines from the same invoiced order."
                ),
            });
            return;
        }

        // The order that will contain the refund orderlines.
        // Use the destinationOrder from props if the order to refund has the same
        // partner as the destinationOrder.
        const destinationOrder =
            this.props.destinationOrder &&
            partner === this.props.destinationOrder.get_partner() &&
            !this.pos.doNotAllowRefundAndSales()
                ? this.props.destinationOrder
                : this._getEmptyOrder(partner);

        // Add orderline for each toRefundDetail to the destinationOrder.
        const originalToDestinationLineMap = new Map();

        // First pass: add all products to the destination order
        for (const refundDetail of allToRefundDetails) {
            const product = this.pos.db.get_product_by_id(refundDetail.orderline.productId);
            const options = this._prepareRefundOrderlineOptions(refundDetail);
            const newOrderline = await destinationOrder.add_product(product, options);
            originalToDestinationLineMap.set(refundDetail.orderline.id, newOrderline);
            refundDetail.destinationOrderUid = destinationOrder.uid;
        }
        // Second pass: update combo relationships in the destination order
        for (const refundDetail of allToRefundDetails) {
            const originalOrderline = refundDetail.orderline;
            const destinationOrderline = originalToDestinationLineMap.get(originalOrderline.id);
            if (originalOrderline.comboParent) {
                const comboParentLine = originalToDestinationLineMap.get(
                    originalOrderline.comboParent.id
                );
                if (comboParentLine) {
                    destinationOrderline.comboParent = comboParentLine;
                }
            }
            if (originalOrderline.comboLines && originalOrderline.comboLines.length > 0) {
                destinationOrderline.comboLines = originalOrderline.comboLines.map((comboLine) => {
                    return originalToDestinationLineMap.get(comboLine.id);
                });
            }
        }

        destinationOrder.refund_order = true;
        
        //Add a check too see if the fiscal position exist in the pos
        if (order.fiscal_position_not_found) {
            this.showPopup("ErrorPopup", {
                title: _t("Fiscal Position not found"),
                body: _t(
                    "The fiscal position used in the original order is not loaded. Make sure it is loaded by adding it in the pos configuration."
                ),
            });
            return;
        }
        destinationOrder.fiscal_position = order.fiscal_position;
        // Set the partner to the destinationOrder.
        this.setPartnerToRefundOrder(partner, destinationOrder);

        if (this.pos.get_order().cid !== destinationOrder.cid) {
            this.pos.set_order(destinationOrder);
        }
        await this.addAdditionalRefundInfo(order, destinationOrder);

        this.pos.showScreen("PaymentScreen");

    },
});
