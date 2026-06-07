# -*- coding: utf-8 -*-
{
    'name': 'Help Chatbot',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'AI-powered Help Chatbot for Odoo Business Process Guidance',
    'description': """
        Adds a Help button in the systray that opens an AI-powered chatbot.
        The chatbot helps non-technical users solve Odoo issues using
        simple, business-friendly language with step-by-step guidance.

        Supported AI Providers:
        - OpenAI (GPT-4o, GPT-4, GPT-3.5-turbo)
        - Anthropic (Claude)
    """,
    'author': 'Custom',
    'website': '',
    'depends': ['web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_config_parameter_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_help_chatbot/static/src/scss/help_chatbot.scss',
            'odoo_help_chatbot/static/src/xml/help_chatbot_systray.xml',
            'odoo_help_chatbot/static/src/js/help_chatbot_systray.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
