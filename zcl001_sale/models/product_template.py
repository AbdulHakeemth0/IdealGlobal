from odoo import api ,fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    new_product = fields.Boolean(string='New Product')
    launch_time = fields.Datetime(string="Launch Time")
    warranty = fields.Datetime(string="Warranty")
    division_group = fields.Char(string="Division Group")
    name_arabic = fields.Char(string="Arabic Name")

    @api.constrains('name')
    def _check_user_access(self):
        if not self.env.user.create_product:
            raise AccessError("Access Denied")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        domain = ['|', ('product_code', operator, name),
                  ('name', operator, name)]
        products = self.search(domain + args, limit=limit)
        return products.name_get()

class Stockmove(models.Model):

    _inherit = "stock.move"

    #product_code = fields.Char(related="product_id.product_code", string="Product Code")
    product = fields.Char(related="product_id.name", string='Product')





