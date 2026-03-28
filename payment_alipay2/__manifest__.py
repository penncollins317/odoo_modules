# -*- coding: utf-8 -*-
{
    'name': "payment_alipay2",
    'summary': "支付宝对接",
    'description': """
Long description of module's purpose
    """,
    'author': "Penn Collins",
    'website': "https://echovoid.top",
    'category': 'Accounting/Payment Providers',
    'version': '17.0.0.260328',
    'depends': ['payment'],
    'external_dependencies':{
        'python': ['alipay-sdk-python']
    },
    'data': [
        'views/payment_alipay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'application': True,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}

