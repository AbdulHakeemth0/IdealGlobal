from odoo import models,fields,api,_
import base64
from datetime import datetime, date


class JvbranchExpenseReport(models.AbstractModel):
    _name = 'report.zcl003_expense.jv_branch_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, moves):
        print("*****************************88")
        sheet = workbook.add_worksheet("Jv Branch Expense Report")
        bold = workbook.add_format({'bold': True})
        center_style = workbook.add_format({'valign': 'center', 'bold': True})
        wrap_text = workbook.add_format({'text_wrap': True})
        money = workbook.add_format({'num_format': '$#,##0.00'})
        format_1 = workbook.add_format({'align': 'center', 'bold': True})
        format_2 = workbook.add_format({'align': 'left', 'bg_color': 'gray'})
        format_3 = workbook.add_format({'align': 'left', 'text_wrap': 15, 'bg_color': 'gray'})


        sheet.merge_range(0, 0, 0+1, 0 + 3, 'Jv Branch Expense Report', format_1)
        sheet.write(2, 0, 'Journal ID', format_3)
        sheet.write(2, 1, 'Due Date', format_3)
        sheet.write(2, 2, 'Current Balance of Customer', format_3)
        sheet.write(2, 3, 'Balance Limit', format_3)
        sheet.write(2, 4, 'Sales Team', format_3)
        sheet.write(2, 5, 'Branch', format_3)
        sheet.write(2, 6, 'Bill No', format_3)
        sheet.write(2, 7, 'Narration', format_3)
        sheet.write(2, 8, 'Accounting Date', format_3)
        sheet.write(2, 9, 'Reference', format_3)
        sheet.write(2, 10, 'Sales Account', format_3)
        sheet.write(2, 11, 'Delivery Terms', format_3)
        sheet.write(2, 12, 'Delivery Note No', format_3)
        sheet.write(2, 13, 'State', format_3)
        sheet.write(2, 14, 'Account', format_3)
        sheet.write(2, 15, 'Partner', format_3)
        sheet.write(2, 16, 'Debit', format_3)
        sheet.write(2, 17, 'Credit', format_3)

        #
        #
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 25)


        row = 3
        col = 0
        row_update = 0
        rec_updates = 0
        for move in moves:

            for rec in data['dict']:
                row_update += 1
                rec_updates += 1
                print(rec_updates,"AAAAAAAAAAaaaaa")


                sheet.write(row, 0, rec['journal_id'])
                sheet.write(row, 1, rec['due_days'])
                sheet.write(row, 2, rec['current_balance_customer'])
                sheet.write(row, 3, rec['balance_limit'])
                sheet.write(row, 4, rec['team_id'])
                sheet.write(row, 5, rec['branch_id'])
                sheet.write(row, 6, rec['bill_no'])
                sheet.write(row, 7, rec['narration'])
                sheet.write(row, 8, rec['date'])
                sheet.write(row, 9, rec['ref'])
                sheet.write(row, 10, rec['sales_account'])
                sheet.write(row, 11, rec['delivery_terms'])
                sheet.write(row, 12, rec['delivery_note_no'])
                sheet.write(row, 13, rec['state'])
                for line_data in rec['move_lines']:
                    sheet.write(row, 14, line_data['account_id'])
                    sheet.write(row, 15, line_data['partner_id'])
                    sheet.write(row, 16, line_data['debit'])
                    sheet.write(row, 17, line_data['credit'])
                    row +=1

            row +=1
            row_update = row+1

        row_update += 1
        col = 0

        last_head = str('Total records in this page :')
        last_value = str(rec_updates)
        last_comb = last_head + last_value
        sheet.merge_range(row_update + 3, col, row_update + 3, 0 + 3, last_comb, format_2)

