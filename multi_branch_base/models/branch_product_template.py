# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """inherited product"""
    _inherit = 'product.template'

    branch_id = fields.Many2one("res.branch", string='Branch', store=True,
                                help='Leave this field empty if this product is'
                                     ' shared between all branches'
                                )
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Allowed Branches",
                                          compute='_compute_allowed_branch_ids')
    product_discount = fields.Integer(string='Discount')
    product_amount = fields.Integer(string="Product Amount")
    method_period = fields.Integer(string='Period Length')
    image_url = fields.Char(string="Image")
    product_code = fields.Char(string="Product Code")

    @api.depends('company_id')
    def _compute_allowed_branch_ids(self):
        for po in self:
            po.allowed_branch_ids = self.env.user.branch_ids.ids

    # @api.onchange('product_amount', 'product_discount')
    # def _onchange_product_amount_discount(self):
    #     if self.product_amount and self.product_discount:
    #         discounted_amount = self.product_amount * (self.product_discount / 100)
    #         self.list_price = discounted_amount
    #     else:
    #         self.list_price = self.product_amount

    @api.onchange('product_amount', 'product_discount')
    def _onchange_product_amount_discount(self):
        if self.product_amount and self.product_discount:
            discounted_amount = self.product_amount - (self.product_amount * self.product_discount / 100)
            self.list_price = discounted_amount
        else:
            self.list_price = self.product_amount