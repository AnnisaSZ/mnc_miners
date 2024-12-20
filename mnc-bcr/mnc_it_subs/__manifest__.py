{
    'name': "mnc_it_subs",
    'summary': """MNC IT Subscription""",
    'description': """
        MNC IT Subscription:
            - MNC IT Subscription
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "IT",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mail',
    ],
    # always loaded
    'data': [
        'data/data.xml',
        'data/ir_cron_data.xml',
        'data/template_email.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/configuration_views.xml',
        'views/it_subs_form_views.xml',
        'views/menuitem.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
