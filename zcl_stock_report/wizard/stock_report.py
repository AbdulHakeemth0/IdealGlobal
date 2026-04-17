# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Anoop Jayaprakash
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import models, fields


class StockReport(models.TransientModel):
    _name = "stock.pdf.wizard"

    product_id = fields.Many2many('product.product')

    def stock_print_pdf(self):
        data_list = []
        if self.product_id:
            data = self.env['product.product'].browse(
                self.product_id.ids).exists()
        else:
            data = self.env['product.product'].search([])
        for rec in data:
            data_list.append({
                'product': rec.display_name,
                'available_quantity': rec.qty_available,
                'free_quantity': rec.free_qty,
                'incoming_quantity': rec.incoming_qty,
                'outgoing_quantity': rec.outgoing_qty,
            })
        datas = {
            'list_data': data_list
        }
        return self.env.ref(
            'zcl_stock_report.action_stock_pdf_report').report_action(None,
                                                                      data=datas)
