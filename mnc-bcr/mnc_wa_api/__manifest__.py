{
    'name': "Miners x WA",
    'summary': """Integration Miners with WA""",
    'description': """
        Integration module x wa, using provide Mekari Qontak
    """,

    'author': "IT MNC Energy Investments",
    'website': "https://mncenergy.com",
    'category': "HR",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'mnc_attendance',
    ],
    # always loaded
    'data': [
        'data/data.xml',
        'data/email_template.xml',
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/settings.xml',
        'views/template_views.xml',
        'views/recipient_views.xml',
        'views/logging_views.xml',
        'views/menuitem_views.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
