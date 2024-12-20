{
    'name': "Fuel Management",
    'summary': """Fuel Management""",
    'description': """
        Fuel Management System MNC Energy Investments:
            -Fuel Management System
    """,

    'author': "IT MNCEI",
    'website': "https://mncenergy.com",
    'category': "Fuel Management",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'ks_list_view_manager',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/unit_consume_views.xml',
        'views/assets.xml',
        'views/fuel_views.xml',
        'views/master_fuel_views.xml',
        'views/maintank_views.xml',
        'views/fuel_report_views.xml',
        'views/menuitem_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
