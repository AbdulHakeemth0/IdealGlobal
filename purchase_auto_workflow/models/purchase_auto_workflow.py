from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def purchase_auto(self):
        self.button_confirm()
        if self.picking_ids:
            for recept in self.picking_ids:
                if recept:
                    for rec in recept:
                        for res in rec.move_ids:
                            res.quantity_done = res.product_uom_qty
                        rec.button_validate()
        self.action_create_invoice()
