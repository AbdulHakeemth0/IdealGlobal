{
    'name': "Prefix Code",
    'summary': """ Prefix Code odoo 16""",
    'license': 'LGPL-3',
    'version': "16",
    'sequence': 2,
    'category': "Extra Sale",
    'website': 'www.zinfog.com',
    'author': 'zinfog',
    'depends': ['base', "sale", "account", "contacts", 'purchase', "sale_management", "stock",],
    "data": [
        'views/sales_team.xml',
        # 'views/sale_order.xml',
        "views/invoice.xml",
        "views/stock_picking.xml",
    ],

    "installable": True,
    "application": True,
    "auto-install": False,





}
