from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'



    customer_credit_limit = fields.Monetary(
        string='Customer Credit Limit',
        help='The maximum credit limit allowed for the customer.'
    )
    customer_days_notification = fields.Integer(
        string='Customer Days Notification',
        help='The number of days before sending a notification to the customer.'
    )

    building_name = fields.Char(string="Building Name")
    ref = fields.Char(copy=False, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='User')
    vatin_id = fields.Many2one('vat.number', string="VATIN")
    pc = fields.Integer(string="PC")
    po_box = fields.Integer(string="PO Box")
    crno_id = fields.Many2one('cr.number', string="CR No")
    grade_id = fields.Many2one('grade.master', string="Grade")
    guaranty_cheque = fields.Char(string="Guaranty Cheque")
    documents_id = fields.Many2one('documents.master', string="Documents")
    block = fields.Integer(string="Block")
    rate_type_id = fields.Many2one('rate.type', string="Rate Type")
    category = fields.Char(string="Category")
    ca_remarks = fields.Char(string="CA Remarks")
    id_proof = fields.Char(string="ID Proof")
    id_doc = fields.Binary(string="Doc")
    pdc_cheque = fields.Char(string='PDC Cheque')
    block_reason = fields.Char(string='Block Reason')
    owner_id = fields.Many2one('res.partner',string="Owner Name")
    owner_phone = fields.Char(related='owner_id.phone',string="Owner Phone")
    owner_email = fields.Char(related='owner_id.email',string="Owner Email")
    sponsor_id = fields.Many2one('res.partner', string="Sponsor Name")
    sponsor_phone = fields.Char(related='sponsor_id.phone', string="Sponsor Phone")
    sponsor_email = fields.Char(related='sponsor_id.email', string="Sponsor Email")
    contact_person_id = fields.Many2one('res.partner', string="Contact Person Name")
    contact_person_phone = fields.Char(related='contact_person_id.phone', string="CP Phone")
    contact_person_email = fields.Char(related='contact_person_id.email', string="CP Email")
    # walkin_customers = fields.Boolean(string="Walk-in Customer")
    # walkin_customer_ids = fields.One2many("walkin.customer", 'customer_id',
    #                                       string="Walk-in Customers")


    non_reconciled_receivable_balance = fields.Monetary(
        string='Current Balance Of Customer',
        compute='_compute_non_reconciled_receivable_balance',
        currency_field='currency_id'
    )
    current_balance_customer = fields.Monetary(string="Balance Limit", compute='_compute_current_balance')


    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('contact.sequence') or _('New')
        res = super(ResPartner, self).create(vals)
        return res

    def _compute_non_reconciled_receivable_balance(self):
        for partner in self:
            total = 0.0
            receivable_lines = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('reconciled', '=', False),
                ('move_id.state', '=', 'posted')
            ])
            for line in receivable_lines:
                total += line.amount_residual
            partner.non_reconciled_receivable_balance = total

    def _compute_current_balance(self):
        for val in self:
            val.current_balance_customer = self.customer_credit_limit - val.non_reconciled_receivable_balance

    class VATNumber(models.Model):
        _name = 'vat.number'

        name = fields.Char(string="Name")

    class CRNumber(models.Model):
        _name = 'cr.number'

        name = fields.Integer(string="Name")

    class GradeMaster(models.Model):
        _name = 'grade.master'

        name = fields.Char(string="Name")

    class DocumentsMaster(models.Model):
        _name = 'documents.master'

        name = fields.Char(string="Name")

    class RateType(models.Model):
        _name = 'rate.type'

        name = fields.Char(string="Name")

