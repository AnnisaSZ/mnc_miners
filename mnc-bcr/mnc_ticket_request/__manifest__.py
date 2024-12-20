{
    'name': "MNC - Ticket Request",
    'summary': """Form Ticket - MNCEI""",
    'description': """
        List Ticket Helpdesk
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Purchase",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mnc_hr',
    ],
    # always loaded
    'data': [
        'data/data.xml',
        'data/notification_email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/ticket_views.xml',
        'views/ticket_addons.xml',
        'views/res_users.xml',
        'views/setting_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
