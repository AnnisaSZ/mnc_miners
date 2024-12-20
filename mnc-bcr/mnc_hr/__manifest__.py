{
    'name': 'HR of MNC Energy Invenstments',
    'version': '14.0.0.0.0',
    'license': 'OPL-1',
    'summary': "HR",
    'author': "Andi-IT MNCEI",
    'website': "https://mncenergy.com",
    'support': '',
    'description': '''
        Manage Employee in MNC Energy Invenstments
    ''',
    'depends': [
        'base',
        'mail',
        'web_tree_image_tooltip',
        'base_field_big_int'
    ],
    'data': [
        'data/data.xml',
        'data/email_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/assets.xml',
        'views/mncei_employee.xml',
        'views/addons_hr_views.xml',
        'views/menu_items.xml',
        'wizard/employee_resign_views.xml',
    ],
    'images': [],
    'application': True,
}
