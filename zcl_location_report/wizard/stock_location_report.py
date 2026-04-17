# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Anoop Jayaprakash
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import models, fields


class StockLocationInherit(models.TransientModel):
    _name = "stock.location.pdf.wizard"

    product_id = fields.Many2many('product.product')
    location_id = fields.Many2one('stock.location')

    def stock_location_print_pdf(self):
        data_list = []
        if self.product_id:
            if self.location_id:
                data = self.env['stock.quant'].search([('location_id.id', '=', self.location_id.id), ('product_id.id', 'in', self.product_id.ids)])
            else:
                data = self.env['stock.quant'].search([('product_id.id', 'in', self.product_id.ids)])
        else:
            if self.location_id:
                data = self.env['stock.quant'].search([('location_id.id', '=', self.location_id.id)])
            else:
                data = self.env['stock.quant'].search([])
        for rec in data:
            data_list.append({
                'location': rec.location_id.complete_name,
                'product': rec.product_id.product_tmpl_id.name,
                'lot_serial_no': rec.lot_id.name,
                'on_hand_quantity': rec.inventory_quantity_auto_apply,
                'reserved_quantity': rec.reserved_quantity,
            })
        datas = {
            'list_data': data_list
        }
        return self.env.ref('zcl_location_report.action_stock_location_pdf_report').report_action(
            None, data=datas)
