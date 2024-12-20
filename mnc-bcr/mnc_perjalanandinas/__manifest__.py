{
    'name': "Perjalanan Dinas",
    'summary': """Permohonan Perjalanan Dinas""",
    'description': """
        Permohonan Perjalanan Dinas MNC Energy Investments:
            -MNCEI perjalanan dinas
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Perdin",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'mnc_hr',
        'mnc_user_signature',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/pr_report.xml',
        'data/sequence.xml',
        'data/templates.xml',
        'views/setting_views.xml',
        'views/perjalanandinas.xml',
        'wizard/perdin_approval_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
