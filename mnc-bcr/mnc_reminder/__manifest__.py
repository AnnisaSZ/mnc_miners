{
    'name': "mnc_reminder",
    'summary': """Data Input Reminder""",
    'description': """
        Data Input Reminder
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'base_setup',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/module_reminder_view.xml',
        'views/setting_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
