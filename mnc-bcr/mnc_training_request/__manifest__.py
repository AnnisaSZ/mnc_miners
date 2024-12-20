# -*- coding: utf-8 -*-
{
    'name': "MNC - Training Requisition",

    'summary': """"Form TR - MNCEI""",
    'description': """
        Training submission form
    """,

    'author': "it coals",
    'website': "http://www.mncenergy.com",
    'category': 'Training',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mnc_hr',
        'mnc_user_signature',
    ],

    # always loaded
    'data': [
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'data': [
        'data/sequence.xml',
        'data/notification_email_template.xml',
        'security/ir.model.access.csv',
        # 'data/sequence.xml',
        'security/security.xml',
        'wizard/tr_approval_wizard.xml',
        'report/training_report.xml',
        # 'views/templates.xml',
        'views/views.xml',
    ]
}
