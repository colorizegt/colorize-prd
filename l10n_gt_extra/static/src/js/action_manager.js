/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { BlockUI } from "@web/core/ui/block_ui";
// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("l10n_gt_extra_xlsx", async (action) => {
    if (action.report_type === 'l10n_gt_extra_xlsx') {
        const blockUI = new BlockUI();
        await download({
            url: '/l10n_gt_extra_xlsx_reports',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
});