# -*- coding: utf-8 -*-
{
    'name': "BCR Timbangan SH",

    'summary': """
        BCR Timbangan SH Module create by Syarif Hidayatullah """,

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
        'bcr_master',
        'purchase',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_cron_data.xml',
        'views/views.xml',
        'views/templates.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
