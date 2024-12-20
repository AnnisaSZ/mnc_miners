# -*- coding: utf-8 -*-
{
    'name': "MNC - Meeting",

    'summary': """"Form Booking Meeting Room""",
    'description': """
        Form and List View Booking Meeting Room
    """,

    'author': "it coals",
    'website': "http://www.mncenergy.com",
    'category': 'calendar',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'mnc_hr',
        'web_gantt_view'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'data': [
        'data/notification_email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/meeting_views.xml',
        'views/room_views.xml',
        'views/menuitem.xml',
        'wizard/reschedule_meeting_views.xml',
    ]
}
