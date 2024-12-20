{
    'name': "Fleet Management",
    'summary': """Fleet Productivity & Cost Controll""",
    'description': """
        Fleet Productivity & Cost Controll
    """,

    'author': "IT MNC Energy Investments",
    'website': "https://mncenergy.com",
    'category': "HR",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'bcr_master',
        'bcr_master_ext',
        'bcr_barging_sales',
        'mnc_fuel_management',
    ],
    # always loaded
    'data': [
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/settings.xml',
        'views/master_views.xml',
        'views/breakdown_views.xml',
        'views/hourly_production_views.xml',
        'views/shift_production_views.xml',
        'views/menuitem_views.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
