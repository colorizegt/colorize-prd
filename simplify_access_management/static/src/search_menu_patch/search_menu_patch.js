/** @odoo-module **/
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, useState } from "@odoo/owl";

patch(SearchBarMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.orm = useService("orm");
    this.access = useState({
      removeCustomFilter: false,
      removeCustomGroup: false,
    });
    onWillStart(async () => {
      // ⚠️ Odoo 19: usar this.env.searchModel?.resModel
      const resModel = this.env?.searchModel?.resModel;
      if (!resModel) {
        return;
      }
      try {
        // ⚠️ ADVERTENCIA: El método 'is_custom_filter_and_group_available'
        // NO EXISTE en el modelo 'access.management'. Debe ser creado o
        // eliminar esta llamada.
        const res = await this.orm.call(
          "access.management",
          "is_custom_filter_and_group_available",
          ["", resModel]
        );
        this.access.removeCustomFilter = res.filter;
        this.access.removeCustomGroup = res.group;
      } catch (error) {
        console.warn(
          "[simplify_access_management] Error al consultar filtros custom:",
          error
        );
      }
    });
  },

  get hideCustomGroupBy() {
    return (
      this.env.searchModel.hideCustomGroupBy || this.access.removeCustomGroup
    );
  },
});
