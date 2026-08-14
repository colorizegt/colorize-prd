# -*- coding: utf-8 -*-

from odoo import models


class AgedReceivableCustomHandler(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _aged_partner_report_custom_engine_common(
        self,
        options,
        internal_type,
        current_groupby,
        next_groupby,
        offset=0,
        limit=None,
    ):
        """Add account.move.fel_gt_dte_number to Aged Receivable results.

        The standard Odoo 17 handler already computes all Aged Receivable
        values.  We keep that implementation intact and only enrich the
        generated result dictionaries with the DTE number.

        The report is grouped by partner_id, id.  The second level (`id`)
        corresponds to account.move.line, so we can safely reach the invoice
        through aml.move_id.
        """
        result = super()._aged_partner_report_custom_engine_common(
            options,
            internal_type,
            current_groupby,
            next_groupby,
            offset=offset,
            limit=limit,
        )

        # Grand total / non-grouped result.
        if not current_groupby:
            if isinstance(result, dict):
                result["fel_gt_dte_number"] = None
            return result

        # Grouped results are returned by Odoo as:
        # [(grouping_key, result_dict), ...]
        if not isinstance(result, list):
            return result

        dte_by_aml_id = {}
        if current_groupby == "id":
            aml_ids = [
                grouping_key
                for grouping_key, values in result
                if grouping_key and isinstance(values, dict)
            ]
            if aml_ids:
                amls = self.env["account.move.line"].browse(aml_ids).exists()
                dte_by_aml_id = {
                    aml.id: (aml.move_id.fel_gt_dte_number or None)
                    for aml in amls
                }

        for grouping_key, values in result:
            if not isinstance(values, dict):
                continue

            # At partner level there is no single DTE, so keep the cell blank.
            values["fel_gt_dte_number"] = (
                dte_by_aml_id.get(grouping_key)
                if current_groupby == "id"
                else None
            )

        return result
