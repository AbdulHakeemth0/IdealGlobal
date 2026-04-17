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

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _,api
from odoo.exceptions import UserError,ValidationError


class AccountAgedTrialBalance(models.TransientModel):
    _name = 'account.aged.trial.balance'
    _inherit = 'account.common.partner.report'
    _description = 'Account Aged Trial balance Report'

    name = fields.Char(string="Account Aged Trial balance Report", default="Account Aged Trial balance Report", required=True, translate=True)

    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True)
    period_length = fields.Integer(string='Period Length (days)',
                                   required=True, default=30)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))

    # partner_id = fields.Many2one('res.partner',string="Partner")

    length_1 = fields.Integer(string='Period Length1(days)', default=10, required=True)
    length_2 = fields.Integer(string='Period Length2(days)', default=None)
    length_3 = fields.Integer(string='Period Length3(days)', default=None)
    length_4 = fields.Integer(string='Period Length4(days)', default=None)
    length_5 = fields.Integer(string='Period Length5(days)', default=None)

    # def _print_report(self, data):
    #     res = {}
    #     data = self.pre_print_report(data)
    #     data['form'].update(self.read(['period_length'])[0])
    #     data['form'].update({'customer': self.partner_id.id})
    #     period_length = data['form']['period_length']
    #     if period_length <= 0:
    #         raise UserError(_('You must set a period length greater than 0.'))
    #     if not data['form']['date_from']:
    #         raise UserError(_('You must set a start date.'))
    #
    #     start = data['form']['date_from']
    #
    #     for i in range(5)[::-1]:
    #         stop = start - relativedelta(days=period_length - 1)
    #         res[str(i)] = {
    #             'name': (i != 0 and (
    #                         str((5 - (i + 1)) * period_length) + '-' + str(
    #                     (5 - i) * period_length)) or (
    #                                  '+' + str(4 * period_length))),
    #             'stop': start.strftime('%Y-%m-%d'),
    #             'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
    #         }
    #         start = stop - relativedelta(days=1)
    #     data['form'].update(res)
    #     return self.env.ref(
    #         'base_accounting_kit.action_report_aged_partner_balance').with_context(
    #         landscape=True).report_action(self, data=data)
    @api.onchange('length_1')
    def _onchange_of_length_1(self):
        if not self.length_1 > 0:
            raise ValidationError("Period Length 1 should be greater than 0")

    @api.onchange('length_2')
    def _onchange_of_length_2(self):
        if self.length_2 and not self.length_1:
            raise ValidationError("Please provide previous Period Length")
        if self.length_1 and self.length_2 and self.length_2 <= self.length_1:
            raise ValidationError("Period Length 2 should be greater than Period Length 1")

    @api.onchange('length_3')
    def _onchange_of_length_3(self):
        if self.length_3:
            if not self.length_1:
                raise ValidationError("Please provide previous Period Length")
            if not self.length_2:
                raise ValidationError("Please provide previous Period Length")
            if self.length_2 and self.length_3 <= self.length_2:
                raise ValidationError("Period Length 3 should be greater than Period Length 2")

    @api.onchange('length_4')
    def _onchange_of_length_4(self):
        if self.length_4:
            if not self.length_1:
                raise ValidationError("Please provide previous Period Length")
            if not self.length_2:
                raise ValidationError("Please provide previous Period Length")
            if not self.length_3:
                raise ValidationError("Please provide previous Period Length")
            if self.length_3 and self.length_4 <= self.length_3:
                raise ValidationError("Period Length 4 should be greater than Period Length 3")

    @api.onchange('length_5')
    def _onchange_of_length_5(self):
        if self.length_5:
            if not self.length_1:
                raise ValidationError("Please provide previous Period Length")
            if not self.length_2:
                raise ValidationError("Please provide previous Period Length")
            if not self.length_3:
                raise ValidationError("Please provide previous  Period Length")
            if not self.length_4:
                raise ValidationError("Please provide previous Period Length")
            if self.length_4 and self.length_5 <= self.length_4:
                raise ValidationError("Period Length 5 should be greater than Period Length 4")

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        # ADD NEW LENGTHS LISTS AND EFFECT THE NEW FILTER CONDITION ON REPORTS TOO
        lengths = []
        start = data['form']['date_from']
        if self.length_1:
            data['form'].update(self.read(['length_1'])[0])
            length_1 = data['form']['length_1']
            lengths.append(length_1)
        if self.length_2:
            data['form'].update(self.read(['length_2'])[0])
            length_2 = data['form']['length_2']
            lengths.append(length_2)
        if self.length_3:
            data['form'].update(self.read(['length_3'])[0])
            length_3 = data['form']['length_3']
            lengths.append(length_3)
        if self.length_4:
            data['form'].update(self.read(['length_4'])[0])
            length_4 = data['form']['length_4']
            lengths.append(length_4)
        if self.length_5:
            data['form'].update(self.read(['length_5'])[0])
            length_5 = data['form']['length_5']
            lengths.append(length_5)

        lengths.sort(reverse=True)
        # Initialize start as the current date
        current_sum = 0

        for i in range(len(lengths))[::-1]:
            current_length = lengths[i]

            # Compute the stop date based on the current period length
            stop = start - relativedelta(days=(current_length - current_sum) - 1)

            # Determine the name for the period
            if i != 0:
                res[str(i)] = {
                    'name': f'{current_sum}-{current_length}',  # Use current range, not cumulative
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': stop.strftime('%Y-%m-%d')
                }
            else:
                # For the last period, use the '+' notation
                res[str(i)] = {
                    'name': f'{current_sum}-{current_length}',
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': stop.strftime('%Y-%m-%d')
                }

            # Move current sum to the next period and update the start date for the next iteration
            current_sum = current_length

            start = stop - relativedelta(days=1)

        # ---------------- OLD CONDITIONS ---------------#

        # for i in range(5)[::-1]:
        #     stop = start - relativedelta(days=period_length - 1)
        #     res[str(i)] = {
        #         'name': (i != 0 and (
        #                 str((5 - (i + 1)) * period_length) + '-' + str(
        #             (5 - i) * period_length)) or (
        #                          '+' + str(4 * period_length))),
        #         'stop': start.strftime('%Y-%m-%d'),
        #         'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
        #     }
        #     start = stop - relativedelta(days=1)



        data['form'].update(res)
        return self.env.ref(
            'base_accounting_kit.action_report_aged_partner_balance').with_context(
            landscape=True).report_action(self, data=data)

