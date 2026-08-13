from odoo import models, fields, api
from odoo.api import ValuesType, Self


class DiscountLevelPosOrderExt(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        created_recs = super().create(vals_list)
        for rec in created_recs:
            if rec.discount_reason:
                body = "Discount Reason: \n" + rec.discount_reason
                rec.with_context(company_id=self.env.company.id).message_post(body=body, author_id=rec.create_uid.id, subtype_xmlid="mail.mt_comment", message_type="comment")

            if rec.discount_reason_file:
                self.env['ir.attachment'].create({
                    'name': rec.discount_reason_file_name,
                    'type': 'binary',
                    'datas': rec.discount_reason_file,
                    'res_model': 'pos.order',
                    'res_id': rec.id
                })
        return created_recs
    discount_reason = fields.Text('Discount Reason', tracking=True)
    discount_reason_file = fields.Binary('Discount Reason File', tracking=True)
    discount_reason_file_name = fields.Char('Discount Reason File Name')