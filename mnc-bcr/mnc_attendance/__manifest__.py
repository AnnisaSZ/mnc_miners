{
    'name': "HR - Attendance",
    'summary': """HR Attendance""",
    'description': """
        Attendance:
            - Attendance
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "HR",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'hr_holidays_public',
        'bcr_api_sh',
        'mnc_hr',
        'mnc_ticket_request',
        'hr_attendance',
        'queue_job',
        'hr_holidays',
        # 'mnc_sap', #depends because for getprofile and mobile apps API
    ],
    # 'external_dependencies': {
    #     'python': ['reportlab', 'openpyxl'],
    # },
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/report_attendance.xml',
        'data/email_template.xml',
        'views/assets.xml',
        'views/holiday_public_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_leave_views.xml',
        'views/wdms_views.xml',
        'views/res_config_views.xml',
        'views/resource_calendar.xml',
        'views/mncei_employee_views.xml',
        'views/menu_items.xml',
        'wizard/resource_views.xml',
        'wizard/report_attendance_views.xml',
    ],
    'qweb': ['static/src/xml/attendance_buttons.xml'],
    # only loaded in demonstration mode
    'application': True,
}
