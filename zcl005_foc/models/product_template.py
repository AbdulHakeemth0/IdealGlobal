# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    free_of_cost = fields.Boolean(string="Free Of Cost",help="If enabled customer will get special discount")
