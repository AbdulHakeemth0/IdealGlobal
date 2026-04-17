# -- coding: utf-8 --
###################################################################################

# Author       :  Sayooj t k
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# This program is free software:
# you can modify it under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
############################################################

from odoo import fields, models, api



class CollectionIncentive(models.Model):
    _name = "collection.incentive"
    _description = "Collection Incentive"
    _rec_name = 'zone'

    zone = fields.Many2one('crm.team', string="Zone", required=True)
    user_id = fields.Many2one('res.partner', string="User",  store=True)
    collection_incentive_amount = fields.Float(string="Collection Incentive Amount", store=True)
    invoice_ids = fields.One2many('collection.incentive.line', 'line_id')

    @api.onchange('zone')
    def _onchange_zone(self):
        if self.zone and self.zone.user_id:
            self.user_id = self.zone.user_id.partner_id.id
        if self.user_id:
            # sales team wise invoices
            rec = self.env['account.move'].sudo().search([('partner_id.id', '=', self.zone.user_id.partner_id.id), ('payment_state', '!=', 'not_paid')])
            if rec:
                self.invoice_ids = [(5, 0, 0)]
                for res in rec:
                    # looping in payments of invoices
                    for payment in res.invoice_payments_widget['content']:
                        amount_numeric = payment['amount']

                        # find the date difference
                        date_difference = (payment['date'] - res.invoice_date).days

                        # calculation of calculation incentive based on days
                        incentive = 0.0

                        # deduct amount
                        if date_difference > 215:
                            incentive -= (3 / 100) * amount_numeric
                        elif date_difference > 185 and date_difference <= 215:
                            incentive -= (1 / 100) * amount_numeric
                        elif date_difference >= 175 and date_difference <= 185:
                            incentive -= (0.50 / 100) * amount_numeric

                        # amount adding
                        elif date_difference > 125 and date_difference <= 155:
                            incentive = (0.75 / 100) * amount_numeric
                        elif date_difference > 95 and date_difference <= 125:
                            incentive = (1 / 100) * amount_numeric
                        elif date_difference > 65 and date_difference <= 95:
                            incentive = (1.25 / 100) * amount_numeric
                        elif date_difference > 35 and date_difference <= 65:
                            incentive = (1.5 / 100) * amount_numeric
                        elif date_difference <= 35:
                            incentive = (2 / 100) * amount_numeric
                        else:
                            pass

                        # create the lines of collection incentive
                        self.invoice_ids = [fields.Command.create({'invoice_id': res.id, 'amount': payment['amount'], 'date': res.invoice_date, 'payment_date': payment['date'], 'collection_incentive': incentive})]
                        self.collection_incentive_amount += incentive
        else:
            if self.invoice_ids:
                for rec in self.invoice_ids:
                    rec.unlink()



class CollectionIncentiveLine(models.Model):
    _name = "collection.incentive.line"
    _description = "Collection Incentive Line"
    _order = "payment_date desc"

    line_id = fields.Many2one('collection.incentive', string='lines')
    invoice_id = fields.Many2one('account.move', string="Invoices")
    invoice_id_id = fields.Char(string="Invoices id")
    amount = fields.Float(string="Amount",)
    date = fields.Date(string="Invoice date",)
    payment_date = fields.Date(string="Payment date",)
    collection_incentive = fields.Float(string="Collection Incentive", default=0.0)



