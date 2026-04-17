from odoo import api, fields, models
from odoo.exceptions import AccessError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.constrains('name')
    def _check_user_access(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.picking_type_id.code == 'outgoing':
                    if not self.env.user.create_delivery_order:
                        raise AccessError("Access Denied")
                elif self.picking_type_id.code == 'incoming':
                    if not self.env.user.create_transfer_request:
                        raise AccessError("Access Denied")

    def button_validate(self):
        if self.env.user.id != self.env.ref('base.public_user').id:
            if self.env.user.id != self.env.ref('base.user_root').id:
                if self.picking_type_id.code == 'outgoing':
                    if not self.env.user.confirm_delivery_order:
                        raise AccessError("Access Denied")
                    else:
                        return super(StockPicking,self).button_validate()
                elif self.picking_type_id.code == 'incoming':
                    if not self.env.user.confirm_transfer_request:
                        raise AccessError("Access Denied")
                    else:
                        return super(StockPicking,self).button_validate()
                else:
                    return super(StockPicking, self).button_validate()
            else:
                return super(StockPicking, self).button_validate()
        else:
            return super(StockPicking, self).button_validate()
