{
    'name': "Hazard Report",
    'summary': """Safety Accountibility Program""",
    'description': """
        Safety Accountibility Program:
            - Safety Accountibility Program
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "SAP",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'bcr_master',
        'bcr_api_sh',
        'mnc_hr',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/email_template.xml',
        'views/notifcation_views.xml',
        'views/config_views.xml',
        'views/sap.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
