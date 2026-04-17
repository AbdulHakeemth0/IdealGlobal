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

from odoo import fields, models, api


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"


    name = fields.Char(string="Partner Ledger Report", default="Partner Ledger Report", required=True, translate=True)
    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on report if the "
                                          "currency differs from the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')

    # partners_ids = fields.Many2many('res.partner', string='Partner')
    partner_ids = fields.Many2many('res.partner', string="Partner")

    zone = fields.Many2one('crm.team', string='Zone')

    # partners_id = fields.Many2one('res.partner',string='Partner')

    @api.onchange('partner_ids')
    def _onchange_partners_ids(self):
        if self.partner_ids and not self.zone:
            self.partner_ids = False
            return {
                'warning': {
                    'title': "Zone Not Selected",
                    'message': "You cannot select partners without selecting a zone first.",
                }
            }

    @api.onchange('zone')
    def _onchange_zone(self):
        if self.zone:
            domain = [('team_id', '=', self.zone.id)]
            return {'domain': {'partner_ids': domain}}
        else:
            return {'domain': {'partner_ids': []}}


    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids})
        # data['form'].update({'partner': self.partners_ids.ids})
        return self.env.ref(
            'base_accounting_kit.action_report_partnerledger').report_action(
            self, data=data)
