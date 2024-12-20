{
    'name': 'Legal of MNC Energy Invenstments',
    'version': '12.0.0.0.0',
    'license': 'OPL-1',
    'summary': "Legal Document",
    'author': "Andi - IT MNCEI",
    'website': "https://mncenergy.com",
    'support': '',
    'description': '''
        Manage Dokument in MNCEI
    ''',
    'depends': [
        'base',
        'mail',
        'hr_skills'
    ],
    'data': [
        'data/data.xml',
        'data/resume_datas.xml',
        'data/email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/input_email.xml',
        # 'views/templates.xml',
        'views/doc_perizinan_views.xml',
        'views/laporan_views.xml',
        'views/mncei_doc.xml',
        'views/doc_addons_views.xml',
        # 'views/res_company_views.xml',
    ],
    'qweb': [
        'static/src/xml/resume_templates.xml',
    ],
    'images': [],
    'application': True,
}
