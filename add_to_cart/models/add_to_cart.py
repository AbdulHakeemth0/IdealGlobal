from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.http import request


class AddToCart(models.Model):
    _name = "add.to.cart"
    _description = "Add To Cart"
    _rec_name = "partner_id"

    partner_id = fields.Many2one('res.partner', 'Customer')
    country_id = fields.Many2one('res.country', 'Country')
    date = fields.Date(string="Date", default=fields.Date.context_today)
    total = fields.Float(string="Total", compute="_compute_cost")
    order_line_ids = fields.One2many('add.to.cart.line', 'add_to_cart_id', "Order Line")
    narration = fields.Text(string="Narration")

    @api.model
    def create(self, vals):
        res = super(AddToCart, self).create(vals)
        add_to_cart = self.env['add.to.cart'].search([('partner_id', '=', res.partner_id.id)])
        if len(add_to_cart) > 1:
            raise UserError(_('ALREADY THIS "%s" USER HAVE A CART') % (add_to_cart.partner_id.name))
        return res

    @api.depends('order_line_ids.qty', 'order_line_ids.price')
    def _compute_cost(self):
        for rec in self:
            rec.total = sum(rec.order_line_ids.mapped('price'))


class AddToCartLine(models.Model):
    _name = "add.to.cart.line"
    _description = "Add To Cart Line"
    _rec_name = "product_id"

    add_to_cart_id = fields.Many2one('add.to.cart', "Add To Cart")
    product_id = fields.Many2one('product.product', string="Product Code")
    image = fields.Char(string="Image")
    qty = fields.Float("Quantity")
    unit_price = fields.Float("Unit Price")
    price = fields.Float("Price")

