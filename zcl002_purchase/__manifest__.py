{
    'name': "Purchase Order",
    'summary': """purchase order for odoo 16""",
    'license': 'LGPL-3',
    'version': "16",
    'sequence': 2,
    'category': "Extra Tools",
    'website': 'www.zinfog.com',
    'author': 'zinfog',
    'depends': ['base', "purchase"],
    "data": [
        'views/purchase_inherit.xml',
        "views/product_inherit.xml",
        "security/ir.model.access.csv",


    ],


    "installable": True,
    "application": True,
    "auto-install": False,


}