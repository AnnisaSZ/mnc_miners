# -*- coding: utf-8 -*-
{
    'name': "BCR PLANNING CUSTOM SH",

    'summary': """
        BCR PLANNING CUSTOM SH Module create by Syarif Hidayatullah """,

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
        'bcr_planning',
        'uom',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'security/ir_rule.xml',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/input.xml',
        'views/review.xml',
        'views/approve.xml',
        'views/position_field.xml',
        # 'data/ir_cron_data.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
