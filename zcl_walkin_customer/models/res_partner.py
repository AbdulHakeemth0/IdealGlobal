# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    walkin_customer = fields.Boolean(string="Walkin Customer",default=False)
    walkin_customer_ids = fields.One2many('walkin.customer.line','walkin_cust_id',string="Walkin customer")

class WalkinCustomerLine(models.Model):
    _name = "walkin.customer.line"
    _description = "Walkin customer details"

    name = fields.Char(string="Name")
    phone = fields.Char(string="Phone")
    walkin_cust_id = fields.Many2one('res.partner')
