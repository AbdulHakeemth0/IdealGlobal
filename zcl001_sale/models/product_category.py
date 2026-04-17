from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    img_url = fields.Char(string="Image URL")