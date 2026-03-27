# -*- coding: utf-8 -*-
{
    'name': "auto_backup_qiniu",

    'summary': "Database backup upload to Qiniu Cloud",

    'description': """
                                                                                                                                                                           Long description of module's purpose
                                                                                                                                                                               """,

    'author': "Penn Collins",
    'website': "https://echovoid.top",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services/backup',
    'version': '17.0.0.260328',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'external_dependencies': {
        'python': ['qiniu']
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/qiniu_backup_views.xml',
        'views/res_config_settings_inherit.xml',
        'data/ir_cron.xml',
    ],
    'sequence': 1,
    'auto_install': False,
    'installable': True,
    'application': True,
}
