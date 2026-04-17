from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, AccessError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sales_account = fields.Char(string="Sales Account")
    delivery_terms = fields.Char(string="Delivery Terms")
    narration = fields.Text(string="Narration")
    delivery_note_no = fields.Char(string="Delivery Note No")
    current_balance_customer = fields.Integer(
        string="Current Balance Of Customer")
    # zone = fields.Char(string="Zone")
    balance_limit = fields.Char(string="Balance Limit")
    due_days = fields.Char(string="Due Days")
    sales_type = fields.Selection([('sale', 'Sale'), ('foc', 'FOC')],
                                  'Sales Type', default='sale')

    universal_discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Amount')],
        string='Universal Discount Type',
        default='percent')
    universal_discount_rate = fields.Float(string='Universal Discount',
                                           store=True,
                                           track_visibility='always')
    universal_discount_amount = fields.Monetary(string='Universal Discount',
                                                store=True,
                                                track_visibility='always')
    universal_total_display_discount_amount = fields.Monetary(
        string='Universal Discount', store=True)
    universal_discount_enable = fields.Boolean(string='Universal Discount')
    user_id = fields.Many2one('res.users', string='User')
    special_sale_order = fields.Boolean(string="Special Sale Order")
    amount_tax = fields.Monetary(string="Taxes", store=True, compute='_compute_amounts',digits=(16, 3))



    @api.onchange('partner_id')
    def _check_user_access(self):
        if self.partner_id:
            if self.sale_return:
                if not self.env.user.create_sale_return:
                    raise AccessError("Access Denied")
            else:
                if not self.env.user.create_sale_order:
                    raise AccessError("Access Denied")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total',
                 'amount_untaxed', 'currency_id',
                 'universal_discount_type', 'universal_discount_rate',
                 'universal_discount_amount',
                 'universal_discount_enable')
    def _compute_tax_totals(self):
        for order in self:
            order_lines = order.order_line.filtered(
                lambda x: not x.display_type)
            rec = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )
            # if self.partner_id:
            #
            #    if self.universal_discount_type == 'percent':
            #         self.universal_discount_rate = self.partner_id.sale_universal_discount_rate
            #
            #    if self.universal_discount_type == 'amount':
            #         self.universal_discount_amount = self.partner_id.sale_universal_discount_amount

            if order.universal_discount_enable:
                rec[
                    'amount_untaxed'] = order._compute_universal_total_display_discount_amount()
                order.tax_totals = rec
            else:
                order.universal_total_display_discount_amount = 0
                order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                    [x._convert_to_tax_base_line_dict() for x in order_lines],
                    order.currency_id or order.company_id.currency_id, )

    @api.depends('order_line.price_subtotal', 'order_line.price_tax',
                 'order_line.price_total')
    def _compute_amounts(self):

        for order in self:
            order_lines = order.order_line.filtered(
                lambda x: not x.display_type)
            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                if self.universal_discount_enable:
                    amount_untaxed = self._compute_universal_total_display_discount_amount()
                else:
                    amount_untaxed = totals.get(order.currency_id, {}).get(
                        'amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax',
                                                                   0.0)
            else:
                if self.universal_discount_enable:
                    amount_untaxed = self._compute_universal_total_display_discount_amount()
                else:
                    amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))
            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.tax_totals['amount_total']

    def _compute_universal_total_display_discount_amount(self):
        for rec in self:
            total_amount = float(sum(rec.order_line.mapped('price_subtotal')))
            if rec.universal_discount_type == "amount":
                rec.universal_total_display_discount_amount = rec.universal_discount_amount if 0 < rec.universal_discount_amount <= total_amount else 0
            elif rec.universal_discount_type == "percent":
                rec.universal_total_display_discount_amount = (
                                                                          total_amount * rec.universal_discount_rate) / 100 if 0 < rec.universal_discount_rate <= 100 else 0
            else:
                rec.universal_total_display_discount_amount = 0
            return total_amount - rec.universal_total_display_discount_amount

    def action_confirm(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.env.user.confirm_sale_order:
                    for order in self:
                        partner = order.partner_id

                        customer_credit_limit = partner.customer_credit_limit
                        customer_days_notification = partner.customer_days_notification
                        if customer_credit_limit and order.amount_total > customer_credit_limit:
                            raise exceptions.UserError(
                                "The outstanding amount exceeds the customer's credit limit.")
                        if customer_days_notification:
                            # Calculate the date from the order confirmation date and the customer days
                            date_due = fields.Date.today() + timedelta(
                                days=customer_days_notification)
                            # Check if there are any pending invoices with respect to the given customer days
                            pending_invoices = self.env['account.move'].search([
                                ('partner_id', '=', partner.id),
                                ('state', 'in', ['posted', 'draft']),
                                ('invoice_date_due', '<', date_due),
                            ])
                            pending_amount = sum(
                                invoice.amount_total for invoice in pending_invoices)
                            if pending_amount >= customer_credit_limit:
                                raise exceptions.UserError(
                                    "There are pending invoices for the customer. Pending Amount: %s" % pending_amount)
                    return super(SaleOrder, self).action_confirm()
                else:
                    raise AccessError("Access Denied")
            else:
                return super(SaleOrder, self).action_confirm()
        else:
            return super(SaleOrder, self).action_confirm()

    def action_run_workflow(self):
        self.action_confirm()
        self._create_invoices(final=True)

    def _prepare_invoice(self):
        ks_res = super()._prepare_invoice()
        for rec in self:
            ks_res.update({
                'universal_discount_enable': True,
                'universal_discount_type': 'percent',
                'universal_discount_rate': rec.universal_discount_rate,
                'invoice_date': rec.date_order
                # fields.Date.context_today(self)
            })
        return ks_res

    @api.onchange('order_line')
    def _onchange_orderline(self):
        if self.special_sale_order:
            for rec in self.order_line:
                rec.price_unit = 0

    # commented the main function

    # def _prepare_invoice(self):
    #     ks_res = super()._prepare_invoice()
    #     for rec in self:
    #         ks_res['universal_discount_enable'] = True
    #         ks_res['universal_discount_type'] = 'percent'
    #         ks_res['universal_discount_rate'] = rec.universal_discount_rate
    #         # dates= datetime.date.today()
    #         # ks_res['invoice_date'] = dates
    #         ks_res['invoice_date'] = datetime.date.today().strftime('%Y-%m-%d')
    #
    #     return  ks_res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float('Qty Available',
                                 related="product_id.qty_available")
    image_url = fields.Char(string="Image")
    stock_in_hand = fields.Char('Stock In Hand')
    discount_on_foc = fields.Char('Discount On FOC')
    django_orderitems_id = fields.Integer()
    # product_code = fields.Char(string="Product Code",related='product_template_id.product_code')
    return_qty = fields.Float()

    def last_po_view(self):
        if self.product_id:
            po_line_id = self.env['purchase.order.line'].search(
                [('product_id', '=', self.product_id.id)]).mapped('order_id')
            if po_line_id:
                action = {
                    'name': _('Last Purchase Order'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.order',
                    'view_mode': 'tree, form',
                    'domain': [('id', '=', po_line_id.ids[0])],
                    'res_id': po_line_id.ids[0]

                }
                return action
            else:
                raise ValidationError(
                    _('There is No Purchase Order for this product'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id
