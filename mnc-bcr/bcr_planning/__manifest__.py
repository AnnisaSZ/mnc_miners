{
    "name": "BCR Process",
    "version": "1.0",
    "author": "MNC",
    "category": "bcr",
    "summary": "Process BCR",
    "description": """ 
        
    """,
    "depends": [
        'bcr_master',
    ],
    "data": [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',

        'views/menu.xml',
        'views/planning_production.xml',
        'views/planning_hauling.xml',
        'views/planning_barging.xml',
        'views/act_production.xml',
        'views/act_hauling.xml',
        'views/act_delay.xml',
        'views/act_stockroom.xml',
        'views/act_barging.xml',
        'views/fuel_dump_truck.xml',
        'views/fuel_excavator.xml',
        'views/fuel_kendaraan_alat.xml',
        'views/fuel_kendaraan_mobil.xml',
    ],
    "qweb": [],
    "image": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
