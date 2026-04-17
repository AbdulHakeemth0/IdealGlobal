{
    'name': "Zinfog Product Cost After Landed Cost",
    'version': '0.1',
    'summary': "Fames custom modules",
    'description': "",
    'category': '',
    'website': "",
    'depends': ['stock_landed_costs', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/landed_product_cost_view.xml',
        'views/product_inherit.xml',
        'views/lc_cron_job.xml',
    ],

}
