from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.http import request


class SalesTeam(models.Model):
    _inherit = "crm.team"

    prefix_name = fields.Char("Prefix Name")
    prefix_code_sale = fields.Char("Prefix Code Sale")
    prefix_code_invoice = fields.Char("Prefix Code Invoice")
    prefix_code_debit = fields.Char("Prefix Code Receipt")
    prefix_letter_sale = fields.Char("Prefix Sale")
    prefix_letter_invoice = fields.Char("Prefix Invoice")
    prefix_letter_debit = fields.Char("Prefix Receipt")
    prefix_padding = fields.Integer("Padding")
    prefix_code_delivery = fields.Char("Prefix Code Delivery")
    prefix_letter_delivery = fields.Char("Prefix Delivery")
    prefix_code_expense = fields.Char("Prefix Code Expense")
    prefix_letter_expense = fields.Char("Prefix Expense")
    cash_account = fields.Many2one('account.account', string="Cash Account")
    sale_account = fields.Many2one('account.account', domain="[('account_type','=','income')]", string="Sale Account")
    customer_receivable_account = fields.Many2one('account.account', string="Customer Receivable Account", domain="[('account_type', '=', 'asset_receivable')]")
    customer_payable_account = fields.Many2one('account.account', string="Customer Payable Account", domain="[('account_type', '=', 'liability_payable')]")

    def prefix_generate(self):
        if not self.env['ir.sequence'].search([('code', '=',  self.prefix_code_sale)]):
            code_sale = self.env['ir.sequence'].sudo().create({
                'name': self.prefix_name,
                'code': self.prefix_code_sale,
                'prefix': self.prefix_letter_sale,
                'padding': self.prefix_padding,
                'active': True,
            })
            if self.name == 'SAADA':
                code_sale.number_next = 360
            if self.name == 'AUQAD':
                code_sale.number_next = 129

        if not self.env['ir.sequence'].sudo().search([('code', '=', self.prefix_code_invoice)]):
            code_invoice = self.env['ir.sequence'].sudo().create({
                'name': self.prefix_name,
                'code': self.prefix_code_invoice,
                'prefix': self.prefix_letter_invoice,
                'padding': self.prefix_padding,
                'active': True,
            })
            if self.name == 'SAADA':
                code_invoice.number_next = 360
            if self.name == 'AUQAD':
                code_invoice.number_next = 129
        if not self.env['ir.sequence'].sudo().search([('code', '=', self.prefix_code_debit)]):
            code_invoice = self.env['ir.sequence'].sudo().create({
                'name': self.prefix_name,
                'code': self.prefix_code_debit,
                'prefix': self.prefix_letter_debit,
                'padding': self.prefix_padding,
                'active': True,
            })
            if self.name == 'SAADA':
                code_invoice.number_next = 360
            if self.name == 'AUQAD':
                code_invoice.number_next = 129
        if not self.env['ir.sequence'].sudo().search([('code', '=', self.prefix_code_delivery)]):
            code_invoice = self.env['ir.sequence'].sudo().create({
                'name': self.prefix_name,
                'code': self.prefix_code_delivery,
                'prefix': self.prefix_letter_delivery,
                'padding': self.prefix_padding,
                'active': True,
            })
            if self.name == 'SAADA':
                code_invoice.number_next = 360
            if self.name == 'AUQAD':
                code_invoice.number_next = 129

    _sql_constraints = [
        ('unique_prefix_code_sale', 'unique (prefix_code_sale)', _('prefix code sale already exists!')),
        ('unique_prefix_code_invoice', 'unique (prefix_code_invoice)', _('prefix code invoice already exists!')),
        ('unique_prefix_code_debit', 'unique (prefix_code_debit)', _('prefix code debit already exists!')),
        ('unique_prefix_letter_sale', 'unique (prefix_letter_sale)', _('prefix letter sale already exists!')),
        ('unique_prefix_letter_invoice', 'unique (prefix_letter_invoice)', _('prefix letter invoice already exists!')),
        ('unique_prefix_letter_debit', 'unique (prefix_letter_debit)', _('prefix letter debit already exists!')),
        ('unique_prefix_code_delivery', 'unique (prefix_code_delivery)',_('prefix code delivery already exists!')),
        ('unique_prefix_letter_delivery', 'unique (prefix_letter_delivery)', _('prefix letter delivery already exists!')),
        ('unique_prefix_code_expense', 'unique (prefix_code_expense)', _('prefix code expense already exists!')),
        ('unique_prefix_letter_expense', 'unique (prefix_letter_expense)',
         _('prefix letter expense already exists!')),

    ]


class InhCustomer(models.Model):
    _inherit = "res.partner"



    property_account_receivable_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        store=True,
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=True
    )

    property_account_payable_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Account Payable",
        store=True,
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=True
    )

    test_account_id  = fields.Many2one('account.account', compute="_test_compute",store=True)

    @api.depends('team_id.customer_receivable_account','team_id.customer_payable_account')
    def _test_compute(self):
        for rec in self:
            if rec.team_id:
                if rec.team_id.customer_receivable_account:
                    rec.test_account_id = rec.team_id.customer_receivable_account.id
                    rec.property_account_receivable_id = rec.test_account_id.id
                if rec.team_id.customer_payable_account:
                    rec.property_account_payable_id = rec.team_id.customer_payable_account.id


