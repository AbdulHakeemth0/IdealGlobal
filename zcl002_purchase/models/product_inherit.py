from odoo import fields , models, api
from datetime import datetime, timedelta



class TemplateType(models.Model):

    _name = "product.group"
    _description = "Product Group"
    _rec_name = "br_name"


    br_name = fields.Char(string="Brand Name")


class Items(models.Model):

    _name ="group.type"
    _description = "Group Type"
    _rec_name = "item_name"

    item_name = fields.Char(string="Items")


class ItemsSub(models.Model):
    _name="item.template"
    _description = "Item Template"
    _rec_name = "sub_item"

    sub_item = fields.Char(string="Sub Item")


class ItemCategory(models.Model):
    _name ="category.group"
    _description = "Category Group"
    _rec_name = "cate_item"


    cate_item = fields.Char(string="Category Item")


class StockType(models.Model):
    _name = "stock.item"
    _description = "Stock Item"
    _rec_name = "dead_type"

    dead_type = fields.Char(string="Dead Type")








class Product(models.Model):

    _inherit = 'product.template'


    brand_name = fields.Many2one("product.group",string='Brand Name')
    item_group = fields.Many2one("group.type", string="Item Group")
    item_sub_group = fields.Many2one("item.template", string="Item Sub Group")
    item_category = fields.Many2one("category.group" , string="Item Category")
    country = fields.Many2one("res.country", string="Country of origin")
    feed_goods = fields.Integer(string="Feeds of Goods")
    dead_stock = fields.Many2one("stock.item", string="Dead Stock")
    lunch_times = fields.Datetime(string="Lunch Time")
    box = fields.Float(string='Box')
    bag = fields.Float(string='Bag')


