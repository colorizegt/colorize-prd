/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { registry } from "@web/core/registry";
import { onWillStart, useState } from "@odoo/owl";

const cogMenuRegistry = registry.category("cogMenu");

patch(CogMenu.prototype, {
  setup() {
    super.setup();
    this.access = useState({ removeSpreadsheet: false });
    onWillStart(async () => {
      // Odoo 19: usar this.env.config
      const config = this.env?.config;
      if (config?.actionType === "ir.actions.act_window") {
        try {
          const res = await this.orm.call(
            "access.management",
            "is_spread_sheet_available",
            [1, config.actionType, config.actionId]
          );
          this.access.removeSpreadsheet = res;
          // Odoo 19: registryItems es una propiedad computed, refrescar
          this.registryItems = await this._registryItems();
        } catch (error) {
          console.warn(
            "[simplify_access_management] Error al consultar spreadsheet:",
            error
          );
        }
      }
    });
  },

  async _registryItems() {
    const items = [];
    for (const item of cogMenuRegistry.getAll()) {
      if (
        item?.Component?.name === "SpreadsheetCogMenu" &&
        this.access.removeSpreadsheet
      ) {
        continue;
      }
      if ("isDisplayed" in item ? await item.isDisplayed(this.env) : true) {
        items.push({
          Component: item.Component,
          groupNumber: item.groupNumber,
          key: item.Component.name,
        });
      }
    }
    return items;
  },
});
