from odoo import api, fields, models, SUPERUSER_ID, _


class ProductPriceListInherit(models.Model):
    _inherit = "product.pricelist"

    pricelist_category_id = fields.Many2one("price.category", string="Category")

    @api.model_create_multi
    def create(self, vals_list):
        value = super().create(vals_list)
        if self.item_ids:
            for rec in self.item_ids:
                rec.unlink()
        for rec in value.pricelist_category_id:
            for res in rec.line_ids:
                self.env['product.pricelist.item'].create({
                    "product_tmpl_id": res.product_id.id,
                    "fixed_price": res.price,
                    "pricelist_id": value.id,
                    'min_quantity': 1,
                })
        return value

    def write(self, vals):
        result = super().write(vals)
        if self.item_ids:
            for rec in self.item_ids:
                rec.unlink()
        for rec in self.pricelist_category_id:
            for res in rec.line_ids:
                self.env['product.pricelist.item'].create({
                    "product_tmpl_id": res.product_id.id,
                    "fixed_price": res.price,
                    "pricelist_id": self.id,
                    'min_quantity': 1,
                })
        return result


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_code = fields.Char(related='product_tmpl_id.product_code',
                               string="Product Code")
    fixed_price = fields.Float(string="Fixed Price", digits=(12, 3))

    # @api.depends('item_ids')
    # def change_price(self):
    #     print(self.env['product.pricelist'].search({[('pricelist_category_id.id', '=',self.pricelist_category_id.id)]}))

    # category = self.search([('pricelist_category_id', '=', self.pricelist_category_id.id)])
    # for rec in self.item_ids:
    #     product = rec.product_tmpl_id.id
    #     price = rec.fixed_price
    #     for c in category:
    #         for i in c.item_ids:
    #             if i.product_tmpl_id.id == product:
    #                 i.fixed_price = price

    # def write(self, vals):
    #     value = super().write(vals)
    #     self.item_ids = [(5, 0, 0)]
    #     for rec in self.pricelist_category_id:
    #         for res in rec.line_ids:
    #             self.env['product.pricelist.item'].create({
    #                 "product_tmpl_id": res.product_id.id,
    #                 "fixed_price": res.price,
    #                 "pricelist_id": self.id,
    #                 'min_quantity': 1,
    #             })
    #     return value
