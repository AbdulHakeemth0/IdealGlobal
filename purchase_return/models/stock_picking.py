from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    delivery_type = fields.Boolean(string="Purchase Return")

    @api.onchange('delivery_type')
    def _onchange_delivery_type(self):
        if self.delivery_type:
            returns = self.env['stock.picking.type'].search([('delivery_type', '=', True)])
            if len(returns) >= 1:
                raise UserError(_("Its Already One Form Is True"))