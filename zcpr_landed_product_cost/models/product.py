from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    latest_product_cost = fields.Monetary("Cost After LC", readonly=1, store=True)
