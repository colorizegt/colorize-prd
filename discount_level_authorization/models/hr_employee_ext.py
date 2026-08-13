from odoo import fields, models, api, exceptions
import hashlib


class ResUsersExt(models.Model):
    _inherit = "hr.employee"

    allowed_discount_percentage = fields.Integer(
        string='Allowed Discount %',
        help='The allowed discount percentage for this user.')

    @api.constrains('allowed_discount_percentage')
    def _check_discount_percentage(self):
        """
        Ensure that the allowed discount percentage is between 0 and 100.
        """
        for record in self:
            if record.allowed_discount_percentage < 0 or record.allowed_discount_percentage > 100:
                raise exceptions.ValidationError("Discount percentage must be between 0% and 100%.")


    def get_barcodes_and_pin_hashed_ext(self):
        """
        overwritten source method to add allowed_discount_percentage field to employees data
        """
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            return []
        visible_emp_ids = self.search([('id', 'in', self.ids)])
        employees_data = self.sudo().search_read([('id', 'in', visible_emp_ids.ids)], ['barcode', 'pin','allowed_discount_percentage'])

        for e in employees_data:
            e['barcode'] = hashlib.sha1(e['barcode'].encode('utf8')).hexdigest() if e['barcode'] else False
            e['pin'] = hashlib.sha1(e['pin'].encode('utf8')).hexdigest() if e['pin'] else False
        return employees_data

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Override to include allowed_discount_percentage in the fields loaded for POS data."""
        fields = super()._load_pos_data_fields(config_id)
        if 'allowed_discount_percentage' not in fields:
            fields.append('allowed_discount_percentage')
        return fields
    
class ChrisHREmployeePublicExt(models.Model):
    _inherit = 'hr.employee.public'

    allowed_discount_percentage = fields.Integer(related='employee_id.allowed_discount_percentage', readonly=True)
