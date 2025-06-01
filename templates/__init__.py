# -*- coding: utf-8 -*-
# ====================
# فایل: templates/__init__.py
# ====================


"""
قالب‌های پیام و کیبورد برای MrTrader Bot
"""

try:
    from .keyboards import KeyboardTemplates
    from .messages import MessageTemplates
    __all__ = ['KeyboardTemplates', 'MessageTemplates']
except ImportError as e:
    print(f"Warning: Could not import template modules: {e}")
    __all__ = []
