# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    free_of_cost = fields.Boolean(string="Free Of Cost",help="If enabled customer will get special discount")
    max_sale_amount = fields.Float(string="Maximum Sale Amount")
    discount_percentage = fields.Float(string="Discount Percentage")
