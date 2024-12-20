{
    "name": "BCR Operational Actual",
    "version": "1.0",
    "author": "IT MNC Energy",
    "category": "bcr",
    "summary": "Operational Actual BCR",
    "description": """

    """,
    "depends": [
        'bcr_operational',
    ],
    "data": [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/act_operational_views.xml',
        'views/act_delay_views.xml',
        'views/act_inventory_views.xml',
        'views/act_survey_views.xml',
        'views/act_stockopname_views.xml',
        'views/menuitem.xml',
    ],
}
