{
    'name': "mnc_fis",
    'summary': """Flight Information Sheet """,
    'description': """
        Flight Information Sheet:
            - Flight Information Sheet
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "FIS",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
    ],
    # always loaded
    'data': [
        'data/paperformat.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/report_fis_view.xml',
        'views/configuration_views.xml',
        'views/menuitem.xml',
        'reports/report_fis_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
