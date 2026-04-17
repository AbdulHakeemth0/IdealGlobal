from odoo import models, fields, api
from odoo.exceptions import AccessError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    team_id = fields.Many2one('crm.team', 'Sales Team',
        help='If set, this Sales Team will be used for sales and assignments related to this partner')

    @api.constrains('name')
    def _check_user_access(self):
        if not self.env.user.create_customer:
            raise AccessError("Access Denied")

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            domain = [('user_id', '=', self.user_id.id)]
            teams = self.env['crm.team'].search(domain).ids
            return {'domain': {'team_id': [('id', 'in', teams)]}}

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            domain = [('team_id', '=', self.team_id.id)]
            price_list = self.env['product.pricelist'].search(domain).ids
            return {'domain': {'property_product_pricelist': [('id', 'in', price_list)]}}


class ResUsers(models.Model):
    _inherit = "res.users"

    create_customer = fields.Boolean()
    create_product = fields.Boolean()
    create_sale_order = fields.Boolean()
    confirm_sale_order = fields.Boolean()
    create_invoice = fields.Boolean()
    confirm_invoice = fields.Boolean()
    create_purchase_order = fields.Boolean()
    confirm_purchase_order = fields.Boolean()
    create_customer_payment = fields.Boolean()
    confirm_customer_payment = fields.Boolean()
    create_vendor_payment = fields.Boolean()
    confirm_vendor_payment = fields.Boolean()
    create_sale_return = fields.Boolean()
    confirm_sale_return = fields.Boolean()
    create_delivery_order = fields.Boolean()
    create_transfer_request = fields.Boolean()
    create_bill = fields.Boolean()
    confirm_bill = fields.Boolean()
    confirm_delivery_order = fields.Boolean()
    confirm_transfer_request = fields.Boolean()



