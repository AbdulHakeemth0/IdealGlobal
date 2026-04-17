from odoo import api ,fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    new_product = fields.Boolean(string='New Product')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        domain = ['|', ('product_code', operator, name),
                  ('name', operator, name)]
        products = self.search(domain + args, limit=limit)
        return products.name_get()