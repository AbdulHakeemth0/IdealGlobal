{
    'name': "Sale Order",
    'summary': """ Sale order for odoo 16""",
    'license': 'LGPL-3',
    'version': "16",
    'sequence': 2,
    'category': "Extra Sale",
    'website': 'www.zinfog.com',
    'author': 'zinfog',
    'depends': ['base', "sale", "account","contacts",'purchase', "stock", "sale_management","sale_automatic_workflow", 'sales_team', 'hr'],
    "data": [
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/sale_inherit.xml',
        'views/invoice_inherit.xml',
        'views/partner_inherit.xml',
        'views/product_inherit.xml',
        'report/sale_order_report_inherit.xml',
        'report/invoice_report_inherit.xml',
        'data/ressequence.xml',
        "security/user_security.xml",
        "views/account_inherit.xml",
        "views/product_category.xml",
        "views/product_template_view.xml",
        "views/new_invoice_inherit.xml",
        "views/new1_creaditnote_inherit.xml",
        "views/new_journalentries_inherit.xml",
        "views/price_list.xml",
        "views/contact_team.xml",
        "views/stock_move.xml",
        "views/customer_payment_menu.xml",
        "views/discount_menu.xml",

    ],

    "installable": True,
    "application": True,
    "auto-install": False,





}
