from odoo import models, fields,exceptions, api, _
from lxml import etree


class PurchaseReturnWizardsLine(models.TransientModel):
    _name = "purchase.return.wizard.line"

    purchase_order = fields.Many2one('purchase.order', 'Purchase Order')
    purchase_order_line = fields.Many2one('purchase.order.line', 'Purchase Order')
    purchase_return_wizard_id = fields.Many2one('purchase.order.line', string='wizard')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char("Name")
    qty = fields.Float("Quantity")
    taxes_id = fields.Many2many('account.tax', string="Taxes")
    price_unit = fields.Float("Price Unit")
    sub_total = fields.Float("Sub Total")
    piking_bill = fields.Char(string="Bill No")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node_form in doc.xpath("//tree"):
            node_form.set("create", 'false')
            node_form.set("edit", 'false')
            res['arch'] = etree.tostring(doc)
        for node_form in doc.xpath("//form"):
            node_form.set("create", 'false')
            node_form.set("edit", 'false')
            res['arch'] = etree.tostring(doc)
        return res

    def add_to_the_line(self):
        self.purchase_return_wizard_id.price_unit = self.price_unit
        order_lines = self.env['purchase.order.line'].search([('id', '=', self.purchase_order_line.id)])
        self.purchase_return_wizard_id.taxes_id = order_lines.taxes_id.ids