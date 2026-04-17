# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    foc_confirm = fields.Boolean(string="FOC Confirm", default=False)

    def action_confirm(self):
        if not self.foc_confirm:
            if self.partner_id.free_of_cost:
                if self.amount_total >= self.partner_id.max_sale_amount:
                    self.foc_confirm = True
                    return {
                        'name': 'Sale order',
                        'type': 'ir.actions.act_window',
                        'res_model': 'sale.foc',
                        'view_mode': 'form',
                        "target": 'new',
                        'context': {'default_sale_order': self.id}
                    }
                else:
                    return super(SaleOrder, self).action_confirm()
            else:
                return super(SaleOrder, self).action_confirm()
        else:
            return super(SaleOrder, self).action_confirm()
