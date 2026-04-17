from odoo import models, fields, api


class SaleOrder(models.Model):

     _inherit = "sale.order"

     special_sale_order = fields.Boolean(string="Special Sale Order")

     @api.onchange('order_line')
     def _onchange_orderline(self):
         if self.special_sale_order:
             for rec in self.order_line:
                 rec.price_unit = 0

class SaleOrderLine(models.Model):
    """class defined for adding product code in the sale order"""
    _inherit = 'sale.order.line'

    product_code = fields.Char(string="Product Code",related='product_template_id.product_code')
