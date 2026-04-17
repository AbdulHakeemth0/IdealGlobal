from odoo import api, fields, models, _


class CategoryFocSale(models.Model):
    _name = 'category.foc.sale'
    _description = "Category FOC"
    _rec_name = "foc_name"

    document_number = fields.Char(string="Document Number", default=lambda self: _('New'), readonly=True)
    foc_name = fields.Char(string="FOC Name")
    product_category = fields.Many2one("product.category", string="Product Category")
    limit = fields.Char(string="Limit")
    percentage = fields.Char(string="Percentage")
    product_lines = fields.One2many("category.foc.products", 'category_foc_sale_id')

    @api.model
    def create(self, vals):
        if vals.get('document_number', _('New')) == _('New'):
            vals['document_number'] = self.env['ir.sequence'].next_by_code('sale.foc.category') or _('New')

        res = super(CategoryFocSale, self).create(vals)
        return res

    @api.onchange('product_category')
    def onchange_product_category(self):
        product_list = []
        for rec in self:
            print("product categoryyyyyyyyyyyyyyyyyyyyy", rec.product_category)
            products = self.env['product.product'].search([('categ_id', '=', rec.product_category.id)])
            print("productssssssssssssssssss", products)
            for prod in products:
                categ_product = ({
                    'category_foc_sale_id': rec.id,
                    'product_id': prod.id
                })
                print("categ_productsss", categ_product)
                product_list.append(categ_product)
                category_product_line = self.env['category.foc.products']
                category_product_line.sudo().create(categ_product)


class CategoryFocProductLines(models.Model):
    _name = 'category.foc.products'
    _description = "Category FOC Product Lines"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product")
    category_foc_sale_id = fields.Many2one('category.foc.sale')
