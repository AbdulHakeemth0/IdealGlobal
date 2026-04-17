{
    'name': "Sale Order Return",
    'summary': """ Sale order Return For odoo 16""",
    'license': 'LGPL-3',
    'version': "16",
    'sequence': 2,
    'category': "Extra Sale",
    'website': 'www.zinfog.com',
    'author': 'zinfog',
    'depends': [
        'base', "sale", "account", "stock"
    ],
    "data": [
        "security/ir.model.access.csv",
        'data/sequance.xml',
        'views/sale_return.xml',
        'views/stock_picking.xml',
        'wizards/sale_return_wizard.xml',

    ],

    "installable": True,
    "application": True,
    "auto-install": False,





}
