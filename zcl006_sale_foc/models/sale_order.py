from odoo import models, fields, api, exceptions, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_apply_foc(self):
        print("lllllllllllllll")
        sale_product_list = set(rec.product_id.id for rec in self.order_line)
        print("sale_product_list", sale_product_list)
        product_foc_records = self.env['second.foc.sale'].search([])
        common_foc_ids = []
        # for foc in category_foc_records or product_foc_records:
        for foc in product_foc_records:
            print("focccc ", foc.document_number)

        return {
            'name': 'Apply FOC',
            'type': 'ir.actions.act_window',
            'res_model': 'foc.sale.wizard',
            'view_mode': 'form',
            "target": 'new',
            'context': {'default_sale_order': self.id}
        }

    def action_apply_categ_foc(self):
        print("cattttttttttttttttttttt")
        sale_product_list = set(rec.product_id.id for rec in self.order_line)
        print("sale_product_list", sale_product_list)
        category_foc_records = self.env['category.foc.sale'].search([])
        for foc in category_foc_records:
            print("focccc cattt ", foc.document_number)
            active_id = self.env.context.get('active_id')
            sale_order = self.env['sale.order'].browse(active_id).exists()
            categ_wizard = self.env['foc.category.wizard'].browse(active_id).exists()
            categ_wizard.sale_order_amount = sale_order.amount_total
            print("self.sale_order_amount", categ_wizard.sale_order_amount)
        return {
            'name': 'Apply Category FOC',
            'type': 'ir.actions.act_window',
            'res_model': 'foc.category.wizard',
            'view_mode': 'form',
            "target": 'new',
            'context': {
                'default_sale_order': self.id,
                'foc_type': "Category FOC",
                'sale_order_amount': float(self.amount_total),
            }
        }