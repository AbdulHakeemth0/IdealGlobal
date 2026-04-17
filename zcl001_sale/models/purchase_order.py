from odoo import api,fields, models
from odoo.exceptions import AccessError


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.constrains('name')
    def _check_user_access(self):
        if not self.env.user.create_purchase_order:
            raise AccessError("Access Denied")

    def button_confirm(self):
        if self.env.user.confirm_purchase_order:
            return super(PurchaseOrder,self).button_confirm()
        else:
            raise AccessError("Access Denied")