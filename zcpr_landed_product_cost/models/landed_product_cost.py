from odoo import api, models, fields


class ProductLandedCostValue(models.Model):
    _name = 'product.landed.cost.value'
    _description = "Product Landed Cost Value"

    name = fields.Char('Description')
    landed_cost_id = fields.Many2one(
        'stock.landed.cost', 'Landed Cost',
        required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    price_unit = fields.Monetary('Cost', required=True)
    currency_id = fields.Many2one('res.currency', related='landed_cost_id.currency_id')


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    product_cost_lines = fields.One2many(
        'product.landed.cost.value', 'landed_cost_id', 'Product Cost Lines',
        copy=True, states={'done': [('readonly', True)]})

    def cron_product_cost_after_lc(self):
        costs = self.env['stock.landed.cost'].sudo().search([('state', '=', 'done')])
        for cost in costs:
            cost.compute_product_cost()
            for line in cost.product_cost_lines:
                line.product_id.update({
                    'latest_product_cost': line.price_unit
                })

    def compute_product_cost(self):
        for record in self:
            ProductCost = self.env['product.landed.cost.value']
            ProductCost.search([('landed_cost_id', 'in', self.ids)]).unlink()
            product_cost_dict = {}
            for move in record.picking_ids.move_lines:
                for line in record.valuation_adjustment_lines:
                    if move.id not in product_cost_dict and move.product_id.id == line.product_id.id:
                        value = sum(move.stock_valuation_layer_ids.mapped('value')) + line.additional_landed_cost
                        product_cost_dict[move.id] = {
                            'qty': move.product_qty,
                            'value': value,
                            'product_id': move.product_id.id
                        }
                    elif move.product_id.id == line.product_id.id:
                        value = line.additional_landed_cost
                        product_cost_dict[move.id]['value'] += value
            product_value_dict = {}
            for key, value in product_cost_dict.items():
                product = self.env['product.product'].sudo().search([('id', '=', value['product_id'])])
                if product.id not in product_value_dict:
                    product_value_dict[value['product_id']] = {
                        'name': product.name,
                        'product_id': product.id,
                        'landed_cost_id': record.id,
                        'price_unit': value['value'],
                        'qty': value['qty']
                    }
                else:
                    product_value_dict[value['product_id']]['price_unit'] += value['value']
                    product_value_dict[value['product_id']]['qty'] += value['qty']
            for key, value in product_value_dict.items():
                ProductCost.sudo().create({
                    'name': value['name'],
                    'product_id': value['product_id'],
                    'landed_cost_id': value['landed_cost_id'],
                    'price_unit': record.currency_id.round(value['price_unit'] / value['qty'])
                })

    def compute_landed_cost(self):
        res = super(StockLandedCost, self).compute_landed_cost()
        self.compute_product_cost()
        return res

    def button_validate(self):
        res = super(StockLandedCost, self).button_validate()
        for line in self.product_cost_lines:
            line.product_id.update({
                'latest_product_cost': line.price_unit
            })
        return res
