{
    "name": "BCR Operational Planning",
    "version": "1.0",
    "author": "IT MNC Energy",
    "category": "bcr",
    "summary": "Operational Planning BCR",
    "description": """

    """,
    "depends": [
        'base',
        'mail',
        'bcr_master_ext',
        'bcr_planning',
    ],
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/data.xml',
        'views/master_menu.xml',
        'views/planning_opr_views.xml',
        'views/validation_views.xml',
        'views/menuitem.xml',
    ],
}
