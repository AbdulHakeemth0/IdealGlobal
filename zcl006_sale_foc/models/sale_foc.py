from odoo import api, fields, models, _


class SecondFocSale(models.Model):
    _name = 'second.foc.sale'
    _description = "Second FOC"
    _rec_name = "foc_name"

    document_number = fields.Char(string="Document Number", default=lambda self: _('New'), readonly=True)
    foc_name = fields.Char(string="FOC Name")
    limit = fields.Char(string="Limit")
    percentage = fields.Char(string="Percentage")
    product_lines = fields.One2many("foc.product.line", 'second_foc_sale_id')

    @api.model
    def create(self, vals):
        if vals.get('document_number', _('New')) == _('New'):
            vals['document_number'] = self.env['ir.sequence'].next_by_code('sale.foc.second') or _('New')
        res = super(SecondFocSale, self).create(vals)
        return res


class FocProductLines(models.Model):
    _name = 'foc.product.line'
    _description = "FOC Product Lines"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product")
    second_foc_sale_id = fields.Many2one('second.foc.sale')
