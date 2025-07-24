# -*- coding: utf-8 -*-
# =========================
# managers/__init__.py
# =========================
"""
مدیریت‌کننده‌های مختلف سیستم
"""


# Import managers one by one with error handling
__all__ = []

try:
    from .user_manager import UserManager
    __all__.append('UserManager')
except ImportError:
    print("Warning: Could not import UserManager")

try:
    from .admin_manager import AdminManager
    __all__.append('AdminManager')
except ImportError:
    print("Warning: Could not import AdminManager")

try:
    from .security_manager import SecurityManager
    __all__.append('SecurityManager')
except ImportError:
    print("Warning: Could not import SecurityManager")

try:
    from .referral_manager import ReferralManager
    __all__.append('ReferralManager')
except ImportError:
    print("Warning: Could not import ReferralManager")

try:
    from .settings_manager import SettingsManager
    __all__.append('SettingsManager')
except ImportError:
    print("Warning: Could not import SettingsManager")

try:
    from .message_manager import MessageManager
    __all__.append('MessageManager')
except ImportError:
    print("Warning: Could not import MessageManager")

try:
    from .payment_manager import PaymentManager
    __all__.append('PaymentManager')
except ImportError:
    print("Warning: Could not import PaymentManager")

try:
    from .symbol_manager import SymbolManager
    __all__.append('SymbolManager')
except ImportError:
    print("Warning: Could not import SymbolManager")

try:
    from .strategy_manager import StrategyManager
    __all__.append('StrategyManager')
except ImportError:
    print("Warning: Could not import StrategyManager")

try:
    from .report_manager import ReportManager
    __all__.append('ReportManager')
except ImportError:
    print("Warning: Could not import ReportManager")

try:
    from .backup_manager import BackupManager
    __all__.append('BackupManager')
except ImportError:
    print("Warning: Could not import BackupManager")
