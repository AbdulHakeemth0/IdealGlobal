# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import api, fields,models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange('user_id')
    def _onchange_name(self):
        if self.user_id.branch_id:
            self.branch_id = self.user_id.branch_id.id
