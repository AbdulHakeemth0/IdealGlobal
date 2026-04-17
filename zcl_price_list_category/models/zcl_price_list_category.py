# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Anoop Jayaprakash, Merlin Thomas
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# This program is free software:
# you can modify it under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

###################################################################################

from odoo import api, fields, models


class PriceCategory(models.Model):
    _name = "price.category"

    name = fields.Char(string='Category')
    line_ids = fields.One2many("price.category.list", "line_id")

    @api.onchange('line_ids')
    def change_product_price(self):
        category = self.env['product.pricelist'].search([('pricelist_category_id.name','=',self.name)])
        print(category)
        for rec in self.line_ids:
            rec.product_code = rec.product_id.product_code
            product = rec.product_id.id
            price = rec.price
            for c in category:
                for i in c.item_ids:
                    if i.product_tmpl_id.id == product:
                        i.fixed_price = price




class PriceCategoryList(models.Model):
    _name = "price.category.list"
    price = fields.Float(string='Price',digits=(12,3))
    product_id = fields.Many2one("product.template")
    product_code =fields.Char(string="Product Code")
    line_id = fields.Many2one("price.category")
