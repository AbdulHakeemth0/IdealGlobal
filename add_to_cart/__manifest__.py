{
    "name": "ADD TO CART",
    "summary": """Add To Cart for Odoo 16""",
    "license": 'LGPL-3',
    "version": "16",
    'sequence': 3,
    "category": "Extra Tools",
    'website': 'www.zinfog.com',
    'author': 'Zinfog',
    "depends": [
        "sale", "sfk_rest"
    ],
    "data": [
	        "security/ir.model.access.csv",
            "views/add_to_cart.xml"
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
