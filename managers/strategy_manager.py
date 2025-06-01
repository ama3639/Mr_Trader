"""
مدیریت استراتژی‌های معاملاتی و بررسی دسترسی پکیج‌ها
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import asyncio

from core.config import Config
from utils.logger import logger
from database.database_manager import database_manager
from managers.settings_manager import settings_manager
from api.api_client import api_client
from core.cache import cache


class PackageLevel(Enum):
    """سطوح پکیج‌های دسترسی"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"


class StrategyManager:
    """مدیریت استراتژی‌ها و کنترل دسترسی"""
    
    # نقشه کامل تمام 35 استراتژی
    ALL_STRATEGIES = {
        # DEMO (2 استراتژی)
        "demo_price_action": {
            "name": "دمو پرایس اکشن",
            "package": "free",
            "category": "demo",
            "difficulty": "دمو",
            "description": "نسخه دمو تحلیل حرکت قیمت - محدود به 5 تحلیل در روز"
        },
        "demo_rsi": {
            "name": "دمو RSI", 
            "package": "free",
            "category": "demo",
            "difficulty": "دمو",
            "description": "نسخه دمو شاخص قدرت نسبی - محدود به 5 تحلیل در روز"
        },
        
        # BASIC Package (9 استراتژی)
        "cci_analysis": {
            "name": "تحلیل CCI",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "شاخص کانال کالا برای تشخیص نقاط اشباع خرید و فروش"
        },
        "ema_analysis": {
            "name": "تحلیل EMA",
            "package": "basic",
            "category": "technical_indicators", 
            "difficulty": "مبتدی",
            "description": "میانگین متحرک نمایی برای تشخیص روند و نقاط ورود"
        },
        "ichimoku": {
            "name": "ابر ایچیموکو",
            "package": "basic",
            "category": "trend_analysis",
            "difficulty": "متوسط",
            "description": "سیستم جامع تحلیل ژاپنی با ابر ایچیموکو"
        },
        "ichimoku_low_signal": {
            "name": "سیگنال پایین ایچیموکو",
            "package": "basic",
            "category": "trend_analysis",
            "difficulty": "متوسط",
            "description": "سیگنال‌های کم ریسک و محافظه‌کارانه ایچیموکو"
        },
        "macd": {
            "name": "تحلیل MACD",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "واگرایی همگرایی میانگین متحرک برای تشخیص تغییر روند"
        },
        "price_action_pandas_ta": {
            "name": "پرایس اکشن pandas",
            "package": "basic",
            "category": "price_action",
            "difficulty": "مبتدی",
            "description": "تحلیل حرکت قیمت با کتابخانه pandas و اندیکاتورهای تکنیکال"
        },
        "project_price_live_binance": {
            "name": "قیمت زنده بایننس",
            "package": "basic",
            "category": "volume_analysis",
            "difficulty": "مبتدی",
            "description": "دریافت قیمت‌های زنده و تحلیل آنی از صرافی بایننس"
        },
        "rsi": {
            "name": "تحلیل RSI",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی", 
            "description": "شاخص قدرت نسبی برای شناسایی شرایط اشباع"
        },
        "williams_r_analysis": {
            "name": "تحلیل Williams R",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "اندیکاتور Williams %R برای تشخیص نقاط برگشت"
        },
        
        # PREMIUM Package (17 استراتژی اضافی)
        "a_candlestick": {
            "name": "تحلیل کندل استیک",
            "package": "premium",
            "category": "price_action",
            "difficulty": "پیشرفته",
            "description": "تشخیص و تحلیل الگوهای کندل استیک ژاپنی"
        },
        "b_pivot": {
            "name": "نقاط محوری",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "محاسبه و تحلیل نقاط محوری حمایت و مقاومت"
        },
        "bollinger_bands": {
            "name": "باندهای بولینگر",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "باندهای بولینگر برای تحلیل نوسانات و نقاط ورود"
        },
        "c_trend_lines": {
            "name": "خطوط روند",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "ترسیم و تحلیل خطوط روند و کانال‌های قیمتی"
        },
        "cup_handle": {
            "name": "الگوی کاپ اند هندل",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "شناسایی الگوی برگشتی کاپ اند هندل"
        },
        "double_top_pattern": {
            "name": "الگوی دو قله",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص الگوهای دو قله و دو کف برای پیش‌بینی برگشت روند"
        },
        "fibonacci_strategy": {
            "name": "استراتژی فیبوناچی",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "استفاده از سطوح فیبوناچی ریتریسمنت برای نقاط ورود"
        },
        "flag_pattern": {
            "name": "الگوی پرچم",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "شناسایی الگوی ادامه‌دهنده پرچم در روندهای قوی"
        },
        "head_shoulders_analysis": {
            "name": "الگوی سر و شانه",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تحلیل الگوی برگشتی سر و شانه"
        },
        "heikin_ashi": {
            "name": "کندل هایکن آشی",
            "package": "premium",
            "category": "price_action",
            "difficulty": "متخصص",
            "description": "تحلیل با کندل‌های هایکن آشی برای تشخیص روند"
        },
        "ichimoku_hi_signal": {
            "name": "سیگنال بالا ایچیموکو",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "سیگنال‌های قوی و پرریسک ایچیموکو"
        },
        "macd_divergence": {
            "name": "واگرایی MACD",
            "package": "premium",
            "category": "divergence_analysis",
            "difficulty": "متخصص",
            "description": "تشخیص واگرایی‌های MACD برای پیش‌بینی تغییر روند"
        },
        "martingale_low": {
            "name": "مارتینگل پایین",
            "package": "premium",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "استراتژی مارتینگل با ریسک پایین و مدیریت سرمایه"
        },
        "momentum": {
            "name": "تحلیل مومنتوم",
            "package": "premium",
            "category": "advanced_systems",
            "difficulty": "پیشرفته",
            "description": "تحلیل قدرت و مومنتوم حرکت قیمت"
        },
        "price_action_hi": {
            "name": "پرایس اکشن پیشرفته",
            "package": "premium",
            "category": "price_action",
            "difficulty": "پیشرفته",
            "description": "تحلیل پیشرفته حرکت قیمت با الگوهای پیچیده"
        },
        "stochastic": {
            "name": "تحلیل استوکاستیک",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "متخصص",
            "description": "نوسان‌گر استوکاستیک برای تشخیص اشباع و نقاط برگشت"
        },
        "triangle_pattern": {
            "name": "الگوی مثلث",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص انواع الگوهای مثلث صعودی، نزولی و متقارن"
        },
        "wedge_pattern": {
            "name": "الگوی گوه",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تحلیل الگوهای گوه صعودی و نزولی"
        },
        
        # VIP Package (9 استراتژی اضافی)
        "atr": {
            "name": "تحلیل ATR",
            "package": "vip",
            "category": "technical_indicators",
            "difficulty": "متخصص",
            "description": "میانگین دامنه واقعی برای محاسبه نوسانات و تنظیم stop loss"
        },
        "crt": {
            "name": "تحلیل CRT",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم تحلیل CRT پیشرفته برای شناسایی روندها"
        },
        "diamond_pattern": {
            "name": "الگوی الماس",
            "package": "vip",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص الگوی نادر و قوی الماس"
        },
        "multi_level_resistance": {
            "name": "مقاومت چند سطحی",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "تحلیل چند سطحی حمایت و مقاومت"
        },
        "p3": {
            "name": "تحلیل P3",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم تحلیل P3 برای پیش‌بینی نقاط عطف"
        },
        "rtm": {
            "name": "تحلیل RTM",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم RTM پیشرفته برای تحلیل ریسک و بازده"
        },
        "sma": {
            "name": "تحلیل SMA",
            "package": "vip",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "میانگین متحرک ساده با تحلیل‌های پیشرفته"
        },
        "volume_profile": {
            "name": "پروفایل حجم",
            "package": "vip",
            "category": "volume_analysis",
            "difficulty": "متخصص",
            "description": "تحلیل پروفایل حجم معاملات برای شناسایی نواحی مهم"
        },
        "vwap": {
            "name": "تحلیل VWAP",
            "package": "vip",
            "category": "volume_analysis",
            "difficulty": "متخصص",
            "description": "میانگین موزون حجمی برای شناسایی قیمت منصفانه"
        }
    }
    
    @classmethod
    def get_user_package_level(cls, user_id: int) -> Optional[PackageLevel]:
        """دریافت سطح پکیج کاربر"""
        try:
            user_data = database_manager.get_user_by_telegram_id(user_id)
            if not user_data:
                return PackageLevel.FREE
                
            package_type = user_data.get('package', 'free')
            if package_type == 'none' or not package_type:
                return PackageLevel.FREE
                
            # تبدیل نام پکیج به enum
            package_mapping = {
                'free': PackageLevel.FREE,
                'basic': PackageLevel.BASIC,
                'premium': PackageLevel.PREMIUM,
                'vip': PackageLevel.VIP,
                'ghost': PackageLevel.GHOST,
            }
            
            return package_mapping.get(package_type.lower(), PackageLevel.FREE)
            
        except Exception as e:
            logger.error(f"Error getting user package level: {e}")
            return PackageLevel.FREE
    
    @classmethod
    def is_package_expired(cls, user_id: int) -> bool:
        """بررسی انقضای پکیج کاربر"""
        try:
            user_data = database_manager.get_user_by_telegram_id(user_id)
            if not user_data:
                return True
                
            package_expiry = user_data.get('package_expiry')
            if not package_expiry:
                # اگر پکیج رایگان است، هرگز منقضی نمی‌شود
                package_type = user_data.get('package', 'free')
                return package_type != 'free'
                
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
        """بررسی دسترسی کاربر به استراتژی مشخص"""
        try:
            # بررسی وجود استراتژی
            if strategy not in cls.ALL_STRATEGIES:
                return False, "❌ استراتژی نامعتبر است."
            
            strategy_info = cls.ALL_STRATEGIES[strategy]
            required_package = strategy_info["package"]
            
            # دریافت سطح پکیج کاربر
            user_package = cls.get_user_package_level(user_id)
            if not user_package:
                user_package = PackageLevel.FREE
            
            user_package_name = user_package.value
            
            # کاربران رایگان فقط به دمو دسترسی دارند
            if user_package == PackageLevel.FREE:
                if strategy.startswith('demo_'):
                    return True, "دسترسی تأیید شد."
                else:
                    return False, (
                        "🚫 **دسترسی محدود**\n\n"
                        "برای استفاده از این استراتژی نیاز به خرید پکیج دارید.\n"
                        "🥉 پکیج Basic: 9 استراتژی اصلی\n"
                        "🥈 پکیج Premium: 26 استراتژی پیشرفته\n"
                        "👑 پکیج VIP: 35 استراتژی کامل\n\n"
                        "لطفاً یکی از پکیج‌های موجود را خریداری کنید."
                    )
            
            # بررسی انقضای پکیج (غیر از free)
            if cls.is_package_expired(user_id):
                return False, (
                    "⏰ **پکیج منقضی شده**\n\n"
                    "پکیج شما منقضی شده است.\n"
                    "برای ادامه استفاده، لطفاً پکیج خود را تمدید کنید."
                )
            
            # بررسی سطح دسترسی پکیج
            package_hierarchy = {
                "free": 0,
                "basic": 1, 
                "premium": 2,
                "vip": 3,
                "ghost": 4
            }
            
            user_level = package_hierarchy.get(user_package_name, 0)
            required_level = package_hierarchy.get(required_package, 3)
            
            if user_level < required_level:
                package_names = {
                    "basic": "🥉 بیسیک",
                    "premium": "🥈 پریمیوم", 
                    "vip": "👑 وی‌آی‌پی",
                    "ghost": "👻 گوست"
                }
                
                current_package_name = package_names.get(user_package_name, user_package_name)
                required_package_display = package_names.get(required_package, required_package)
                
                return False, (
                    f"🔒 **دسترسی محدود**\n\n"
                    f"این استراتژی نیاز به پکیج **{required_package_display}** یا بالاتر دارد.\n"
                    f"پکیج فعلی شما: **{current_package_name}**\n\n"
                    f"برای دسترسی، لطفاً پکیج خود را ارتقا دهید."
                )
            
            return True, "دسترسی تأیید شد."
            
        except Exception as e:
            logger.error(f"Error checking strategy access: {e}")
            return False, "❌ خطا در بررسی دسترسی. لطفاً دوباره تلاش کنید."
    
    @classmethod
    def check_timeframe_access(cls, user_id: int, timeframe: str) -> Tuple[bool, str]:
        """بررسی دسترسی کاربر به تایم‌فریم مشخص"""
        try:
            user_package = cls.get_user_package_level(user_id)
            if not user_package:
                user_package = PackageLevel.FREE
            
            user_package_name = user_package.value
            allowed_timeframes = Config.get_package_timeframes(user_package_name)
            
            if timeframe not in allowed_timeframes:
                return False, (
                    f"⏰ **تایم‌فریم محدود**\n\n"
                    f"تایم‌فریم {timeframe} برای پکیج {user_package_name} مجاز نیست.\n"
                    f"تایم‌فریم‌های مجاز: {', '.join(allowed_timeframes[:5])}{'...' if len(allowed_timeframes) > 5 else ''}\n\n"
                    f"برای دسترسی به همه تایم‌فریم‌ها، پکیج خود را ارتقا دهید."
                )
            
            return True, "تایم‌فریم مجاز است."
            
        except Exception as e:
            logger.error(f"Error checking timeframe access: {e}")
            return False, "❌ خطا در بررسی دسترسی تایم‌فریم."
    
    @classmethod
    def check_demo_usage_limit(cls, user_id: int) -> Tuple[bool, str, int]:
        """بررسی محدودیت استفاده از دمو"""
        try:
            # دریافت تعداد استفاده امروز
            today = datetime.now().date()
            usage_count = database_manager.get_demo_usage_count(user_id, today)
            
            if usage_count >= Config.DEMO_DAILY_LIMIT:
                return False, (
                    f"🚫 **محدودیت دمو**\n\n"
                    f"شما امروز {Config.DEMO_DAILY_LIMIT} تحلیل دمو انجام داده‌اید.\n"
                    f"برای دسترسی نامحدود، پکیج خود را ارتقا دهید."
                ), usage_count
            
            return True, "استفاده مجاز است.", usage_count
            
        except Exception as e:
            logger.error(f"Error checking demo usage limit: {e}")
            return False, "❌ خطا در بررسی محدودیت.", 0
    
    @classmethod
    def get_strategy_display_name(cls, strategy: str) -> str:
        """دریافت نام نمایشی استراتژی"""
        if strategy in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy]["name"]
        return strategy.replace('_', ' ').title()
    
    @classmethod
    def get_strategy_description(cls, strategy: str) -> str:
        """دریافت توضیحات استراتژی"""
        if strategy in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy]["description"]
        return "استراتژی تحلیل تکنیکال"
    
    @classmethod
    def get_strategy_category(cls, strategy: str) -> str:
        """دریافت دسته‌بندی استراتژی"""
        if strategy in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy]["category"]
        return "general"
    
    @classmethod
    def get_strategy_difficulty(cls, strategy: str) -> str:
        """دریافت سطح دشواری استراتژی"""
        if strategy in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy]["difficulty"]
        return "متوسط"
    
    @classmethod
    def get_available_strategies_for_user(cls, user_id: int) -> List[str]:
        """دریافت لیست استراتژی‌های در دسترس کاربر"""
        try:
            user_package = cls.get_user_package_level(user_id)
            if not user_package:
                return ["demo_price_action", "demo_rsi"]  # استراتژی‌های دمو
            
            if user_package == PackageLevel.FREE:
                return ["demo_price_action", "demo_rsi"]
            
            if cls.is_package_expired(user_id):
                return ["demo_price_action", "demo_rsi"]
            
            # دریافت استراتژی‌های پکیج کاربر
            user_package_name = user_package.value
            available_strategies = []
            
            package_hierarchy = {
                "basic": ["basic"],
                "premium": ["basic", "premium"],
                "vip": ["basic", "premium", "vip"],
                "ghost": ["basic", "premium", "vip", "ghost"]
            }
            
            allowed_packages = package_hierarchy.get(user_package_name, [])
            
            for strategy_key, strategy_info in cls.ALL_STRATEGIES.items():
                if strategy_info["package"] in allowed_packages:
                    available_strategies.append(strategy_key)
            
            return available_strategies
            
        except Exception as e:
            logger.error(f"Error getting available strategies: {e}")
            return []
    
    @classmethod
    def get_strategies_by_package(cls, package_name: str) -> List[Dict[str, Any]]:
        """دریافت استراتژی‌های دسته‌بندی شده بر اساس پکیج"""
        try:
            strategy_list = []
            
            for strategy_key, strategy_info in cls.ALL_STRATEGIES.items():
                if strategy_info["package"] == package_name:
                    strategy_list.append({
                        "key": strategy_key,
                        "name": strategy_info["name"],
                        "description": strategy_info["description"],
                        "category": strategy_info["category"],
                        "difficulty": strategy_info["difficulty"]
                    })
            
            return strategy_list
            
        except Exception as e:
            logger.error(f"Error getting strategies by package: {e}")
            return []
    
    @classmethod
    def validate_strategy_parameters(cls, strategy: str, symbol: str, currency: str, timeframe: str) -> Tuple[bool, str]:
        """اعتبارسنجی پارامترهای استراتژی"""
        try:
            # بررسی استراتژی
            if strategy not in cls.ALL_STRATEGIES:
                return False, "❌ استراتژی نامعتبر است"
            
            # بررسی نماد
            if not symbol or len(symbol) < 2:
                return False, "❌ نماد ارز نامعتبر است"
            
            # بررسی ارز مرجع
            if currency.upper() not in Config.SUPPORTED_CURRENCIES:
                return False, f"❌ ارز مرجع باید یکی از موارد زیر باشد: {', '.join(Config.SUPPORTED_CURRENCIES)}"
            
            # بررسی تایم‌فریم
            if timeframe not in Config.SUPPORTED_TIMEFRAMES:
                return False, f"❌ تایم‌فریم باید یکی از موارد زیر باشد: {', '.join(Config.SUPPORTED_TIMEFRAMES[:8])}"
            
            return True, "✅ پارامترها معتبر هستند"
            
        except Exception as e:
            logger.error(f"Error validating strategy parameters: {e}")
            return False, "❌ خطا در اعتبارسنجی پارامترها"
    
    @classmethod
    async def analyze_strategy(cls, user_id: int, strategy: str, symbol: str, currency: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """انجام تحلیل استراتژی با مدیریت کش"""
        try:
            # بررسی دسترسی
            has_access, access_message = cls.check_strategy_access(user_id, strategy)
            if not has_access:
                return {"error": access_message}
            
            # بررسی تایم‌فریم
            timeframe_allowed, timeframe_message = cls.check_timeframe_access(user_id, timeframe)
            if not timeframe_allowed:
                return {"error": timeframe_message}
            
            # بررسی محدودیت دمو
            if strategy.startswith('demo_'):
                can_use_demo, demo_message, usage_count = cls.check_demo_usage_limit(user_id)
                if not can_use_demo:
                    return {"error": demo_message}
            
            # بررسی کش
            cache_key = f"analysis_{strategy}_{symbol}_{currency}_{timeframe}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for {cache_key}")
                cached_result["is_cached"] = True
                return cached_result
            
            # فراخوانی API
            try:
                analysis_data = await api_client.fetch_strategy_analysis(
                    strategy, symbol, currency, timeframe
                )
                
                if analysis_data:
                    # ذخیره در کش
                    cache.set(cache_key, analysis_data, ttl=Config.SIGNAL_CACHE_DURATION)
                    analysis_data["is_cached"] = False
                    
                    # ثبت آمار استفاده
                    if strategy.startswith('demo_'):
                        cls.increment_demo_usage(user_id)
                    
                    return analysis_data
                else:
                    return {"error": "❌ خطا در دریافت داده‌ها از سرور"}
                    
            except Exception as api_error:
                logger.error(f"API error for {strategy}: {api_error}")
                return {"error": f"❌ خطای API: {str(api_error)}"}
                
        except Exception as e:
            logger.error(f"Error analyzing strategy: {e}")
            return {"error": "❌ خطای غیرمنتظره در تحلیل"}
    
    @classmethod
    def increment_demo_usage(cls, user_id: int) -> None:
        """افزایش شمارنده استفاده از دمو"""
        try:
            today = datetime.now().date()
            database_manager.increment_demo_usage(user_id, today)
        except Exception as e:
            logger.error(f"Error incrementing demo usage: {e}")
    
    @classmethod
    def can_use_strategy(cls, user_id: int, strategy: str) -> Tuple[bool, str]:
        """بررسی کامل امکان استفاده از استراتژی"""
        try:
            # بررسی دسترسی استراتژی
            has_access, access_message = cls.check_strategy_access(user_id, strategy)
            if not has_access:
                return False, access_message
            
            # بررسی محدودیت دمو برای کاربران رایگان
            user_package = cls.get_user_package_level(user_id)
            if user_package == PackageLevel.FREE and strategy.startswith('demo_'):
                can_use_demo, demo_message, usage_count = cls.check_demo_usage_limit(user_id)
                if not can_use_demo:
                    return False, demo_message
                
                # پیام هشدار برای نزدیک شدن به حد محدودیت
                if usage_count >= Config.DEMO_DAILY_LIMIT - 1:
                    return True, f"⚠️ این آخرین تحلیل دمو شما امروز است. ({usage_count + 1}/{Config.DEMO_DAILY_LIMIT})"
            
            return True, "استفاده مجاز است."
            
        except Exception as e:
            logger.error(f"Error checking strategy usage: {e}")
            return False, "❌ خطا در بررسی دسترسی."
    
    @classmethod
    def get_strategy_type_from_name(cls, strategy: str) -> str:
        """تشخیص نوع استراتژی برای انتخاب قالب پیام مناسب"""
        try:
            if strategy in cls.ALL_STRATEGIES:
                category = cls.ALL_STRATEGIES[strategy]["category"]
                
                category_mapping = {
                    "technical_indicators": "rsi" if "rsi" in strategy else "general",
                    "pattern_recognition": "pattern",
                    "trend_analysis": "ichimoku" if "ichimoku" in strategy else "fibonacci" if "fibonacci" in strategy else "general",
                    "price_action": "candlestick" if "candlestick" in strategy or "heikin" in strategy else "general",
                    "volume_analysis": "volume",
                    "advanced_systems": "momentum" if "momentum" in strategy else "general",
                    "divergence_analysis": "macd",
                    "demo": "general"
                }
                
                return category_mapping.get(category, "general")
            
            # fallback به روش قدیمی
            if "momentum" in strategy.lower():
                return "momentum"
            elif any(pattern in strategy.lower() for pattern in ["double_top", "triangle", "wedge", "diamond", "cup_handle", "flag", "head_shoulders"]):
                return "pattern"
            elif "ichimoku" in strategy.lower():
                return "ichimoku"
            elif "fibonacci" in strategy.lower():
                return "fibonacci"
            elif "bollinger" in strategy.lower():
                return "bollinger"
            elif "rsi" in strategy.lower():
                return "rsi"
            elif "volume" in strategy.lower():
                return "volume"
            elif "candlestick" in strategy.lower() or "heikin" in strategy.lower():
                return "candlestick"
            else:
                return "general"
        except:
            return "general"
    
    @classmethod
    def get_strategy_statistics(cls) -> Dict[str, Any]:
        """آمار استراتژی‌ها"""
        try:
            stats = {
                "total_strategies": len(cls.ALL_STRATEGIES),
                "strategies_by_package": {},
                "strategies_by_category": {},
                "strategies_by_difficulty": {}
            }
            
            # آمار بر اساس پکیج
            packages = {}
            categories = {}
            difficulties = {}
            
            for strategy_key, strategy_info in cls.ALL_STRATEGIES.items():
                package = strategy_info["package"]
                category = strategy_info["category"] 
                difficulty = strategy_info["difficulty"]
                
                # پکیج
                if package not in packages:
                    packages[package] = []
                packages[package].append(strategy_key)
                
                # دسته‌بندی
                if category not in categories:
                    categories[category] = []
                categories[category].append(strategy_key)
                
                # سطح دشواری
                if difficulty not in difficulties:
                    difficulties[difficulty] = []
                difficulties[difficulty].append(strategy_key)
            
            stats["strategies_by_package"] = {
                pkg: {"count": len(strategies), "strategies": strategies} 
                for pkg, strategies in packages.items()
            }
            
            stats["strategies_by_category"] = {
                cat: len(strategies) for cat, strategies in categories.items()
            }
            
            stats["strategies_by_difficulty"] = {
                diff: len(strategies) for diff, strategies in difficulties.items()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting strategy statistics: {e}")
            return {}
    
    @classmethod
    def get_user_usage_stats(cls, user_id: int) -> Dict[str, Any]:
        """دریافت آمار استفاده کاربر"""
        try:
            # دریافت آمار از دیتابیس
            stats = database_manager.get_user_usage_stats(user_id)
            
            # اضافه کردن اطلاعات پکیج
            user_package = cls.get_user_package_level(user_id)
            package_info = {
                "package_level": user_package.value if user_package else "free",
                "is_expired": cls.is_package_expired(user_id),
                "available_strategies": len(cls.get_available_strategies_for_user(user_id))
            }
            
            stats.update(package_info)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user usage stats: {e}")
            return {}
    
    @classmethod
    def is_strategy_available(cls, strategy: str) -> bool:
        """بررسی در دسترس بودن استراتژی"""
        return strategy in cls.ALL_STRATEGIES