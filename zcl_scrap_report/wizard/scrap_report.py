# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Anoop Jayaprakash
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

###################################################################################

from odoo import models, fields


class StockReport(models.TransientModel):
    _name = "scrap.pdf.wizard"

    product_id = fields.Many2many('product.product')

    def scrap_print_pdf(self):
        data_list = []
        if self.product_id:
            data = self.env['stock.scrap'].search([('product_id','in',self.product_id.ids)])
            print(data,"#####")
        else:
            data = self.env['stock.scrap'].search([])
        for rec in data:
            data_list.append({
                'reference': rec.name,
                'date': rec.date_done,
                'product': rec.product_id.name,
                'quantity': rec.scrap_qty,
                'source_location': rec.location_id.name,
                'scrap_location': rec.scrap_location_id.name,
                'status': rec.state,
            })
        datas = {
            'list_data': data_list
        }
        print(datas,"mmmmmmmmmmmmmmmmmmmmmmmmmmm")
        return self.env.ref(
            'zcl_scrap_report.action_scrap_pdf_report').report_action(None,
                                                                      data=datas)
