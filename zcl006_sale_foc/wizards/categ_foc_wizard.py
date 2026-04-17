from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SaleCategoryFOC(models.Model):
    _name = 'foc.category.wizard'
    _description = "Category FOC Wizard"

    categ_foc_product_line_ids = fields.One2many('category.wizard.products', 'categ_foc_product_id', string="Category FOC Products")
    foc_type = fields.Selection([('category_foc', 'Category FOC')], string="FOC Type", default='category_foc', readonly=True)
    foc_name = fields.Many2one("category.foc.sale", "Category FOC")
    sale_order_amount = fields.Float(string="Sale order amount", readonly=True)
    sale_order_foc_amount = fields.Float(string="Sale order FOC amount", readonly=True)
    percentage_amount = fields.Float(string="Percentage amount")
    total_amount = fields.Float(string="Total amount", readonly=True, store=True)
    # categ_foc_name = fields.Many2one("category.foc.sale", "FOC")
    common_categ_foc_names = fields.Many2many("category.foc.sale", string="Category FOC", store=True, readonly=False)
    eligible_foc_names = fields.Many2many("category.foc.sale", 'eligible_foc_rel', string="Eligible Category FOC", readonly=True)

    @api.onchange('foc_type')
    def onchange_foc_type(self):
        if self.foc_type == 'category_foc':
            active_id = self.env.context.get('active_id')
            sale_order = self.env['sale.order'].browse(active_id).exists()
            sale_product_list = set(rec.product_id.id for rec in sale_order.order_line)
            print("sale_product_list", sale_product_list)
            category_foc_records = self.env['category.foc.sale'].search([])
            common_products = set()
            common_foc_records = self.env['category.foc.sale']
            common_foc_names_list = []
            common_foc_ids = []
            for categ_foc in category_foc_records:
                foc_product_list = set(prod.id for prod in categ_foc.product_lines.product_id)
                print("foc_product_list", foc_product_list)
                common_products.update(sale_product_list.intersection(foc_product_list))
                print("common_products", common_products)
                for rec in common_products:
                    print("recccccccccc", rec)
                    for line in categ_foc.product_lines:
                        print("linesssssssssssssssss", line)
                        if line.product_id.id == rec:
                            print("line.product_id.id", line.product_id.id)
                            common_foc_ids.append(categ_foc.id)
                    self.eligible_foc_names = [(6, 0, common_foc_ids)]

    @api.onchange('foc_name')
    def onchange_common_categ_foc_names_select(self):
        # for fname in self.common_categ_foc_names:
        foc = self.env['category.foc.sale'].search([('foc_name', '=', self.foc_name.foc_name)])
        print("focfocfocfocnewwwwwcatee", foc)
        for rec in foc:
            active_id = self.env.context.get('active_id')
            sale_order = self.env['sale.order'].browse(active_id).exists()
            sale_amount = 0.00
            for s_line in sale_order.order_line:
                for p_line in rec.product_lines:
                    if s_line.product_id.id == p_line.product_id.id:
                        sale_amount += s_line.price_subtotal
                        print("sale_amount", sale_amount)
                    self.sale_order_foc_amount = sale_amount
                    self.sale_order_amount = sale_order.amount_total
                    if self.sale_order_foc_amount <= 0.00:
                        self.percentage_amount = 0.00
                    else:
                        print("self.sale_order_foc_amount", self.sale_order_foc_amount)
                        if self.sale_order_foc_amount >= float(rec.limit):
                            self.percentage_amount = self.sale_order_foc_amount * float(rec.percentage) / 100
                            print("self.percentage_amount", self.percentage_amount)
                        else:
                            self.percentage_amount = 0.00

    @api.onchange('sale_order_foc_amount')
    def onchange_sale_order_foc_amount(self):
        for fname in self.common_categ_foc_names:
            foc = self.env['category.foc.sale'].search([('foc_name', '=', fname.foc_name)])
            print("focfocfocfoc", foc)
            for rec in foc:
                if self.sale_order_foc_amount > 0.00:
                    if self.sale_order_foc_amount >= float(rec.limit):
                        self.percentage_amount = self.sale_order_foc_amount * float(rec.percentage) / 100
                        print("self.percentage_amount", self.percentage_amount)
                else:
                    self.percentage_amount = 0.00

    def confirm_category_foc(self):
        print("cccccccccccccc")
        active_id = self.env.context.get('active_id')
        sale_order = self.env['sale.order'].browse(active_id).exists()
        tot_amount = 0
        print("sale_order", sale_order)
        print("res.common_categ_foc_names.product_category", self.common_categ_foc_names.product_category.id)

        for rec in self.categ_foc_product_line_ids:
            product = self.env['product.product'].search([('name', '=', rec.product_id.product_id.name)])
            tot_amount += (product.lst_price * rec.product_qty)
            self.total_amount = tot_amount
            print("tot_amounttot_amounttot_amount", tot_amount)
            print("self.percentage_amount", self.percentage_amount)
        # percentage = self.percentage_amount
        if self.percentage_amount < tot_amount:
            print("percentageeeeee lesssssssss")
            raise ValidationError('FOC limit exceeded')
        else:
            for rec in self.categ_foc_product_line_ids:
                product = self.env['product.product'].search([('name', '=', rec.product_id.product_id.name)])
                self.env['sale.order.line'].create(
                    {'product_id': product.id,
                     'product_uom_qty': rec.product_qty,
                     'price_unit': 0, 'order_id': sale_order.id})


class FocCategoryProductLines(models.Model):
    _name = 'category.wizard.products'
    _description = "FOC Category Product Lines"

    product_qty = fields.Float(string="Quantity")
    categ_foc_product_id = fields.Many2one('foc.category.wizard')
    sale_product_id = fields.Many2one('sale.order.line')
    product_id = fields.Many2one("category.foc.products", string="Product")
    product_price = fields.Float(string="Price", store=True)
    subtotal = fields.Float(string="Subtotal", readonly=True, store=True)
    total = fields.Float(string="Total")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                product = self.env['product.product'].search([('name', '=', rec.product_id.product_id.name)])
                if product:
                    rec.product_price = product.lst_price

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        total_amount = 0
        for rec in self:
            if rec.product_id:
                product = self.env['product.product'].search([('name', '=', rec.product_id.product_id.name)])
                if product:
                    rec.subtotal = product.lst_price * rec.product_qty
                    total_amount += rec.subtotal
        # Update the 'total' field based on the calculated total_amount
        self.total = total_amount
