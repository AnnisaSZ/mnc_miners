{
    'name': "mnc_wbs",
    'summary': """Whistle Blowing System """,
    'description': """
        Whistle Blowing System:
            - Whistle Blowing System 
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "WBS",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'portal',
        'fims_login_background_and_styles',
        'mnc_ticket_request',
    ],
    # always loaded
    'data': [
        'views/assets.xml',
        'data/data.xml',
        'data/sequence.xml',
        'data/notification_email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/security_views.xml',
        'views/template.xml',
        'views/report_list.xml',
        'views/wbs_report_bod_views.xml',
        'views/wbs_report_head_views.xml',
        'views/wbs_report_emp_views.xml',
        'views/master.xml',
        'views/menuitem.xml',
        'wizard/action_summary_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
