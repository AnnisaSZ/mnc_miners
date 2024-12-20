{
    'name': "CMS MNCEI",
    'summary': """Announcement or Information for Employee""",
    'description': """
        MNCEI Information:
            - Announcement For All Employee MNC Energy Investments
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "news",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mail'
    ],
    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/banner_views.xml',
        'views/news_views.xml',
        'views/menuitems_views.xml',
        'wizard/extend_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
