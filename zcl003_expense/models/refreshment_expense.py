from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class RefreshmentType(models.Model):
    _name = "refreshment.expense"
    _description = "Refreshment"
    _rec_name = "expense_acc_ids"
    _inherit = 'mail.thread'

    empo_name_ids = fields.Many2one("res.users", string="Employee Name")
    date_due = fields.Date(string='Date')
    journal_id = fields.Many2one('account.journal', string="Cash / Bank AC")
    expense_acc_ids = fields.Many2one('account.account', string='Expense Account')
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method')
    amount = fields.Float(string="Amount")
    bill_ref = fields.Char(string='Bill Reference')
    STATUS_SELECTION = [
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December'),
    ]
    month = fields.Selection(STATUS_SELECTION, string="Month")
    remarks = fields.Char(string="Remarks")
    ref = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method')
    payment_count = fields.Integer("Payment", compute='compute_payment_count')
    STATUS_SELECTION = [
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancelled'),
        ('reset draft', 'Reset Draft'),
    ]
    state = fields.Selection(STATUS_SELECTION, string="Status", default='draft')
    branch_id = fields.Many2one('res.branch', string="Branch")
    vat = fields.Char(string='VAT')
    journal_expence_line_ids = fields.One2many('expense.journal.line', 'expence_refreshment', "Journal")
    total = fields.Float("Total", compute='_compute_total_credit', store=True)




    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('refreshment.sequence') or _('New')
        res = super(RefreshmentType, self).create(vals)
        return res




    def action_create_payment(self):
        if self.env['account.payment'].search_count([('ref', '=', self.ref)]):
            UserError(_('SORRY.'))
        else:
            payment_vals = {
                  'date': self.date_due,
                  'payment_type': 'outbound',
                  'amount': self.amount,
                  'journal_id': self.journal_id.id,
                  'its_expense': True,
                  'payment_method_line_id': self.payment_method_line_id.id,
                  'ref': self.ref,
                  'expense_ids': self.id,
            }
            payment = self.env['account.payment'].sudo().create(payment_vals)
            print("rtyu")
            return True
    def action_create_payment(self):
        if self.env['account.payment'].search_count([('ref', '=', self.ref)]):
            UserError(_('SORRY.'))
        else:
            payment_vals = {
               'date': self.date_due,
               'payment_type': 'outbound',
               'amount': self.amount,
               'journal_id': self.journal_id.id,
               'its_expense': True,
               'payment_method_line_id': self.payment_method_line_id.id,
               'ref': self.ref,
               'expense_ids': self.id,
            }
            payment = self.env['account.payment'].sudo().create(payment_vals)
            return True
    def action_view_payment(self):
        return {
            'name': 'Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('ref', '=', self.ref)],
            'res_id': self.id,
        }

    def compute_payment_count(self):
        for record in self:
            record.payment_count = self.env['account.payment'].search_count(
                [('ref', '=', self.ref)])


    def draft_action_type(self):
        self.write({'state': 'draft'})
        return True

    def action_confirm_refreshment(self):
        if self.amount == self.total:
            self.write({'state': 'confirm'})
            return True
        else:
            raise UserError(_("Equalise The Debit And Credit"))

    def action_cancel_refreshment(self):
        self.write({'state': 'cancel'})
        return True

    @api.depends('journal_expence_line_ids.debit')
    def _compute_total_credit(self):
        for rec in self:
            total_amount = sum(line.debit for line in rec.journal_expence_line_ids)
            if total_amount <= rec.amount:
                rec.total = total_amount
            else:

                raise UserError(_("Equalise The Debit And Credit"))

class ExpenseJournalLine(models.Model):
    _name = "expense.journal.line"

    expence_fuel = fields.Many2one('expense.expense', "Expense Fuel")
    expence_electric = fields.Many2one('electric.expense', "Electric Expense")
    expence_rent = fields.Many2one('rent.expense', "Rent Expense")
    expence_store = fields.Many2one('store.expense', "Store Expense")
    expence_customer = fields.Many2one('customer.expense', "Customer Expense")
    expence_refreshment = fields.Many2one('refreshment.expense', "Refreshment Expense")

    debit_account = fields.Many2one('account.account', 'Debit Account', required=True)
    debit = fields.Float("Debit")