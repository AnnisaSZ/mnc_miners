{
    'name': "Cost Unit",
    'summary': """Cost Unit""",
    'description': """
        In Apps feature :
            - Asset Depreciation
            - Fuel Price (Under Development)
            - Payment Contractor
    """,

    'author': "IT MNC Energy Investments",
    'website': "https://mncenergy.com",
    'category': "Fleet",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'om_account_accountant',
        'om_account_asset',
        'mnc_maintenance',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/payment_contractor_views.xml',
        'views/rate_contractor_views.xml',
        'views/menuitems.xml',
        'views/asset_views.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
