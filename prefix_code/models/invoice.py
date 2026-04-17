from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.http import request


class InvoiceInherit(models.Model):
    _inherit = "account.move"

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        readonly=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        compute='_compute_journals',
        inverse='_inverse_partner_id',
        store=True,
        check_company=True,
        change_default=True,
        index=True,
        ondelete='restrict',
    )
    bool_divider = fields.Boolean("Divider", default=False)
    sales_team = fields.Many2one('crm.team', string="Zone")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('/'):
                # if vals.get('bool_divider') == True:
                if vals.get('move_type') == 'out_invoice':
                    team_id = self.env['crm.team'].browse(int(vals.get('team_id')))
                    prefix = self.env['ir.sequence'].search([('code', '=', team_id.prefix_code_invoice)], limit=1)
                    if prefix:
                        vals['name'] = self.env['ir.sequence'].next_by_code(prefix.code) or _('/')
        return super(InvoiceInherit, self).create(vals_list)

    @api.depends('team_id')
    def _compute_journals(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                if rec.team_id:
                    journal = self.env['account.journal'].search(
                                  [('team_id', '=', rec.team_id.id)], limit=1)
                    if journal:
                        rec.journal_id = journal.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.team_id = self.partner_id.team_id.id
            self.branch_id = self.partner_id.branch_id


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bool_divider = fields.Boolean("Divider", default=False)
    sales_team_id = fields.Many2one('crm.team', string="Zone")

    # def _check_customer(self):
    #     if self.sales_team_id:
    #         domain = [('team_id','=',self.sales_team_id.id)]
    #         return domain
    # customer_id = fields.Many2one('res.partner',domain="_check_customer")
    @api.onchange('sales_team_id')
    def _onchange_sales_team_id(self):
        if self.sales_team_id:
            if self.sales_team_id.cash_account:
                self.payment_method_line_id.payment_account_id = self.sales_team_id.cash_account.id
                self.outstanding_account_id = self.sales_team_id.cash_account.id
            return {'domain': {'customer_id': [('team_id', '=', self.sales_team_id.id)]}}
        else:
            return {'domain': {'customer_id': []}}

    customer_id = fields.Many2one('res.partner', string="Customer")
    outstanding_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Outstanding Account",
        store=True,
        compute='_compute_outstanding_account_id',
        inverse='_compute_inverse_account_id',
        check_company=True)

    def _compute_inverse_account_id(self):
        print("ss")


    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.partner_id = self.customer_id.id
            self.sales_team_id = self.customer_id.team_id.id
        else:
            self.partner_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('Draft'):
                # if vals.get('bool_divider') == True:
                #     team_id = self.env['crm.team'].browse(int(vals.get('sales_team_id')))
                #     prefix = self.env['ir.sequence'].search([('code', '=', team_id.prefix_code_debit)], limit=1)
                if vals.get('payment_type') == 'inbound':
                    customer = self.env['res.partner'].browse(int(vals.get('partner_id')))
                    prefix = self.env['ir.sequence'].search([('code', '=', customer.team_id.prefix_code_debit)], limit=1)
                    if prefix:
                        vals['name'] = self.env['ir.sequence'].next_by_code(prefix.code) or _('/')
        return super(AccountPayment, self).create(vals_list)

    # @api.onchange('partner_id')
    # def _onchange_partner(self):
    #     if self.partner_id:
    #         self.sales_team_id = self.partner_id.team_id.id

