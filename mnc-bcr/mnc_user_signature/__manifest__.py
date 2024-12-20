# -*- coding: utf-8 -*-
{
    'name': "User Signature",

    'summary': """Signature""",

    'description': """
        User Signature to Upload
    """,

    'author': "My Company",
    'website': "http://www.mncenergy.com",
    'category': 'base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
    ],
}
