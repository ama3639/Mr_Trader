# -*- coding: utf-8 -*-
# =========================
# api/__init__.py
# =========================
"""
ماژول ارتباط با API های خارجی
"""

try:
    from .api_client import ApiClient, api_client
    __all__ = ['ApiClient', 'api_client']
except ImportError as e:
    print(f"Warning: Could not import API client: {e}")
    __all__ = []

