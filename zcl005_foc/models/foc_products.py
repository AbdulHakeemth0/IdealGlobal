# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import api, fields, models


class FOCProducts(models.Model):
    _name = 'foc.product'
    _description = "FOC product model"

    product_id = fields.Many2one("product.product",string="Product",domain="[('product_tmpl_id.free_of_cost','=',True)]")
    qty = fields.Float(string="Quantity")
    sale_foc_id = fields.Many2one('sale.foc')
    subtotal = fields.Float(string="Subtotal",readonly=True, store=True)
    total = fields.Float(string="Total")

    @api.onchange('qty')
    def _onchange_product(self):
        #self.total = self.product_id.lst_price * self.qty
        self.subtotal = self.product_id.lst_price * self.qty
