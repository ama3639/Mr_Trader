# -*- coding: utf-8 -*-
# =========================
# handlers/__init__.py
# =========================
"""
هندلرهای پردازش پیام‌ها و callback ها
"""

__all__ = []

try:
    from .start_handler import StartHandler
    __all__.append('StartHandler')
except ImportError:
    print("Warning: Could not import StartHandler")

try:
    from .callback_handlers import CallbackHandler
    __all__.append('CallbackHandler')
except ImportError:
    print("Warning: Could not import CallbackHandler")

try:
    from .message_handlers import MessageHandler
    __all__.append('MessageHandler')
except ImportError:
    print("Warning: Could not import MessageHandler")
