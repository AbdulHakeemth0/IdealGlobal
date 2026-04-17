from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.http import request


class SaleInherits(models.Model):
    _inherit = "sale.order"

    # sales_team = fields.Many2one('crm.team', string="Zone")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            if vals.get('user_id'):
                team_id = self.env['crm.team'].search([('user_id', '=', int(vals.get('user_id')))], limit=1)
                if team_id:
                    if not vals.get('name') or vals['name'] == _('New'):
                        if vals.get('sale_return') == False:
                            prefix = self.env['ir.sequence'].search([('code', '=', team_id.prefix_code_sale)])
                            if prefix:
                                vals['name'] = self.env['ir.sequence'].next_by_code(prefix.code) or _('New')
        return super().create(vals_list)



