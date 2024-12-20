{
    'name': "Maintenance & Warehouse",
    'summary': """Maintenance & Warehouse""",
    'description': """
       Maintenance & Warehouse
    """,

    'author': "IT MNC Energy Investments",
    'website': "https://mncenergy.com",
    'category': "Fleet",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'mnc_fleet',
        'stock_account',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_views.xml',
        'views/configuration.xml',
        'views/repair_views.xml',
        'views/menuitems.xml',
        'wizard/request_repair_views.xml',
    ],
    # only loaded in demonstration mode
    'application': False,
}
