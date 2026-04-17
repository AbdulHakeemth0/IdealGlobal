from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    its_expense = fields.Boolean(string='Expense', default=False)
    expense_id = fields.Many2one("expense.expense")
    expenses_id = fields.Many2one("electric.expense")
    expen_id = fields.Many2one("rent.expense")
    expe_id = fields.Many2one("store.expense")
    exp_id = fields.Many2one("customer.expense")
    expense_ids = fields.Many2one("refreshment.expense")
    expe_ids = fields.Many2one("transportation.expense")
    ex_id = fields.Many2one("general.expense.expense")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        print('------------------------------------------------------------------------->>>')

        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

        if (not self.expense_id and not self.expenses_id and not self.expen_id and not self.expe_id and not self.exp_id
                and not self.expense_ids and not self.expe_ids and not self.ex_id):
            print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr...............")
            line_vals_list = [
            # Liquidity line.
                {
                    'name': liquidity_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': counterpart_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
        else:
            print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
            line_vals_list = []
            if self.expense_id:
                print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv", self.expense_id)
                dic = {
                    'name': liquidity_line_name,
                    'date_maturity': self.date,
                    # 'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': 0.0,
                    'credit': self.expense_id.amount,
                    'account_id': self.expense_id.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expense_id.journal_expence_line_ids:
                    dic_2 = {
                        'name': counterpart_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': rec.debit,
                        'credit': 0.0,
                        'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
            if self.expenses_id:
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.expenses_id.amount,
                        'account_id': self.expenses_id.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expenses_id.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
                        ##############
            if self.expen_id:
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.expen_id.amount,
                        'account_id': self.expen_id.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expen_id.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)

            if self.expe_id:
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.expe_id.amount,
                        'account_id': self.expe_id.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expe_id.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
            if self.exp_id:
                 dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.exp_id.amount,
                        'account_id': self.exp_id.expense_acc_ids.id,
                 }
                 line_vals_list.append(dic)
                 for rec in self.exp_id.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
            if self.expense_ids:
                print("dfghjk")
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.expense_ids.amount,
                        'account_id': self.expense_ids.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expense_ids.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
            if self.expe_ids:
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.expe_ids.amount,
                        'account_id': self.expe_ids.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.expe_ids.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
            if self.ex_id:
                dic = {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        # 'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': self.ex_id.amount,
                        'account_id': self.ex_id.expense_acc_ids.id,
                }
                line_vals_list.append(dic)
                for rec in self.ex_id.journal_expence_line_ids:
                    dic_2 = {
                            'name': counterpart_line_name,
                            'date_maturity': self.date,
                            # 'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': rec.debit,
                            'credit': 0.0,
                            'account_id': rec.debit_account.id,
                    }
                    line_vals_list.append(dic_2)
        return line_vals_list + write_off_line_vals_list

