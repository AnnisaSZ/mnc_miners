{
    'name': "MNC - Purchase Requisition",
    'summary': """Form PR - MNCEI""",
    'description': """
        List PR dan Form MNCEI
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Purchase",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mnc_hr',
        'mnceiaset',
        'mnc_user_signature',
    ],
    # always loaded
    'data': [
        'data/notification_email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/pr_report.xml',
        'wizard/pr_approval_wizard.xml',
        'views/mnc_pr.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
