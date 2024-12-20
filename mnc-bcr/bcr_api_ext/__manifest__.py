# -*- coding: utf-8 -*-
{
    'name': "BCR API SH",

    'summary': """
        BCR API SH Module""",

    'description': """
        -
    """,
    'author': "IT MNC Energy",
    'website': "https://mncenergy.com/id/beranda/",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    "depends": [
        'bcr_api_sh',
        'bcr_operational',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/api_key_parameter.xml',
        # 'data/templates.xml',
        # 'security/res_groups.xml',
        # 'data/ir_cron_data.xml',
        # 'views/view.xml',
        # 'views/res_users.xml',
        # 'data/data.xml',
    ],
}
