from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning, ValidationError, UserError
from datetime import datetime, timedelta
import datetime

class ExpenseReportWizard(models.TransientModel):
    _name = "expense.report.wizard"

    type = fields.Selection([('electric', 'Electric'), ('expense', 'Expense'),('rent', 'Rent'), ('store', 'Store'), ('customer_incentive', 'Customer Incentive'), ('refreshment', 'Refreshment'), ('transportation_indirect', 'Transportation Indirect'), ('general', 'General')], string="Type")
    branch_id = fields.Many2one('res.branch', string="Branch")
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Allowed Branches",
                                          compute='_compute_allowed_branch_ids')

    @api.depends('branch_id')
    def _compute_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.branch_ids.ids

    def action_expense_report_fn(self):
        data = []
        list = []
        final_list = []
        model = self.type
        print("modellllllllll",model)
        # selected_model = self.get(model)
        # print(selected_model)

        if model == 'electric':

            for rec in self.env['electric.expense'].search([]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['electric.expense'].search([('id', '=', int(datas))])

                document = {
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'narration': documents.narration,
                    'bill_month': documents.bill_month,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)

                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)
            # print(data)
            #     report_data = {
            #         'model': model,
            #         'data': rec,
            #     }
            return self.env.ref('zcl003_expense.electric_expense_report_xlsx').report_action(self, data=data)
        elif model == 'store':
            for rec in self.env['store.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['store.expense'].search([('id', '=', int(datas))])

                document = {
                    'journal_id': documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id': documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids': documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'narration': documents.narration,
                    'type_expense': documents.type_expense,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)

                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::", data)
            # print(data)
            #     report_data = {
            #         'model': model,
            #         'data': rec,
            #     }
            return self.env.ref('zcl003_expense.store_report_xlsx').report_action(self, data=data)

        elif model == 'expense':
            for rec in self.env['expense.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['expense.expense'].search([('id', '=', int(datas))])

                document = {
                    'journal_id': documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id': documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'empo_name_ids': documents.empo_name_ids.name,
                    'expense_acc_ids': documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'narration': documents.narration,
                    'number_plate': documents.number_plate,
                    'kilometer': documents.kilometer,
                    'type_expense': documents.type_expense,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)

                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::", data)
            # print(data)
            #     report_data = {
            #         'model': model,
            #         'data': rec,
            #     }
            return self.env.ref('zcl003_expense.expense_report_xlsx').report_action(self, data=data)
        elif model == 'rent':

            for rec in self.env['rent.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['rent.expense'].search([('id', '=', int(datas))])

                document = {
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'narration': documents.narration,
                    'bill_month': documents.bill_month,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)
                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)

            return self.env.ref('zcl003_expense.rent_report_xlsx').report_action(self, data=data)

        elif model == 'customer_incentive':

            for rec in self.env['customer.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['customer.expense'].search([('id', '=', int(datas))])

                document = {
                    'customer_name' : documents.customer_name.name,
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'narration': documents.narration,
                    'incentive_month': documents.incentive_month,
                    'remarks': documents.remarks,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)
                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)

            return self.env.ref('zcl003_expense.customer_incentive_expense_report_xlsx').report_action(self, data=data)
        elif model == 'refreshment':

            for rec in self.env['refreshment.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['refreshment.expense'].search([('id', '=', int(datas))])

                document = {
                    'empo_name_ids' : documents.empo_name_ids.name,
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'bill_ref': documents.bill_ref,
                    'month': documents.month,
                    'remarks': documents.remarks,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)
                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)

            return self.env.ref('zcl003_expense.refreshment_expense_report_xlsx').report_action(self, data=data)
        elif model == 'transportation_indirect':

            for rec in self.env['transportation.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['transportation.expense'].search([('id', '=', int(datas))])

                document = {
                    'empo_name_ids' : documents.empo_name_ids.name,
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'bill_ref': documents.bill_ref,
                    'remarks': documents.remarks,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)
                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)

            return self.env.ref('zcl003_expense.transportation_indirect_report_xlsx').report_action(self, data=data)
        elif model == 'general':

            for rec in self.env['general.expense.expense'].search([]):
                if self.branch_id:
                    print('branchhh')
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
            for datas in list:
                documents = self.env['general.expense.expense'].search([('id', '=', int(datas))])

                document = {
                    'empo_name_ids' : documents.empo_name_ids.name,
                    'journal_id' : documents.journal_id.name,
                    'date_due': documents.date_due,
                    'branch_id':documents.branch_id.name,
                    'payment_method_line_id': documents.payment_method_line_id.name,
                    'expense_acc_ids' : documents.expense_acc_ids.name,
                    'amount': documents.amount,
                    'bill_ref': documents.bill_ref,
                    'remarks': documents.remarks,
                    'ref': documents.ref,
                    'payment_count': documents.payment_count,
                    'state': documents.state,
                    'expense_lines': [],

                }
                for val in documents.journal_expence_line_ids:
                    docs = {
                        'debit_account' :  val.debit_account.name,
                        'debit' : val.debit,
                    }
                    document['expense_lines'].append(docs)
                final_list.append(document)
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::",data)

            return self.env.ref('zcl003_expense.general_expense_report_xlsx').report_action(self, data=data)
