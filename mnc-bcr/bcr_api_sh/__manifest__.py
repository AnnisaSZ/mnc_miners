# -*- coding: utf-8 -*-
{
    'name': "BCR API SH",

    'summary': """
        BCR API SH Module create by Syarif Hidayatullah """,

    'description': """
        -
    """,

    'author': "Syarif Hidayatullah",
    'website': "https://www.syarifhidayatullah.dev/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    "depends": [
        'base',
        'auth_signup',
        'bcr_master_custom_sh',
        'bcr_planning_custom_sh',
    ],
    # always loaded
    'data': [
        'data/api_key_parameter.xml',
        'data/templates.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/view.xml',
        'views/res_users.xml',
        'data/data.xml',
    ],
}
