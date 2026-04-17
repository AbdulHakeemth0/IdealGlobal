{
    'name': "Purchase Order Return",
    'summary': """ Purchase order Return For odoo 16""",
    'license': 'LGPL-3',
    'version': "16",
    'sequence': 2,
    'category': "Extra Purchase",
    'website': 'www.zinfog.com',
    'author': 'zinfog',
    'depends': [
        'base', "purchase", "account","zcl002_purchase", "stock", "sale"
    ],
    "data": [
        "views/purchas_return.xml",
        "data/sequance.xml",
        "security/ir.model.access.csv",
        'wizards/purchase_return_wizard.xml',
        "views/stock_picking.xml",


    ],

    "installable": True,
    "application": True,
    "auto-install": False,





}
