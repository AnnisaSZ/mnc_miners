{
    "name": "Matrix Approval",
    "version": "14.0.1.0.1",
    "summary": "MNCEI - Matrix Approval in Company",
    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Base Setting",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'base',
        'mnc_hr',
        'mnc_ticket_request',
        'mnc_perjalanandinas',
        'mnc_purchase_request',
        'mnc_training_request',
        'mnc_meeting_room',
        'mnc_ticket_request',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/setting_views.xml',
        'views/perdin_views.xml',
        'views/purchase_request.xml',
        'views/training_views.xml',
        'views/meet_room_views.xml',
        'wizard/pr_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
