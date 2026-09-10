/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, useState } from "@odoo/owl";

patch(FormController.prototype, {
  setup() {
    super.setup();
    // ⚠️ CORREGIDO: Añadir this.orm que faltaba
    this.orm = useService("orm");
    this.access = useState({ removeProperty: false });
    onWillStart(async () => {
      try {
        this.access.removeProperty = await this.orm.call(
          "access.management",
          "is_add_property_available",
          [1, this.props?.resModel]
        );
      } catch (error) {
        console.warn(
          "[simplify_access_management] Error al consultar propiedad:",
          error
        );
      }
    });
  },

  get actionMenuItems() {
    const menuItems = super.actionMenuItems;
    if (this.access.removeProperty && menuItems.action) {
      menuItems.action = menuItems.action.filter(
        (ele) => ele.key != "addPropertyFieldValue"
      );
    }
    return menuItems;
  },
});
