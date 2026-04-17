# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class ReportAgedPartnerBalance(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_agedpartnerbalance'
    _description = 'Aged Partner Balance Report'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length,
                                length_1, length_2, length_3, length_4, length_5):

        # Initialize periods dictionary
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d") - relativedelta(days=1)

        lengths = []
        if length_1:
            lengths.append(length_1)
        if length_2:
            lengths.append(length_2)
        if length_3:
            lengths.append(length_3)
        if length_4:
            lengths.append(length_4)
        if length_5:
            lengths.append(length_5)
        # List of period lengths
        current_sum = 0
        lengths.sort(reverse=True)
        for i in range(len(lengths))[::-1]:
            current_length = lengths[i]

            # Compute the stop date based on the current period length
            stop = start - relativedelta(days=(current_length - current_sum))

            # Determine the name for the period
            if i != 0:
                periods[str(i)] = {
                    'name': f'{current_sum + 1}-{current_length}',  # Use current range, not cumulative
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': ((stop + relativedelta(days=1)).strftime('%Y-%m-%d'))
                }
            else:
                # For the last period, use the '+' notation
                periods[str(i)] = {
                    'name': f'{current_sum + 1}-{current_length}',
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': ((stop + relativedelta(days=1)).strftime('%Y-%m-%d'))
                }

            # Move current sum to the next period and update the start date for the next iteration
            current_sum = current_length

            start = stop

        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        # build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute(
            'SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where max_date > %s',
            (date_from,))
        reconciled_after_date = []

        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        branch = tuple(self.env.user.branch_ids.ids)
        if len(branch) == 1:
            add = f" AND l.branch_id = {branch[0]}"
        else:
            add = f" AND l.branch_id IN {branch}"
        # print(branch,"&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        # add = ''' and l.branch_id IN ''' + str(branch)
        # print(add,">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)''' + add + '''
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.account_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if
                       partner['partner_id']]
        lines = dict(
            (partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}

        # Fetch invoices for each partner
        invoices = {}
        for partner in partners:
            partner_id = partner['partner_id']
            if not partner_id:
                continue
            cr.execute('''
                       SELECT am.name
                       FROM account_move am
                       WHERE am.partner_id = %s
                         AND am.state = 'posted'
                         AND am.amount_residual != 0
                         AND am.date <= %s
                         AND am.company_id IN %s
                   ''', (partner_id, date_from, tuple(company_ids)))
            invoice_records = cr.dictfetchall()
            invoices[partner_id] = invoice_records

        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) ''' + add + ''' AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.account_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s'''
        cr.execute(query, (
            tuple(move_state), tuple(account_type), date_from,
            tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(line.company_id.currency_id,
                                               user_currency, line.balance)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if isinstance(date_from, str):
                    date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                if partial_line.max_date <= date_from:
                    line_amount += ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency,
                        partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if isinstance(date_from, str):
                    date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                if partial_line.max_date <= date_from:
                    line_amount -= ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency,
                        partial_line.amount)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(len(lengths)):
            args_list = (
                tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (
                    periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) ''' + add + ''' AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.account_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id,
                                                   user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    # Change date_from to datetime
                    if isinstance(date_from, str):
                        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                    if partial_line.max_date <= date_from:
                        line_amount += ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency,
                            partial_line.amount)
                for partial_line in line.matched_credit_ids:
                    if isinstance(date_from, str):
                        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                    if partial_line.max_date <= date_from:
                        line_amount -= ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency,
                            partial_line.amount)

                if not self.env.company.currency_id.is_zero(
                        line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })
            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner[
                'partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'],
                                 precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(len(lengths)):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)],
                                     precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum(
                [values['direction']] + [values[str(i)] for i in range(len(lengths))])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(
                    partner['partner_id'])
                values['name'] = browsed_partner.name and len(
                    browsed_partner.name) >= 45 and browsed_partner.name[
                                                    0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
                values['invoices'] = invoices.get(partner['partner_id'], [])

            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['invoices'] = []

            if at_least_one_amount or (
                    self._context.get('include_nullified_amount') and lines[
                partner['partner_id']]):
                res.append(values)



        return res, total, lines

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get(
                'active_model') or not self.env.context.get('active_id'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['asset_receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['liability_payable']
        else:
            account_type = ['liability_payable', 'asset_receivable']

        movelines, total, dummy = self._get_partner_move_lines(account_type,
                                                               date_from,
                                                               target_move,
                                                               data['form']['period_length'],
                                                               data['form'].get('length_1', 0),
                                                               # Returns 0 if 'length_1' doesn't exist
                                                               data['form'].get('length_2', 0),
                                                               # Returns 0 if 'length_2' doesn't exist
                                                               data['form'].get('length_3', 0),
                                                               # Returns 0 if 'length_3' doesn't exist
                                                               data['form'].get('length_4', 0),
                                                               # Returns 0 if 'length_4' doesn't exist
                                                               data['form'].get('length_5', 0),
                                                               # Returns 0 if 'length_5' doesn't exist
                                                               )

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
        }


