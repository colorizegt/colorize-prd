/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    /**
     * Odoo 19: Los datos de hr.employee se cargan automáticamente
     * mediante pos.load.mixin. Accedemos a ellos desde this.models.
     */
    
    async validateDiscountManagerPin(pin) {
        /**
         * Odoo 19: Validamos el PIN mediante RPC al backend.
         * No confiamos en el PIN que viene en los datos cargados.
         */
        if (!pin) {
            return false;
        }
        
        try {
            const result = await this.env.services.orm.call(
                "hr.employee",
                "validate_discount_manager_pin",
                [pin]
            );
            return result;
        } catch (error) {
            console.error("Error validating discount manager PIN:", error);
            return false;
        }
    },

    getDiscountManager() {
        /**
         * Odoo 19: Obtenemos los empleados que son managers de descuento.
         * Los datos vienen de this.models["hr.employee"].
         */
        const employees = this.models["hr.employee"] || [];
        return employees.filter(emp => emp.discount_manager);
    },

    getEmployeeDiscountLimit(employeeId) {
        /**
         * Odoo 19: Obtenemos el límite de descuento de un empleado.
         */
        const employees = this.models["hr.employee"] || [];
        const employee = employees.find(emp => emp.id === employeeId);
        return employee ? employee.limited_discount : 0;
    },
});
