# -*- coding: utf-8 -*-
import base64
import json
import logging
import uuid

import requests

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the "Odoo Business Process Specialist".
You are an expert in Odoo versions 17, 18, and 19. Your role is to help NON-TECHNICAL USERS solve Odoo issues using simple, business-friendly language.
You are part of an Odoo system where a configured AI service generates responses to user questions triggered from a "Help" button.

YOUR OBJECTIVE:

When a user asks a question or faces an issue:
- Explain the problem in simple terms
- Guide them step-by-step using Odoo navigation
- Explain the business reason (WHY)
- Help them avoid the issue in future

If the user shares a screenshot or image:
- Analyze it carefully to understand the context
- Identify the Odoo screen, error message, or workflow shown
- Provide specific guidance based on what you see

You act as a bridge between:
System errors / confusing behavior (no)
Clear business actions (yes)

STRICT RULES:

1. NO TECHNICAL CONTENT
- Do NOT provide code (Python, XML, SQL)
- Do NOT mention database fields or backend logic
- If user asks for technical fix:
  Say: "Please contact your Odoo developer."

2. SIMPLIFY ERRORS
Translate system errors into human meaning:
- Validation Error → Missing required information
- Access Error → Permission issue
- Integrity Error → Data conflict

3. USE NAVIGATION PATHS:
Always use:
[App] > [Menu] > [Submenu]

Example:
Sales > Orders > Quotations

4. EXPLAIN "WHY":
Always include the business reason:
- Accounting rules
- Inventory availability
- Workflow steps

5. STEP-BY-STEP FIX:
Use numbered steps only

6. KEEP IT SIMPLE:
- Short sentences
- No jargon
- Easy English

7. USER-FIRST APPROACH:
Assume the user:
- Is non-technical
- Just wants to complete their task

RESPONSE FORMAT (MANDATORY):

----------------------------------------

The Issue:
(Simple explanation)

The Fix:
1. Step-by-step navigation
2. Clear actions
3. Minimal steps

Why This Happens:
(Business explanation)

Pro Tip:
(Prevention tip)

----------------------------------------

FINAL BEHAVIOR:
- Be clear, practical, and helpful
- Focus only on business workflows
- Do not mention AI provider
- Do not mention system internals"""


class HelpChatbotController(http.Controller):

    def _get_config(self):
        ICP = request.env['ir.config_parameter'].sudo()
        return {
            'provider': ICP.get_param('odoo_help_chatbot.ai_provider', 'openrouter'),
            'api_key': ICP.get_param('odoo_help_chatbot.api_key', ''),
            'model_name': ICP.get_param('odoo_help_chatbot.model_name', 'openai/gpt-4o'),
            'max_tokens': int(ICP.get_param('odoo_help_chatbot.max_tokens', '1024')),
        }

    def _get_conversation_history(self, session_id, limit=20):
        """Text-only history. Images are NOT resent to save tokens."""
        messages = request.env['help.chatbot.message'].search(
            [('user_id', '=', request.env.user.id), ('session_id', '=', session_id)],
            order='create_date asc', limit=limit,
        )
        return [{'role': m.role, 'content': m.content} for m in messages]

    # ── vision content builders ────────────────────────────────────────

    @staticmethod
    def _parse_image_data(image_data):
        """Return (mime, base64_str) from a data-url or raw base64."""
        if image_data.startswith('data:'):
            header, b64 = image_data.split(',', 1)
            mime = header.split(':')[1].split(';')[0]
        else:
            b64 = image_data
            mime = 'image/png'
        return mime, b64

    def _build_openai_content(self, question, image_data=None):
        """OpenAI / OpenRouter vision format."""
        if not image_data:
            return question
        mime, b64 = self._parse_image_data(image_data)
        content = [
            {'type': 'image_url', 'image_url': {'url': f"data:{mime};base64,{b64}", 'detail': 'auto'}},
            {'type': 'text', 'text': question or 'Please analyze this screenshot and help me with what you see.'},
        ]
        return content

    def _build_anthropic_content(self, question, image_data=None):
        """Anthropic vision format."""
        if not image_data:
            return question
        mime, b64 = self._parse_image_data(image_data)
        content = [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': b64}},
            {'type': 'text', 'text': question or 'Please analyze this screenshot and help me with what you see.'},
        ]
        return content

    # ── provider callers ───────────────────────────────────────────────

    def _call_openai(self, config, messages):
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Authorization': f"Bearer {config['api_key']}", 'Content-Type': 'application/json'}
        payload = {'model': config['model_name'], 'messages': messages,
                   'max_tokens': config['max_tokens'], 'temperature': 0.7}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            raise Exception(_('The AI service is taking too long. Please try again.'))
        except requests.exceptions.HTTPError as e:
            _logger.error('OpenAI error: %s %s', e.response.status_code, e.response.text)
            if e.response.status_code == 401:
                raise Exception(_('Invalid API key. Check Settings.'))
            if e.response.status_code == 429:
                raise Exception(_('Rate limit reached. Wait and retry.'))
            raise Exception(_('AI service error. Try again later.'))
        except Exception as e:
            if 'Invalid API key' in str(e) or 'rate limit' in str(e):
                raise
            raise Exception(_('Could not connect to AI service.'))

    def _call_anthropic(self, config, messages):
        url = 'https://api.anthropic.com/v1/messages'
        headers = {'x-api-key': config['api_key'], 'Content-Type': 'application/json',
                   'anthropic-version': '2023-06-01'}
        api_messages = [m for m in messages if m['role'] != 'system']
        system_content = next((m['content'] for m in messages if m['role'] == 'system'), '')
        payload = {'model': config['model_name'], 'max_tokens': config['max_tokens'],
                   'system': system_content, 'messages': api_messages}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()['content'][0]['text']
        except requests.exceptions.Timeout:
            raise Exception(_('The AI service is taking too long. Please try again.'))
        except requests.exceptions.HTTPError as e:
            _logger.error('Anthropic error: %s %s', e.response.status_code, e.response.text)
            if e.response.status_code == 401:
                raise Exception(_('Invalid API key. Check Settings.'))
            if e.response.status_code == 429:
                raise Exception(_('Rate limit reached. Wait and retry.'))
            raise Exception(_('AI service error. Try again later.'))
        except Exception as e:
            if 'Invalid API key' in str(e) or 'rate limit' in str(e):
                raise
            raise Exception(_('Could not connect to AI service.'))

    def _call_openrouter(self, config, messages):
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {'Authorization': f"Bearer {config['api_key']}", 'Content-Type': 'application/json',
                   'HTTP-Referer': 'https://odoo.com', 'X-Title': 'Odoo Help Chatbot'}
        payload = {'model': config['model_name'], 'messages': messages,
                   'max_tokens': config['max_tokens'], 'temperature': 0.7}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            raise Exception(_('The AI service is taking too long. Please try again.'))
        except requests.exceptions.HTTPError as e:
            _logger.error('OpenRouter error: %s %s', e.response.status_code, e.response.text)
            if e.response.status_code == 401:
                raise Exception(_('Invalid API key. Check Settings.'))
            if e.response.status_code == 429:
                raise Exception(_('Rate limit reached. Wait and retry.'))
            if e.response.status_code == 402:
                raise Exception(_('Insufficient OpenRouter credits.'))
            raise Exception(_('AI service error. Try again later.'))
        except Exception as e:
            if any(x in str(e) for x in ('Invalid API key', 'rate limit', 'credits')):
                raise
            raise Exception(_('Could not connect to AI service.'))

    # ── routes ─────────────────────────────────────────────────────────

    @http.route('/help_chatbot/ask', type='jsonrpc', auth='user')
    def ask(self, question, session_id=None, image_data=None):
        """Handle user question with optional image attachment."""
        config = self._get_config()
        if not config['api_key']:
            return {'error': True,
                    'message': _('AI service is not configured. Please ask your administrator '
                                 'to set up the API key in Settings > General Settings > Help Chatbot.')}
        if not session_id:
            session_id = str(uuid.uuid4())

        # Save user message (text only for DB storage)
        display = question or ''
        if image_data:
            display = ('[Screenshot attached] ' + display).strip()
        request.env['help.chatbot.message'].create({
            'user_id': request.env.user.id, 'role': 'user',
            'content': display, 'session_id': session_id,
        })

        # Build messages: system + history (text only) + current (with image)
        history = self._get_conversation_history(session_id)
        if history:
            history = history[:-1]  # remove just-saved msg

        if config['provider'] == 'anthropic':
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
            for h in history:
                messages.append({'role': h['role'], 'content': h['content']})
            messages.append({'role': 'user',
                             'content': self._build_anthropic_content(question, image_data)})
        else:
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
            for h in history:
                messages.append({'role': h['role'], 'content': h['content']})
            messages.append({'role': 'user',
                             'content': self._build_openai_content(question, image_data)})

        try:
            if config['provider'] == 'openai':
                answer = self._call_openai(config, messages)
            elif config['provider'] == 'anthropic':
                answer = self._call_anthropic(config, messages)
            elif config['provider'] == 'openrouter':
                answer = self._call_openrouter(config, messages)
            else:
                return {'error': True, 'message': _('Unknown AI provider.')}

            request.env['help.chatbot.message'].create({
                'user_id': request.env.user.id, 'role': 'assistant',
                'content': answer, 'session_id': session_id,
            })
            return {'error': False, 'answer': answer, 'session_id': session_id}
        except Exception as e:
            _logger.error('Help Chatbot error: %s', str(e))
            return {'error': True, 'message': str(e)}

    @http.route('/help_chatbot/history', type='jsonrpc', auth='user')
    def get_history(self, session_id=None):
        domain = [('user_id', '=', request.env.user.id)]
        if session_id:
            domain.append(('session_id', '=', session_id))
        else:
            latest = request.env['help.chatbot.message'].search(
                [('user_id', '=', request.env.user.id)], order='create_date desc', limit=1)
            if latest and latest.session_id:
                domain.append(('session_id', '=', latest.session_id))
                session_id = latest.session_id
            else:
                return {'messages': [], 'session_id': None}
        messages = request.env['help.chatbot.message'].search(domain, order='create_date asc')
        return {
            'messages': [{'role': m.role, 'content': m.content,
                          'timestamp': m.create_date.isoformat() if m.create_date else ''}
                         for m in messages],
            'session_id': session_id,
        }

    @http.route('/help_chatbot/new_session', type='jsonrpc', auth='user')
    def new_session(self):
        return {'session_id': str(uuid.uuid4())}

    @http.route('/help_chatbot/clear_history', type='jsonrpc', auth='user')
    def clear_history(self, session_id=None):
        domain = [('user_id', '=', request.env.user.id)]
        if session_id:
            domain.append(('session_id', '=', session_id))
        request.env['help.chatbot.message'].search(domain).unlink()
        return {'success': True}
