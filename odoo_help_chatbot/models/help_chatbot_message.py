# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpChatbotMessage(models.Model):
    _name = 'help.chatbot.message'
    _description = 'Help Chatbot Message'
    _order = 'create_date asc'

    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        default=lambda self: self.env.user, ondelete='cascade',
        index=True,
    )
    role = fields.Selection(
        selection=[
            ('user', 'User'),
            ('assistant', 'Assistant'),
        ],
        string='Role', required=True,
    )
    content = fields.Text(string='Content', required=True)
    session_id = fields.Char(
        string='Session ID', index=True,
        help='Groups messages into a conversation session',
    )
