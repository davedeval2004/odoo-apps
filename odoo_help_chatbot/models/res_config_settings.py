# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    helpbot_ai_provider = fields.Selection(
        selection=[
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('openrouter', 'OpenRouter'),
        ],
        string='AI Provider',
        config_parameter='odoo_help_chatbot.ai_provider',
        default='openrouter',
    )
    helpbot_api_key = fields.Char(
        string='API Key',
        config_parameter='odoo_help_chatbot.api_key',
    )
    helpbot_model_name = fields.Char(
        string='Model Name',
        config_parameter='odoo_help_chatbot.model_name',
        default='openai/gpt-4o',
        help='E.g. gpt-4o for OpenAI; '
             'claude-sonnet-4-20250514 for Anthropic; '
             'openai/gpt-4o, anthropic/claude-3.5-sonnet, '
             'google/gemini-2.0-flash-001, meta-llama/llama-3-70b-instruct for OpenRouter',
    )
    helpbot_max_tokens = fields.Integer(
        string='Max Tokens',
        config_parameter='odoo_help_chatbot.max_tokens',
        default=1024,
        help='Maximum tokens in the AI response',
    )
