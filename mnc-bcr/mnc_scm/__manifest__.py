{
    'name': "mnc_scm",
    'summary': """Supply Chain Management""",
    'description': """
        Supply Chain Management:
            - Supply Chain Management
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "SCM",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mnc_hr',
        'account',
        'purchase_requisition',
        'bcr_api_sh',
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/notification_email_template.xml',
        'data/paperformat.xml',
        'views/configuration_views.xml',
        'views/scm.xml',
        'views/orf_views.xml',
        'views/price_comp_views.xml',
        'views/purchase_views.xml',
        'views/slp_views.xml',
        'views/shipping_detail_views.xml',
        'views/menuitem.xml',
        'wizard/prf_approval_views.xml',
        'wizard/slp_approval_wizard_views.xml',
        'wizard/pc_approval_wizard_views.xml',
        'reports/orf_report_template.xml',
        'reports/price_comp_template.xml',
        'reports/submission_letter_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
