from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, AccessError
from odoo.http import request


class SaleInherits(models.Model):
    _inherit = "sale.order"

    sale_return = fields.Boolean("Sale Return", invisible=1, default=False)
    return_sale = fields.Boolean("Return sale", invisible=1, default=False)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    state = fields.Selection(selection_add=[('return', 'Return')])
    picking_count = fields.Integer(compute='_compute_picking_count', string="Transfer")
    debit_count = fields.Integer(compute='_compute_debit_count', string="Debit Note")
    return_count = fields.Integer(compute='_compute_return_count', string="Return Note")
    sale_return_ids = fields.Many2one('sale.order', string="Return ids" )

    def action_view_picking(self):
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
            'res_id': self.id,
        }

    def action_view_debit(self):
        return {
            'name': 'Debit Note',
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

    def _compute_debit_count(self):
        for rec in self:
            if rec.name:
                debit = self.env['account.move'].search([('payment_reference', '=', self.name), ('move_type', '=', 'out_refund')])
                rec.debit_count = int(len(debit))

    def _compute_return_count(self):
        for rec in self:
            if rec.name:
                return_count = self.env['sale.order.line'].search([('return_sale', '=', True), ('order_id', '=', self.id)])
                rec.return_count = int(len(return_count))
    # super cancel button to update quantity when cancel a sale return
    def action_cancel(self):
        res = super(SaleInherits, self).action_cancel()
        for rec in self.order_line:
            if rec.return_line_id:
                order_lines = self.env['sale.order.line'].sudo().search([('id', '=', int(rec.return_line_id))])
                if order_lines:
                    order_lines.return_qty -= rec.product_uom_qty
        return res

    # super cancel button to update quantity when cancel a sale return
    def unlink(self):
        for order in self:
            for rec in order.order_line:
                if rec.return_line_id:
                    order_lines = self.env['sale.order.line'].sudo().search([('id', '=', int(rec.return_line_id))])
                    if order_lines:
                        order_lines.return_qty -= rec.product_uom_qty
        return super(SaleInherits, self).unlink()


    def action_confirm_return(self):
        if self.env.user.confirm_sale_return:
            lines = []
            stock_list = []
            location = self.env['stock.location'].search([('name', '=', 'Stock'), ('location_id.name', '=', 'WH')])
            for rec in self.order_line:
                stock_product = ({
                    'product_id': rec.product_id.id,
                    'name': rec.product_id.name,
                    'product_uom_qty': rec.product_uom_qty,
                    'location_id': self.partner_id.property_stock_customer.id,
                    'location_dest_id': location.id
                })
                stock_list.append((0, 0, stock_product))

                components = ({
                    'product_id': rec.product_id.id,
                    'name': rec.name,
                    'quantity': rec.product_uom_qty,
                    'price_unit': rec.price_unit,
                    'tax_ids': rec.tax_id.ids
                })
                lines.append((0, 0, components))
            journal=self.env['account.journal'].search([('type','=','sale'),('user_id','=',self.user_id.id)],limit=1)
            credit_note = self.env['account.move'].create({
                'move_type': 'out_refund',
                'state': 'draft',
                'partner_id': self.partner_id.id,
                'payment_reference': self.name,
                'invoice_line_ids': lines,
                'journal_id':journal.id,
            })

            returns = self.env['stock.picking.type'].search([('return_bool', '=', True)], limit=1)
            stock_picking = self.env['stock.picking'].create({
                'state': 'draft',
                'partner_id': self.partner_id.id,
                'origin': self.name,
                'picking_type_id': returns.id,
                'move_ids_without_package': stock_list,
            })
            print(stock_picking.location_dest_id.id,"111111111111111")
            stock_picking_confirm = stock_picking.action_confirm()
            stock_picking.action_set_quantities_to_reservation()
            stock_picking.button_validate()

            self.write({'state': 'return'})
        else:
            raise AccessError("Access Denied")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                if vals.get('sale_return', False):
                    vals['name'] = self.env['ir.sequence'].next_by_code('sale.return') or _('New')
        return super().create(vals_list)

    def view_sale_return(self):
        return {
            'name': 'Return order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.sale_return_ids.id)],
            'res_id': self.id,
        }


class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    sale_return = fields.Boolean(related='order_id.sale_return', string="Sale Return")
    return_sale = fields.Boolean(string="Sale Return", default=False)
    sale_return_wizard_ids = fields.One2many('sale.return.wizard.line', 'sale_return_wizard_id', "Sale Return Wizard")
    sale_order_line = fields.Many2one('sale.order.line', 'Sale Order Line')
    sale_orders_id = fields.Many2one('sale.order', 'Sale Order')
    return_line_id = fields.Char("Return sale line id")

    def open_return_wizard(self):
        if self.sale_return:
            product_list = []
            sale_order = self.env['sale.order'].search([('partner_id', '=', self.order_id.partner_id.id), ('state', '=', 'sale'), ('sale_return', '=', False)])
            for sale in sale_order:
                if sale.invoice_ids:
                    order_lines = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', self.product_id.id), ('product_uom_qty', '>=', self.product_uom_qty), ('sale_return', '=', False), ('return_sale', '=', False)])
                    for line in order_lines:
                        if not self.env['sale.return.wizard.line'].search([('sale_order', '=', sale.id), ('sale_order_line', '=', line.id), ('sale_return_wizard_id', '=', self.id)]):
                            component = {
                                'invoice_number': sale.invoice_ids[0].name,
                                'sale_order': sale.id,
                                'sale_order_line': line.id,
                                'sale_return_wizard_id': self.id,
                                'product_id': line.product_id.id,
                                'name': line.product_id.name,
                                'qty': line.product_uom_qty,
                                'tax_id': line.tax_id.ids,
                                'price_unit': line.price_unit,
                                'sub_total': line.price_subtotal,
                            }
                            wizard_line = self.env['sale.return.wizard.line'].sudo().create(component)
            return {
                'name': 'Products',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.return.wizard.line',
                'view_mode': 'tree',
                'view_type': 'tree',
                'target': 'new',
                'domain': [('sale_return_wizard_id', '=', self.id), ('qty', '>=', self.product_uom_qty)],
            }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id