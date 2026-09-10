/** @odoo-module **/
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

patch(SearchBarMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.orm = useService("orm");
    onWillStart(async () => {
      const resModel = this.env?.searchModel?.resModel;
      if (!resModel) {
        return;
      }
      try {
        const res = await this.orm.call("access.management", "get_hidden_field", [
          "",
          resModel,
        ]);
        if (this.fields && Array.isArray(this.fields)) {
          this.fields = this.fields.filter((ele) => !res.includes(ele.name));
        }
      } catch (error) {
        console.warn(
          "[simplify_access_management] Error al filtrar campos:",
          error
        );
      }
    });
  },
});
