# -*- coding: utf-8 -*-
{
    'license': 'AGPL-3',
    'name': "MNC HR - CV",
    'summary': """ This module will help you to print out template cv """,
    'description': """ Print Out CV """,
    'author': "IT MNC Energy",
    'category': 'HR',
    'depends': [
        'base',
        'mnc_hr',
        'mnc_ticket_request'
    ],
    'data': [
        'report/cv_tmpl_energy.xml',
        'views/assets.xml',
        'views/employee_views.xml',
    ],
    'qweb': [
        'static/src/xml/user_menu.xml',
    ],
    'demo': [],
    'installable': True,
}
