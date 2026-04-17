from odoo import fields , models, api

class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    purchase_account = fields.Char(String="Purchase Account")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id


