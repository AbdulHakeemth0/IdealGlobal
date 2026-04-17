from odoo import models
from datetime import datetime, date


class CustomerIncentiveReport(models.AbstractModel):
    _name = 'report.zcl003_expense.customer_incentive_expense_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        print("*****************************88")
        sheet = workbook.add_worksheet("Container Expense Report")
        bold = workbook.add_format({'bold': True})
        format_1 = workbook.add_format({'align': 'center', 'bold': True})
        format_2 = workbook.add_format({'align': 'left', 'bg_color': 'gray'})
        format_3 = workbook.add_format({'align': 'left', 'text_wrap': 15, 'bg_color': 'gray'})


        sheet.merge_range(0, 0, 0+1, 0 + 3, 'Customer Incentive Expense Report', format_1)
        sheet.write(2, 0, 'Customer Name', format_3)
        sheet.write(2, 1, 'Journal ID', format_3)
        sheet.write(2, 2, 'Date', format_3)
        sheet.write(2, 3, 'Payment Method', format_3)
        sheet.write(2, 4, 'Expense Account', format_3)
        sheet.write(2, 5, 'Amount', format_3)
        sheet.write(2, 6, 'Branch', format_3)
        sheet.write(2, 7, 'Incentive Month', format_3)
        sheet.write(2, 8, 'Narration', format_3)
        sheet.write(2, 9, 'Remarks', format_3)
        sheet.write(2, 10, 'Ref', format_3)
        sheet.write(2, 11, 'Payment', format_3)
        sheet.write(2, 12, 'State', format_3)

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

        for rec in data['dict']:
            row_update += 1
            rec_updates += 1

            sheet.write(row, col, rec['customer_name'])
            col += 1
            sheet.write(row, col, rec['journal_id'])
            col += 1
            sheet.write(row, col, rec['date_due'])
            col += 1
            sheet.write(row, col, rec['payment_method_line_id'])
            col += 1
            sheet.write(row, col, rec['expense_acc_ids'])
            col += 1
            sheet.write(row, col, rec['amount'])
            col += 1
            sheet.write(row, col, rec['branch_id'])
            col += 1
            sheet.write(row, col, rec['incentive_month'])
            col += 1
            sheet.write(row, col, rec['narration'])
            col += 1
            sheet.write(row, col, rec['remarks'])
            col += 1
            sheet.write(row, col, rec['ref'])
            col += 1
            sheet.write(row, col, rec['payment_count'])
            col += 1
            sheet.write(row, col, rec['state'])
            col +=1

            row += 1
            col = 0

        last_head = str('Total records in this page :')
        last_value = str(rec_updates)
        last_comb = last_head + last_value
        sheet.merge_range(row_update + 3, col, row_update + 3, 0 + 3, last_comb, format_2)

