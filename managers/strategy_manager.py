"""
مدیریت استراتژی‌های معاملاتی و بررسی دسترسی پکیج‌ها
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta

from core.config import Config
from utils.logger import logger
from database.database_manager import database_manager
from managers.settings_manager import settings_manager


class PackageLevel(Enum):
    """سطوح پکیج‌های دسترسی"""
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"


class StrategyCategory(Enum):
    """دسته‌بندی استراتژی‌ها"""
    PRICE_ACTION = "price_action"
    MARTINGALE = "martingale"
    CUP_HANDLE = "cup_handle"
    ICHIMOKU = "ichimoku"
    FIBONACCI = "fibonacci"
    KOMO_PLUS = "komo_plus"


class StrategyManager:
    """مدیریت استراتژی‌ها و کنترل دسترسی"""
    
    # نام‌های نمایشی استراتژی‌ها
    STRATEGY_DISPLAY_NAMES = {
        StrategyCategory.PRICE_ACTION: "تحلیل پرایس اکشن",
        StrategyCategory.MARTINGALE: "استراتژی مارتینگل", 
        StrategyCategory.CUP_HANDLE: "الگوی کاپ اند هندل",
        StrategyCategory.ICHIMOKU: "ابر ایچیموکو",
        StrategyCategory.FIBONACCI: "فیبوناچی ریتریسمنت",
        StrategyCategory.KOMO_PLUS: "استراتژی کومو پلاس",
    }
    
    @classmethod
    def get_user_package_level(cls, user_id: int) -> Optional[PackageLevel]:
        """دریافت سطح پکیج کاربر"""
        try:
            user_data = database_manager.get_user_by_telegram_id(user_id)
            if not user_data:
                return None
                
            package_type = user_data.get('package', 'none')
            if package_type == 'none':
                return None
                
            # تبدیل نام پکیج به enum
            package_mapping = {
                'basic': PackageLevel.BASIC,
                'premium': PackageLevel.PREMIUM,
                'vip': PackageLevel.VIP,
                'ghost': PackageLevel.GHOST,
            }
            
            return package_mapping.get(package_type.lower())
            
        except Exception as e:
            logger.error(f"Error getting user package level: {e}")
            return None
    
    @classmethod
    def is_package_expired(cls, user_id: int) -> bool:
        """بررسی انقضای پکیج کاربر"""
        try:
            user_data = database_manager.get_user_by_telegram_id(user_id)
            if not user_data:
                return True
                
            package_expiry = user_data.get('package_expiry')
            if not package_expiry:
                return True
                
            # تبدیل رشته به datetime
            if isinstance(package_expiry, str):
                expiry_date = datetime.fromisoformat(package_expiry)
            else:
                expiry_date = package_expiry
                
            return datetime.now() > expiry_date
            
        except Exception as e:
            logger.error(f"Error checking package expiry: {e}")
            return True
    
    @classmethod
    def check_strategy_access(cls, user_id: int, strategy: str) -> Tuple[bool, str]:
        """
        بررسی دسترسی کاربر به استراتژی مشخص
        
        Returns:
            Tuple[bool, str]: (دسترسی دارد, پیام)
        """
        try:
            # بررسی وجود استراتژی
            available_strategies = settings_manager.get_all_strategies()
            if strategy not in available_strategies:
                return False, "استراتژی نامعتبر است."
            
            # دریافت سطح پکیج کاربر
            user_package = cls.get_user_package_level(user_id)
            if not user_package:
                return False, (
                    "🚫 **دسترسی محدود**\n\n"
                    "برای استفاده از این استراتژی نیاز به خرید پکیج دارید.\n"
                    "لطفاً یکی از پکیج‌های موجود را خریداری کنید."
                )
            
            # بررسی انقضای پکیج
            if cls.is_package_expired(user_id):
                return False, (
                    "⏰ **پکیج منقضی شده**\n\n"
                    "پکیج شما منقضی شده است.\n"
                    "برای ادامه استفاده، لطفاً پکیج خود را تمدید کنید."
                )
            
            # بررسی دسترسی به استراتژی
            user_package_name = user_package.value
            if not settings_manager.is_strategy_allowed_for_package(strategy, user_package_name):
                # پیدا کردن کمترین پکیج مورد نیاز
                strategy_package_levels = settings_manager.get_strategy_package_levels(strategy)
                
                if strategy_package_levels:
                    # پیدا کردن پایین‌ترین سطح مورد نیاز
                    package_levels_map = {
                        "basic": 1, "premium": 2, "vip": 3, "ghost": 4
                    }
                    
                    min_level = min(package_levels_map.get(pkg, 4) for pkg in strategy_package_levels)
                    required_package_name = next(
                        (pkg for pkg, level in package_levels_map.items() if level == min_level), 
                        "premium"
                    )
                    
                    package_names = {
                        "basic": "بیسیک",
                        "premium": "پریمیوم", 
                        "vip": "وی‌آی‌پی",
                        "ghost": "گوست"
                    }
                    
                    return False, (
                        f"🔒 **دسترسی محدود**\n\n"
                        f"این استراتژی نیاز به پکیج **{package_names.get(required_package_name, required_package_name)}** یا بالاتر دارد.\n"
                        f"پکیج فعلی شما: **{package_names.get(user_package_name, user_package_name)}**\n\n"
                        f"برای دسترسی، لطفاً پکیج خود را ارتقا دهید."
                    )
            
            return True, "دسترسی تأیید شد."
            
        except Exception as e:
            logger.error(f"Error checking strategy access: {e}")
            return False, "خطا در بررسی دسترسی. لطفاً دوباره تلاش کنید."
    
    @classmethod
    def get_strategy_display_name(cls, strategy: str) -> str:
        """دریافت نام نمایشی استراتژی"""
        try:
            strategy_config = settings_manager.get_strategy_config(strategy)
            if strategy_config:
                return strategy_config.get("name", strategy)
            
            # اگر در تنظیمات نیست، از نام‌های پیش‌فرض استفاده کن
            for category in StrategyCategory:
                if category.value == strategy:
                    return cls.STRATEGY_DISPLAY_NAMES.get(category, strategy)
            
            return strategy
        except Exception:
            return strategy
    
    @classmethod
    def get_available_strategies_for_user(cls, user_id: int) -> List[str]:
        """دریافت لیست استراتژی‌های در دسترس کاربر"""
        try:
            user_package = cls.get_user_package_level(user_id)
            if not user_package:
                return []
            
            if cls.is_package_expired(user_id):
                return []
            
            # دریافت استراتژی‌های پکیج کاربر
            user_package_name = user_package.value
            available_strategies = settings_manager.get_package_strategies(user_package_name)
            
            return available_strategies
            
        except Exception as e:
            logger.error(f"Error getting available strategies: {e}")
            return []
    
    @classmethod
    def get_strategy_api_endpoint(cls, strategy: str) -> Optional[str]:
        """دریافت آدرس API برای استراتژی مشخص"""
        try:
            return settings_manager.get_strategy_url(strategy)
        except Exception as e:
            logger.error(f"Error getting strategy API endpoint: {e}")
            return None
    
    @classmethod
    def get_strategy_timeout(cls, strategy: str) -> int:
        """دریافت timeout استراتژی"""
        try:
            return settings_manager.get_strategy_timeout(strategy)
        except Exception as e:
            logger.error(f"Error getting strategy timeout: {e}")
            return 30
    
    @classmethod
    def get_strategy_retry_count(cls, strategy: str) -> int:
        """دریافت تعداد تلاش مجدد استراتژی"""
        try:
            return settings_manager.get_strategy_retry_count(strategy)
        except Exception as e:
            logger.error(f"Error getting strategy retry count: {e}")
            return 3
    
    @classmethod
    def get_strategy_cache_duration(cls, strategy: str) -> int:
        """دریافت مدت کش استراتژی"""
        try:
            return settings_manager.get_strategy_cache_duration(strategy)
        except Exception as e:
            logger.error(f"Error getting strategy cache duration: {e}")
            return 60
    
    @classmethod
    def get_package_hierarchy(cls) -> Dict[PackageLevel, List[PackageLevel]]:
        """دریافت سلسله مراتب پکیج‌ها (پکیج بالاتر دسترسی به پایین‌تر دارد)"""
        return {
            PackageLevel.BASIC: [PackageLevel.BASIC],
            PackageLevel.PREMIUM: [PackageLevel.BASIC, PackageLevel.PREMIUM],
            PackageLevel.VIP: [PackageLevel.BASIC, PackageLevel.PREMIUM, PackageLevel.VIP],
            PackageLevel.GHOST: [PackageLevel.BASIC, PackageLevel.PREMIUM, PackageLevel.VIP, PackageLevel.GHOST],
        }
    
    @classmethod
    def get_strategy_description(cls, strategy: str) -> str:
        """دریافت توضیحات استراتژی"""
        try:
            strategy_config = settings_manager.get_strategy_config(strategy)
            if strategy_config and "description" in strategy_config:
                return strategy_config["description"]
            
            # توضیحات پیش‌فرض
            descriptions = {
                "price_action": "تحلیل حرکت قیمت و شناسایی الگوهای کندلی",
                "martingale": "استراتژی مدیریت ریسک مارتینگل با ریسک کم",
                "cup_handle": "شناسایی الگوی برگشتی کاپ اند هندل",
                "ichimoku": "تحلیل کامل با سیستم ابر ایچیموکو",
                "fibonacci": "سطوح حمایت و مقاومت فیبوناچی",
                "komo_plus": "استراتژی پیشرفته کومو پلاس"
            }
            
            return descriptions.get(strategy, "استراتژی تحلیل تکنیکال")
            
        except Exception as e:
            logger.error(f"Error getting strategy description: {e}")
            return "استراتژی تحلیل تکنیکال"
    
    @classmethod
    def validate_strategy_parameters(cls, strategy: str, symbol: str, currency: str, timeframe: str) -> Tuple[bool, str]:
        """اعتبارسنجی پارامترهای استراتژی"""
        try:
            # بررسی نماد
            if not symbol or len(symbol) < 2:
                return False, "نماد ارز نامعتبر است"
            
            # بررسی ارز مرجع
            supported_currencies = Config.SUPPORTED_CURRENCIES
            if currency.upper() not in supported_currencies:
                return False, f"ارز مرجع باید یکی از موارد زیر باشد: {', '.join(supported_currencies)}"
            
            # بررسی تایم‌فریم
            supported_timeframes = Config.SUPPORTED_TIMEFRAMES
            if timeframe not in supported_timeframes:
                return False, f"تایم‌فریم باید یکی از موارد زیر باشد: {', '.join(supported_timeframes)}"
            
            # بررسی وجود استراتژی
            available_strategies = settings_manager.get_all_strategies()
            if strategy not in available_strategies:
                return False, "استراتژی انتخاب شده موجود نیست"
            
            return True, "پارامترها معتبر هستند"
            
        except Exception as e:
            logger.error(f"Error validating strategy parameters: {e}")
            return False, "خطا در اعتبارسنجی پارامترها"
    
    @classmethod
    def get_strategy_statistics(cls) -> Dict[str, Any]:
        """آمار استراتژی‌ها"""
        try:
            all_strategies = settings_manager.get_all_strategies()
            all_packages = settings_manager.get_all_packages()
            
            stats = {
                "total_strategies": len(all_strategies),
                "total_packages": len(all_packages),
                "strategies_by_package": {},
                "package_hierarchy": {}
            }
            
            # آمار استراتژی‌ها برای هر پکیج
            for package in all_packages:
                package_strategies = settings_manager.get_package_strategies(package)
                stats["strategies_by_package"][package] = {
                    "count": len(package_strategies),
                    "strategies": package_strategies
                }
                
                package_level = settings_manager.get_package_level(package)
                stats["package_hierarchy"][package] = package_level
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting strategy statistics: {e}")
            return {}
    
    @classmethod
    def is_strategy_available(cls, strategy: str) -> bool:
        """بررسی در دسترس بودن استراتژی"""
        try:
            # بررسی سلامت API
            if settings_manager.is_strategy_healthy(strategy):
                return True
            
            # بررسی وجود در لیست استراتژی‌ها
            available_strategies = settings_manager.get_all_strategies()
            return strategy in available_strategies
            
        except Exception as e:
            logger.error(f"Error checking strategy availability: {e}")
            return False