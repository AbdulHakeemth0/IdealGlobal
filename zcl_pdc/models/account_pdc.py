# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################
from odoo import fields, models


class AccountPDC(models.Model):
    _name = "account.pdc"
    _description = "Post date cheque model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string="Customer")
    payment_from_date = fields.Date(string="Payment From Date")
    payment_to_date = fields.Date(string="Payment To Date")
    effective_from_date = fields.Date(string="Effective From Date")
    effective_to_date = fields.Date(string="Effective To Date")
    journal_id = fields.Many2one('account.journal', string="Journal")
    payment_method = fields.Char(string="Payment Method", default="PDC",
                                 readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')],
                             default="draft")
    payment_type = fields.Selection(
        [('outbound', 'Outbound'), ('inbound', 'Inbound')],required=True)
    amount = fields.Float(string="Amount")

    def pdc_confirm(self):
        self.write({"state":"posted"})
        journal = self.env['account.journal'].search([('type', '=', 'bank')],limit=1)
        if self.payment_type == 'outbound':
            payment = self.env['account.payment'].create({'partner_id':self.partner_id.id,
                                                          'payment_type':'outbound',
                                                          'journal_id':journal.id,
                                                          'amount':self.amount
                                                          })
        if self.payment_type == 'inbound':
            payment = self.env['account.payment'].create({'partner_id':self.partner_id.id,
                                                          'payment_type':'inbound',
                                                          'journal_id':journal.id,
                                                          'amount':self.amount
                                                          })