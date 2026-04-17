from odoo import models, fields, api
from odoo.exceptions import AccessError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    user_id = fields.Many2one('res.users', string='User')
    team_id = fields.Many2one('crm.team',string="Zone")

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            team = self.env['crm.team'].search([('user_id', '=', self.user_id.id)], limit=1)
            self.team_id = team.id
            self.default_account_id = team.sale_account.id
        else:
            self.team_id = False
            self.default_account_id = False
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.constrains('customer_id','amount')
    def _check_user_access(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.partner_type == 'customer':
                    if not self.env.user.create_customer_payment:
                        raise AccessError("Access Denied")
                elif self.partner_type == 'supplier':
                    if not self.env.user.create_vendor_payment:
                        raise AccessError("Access Denied")

    def action_post(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.partner_type == 'customer':
                    if not self.env.user.confirm_customer_payment:
                        raise AccessError("Access Denied")
                    else:
                        return super(AccountPayment,self).action_post()
                elif self.partner_type == 'supplier':
                    if not self.env.user.confirm_vendor_payment:
                        raise AccessError("Access Denied")
                    else:
                        return super(AccountPayment,self).action_post()
                else:
                    return super(AccountPayment, self).action_post()
            else:
                return super(AccountPayment, self).action_post()
        else:
            return super(AccountPayment, self).action_post()