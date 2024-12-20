# -*- coding: utf-8 -*-
{
    'name': "BCR API - BIO",

    'summary': """
        BCR API - Bio""",

    'description': """
        - Login Bio Face & Finger
    """,
    'author': "IT MNC Energy",
    'website': "https://mncenergy.com/id/beranda/",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    "depends": [
        'bcr_api_ext',
    ],
    # always loaded
    'data': [
        'views/user_views.xml',
    ],
}
