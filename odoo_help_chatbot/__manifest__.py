# -*- coding: utf-8 -*-
{
    'name': 'Help Chatbot',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'AI-powered Help Chatbot for Odoo Business Process Guidance',

    'description': """
Help Chatbot

An AI-powered assistant for Odoo users that provides business-friendly,
step-by-step guidance for common Odoo operations and troubleshooting.

Features:
- Systray Help Button
- AI-powered Chat Assistant
- Business-friendly Responses
- Odoo Process Guidance
- OpenAI Integration
- Anthropic Claude Integration
- Configurable AI Models
- Secure User Access Control

Supported Providers:
- OpenAI (GPT-4o, GPT-4, GPT-3.5 Turbo)
- Anthropic Claude
    """,

    'author': 'Flowient',
    'website':'http://www.floient.in',
    'maintainer': 'Flowient',
    'license': 'LGPL-3',
    'price': 10.00,
    'currency': 'USD',
    'depends': ['web','mail'],
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
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}