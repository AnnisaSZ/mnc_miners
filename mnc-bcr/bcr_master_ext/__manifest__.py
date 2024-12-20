{
    "name": "BCR Master - Extention",
    "version": "1.0",
    "author": "IT MNC Energy",
    "category": "bcr",
    "summary": "Master Operational",
    "description": """

    """,
    "depends": [
        # 'bcr_master',
        'bcr_master_custom_sh'
    ],
    "data": [
        # 'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/jetty_views.xml',
        'views/partner_views.xml',
        'views/shift_mode_views.xml',
        'views/source_views.xml',
    ],
}
