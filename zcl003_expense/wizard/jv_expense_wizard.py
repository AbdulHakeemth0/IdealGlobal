from odoo import models, fields, exceptions, api, _


class ExpenseReportWizard(models.TransientModel):
    _name = "jvexpense.report.wizard"

    type = fields.Selection([('jv_container', 'Jv Container'), ('jv_purchase', 'Jv Purchase'),('jv_salary', 'Jv Salary'), ('jv_branch', 'Jv Branch'), ('jv_transfer', 'Jv Transfer'), ('jv_general', 'Jv General'), ('jv_closeentry', 'Jv Closing Entries')], string="Type")
    branch_id = fields.Many2one('res.branch', string="Branch")

    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Allowed Branches",
                                          compute='_compute_allowed_branch_ids')

    @api.depends('branch_id')
    def _compute_allowed_branch_ids(self):
        for rec in self:
            rec.allowed_branch_ids = self.env.user.branch_ids.ids

    def action_expense_report_fn(self):
        list = []
        final_list = []
        final = []
        value = []
        model = self.type
        print("modellllllllll", model)
        # selected_model = self.get(model)
        # print(selected_model)
        line = self.env['account.move.line'].search([])
        print(line)
        if model == 'jv_container':
            for rec in self.env['account.move'].search([('container_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)

            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])

                document = {
                    'container_no': documents.container_no,
                    'journal_id': documents.journal_id.name,
                    'internal_code': documents.internal_code,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines': [],

                }
                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}

            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::", data)

            return self.env.ref('zcl003_expense.jvcontainer_report_xlsx').report_action(self, data=data)
        if model == 'jv_purchase':
            for rec in self.env['account.move'].search([('purchase_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}
            print(":::::::::::::::::::::::::::", data)

            return self.env.ref('zcl003_expense.jv_purchase_report_xlsx').report_action(self, data=data)
        if model == 'jv_salary':
            for rec in self.env['account.move'].search([('salary_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}
            # print(":::::::::::::::::::::::::::", data)

            return self.env.ref('zcl003_expense.jv_salary_report_xlsx').report_action(self, data=data)
        if model == 'jv_branch':
            for rec in self.env['account.move'].search([('branch_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)

            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}

            return self.env.ref('zcl003_expense.jv_branch_report_xlsx').report_action(self, data=data)
        if model == 'jv_transfer':
            for rec in self.env['account.move'].search([('transfer_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}
            # print(":::::::::::::::::::::::::::", data)

            return self.env.ref('zcl003_expense.jv_transfer_report_xlsx').report_action(self, data=data)
        if model == 'jv_general':
            for rec in self.env['account.move'].search([('general_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}
            # print(":::::::::::::::::::::::::::", data)

            return self.env.ref('zcl003_expense.jv_general_report_xlsx').report_action(self, data=data)
        if model == 'jv_closeentry':
            for rec in self.env['account.move'].search([('closingentries_exp', '=', True)]):
                if self.branch_id:
                    if rec.branch_id == self.branch_id:
                        print('branchhh')
                    else:
                        continue
                list.append(rec.id)
                print(list)
            for datas in list:
                documents = self.env['account.move'].search([('id', '=', int(datas))])
                print(documents)

                document = {
                    'journal_id': documents.journal_id.name,
                    'due_days': documents.due_days,
                    'branch_id': documents.branch_id.name,
                    'current_balance_customer': documents.current_balance_customer,
                    'balance_limit': documents.balance_limit,
                    'team_id': documents.team_id.name,
                    'bill_no': documents.bill_no,
                    'date': documents.date,
                    'ref': documents.ref,
                    'sales_account': documents.sales_account,
                    'narration': documents.narration,
                    'delivery_terms': documents.delivery_terms,
                    'delivery_note_no': documents.delivery_note_no,
                    'state': documents.state,
                    'move_lines' : [],


                }
                print(document,"documentssssssssssssssssssssss")

                for val in documents.line_ids:
                    docs = {
                        'account_id' :  val.account_id.name,
                        'partner_id' : val.partner_id.name,
                        'debit' : val.debit,
                        'credit' : val.credit,
                    }
                    document['move_lines'].append(docs)

                final_list.append(document)

                data = {'dict': final_list}
            data = {'dict': final_list}


            return self.env.ref('zcl003_expense.jv_closeentry_report_xlsx').report_action(self, data=data)
