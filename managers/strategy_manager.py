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
from core.cache import cache
from dateutil.parser import parse

class PackageLevel(Enum):
    """سطوح پکیج‌های دسترسی"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"


class StrategyManager:
    """مدیریت استراتژی‌ها و کنترل دسترسی"""
    
    # نقشه کامل تمام 35 استراتژی مطابق API واقعی
    ALL_STRATEGIES = {
        # DEMO (2 استراتژی)
        "demo_price_action": {
            "name": "🎯 دمو پرایس اکشن",
            "package": "free",
            "category": "demo",
            "difficulty": "دمو",
            "description": "نسخه دمو تحلیل حرکت قیمت - محدود به 5 تحلیل در روز",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "demo_rsi": {
            "name": "📈 دمو RSI", 
            "package": "free",
            "category": "demo",
            "difficulty": "دمو",
            "description": "نسخه دمو شاخص قدرت نسبی - محدود به 5 تحلیل در روز",
            "endpoint": "/analyze_RSI_basic/"
        },
        
        # BASIC Package (9 استراتژی)
        "cci_analysis": {
            "name": "📊 تحلیل CCI",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "شاخص کانال کالا برای تشخیص نقاط اشباع خرید و فروش",
            "endpoint": "/analyze_CCI_strategy/"
        },
        "ema_analysis": {
            "name": "📈 تحلیل EMA",
            "package": "basic",
            "category": "technical_indicators", 
            "difficulty": "مبتدی",
            "description": "میانگین متحرک نمایی برای تشخیص روند و نقاط ورود",
            "endpoint": "/analyze_EMA_strategy/"
        },
        "ichimoku": {
            "name": "☁️ ابر ایچیموکو",
            "package": "basic",
            "category": "trend_analysis",
            "difficulty": "متوسط",
            "description": "سیستم جامع تحلیل ژاپنی با ابر ایچیموکو",
            "endpoint": "/analyze_ichimoku_strategy/"
        },
        "ichimoku_low_signal": {
            "name": "☁️ ایچیموکو سیگنال پایین",
            "package": "basic",
            "category": "trend_analysis",
            "difficulty": "متوسط",
            "description": "سیگنال‌های کم ریسک و محافظه‌کارانه ایچیموکو",
            "endpoint": "/analyze_ichimoku_strategy/"
        },
        "macd": {
            "name": "🌊 تحلیل MACD",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "واگرایی همگرایی میانگین متحرک برای تشخیص تغییر روند",
            "endpoint": "/analyze_MACD_basic/"
        },
        "price_action_pandas_ta": {
            "name": "🎯 پرایس اکشن TA",
            "package": "basic",
            "category": "price_action",
            "difficulty": "مبتدی",
            "description": "تحلیل حرکت قیمت با کتابخانه pandas و اندیکاتورهای تکنیکال",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "project_price_live_binance": {
            "name": "🔴 قیمت زنده بایننس",
            "package": "basic",
            "category": "volume_analysis",
            "difficulty": "مبتدی",
            "description": "دریافت قیمت‌های زنده و تحلیل آنی از صرافی بایننس",
            "endpoint": "/live_price/"
        },
        "rsi": {
            "name": "📊 تحلیل RSI",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی", 
            "description": "شاخص قدرت نسبی برای شناسایی شرایط اشباع",
            "endpoint": "/analyze_RSI_basic/"
        },
        "williams_r_analysis": {
            "name": "📉 تحلیل Williams R",
            "package": "basic",
            "category": "technical_indicators",
            "difficulty": "مبتدی",
            "description": "اندیکاتور Williams %R برای تشخیص نقاط برگشت",
            "endpoint": "/analyze_WilliamsR/"
        },
        
        # PREMIUM Package (17 استراتژی اضافی)
        "a_candlestick": {
            "name": "🕯️ تحلیل کندل استیک",
            "package": "premium",
            "category": "price_action",
            "difficulty": "پیشرفته",
            "description": "تشخیص و تحلیل الگوهای کندل استیک ژاپنی",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "b_pivot": {
            "name": "🎯 نقاط محوری",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "محاسبه و تحلیل نقاط محوری حمایت و مقاومت",
            "endpoint": "/analyze_fibonacci/"
        },
        "bollinger_bands": {
            "name": "📊 باندهای بولینگر",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "باندهای بولینگر برای تحلیل نوسانات و نقاط ورود",
            "endpoint": "/analyze_bollinger/"
        },
        "c_trend_lines": {
            "name": "📐 خطوط روند",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "ترسیم و تحلیل خطوط روند و کانال‌های قیمتی",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "double_top_pattern": {
            "name": "⛰️ الگوی دو قله",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص الگوهای دو قله و دو کف برای پیش‌بینی برگشت روند",
            "endpoint": "/analyze_double_top_strategy/"
        },
        "fibonacci_strategy": {
            "name": "🌀 استراتژی فیبوناچی",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "استفاده از سطوح فیبوناچی ریتریسمنت برای نقاط ورود",
            "endpoint": "/analyze_fibonacci/"
        },
        "flag_pattern": {
            "name": "🏁 الگوی پرچم",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "شناسایی الگوی ادامه‌دهنده پرچم در روندهای قوی",
            "endpoint": "/analyze_flag_pattern/"
        },
        "head_shoulders_analysis": {
            "name": "👤 الگوی سر و شانه",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تحلیل الگوی برگشتی سر و شانه",
            "endpoint": "/analyze_head_shoulders_analysis/"
        },
        "heikin_ashi": {
            "name": "🕯️ کندل هایکن آشی",
            "package": "premium",
            "category": "price_action",
            "difficulty": "متخصص",
            "description": "تحلیل با کندل‌های هایکن آشی برای تشخیص روند",
            "endpoint": "/analyze_heikin_ashi_strategy/"
        },
        "macd_divergence": {
            "name": "🌊 واگرایی MACD",
            "package": "premium",
            "category": "divergence_analysis",
            "difficulty": "متخصص",
            "description": "تشخیص واگرایی‌های MACD برای پیش‌بینی تغییر روند",
            "endpoint": "/analyze_macd_divergence_strategy/"
        },
        "martingale_low": {
            "name": "🎰 مارتینگل پایین",
            "package": "premium",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "استراتژی مارتینگل با ریسک پایین و مدیریت سرمایه",
            "endpoint": "/analyze_momentum_strategy/"
        },
        "momentum": {
            "name": "🚀 تحلیل مومنتوم",
            "package": "premium",
            "category": "advanced_systems",
            "difficulty": "پیشرفته",
            "description": "تحلیل قدرت و مومنتوم حرکت قیمت",
            "endpoint": "/analyze_momentum_strategy/"
        },
        "stochastic": {
            "name": "📈 تحلیل استوکاستیک",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "متخصص",
            "description": "نوسان‌گر استوکاستیک برای تشخیص اشباع و نقاط برگشت",
            "endpoint": "/analyze_RSI_basic/"
        },
        "stoch_rsi": {
            "name": "📊 استوکاستیک RSI",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "متخصص",
            "description": "ترکیب استوکاستیک و RSI برای دقت بیشتر",
            "endpoint": "/analyze_RSI_basic/"
        },
        "support_resistance": {
            "name": "🛡️ حمایت و مقاومت",
            "package": "premium",
            "category": "trend_analysis",
            "difficulty": "پیشرفته",
            "description": "تشخیص خودکار سطوح حمایت و مقاومت",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "triangle_pattern": {
            "name": "📐 الگوی مثلث",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص انواع الگوهای مثلث صعودی، نزولی و متقارن",
            "endpoint": "/analyze_double_top_strategy/"
        },
        "wedge_pattern": {
            "name": "📊 الگوی گوه",
            "package": "premium",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تحلیل الگوهای گوه صعودی و نزولی",
            "endpoint": "/analyze_double_top_strategy/"
        },
        "williams_alligator": {
            "name": "🐊 تمساح ویلیامز",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "سیستم تمساح ویلیامز برای تشخیص روند",
            "endpoint": "/analyze_WilliamsR/"
        },
        "parabolic_sar": {
            "name": "📈 سار پارابولیک",
            "package": "premium",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "سیستم سار پارابولیک برای تعیین نقاط توقف",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        
        # VIP Package (9 استراتژی اضافی)
        "atr": {
            "name": "📊 تحلیل ATR",
            "package": "vip",
            "category": "technical_indicators",
            "difficulty": "متخصص",
            "description": "میانگین دامنه واقعی برای محاسبه نوسانات و تنظیم stop loss",
            "endpoint": "/analyze_atr/"
        },
        "sma_advanced": {
            "name": "📈 SMA پیشرفته",
            "package": "vip",
            "category": "technical_indicators",
            "difficulty": "پیشرفته",
            "description": "میانگین متحرک ساده با تحلیل‌های پیشرفته و چندتایم‌فریمه",
            "endpoint": "/analyze_EMA_strategy/"
        },
        "volume_profile": {
            "name": "📊 پروفایل حجم",
            "package": "vip",
            "category": "volume_analysis",
            "difficulty": "متخصص",
            "description": "تحلیل پروفایل حجم معاملات برای شناسایی نواحی مهم",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "vwap": {
            "name": "💎 تحلیل VWAP",
            "package": "vip",
            "category": "volume_analysis",
            "difficulty": "متخصص",
            "description": "میانگین موزون حجمی برای شناسایی قیمت منصفانه",
            "endpoint": "/analyze_price_action_pandas_ta/"
        },
        "diamond_pattern": {
            "name": "💎 الگوی الماس",
            "package": "vip",
            "category": "pattern_recognition",
            "difficulty": "متخصص",
            "description": "تشخیص الگوی نادر و قوی الماس",
            "endpoint": "/analyze_Diamond_Pattern/"
        },
        "crt": {
            "name": "🎯 تحلیل CRT",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم تحلیل CRT پیشرفته برای شناسایی روندها",
            "endpoint": "/analyze_CRT_strategy/"
        },
        "p3": {
            "name": "🎯 سیستم P3",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم تحلیل P3 برای پیش‌بینی نقاط عطف",
            "endpoint": "/analyze_momentum_strategy/"
        },
        "rtm": {
            "name": "🔄 تحلیل RTM",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "سیستم RTM پیشرفته برای تحلیل ریسک و بازده",
            "endpoint": "/analyze_momentum_strategy/"
        },
        "multi_resistance": {
            "name": "🛡️ مقاومت چندگانه",
            "package": "vip",
            "category": "advanced_systems",
            "difficulty": "متخصص",
            "description": "تحلیل چند سطحی حمایت و مقاومت با دقت بالا",
            "endpoint": "/analyze_price_action_pandas_ta/"
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
                'demo': PackageLevel.FREE,  # سازگاری
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
            from managers.user_manager import UserManager
            is_expired, days_left = UserManager.is_package_expired(user_id)
            if is_expired:   
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
    def get_strategy_endpoint(cls, strategy: str) -> Optional[str]:
        """دریافت endpoint API استراتژی"""
        if strategy in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy]["endpoint"]
        return None
    
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
                "basic": ["free", "basic"],
                "premium": ["free", "basic", "premium"],
                "vip": ["free", "basic", "premium", "vip"],
                "ghost": ["free", "basic", "premium", "vip", "ghost"]
            }
            
            allowed_packages = package_hierarchy.get(user_package_name, ["free"])
            
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
                        "difficulty": strategy_info["difficulty"],
                        "endpoint": strategy_info["endpoint"]
                    })
            
            return strategy_list
            
        except Exception as e:
            logger.error(f"Error getting strategies by package: {e}")
            return []
    
    @classmethod
    def get_strategies_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """دریافت استراتژی‌های یک دسته‌بندی"""
        try:
            strategy_list = []
            
            for strategy_key, strategy_info in cls.ALL_STRATEGIES.items():
                if strategy_info["category"] == category:
                    strategy_list.append({
                        "key": strategy_key,
                        "name": strategy_info["name"],
                        "description": strategy_info["description"],
                        "package": strategy_info["package"],
                        "difficulty": strategy_info["difficulty"],
                        "endpoint": strategy_info["endpoint"]
                    })
            
            return strategy_list
            
        except Exception as e:
            logger.error(f"Error getting strategies by category: {e}")
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
    async def analyze_strategy(cls, user_id: int, strategy: str, symbol: str, currency: str, timeframe: str, generate_file: bool = True) -> Optional[Dict[str, Any]]:
        """تحلیل استراتژی با پردازش بهتر API response"""
        try:
            logger.info(f"Starting analysis for user {user_id}: {strategy} {symbol}/{currency} @ {timeframe}")
            
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
            
            # فراخوانی API
            try:
                from api.api_client import api_client
                
                logger.info(f"Calling API for {strategy} analysis: {symbol}/{currency} @ {timeframe}")
                
                analysis_data = await api_client.fetch_strategy_analysis(
                    strategy, symbol, currency, timeframe
                )
                
                if analysis_data and "error" not in analysis_data:
                    # بررسی و تصحیح محتوای analysis_text
                    if not analysis_data.get("analysis_text") and not analysis_data.get("raw_report"):
                        # اگر محتوای تحلیل در response اصلی موجود است، آن را استخراج کن
                        if isinstance(analysis_data, dict):
                            # جستجو برای محتوای تحلیل در کلیدهای مختلف
                            for key, value in analysis_data.items():
                                if isinstance(value, str) and len(value) > 100 and ("تحلیل" in value or "سیگنال" in value):
                                    analysis_data["analysis_text"] = value
                                    break
                    
                    # تولید فایل گزارش در صورت درخواست
                    if generate_file:
                        file_info = await cls._generate_report_file(
                            analysis_data, strategy, symbol, currency, timeframe, user_id
                        )
                        analysis_data["report_file"] = file_info
                    
                    # ثبت آمار
                    if strategy.startswith('demo_'):
                        cls.increment_demo_usage(user_id)
                    
                    analysis_data["is_cached"] = False
                    logger.info(f"Analysis successful for {strategy} {symbol}/{currency}")
                    return analysis_data
                else:
                    error_msg = analysis_data.get("error", "خطای ناشناخته") if analysis_data else "پاسخ خالی از API"
                    logger.error(f"API returned error: {error_msg}")
                    return {"error": f"خطا در دریافت داده‌ها: {error_msg}"}
                    
            except Exception as api_error:
                logger.error(f"API error for {strategy}: {api_error}", exc_info=True)
                return {"error": f"خطای ارتباط با سرور: {str(api_error)}"}
                
        except Exception as e:
            logger.error(f"Error analyzing strategy {strategy}: {e}", exc_info=True)
            return {"error": "خطای غیرمنتظره در تحلیل. لطفاً دوباره تلاش کنید."}

    # 3. تابع تولید فایل گزارش
    @classmethod
    async def _generate_report_file(cls, analysis_result: Dict[str, Any], strategy_key: str,
                                symbol: str, currency: str, timeframe: str, user_id: int) -> Dict[str, Any]:
        """تولید فایل گزارش کامل برای دانلود"""
        try:
            from utils.helpers import extract_signal_details, format_signal_message
            from datetime import datetime
            import os
            
            # استخراج جزئیات سیگنال
            signal_details = extract_signal_details(strategy_key, analysis_result)
            
            # نام نمایشی استراتژی
            strategy_display = cls.get_strategy_display_name(strategy_key)
            
            # محتوای فایل گزارش
            report_content = f"""
                        🤖 MrTrader Bot - گزارش تحلیل                    
                        مهندس محسن اسدی تحلیلگر و مدرس بازارهای مالی

    📊 اطلاعات کلی:
    ─────────────────────────────────────────────────────────────────────────────────
    • نماد: {symbol}/{currency}
    • استراتژی: {strategy_display}
    • تایم‌فریم: {timeframe}
    • زمان تحلیل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    • شناسه کاربر: {user_id}

    🎯 نتایج تحلیل:
    ─────────────────────────────────────────────────────────────────────────────────
    • سیگنال: {signal_details.get('signal_direction', 'نامشخص')}
    • قدرت سیگنال: {signal_details.get('strength', 'متوسط')}
    • درصد اطمینان: {signal_details.get('confidence', 0.5):.1%}

    💰 سطوح معاملاتی:
    ─────────────────────────────────────────────────────────────────────────────────"""

            # اضافه کردن قیمت‌ها اگر موجود باشد
            if signal_details.get("entry_price"):
                report_content += f"\n• قیمت ورود: ${signal_details['entry_price']:,.4f}"
            if signal_details.get("stop_loss"):
                report_content += f"\n• حد ضرر: ${signal_details['stop_loss']:,.4f}"
            if signal_details.get("take_profit"):
                report_content += f"\n• هدف سود: ${signal_details['take_profit']:,.4f}"
            if signal_details.get("risk_reward_ratio"):
                report_content += f"\n• نسبت ریسک/ریوارد: 1:{signal_details['risk_reward_ratio']}"

            report_content += f"""

    📋 تحلیل تفصیلی:
    ─────────────────────────────────────────────────────────────────────────────────
    {analysis_result.get('analysis_text', analysis_result.get('raw_report', 'گزارش دریافت نشد'))}

    ⚠️ اخطارها:
    ─────────────────────────────────────────────────────────────────────────────────
    • این تحلیل صرفاً جنبه آموزشی و اطلاعاتی دارد
    • هیچ‌گونه توصیه سرمایه‌گذاری محسوب نمی‌شود
    • لطفاً قبل از هر تصمیم معاملاتی، تحقیقات تکمیلی انجام دهید
    • ریسک سرمایه‌گذاری در همهء باراهای مالی همواره وجود دارد

                MrTrader Bot v2.0                           
    """
            
            # ایجاد پوشه گزارش‌ها
            reports_dir = "temp_reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # نام فایل منحصربفرد
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{strategy_key}_{symbol}_{currency}_{timeframe}_{timestamp}.txt"
            filepath = os.path.join(reports_dir, filename)
            
            # نوشتن فایل
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return {
                "filename": filename,
                "filepath": filepath,
                "size": os.path.getsize(filepath),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating report file: {e}")
            return {"error": f"خطا در تولید فایل: {str(e)}"}

    @classmethod
    def _get_strategy_display_name(cls, strategy_key: str) -> str:
        """نام نمایشی استراتژی"""
        if strategy_key in cls.ALL_STRATEGIES:
            return cls.ALL_STRATEGIES[strategy_key]["name"]
        
        # fallback mapping
        strategy_names = {
            "cci_analysis": "CCI (شاخص کانال کالا)",
            "rsi": "RSI (شاخص قدرت نسبی)",
            "macd": "MACD (همگرایی واگرایی)",
            "ema_analysis": "EMA (میانگین متحرک نمایی)",
            "williams_r_analysis": "Williams %R",
            "ichimoku": "Ichimoku (ابر ایچی‌موکو)",
            "wedge_pattern": "الگوی گوه (Wedge Pattern)",
            "head_shoulders_analysis": "سر و شانه",
            "double_top_pattern": "دو قله/دو کف",
            "fibonacci_strategy": "فیبوناچی",
            "macd_divergence": "واگرایی MACD",
            "price_action_pandas_ta": "Price Action"
        }
        return strategy_names.get(strategy_key, strategy_key.replace('_', ' ').title())

    
        
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
    
    def get_analysis_endpoint(self, strategy_key: str) -> str:
        """دریافت endpoint صحیح برای هر استراتژی"""
        
        # mapping صحیح استراتژی‌ها به endpoints
        strategy_endpoints = {
            # استراتژی‌های اصلی
            "cci_analysis": "analyze_CCI_strategy",
            "rsi": "analyze_RSI_basic", 
            "macd": "analyze_MACD_basic",
            "ema_analysis": "analyze_EMA_strategy",
            "williams_r_analysis": "analyze_WilliamsR",
            "ichimoku": "analyze_ichimoku_strategy",  # ✅ اصلاح شده
            "ichimoku_low_signal": "analyze_ichimoku_strategy",
            
            # استراتژی‌های الگویی
            "wedge_pattern": "analyze_wedge_pattern_strategy",  # ✅ اصلاح شده - جدا از double_top
            "head_shoulders_analysis": "analyze_head_shoulders_analysis",
            "double_top_pattern": "analyze_double_top_strategy",
            "triangle_pattern": "analyze_double_top_strategy",  # استفاده موقت
            "cup_handle": "analyze_cup_handle_strategy",
            "flag_pattern": "analyze_flag_pattern",
            "diamond_pattern": "analyze_Diamond_Pattern",
            
            # استراتژی‌های تکنیکال پیشرفته
            "fibonacci_strategy": "analyze_fibonacci",
            "bollinger_bands": "analyze_bollinger",
            "macd_divergence": "analyze_macd_divergence_strategy",
            "price_action_pandas_ta": "analyze_price_action_pandas_ta",
            "support_resistance": "analyze_price_action_pandas_ta",
            "parabolic_sar": "analyze_price_action_pandas_ta",
            
            # استراتژی‌های VIP
            "atr": "analyze_atr",
            "volume_profile": "analyze_price_action_pandas_ta",
            "vwap": "analyze_price_action_pandas_ta",
            "crt": "analyze_CRT_strategy",
            "momentum": "analyze_momentum_strategy",
            "stochastic": "analyze_RSI_basic",
            "stoch_rsi": "analyze_RSI_basic",
            
            # دمو
            "demo_price_action": "analyze_price_action_pandas_ta",
            "demo_rsi": "analyze_RSI_basic",
            
            # سایر استراتژی‌ها
            "project_price_live_binance": "live_price",
            "heikin_ashi": "analyze_heikin_ashi_strategy",
            "williams_alligator": "analyze_WilliamsR",
            "martingale_low": "analyze_momentum_strategy",
            "sma_advanced": "analyze_EMA_strategy",
            "multi_resistance": "analyze_price_action_pandas_ta",
            "p3": "analyze_momentum_strategy",
            "rtm": "analyze_momentum_strategy"
        }
        
        endpoint = strategy_endpoints.get(strategy_key)
        if not endpoint:
            logger.warning(f"No endpoint found for strategy: {strategy_key}")
            return "analyze_price_action_pandas_ta"  # fallback
        
        return endpoint

    @classmethod  
    def is_package_expired(cls, user_id: int) -> bool:
        """بررسی انقضای پکیج کاربر"""
        try:
            from managers.user_manager import UserManager
            is_expired, days_left = UserManager.is_package_expired(user_id)
            return is_expired
        except Exception as e:
            logger.error(f"Error checking package expiration: {e}")
            return False
        
    @classmethod
    def is_strategy_available(cls, strategy: str) -> bool:
        """بررسی در دسترس بودن استراتژی"""
        return strategy in cls.ALL_STRATEGIES
    
    @classmethod
    def get_all_strategy_keys(cls) -> List[str]:
        """دریافت لیست تمام کلیدهای استراتژی"""
        return list(cls.ALL_STRATEGIES.keys())
    
    @classmethod
    def get_package_strategy_count(cls, package_name: str) -> int:
        """دریافت تعداد استراتژی‌های یک پکیج"""
        return len(cls.get_strategies_by_package(package_name))


# Export
__all__ = ['StrategyManager', 'PackageLevel']