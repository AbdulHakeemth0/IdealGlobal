from odoo import fields, models


class WalkinCustomer(models.Model):
    _name = "walkin.customer"
    _description = "walkin customer model"

    customer_id = fields.Many2one('res.partner')
    name = fields.Char(string="Name")
    phone = fields.Char(string="Phone")
