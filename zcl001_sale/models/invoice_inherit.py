from odoo import fields, models,api,_
from datetime import datetime
from odoo.exceptions import AccessError


class InvoiceInherit(models.Model):

    _inherit = "account.move"

    sales_account = fields.Char(string="Sales Account")
    delivery_terms = fields.Char(string="Delivery Terms")
    narration = fields.Text(string="Narration")
    delivery_note_no = fields.Char(string="Delivery Note No")
    current_balance_customer = fields.Integer(string="Current Balance Of Customer")
    zone = fields.Char(string="Zone")
    balance_limit = fields.Char(string="Balance Limit")
    # due_days = fields.Char(string="Due Date", compute='_compute_due_date',store=True)
    due_days = fields.Char(string="Due Date")
    sales_type = fields.Selection([('sale', 'Sale'), ('foc', 'FOC')], 'Sales Type', default='sale')
    user_id = fields.Many2one('res.users', string='User')
    # @api.depends('due_days')
    # def _compute_due_date(self):
    #     current_date = datetime.now().date()
    #     if self.invoice_date:
    #         self.due_days = (self.invoice_date - current_date).days
    #     else:
    #         self.due_days = None

    # inv_amount = fields.Float(string="Invoice Amount")


    @api.constrains('name')
    def _check_user_access(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.move_type == 'out_invoice':
                    if not self.env.user.create_invoice:
                        raise AccessError("Access Denied")
                elif self.move_type == 'in_invoice':
                    if not self.env.user.create_bill:
                        raise AccessError("Access Denied")

    def action_post(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.move_type == 'out_invoice':
                    if not self.env.user.confirm_invoice:
                        raise AccessError("Access Denied")
                    else:
                        return super(InvoiceInherit,self).action_post()
                elif self.move_type == 'in_invoice':
                    if not self.env.user.confirm_bill:
                        raise AccessError("Access Denied")
                    else:
                        return super(InvoiceInherit,self).action_post()
                else:
                    return super(InvoiceInherit, self).action_post()
            else:
                return super(InvoiceInherit, self).action_post()
        else:
            return super(InvoiceInherit, self).action_post()


class InvoiceInheritLine(models.Model):
    _inherit = "account.move.line"

    stock_in_hand = fields.Char('Stock In Hand')
    discount_on_foc = fields.Char('Discount On FOC')

    inv_amount = fields.Monetary(string="Invoice Amount")


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id.id
