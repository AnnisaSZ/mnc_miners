{
    'name': "Project Ext",
    'summary': """Project""",
    'description': """
       Project Extention Modules
    """,

    'author': "IT MNC Energy Investments",
    'website': "https://mncenergy.com",
    'category': "Project",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'project',
    ],
    # always loaded
    'data': [
        'data/datas.xml',
        'security/ir.model.access.csv',
        'views/project_stage.xml',
    ],
    # only loaded in demonstration mode
    'application': False,
}
