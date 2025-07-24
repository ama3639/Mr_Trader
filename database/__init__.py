# -*- coding: utf-8 -*-
# =========================
# database/__init__.py  
# =========================
"""
ماژول مدیریت دیتابیس
"""

try:
    from .database_manager import DatabaseManager
    __all__ = ['DatabaseManager']
except ImportError as e:
    print(f"Warning: Could not import DatabaseManager: {e}")
    __all__ = []
