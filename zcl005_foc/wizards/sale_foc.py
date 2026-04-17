# -*- coding: utf-8 -*-
###############################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###############################################################################

from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleFOC(models.Model):
    _name = 'sale.foc'
    _description = "Free of cost model"

    foc_product_ids = fields.One2many('foc.product', 'sale_foc_id',
                                      string="FOC Products")
    sale_order = fields.Char(string="Sale order id")

    def confirm_foc(self):
        active_id = self.env.context.get('active_id')
        sale_order = self.env['sale.order'].browse(active_id).exists()
        total_amount = 0
        for rec in self.foc_product_ids:
            total_amount += rec.product_id.lst_price * rec.qty
        if sale_order.partner_id.discount_percentage:
            percentage_amount = sale_order.amount_total * sale_order.partner_id.discount_percentage
            if total_amount > percentage_amount:
                raise ValidationError(
                    'Discount limit ' + str(percentage_amount) + ' exceeded')
            else:
                for rec in self.foc_product_ids:
                    self.env['sale.order.line'].create(
                        {'product_id': rec.product_id.id,
                         'product_uom_qty': rec.qty,
                         'price_unit': 0, 'order_id': sale_order.id})

                sale_order.sudo().action_confirm()
