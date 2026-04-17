from odoo import models, fields, api, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    image = fields.Char(string='Image')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        domain = ['|', ('product_code', operator, name),('name', operator, name)]
        products = self.search(domain + args, limit=limit)
        return products.name_get()