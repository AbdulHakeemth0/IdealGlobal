from odoo import models
from datetime import datetime, date


class ElectricExpenseReport(models.AbstractModel):
    _name = 'report.zcl003_expense.expense_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        print("*****************************88")
        sheet = workbook.add_worksheet("Expense Report")
        bold = workbook.add_format({'bold': True})
        format_1 = workbook.add_format({'align': 'center', 'bold': True})
        format_2 = workbook.add_format({'align': 'left', 'bg_color': 'gray'})
        format_3 = workbook.add_format({'align': 'left', 'text_wrap': 15, 'bg_color': 'gray'})


        sheet.merge_range(0, 0, 0+1, 0 + 3, 'Expense Report', format_1)
        sheet.write(2, 0, 'Journal ID', format_3)
        sheet.write(2, 1, 'Date', format_3)
        sheet.write(2, 2, 'Payment Method', format_3)
        sheet.write(2, 3, 'Expense Account', format_3)
        sheet.write(2, 4, 'Employee Name', format_3)
        sheet.write(2, 5, 'Amount', format_3)
        sheet.write(2, 6, 'Branch', format_3)
        sheet.write(2, 7, 'Narration', format_3)
        sheet.write(2, 8, 'Number Plate', format_3)
        sheet.write(2, 9, 'Kilometer', format_3)
        sheet.write(2, 10, 'Type Expense', format_3)
        sheet.write(2, 11, 'Ref', format_3)
        sheet.write(2, 12, 'Payment Count', format_3)
        sheet.write(2, 13, 'State', format_3)
        sheet.write(2, 14, 'Debit Account', format_3)
        sheet.write(2, 15, 'Debit', format_3)

        #
        #
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 25)
        sheet.set_column('O:O', 25)


        row = 3
        col = 0
        row_update = 0
        rec_updates = 0

        for rec in data['dict']:
            row_update += 1
            rec_updates += 1

            sheet.write(row, 0, rec['journal_id'])
            sheet.write(row, 1, rec['date_due'])
            sheet.write(row, 2, rec['payment_method_line_id'])
            sheet.write(row, 3, rec['expense_acc_ids'])
            sheet.write(row, 4, rec['empo_name_ids'])
            sheet.write(row, 5, rec['amount'])
            sheet.write(row, 6, rec['branch_id'])
            sheet.write(row, 7, rec['narration'])
            sheet.write(row, 8, rec['number_plate'])
            sheet.write(row, 9, rec['kilometer'])
            sheet.write(row, 10, rec['type_expense'])
            sheet.write(row, 11, rec['ref'])
            sheet.write(row, 12, rec['payment_count'])
            sheet.write(row, 13, rec['state'])
            for line_data in rec['expense_lines']:
                sheet.write(row, 14, line_data['debit_account'])
                sheet.write(row, 15, line_data['debit'])
                row += 1
            row += 1
            row_update = row + 1

        row_update += 1
        col = 0



        last_head = str('Total records in this page :')
        last_value = str(rec_updates)
        last_comb = last_head + last_value
        sheet.merge_range(row_update + 3, col, row_update + 3, 0 + 3, last_comb, format_2)

