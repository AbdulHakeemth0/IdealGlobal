from odoo import api, fields, models, SUPERUSER_ID, _

class PurchaseInherits(models.Model):
    _inherit = "purchase.order"

    purchase_return = fields.Boolean("Purchase Return", invisible=1, default=False)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    state = fields.Selection(selection_add=[('return', 'Return')])
    picking_count = fields.Integer(compute='_compute_picking_count', string="Transfer")
    refund_count = fields.Integer(compute='_compute_refund_count', string="Refund Note")

    def action_view_picking(self):
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
            'res_id': self.id,
        }
    def action_view_refund(self):
        return {
            'name': 'Refund Note',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('payment_reference', '=', self.name), ('move_type', '=', 'out_refund')],
            'res_id': self.id,
        }
    def _compute_picking_count(self):
        for rec in self:
            if rec.name:
                picking = self.env['stock.picking'].search([('origin', '=', self.name)])
                rec.picking_count = int(len(picking))

    def _compute_refund_count(self):
        for rec in self:
            if rec.name:
                refund = self.env['account.move'].search(
                    [('payment_reference', '=', self.name), ('move_type', '=', 'out_refund')])
                rec.refund_count = int(len(refund))


    def button_cancel(self):
        lines = []
        stock_list = []
        # location = self.env['stock.location'].search([('return_location', '=', True)], limit=1)
        for rec in self.order_line:
            stock_product = ({
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'product_uom_qty': rec.product_qty,
                'location_id': rec.product_id.property_stock_production.id,
                'location_dest_id': rec.product_id.property_stock_inventory.id
            })
            stock_list.append((0, 0, stock_product))

            components = ({
                'product_id': rec.product_id.id,
                'name': rec.name,
                'quantity': rec.product_qty,
                'price_unit': rec.price_unit,
                'tax_ids': rec.taxes_id.ids
            })
            lines.append((0, 0, components))

        refund_count = self.env['account.move'].create({
            'move_type': 'out_refund',
            'state': 'draft',
            'partner_id': self.partner_id.id,
            'payment_reference': self.name,
            'invoice_line_ids': lines,
        })

        returns = self.env['stock.picking.type'].search([('delivery_type', '=', True)], limit=1)
        stock_picking = self.env['stock.picking'].create({
            'state': 'draft',
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'picking_type_id': returns.id,
            'location_id': self.order_line.product_id.property_stock_production.id,
            'location_dest_id': self.order_line.product_id.property_stock_inventory.id,
            'move_ids_without_package': stock_list
        })
        stock_picking_confirm = stock_picking.action_confirm()
        self.write({'state': 'return'})


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                if vals.get('purchase_return', False):
                    vals['name'] = self.env['ir.sequence'].next_by_code('purchase.return') or _('New')
        return super().create(vals_list)









class PurchaseOrderLineInherit(models.Model):
    _inherit = "purchase.order.line"

    purchase_return = fields.Boolean(related='order_id.purchase_return', string="Purchase Return")
    purchase_return_wizard_ids = fields.One2many('purchase.return.wizard.line', 'purchase_return_wizard_id', "Purchase Return Wizard")
    purchase_order_line = fields.Many2one('purchase.order.line', 'Purchase Order Line')
    purchase_orders_id = fields.Many2one('purchase.order', 'Purchase Order')

    def open_return_wizard(self):
        if self.purchase_return:
            product_list = []
            purchase_order = self.env['purchase.order'].search([('partner_id', '=', self.order_id.partner_id.id), ('state', '=', 'purchase'), ('purchase_return', '=', False)])
            for purchase in purchase_order:
                if purchase.picking_ids:
                    order_lines = self.env['purchase.order.line'].search([('order_id', '=', purchase.id), ('product_id', '=', self.product_id.id), ('product_qty', '>=', self.product_qty), ('purchase_return', '=', False)])
                    for line in order_lines:
                        if not self.env['purchase.return.wizard.line'].search([('purchase_order', '=', purchase.id), ('purchase_order_line', '=', line.id), ('purchase_return_wizard_id', '=', self.id)]):
                            component = {
                                'purchase_order': purchase.id,
                                'purchase_order_line': line.id,
                                'purchase_return_wizard_id': self.id,
                                'product_id': line.product_id.id,
                                'name': line.product_id.name,
                                'qty': line.product_qty,
                                'taxes_id': line.taxes_id,
                                'price_unit': line.price_unit,
                                'sub_total': line.price_subtotal,
                                'piking_bill': purchase.picking_ids[0].name
                            }
                            wizard_line = self.env['purchase.return.wizard.line'].create(component)
            return {
                'name': 'Products',
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.return.wizard.line',
                'view_mode': 'tree',
                'view_type': 'tree',
                'target': 'new',
                'domain': [('purchase_return_wizard_id', '=', self.id), ('qty', '>=', self.product_qty)],
            }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id