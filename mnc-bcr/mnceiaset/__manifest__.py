{
    'name': "mnceiaset",
    'summary': """Pencatatan Aset MNCEI""",
    'description': """
        Asset Management MNC Energy Investments:
            - mncei aset courses
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Aset",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mnc_hr',
    ],
    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/mnceiaset.xml',
        'views/categ_aset.xml',
        'views/pemegang_asset_views.xml',
        'security/security.xml',
        'report/aset_label.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
