/** @odoo-module **/
import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";
import { session } from "@web/session";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");

    onMounted(async () => {
      // Odoo 19: obtener cids del hash o session
      const hash = window.location.hash.replace("#", "").split("&");
      let cids;
      const cidIndex = hash.findIndex((ele) => ele.includes("cid"));
      if (cidIndex === -1) {
        cids = session.company_id;
      } else {
        const cidList = hash[cidIndex].split("=")[1].split(",");
        cids = cidList.length > 0 ? parseInt(cidList[0]) : session.company_id;
      }

      let model;
      const modelEntry = hash.find((ele) => ele.includes("model"));
      if (modelEntry) {
        model = modelEntry.split("=")?.[1].split(",")?.[0];
      }
      if (!model) {
        model = this.props?.resModel;
      }

      if (!cids || !model) {
        return;
      }

      try {
        const result = await this.orm.call(
          "access.management",
          "get_chatter_hide_details",
          [session.user_id, cids, model]
        );

        // Odoo 19: usar CSS classes en lugar de jQuery
        const hideClasses = [];
        if (!result["hide_send_mail"]) {
          hideClasses.push(".o-mail-Chatter-sendMessage");
        }
        if (!result["hide_log_notes"]) {
          hideClasses.push(".o-mail-Chatter-logNote");
        }
        if (!result["hide_schedule_activity"]) {
          hideClasses.push(".o-mail-Chatter-activity");
        }

        if (hideClasses.length) {
          const style = document.createElement("style");
          style.id = "sam-hide-chatter-style";
          style.textContent = `${hideClasses.join(", ")} { display: none !important; }`;
          document.head.appendChild(style);
        }
      } catch (error) {
        console.warn(
          "[simplify_access_management] Error al ocultar chatter:",
          error
        );
      }
    });
  },
});
