from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.http import request


class StockPickingType(models.Model):

    _inherit = "stock.picking"

    sales_team = fields.Many2one('crm.team', string="Zone")
    branch_id = fields.Many2one('res.branch', string='Branch', store=True,
                                help='Leave this field empty if this account is'
                                     ' shared between all branches')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sale_team = self.env['sale.order'].search([('name', '=', (vals.get('origin')))], limit=1)
            if not sale_team:
                if vals.get('sales_team'):
                    sale_team = self.env['crm.team'].search([('id', '=', int(vals.get('sales_team')))])
            else:
                sale_team = self.env['crm.team'].search([('id', '=', sale_team.team_id.id)])
            if sale_team:
                if not vals.get('name') or vals['name'] == _('New'):
                    if vals.get('is_locked') == True or sale_team:
                        prefix = self.env['ir.sequence'].search([('code', '=', sale_team.prefix_code_delivery)], limit=1)
                        if prefix:
                            vals['name'] = self.env['ir.sequence'].next_by_code(prefix.code) or _('New')
        return super().create(vals_list)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.branch_id = self.partner_id.branch_id