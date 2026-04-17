from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from odoo.http import request

class ProductPriceList(models.Model):
    _inherit = "product.pricelist"

    team_id = fields.Many2one(comodel_name="crm.team", string="Sales Team")
