{
    'name': "Document Archive",
    'summary': """Document Archive System""",
    'description': """
        Document Archive System MNC Energy Investments:
            -Document Archive System
    """,

    'author': "it coals",
    'website': "https://mncenergy.com",
    'category': "Document Archive",
    'version': '0.1',

    # any module necessary for this one to work corectly
    'depends': [
        'mnc_hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/arsip_dokumen.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}