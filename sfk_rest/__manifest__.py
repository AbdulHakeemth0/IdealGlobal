
{
    "name": " SFK REST API",
    "summary": """Restful API for Odoo 16""",
    "version": "16.0.0.1",
    "category": "Extra Tools",
    'website': 'www.zinfog.com',
    'author': 'Zinfog',
    "depends": [
        "base", "sale", "account", "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/rest_menu.xml",
        "views/rest_token_view.xml",
        # "views/add_to_cart_view.xml",
    ],
    "qweb": [
    ],
    "images": [
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
    
}