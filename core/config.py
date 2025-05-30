"""
تنظیمات و پیکربندی سیستم
"""

import os
from pathlib import Path
from typing import Dict, List


class Config:
    """کلاس تنظیمات سیستم"""
    
    # مسیرهای پروژه
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    BACKUPS_DIR = BASE_DIR / "backups"
    REPORTS_DIR = BASE_DIR / "reports"
    CONFIG_DIR = BASE_DIR / "config"
    
    # تنظیمات پایگاه داده
    DATABASE_FILE = str(DATA_DIR / "mrtrader.db")
    
    # تنظیمات ربات تلگرام
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
    
    # تنظیمات امنیت
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    API_KEY = os.getenv("API_KEY", "")
    
    # تنظیمات محیط
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", 10 * 1024 * 1024))  # 10 مگابایت
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    BOT_VERSION = os.getenv("BOT_VERSION", "2.6.1")
    
    # تنظیمات کش
    CACHE_ENABLED = True
    SIGNAL_CACHE_DURATION = 60  # ثانیه (1 دقیقه)
    PRICE_CACHE_DURATION = 30   # ثانیه (30 ثانیه)
    DEFAULT_CACHE_DURATION = 300  # ثانیه (5 دقیقه)
    
    # تنظیمات rate limiting
    RATE_LIMIT_ENABLED = True
    MAX_REQUESTS_PER_MINUTE = 10
    PREMIUM_MAX_REQUESTS_PER_MINUTE = 20
    VIP_MAX_REQUESTS_PER_MINUTE = 30
    GHOST_MAX_REQUESTS_PER_MINUTE = 50
    
    # تنظیمات پکیج‌ها
    PACKAGE_PRICES = {
        "basic": 50000,      # تومان
        "premium": 150000,   # تومان
        "vip": 350000,       # تومان
        "ghost": 750000      # تومان
    }
    
    PACKAGE_DURATIONS = {
        "basic": 30,         # روز
        "premium": 30,       # روز
        "vip": 30,           # روز
        "ghost": 30          # روز
    }
    
    # سطح‌بندی پکیج‌ها و دسترسی‌ها
    PACKAGE_HIERARCHY = {
        "basic": {
            "level": 1,
            "max_requests_per_minute": 10,
            "strategies": ["price_action"]
        },
        "premium": {
            "level": 2,
            "max_requests_per_minute": 20,
            "strategies": ["price_action", "martingale", "cup_handle"]
        },
        "vip": {
            "level": 3,
            "max_requests_per_minute": 30,
            "strategies": ["price_action", "martingale", "cup_handle", "ichimoku", "fibonacci"]
        },
        "ghost": {
            "level": 4,
            "max_requests_per_minute": 50,
            "strategies": ["price_action", "martingale", "cup_handle", "ichimoku", "fibonacci", "komo_plus"]
        }
    }
    
    # تنظیمات استراتژی‌ها
    STRATEGY_NAMES = {
        "price_action": "تحلیل پرایس اکشن",
        "martingale": "استراتژی مارتینگل",
        "cup_handle": "الگوی کاپ اند هندل",
        "ichimoku": "ابر ایچیموکو",
        "fibonacci": "فیبوناچی ریتریسمنت",
        "komo_plus": "استراتژی کومو پلاس"
    }
    
    STRATEGY_DESCRIPTIONS = {
        "price_action": "تحلیل حرکت قیمت و شناسایی الگوهای کندلی",
        "martingale": "استراتژی مدیریت ریسک مارتینگل با ریسک کم",
        "cup_handle": "شناسایی الگوی برگشتی کاپ اند هندل",
        "ichimoku": "تحلیل کامل با سیستم ابر ایچیموکو",
        "fibonacci": "سطوح حمایت و مقاومت فیبوناچی",
        "komo_plus": "استراتژی پیشرفته کومو پلاس"
    }
    
    # تنظیمات ارزها و جفت ارزها
    SUPPORTED_SYMBOLS = [
        "BTC", "ETH", "BNB", "ADA", "XRP", "DOT", "LINK", "LTC", 
        "UNI", "AAVE", "SUSHI", "COMP", "MKR", "YFI", "SNX", "CRV"
    ]
    
    SUPPORTED_CURRENCIES = ["USDT", "BUSD", "USD", "EUR"]
    
    SUPPORTED_TIMEFRAMES = [
        "1m", "3m", "5m", "15m", "30m", "1h", 
        "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"
    ]
    
    TIMEFRAME_NAMES = {
        "1m": "1 دقیقه",
        "3m": "3 دقیقه", 
        "5m": "5 دقیقه",
        "15m": "15 دقیقه",
        "30m": "30 دقیقه",
        "1h": "1 ساعت",
        "2h": "2 ساعت",
        "4h": "4 ساعت",
        "6h": "6 ساعت",
        "8h": "8 ساعت",
        "12h": "12 ساعت",
        "1d": "1 روز",
        "3d": "3 روز",
        "1w": "1 هفته",
        "1M": "1 ماه"
    }
    
    # تنظیمات رفرال
    REFERRAL_ENABLED = True
    REFERRAL_COMMISSION_PERCENT = 10  # درصد
    MIN_REFERRAL_PAYOUT = 50000      # تومان
    
    # تنظیمات بکاپ
    AUTO_BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 24
    MAX_BACKUP_FILES = 7
    
    # پیام‌های سیستم
    MESSAGES = {
        "welcome": (
            "🤖 **به ربات MrTrader خوش آمدید!**\n\n"
            "من یک ربات هوشمند برای تحلیل بازار ارزهای دیجیتال هستم.\n"
            "برای شروع، از منوی زیر استفاده کنید:"
        ),
        "unauthorized": (
            "⛔ شما مجاز به استفاده از این قابلیت نیستید.\n"
            "برای دسترسی کامل، یکی از پکیج‌های ما را خریداری کنید."
        ),
        "package_expired": (
            "⏰ پکیج شما منقضی شده است.\n"
            "برای ادامه استفاده، لطفاً پکیج خود را تمدید کنید."
        ),
        "package_required": (
            "📦 برای استفاده از این استراتژی، نیاز به خرید پکیج دارید:\n"
            "💎 Premium: {premium_price:,} تومان\n"
            "👑 VIP: {vip_price:,} تومان\n"
            "👻 Ghost: {ghost_price:,} تومان"
        ),
        "error_occurred": (
            "❌ خطایی رخ داده است.\n"
            "لطفاً بعداً دوباره تلاش کنید."
        ),
        "rate_limit_exceeded": (
            "⏱️ تعداد درخواست‌های شما از حد مجاز گذشته است.\n"
            "لطفاً کمی صبر کنید و سپس دوباره تلاش کنید."
        ),
        "cached_result": (
            "📊 نتیجه از کش (آخرین بروزرسانی: {time})"
        ),
        "fresh_result": (
            "🔄 تحلیل جدید انجام شد"
        ),
        "maintenance": (
            "🔧 سیستم در حال تعمیر و نگهداری است.\n"
            "لطفاً کمی بعد مراجعه کنید."
        )
    }
    
    # تنظیمات شبکه
    REQUEST_TIMEOUT = 30  # ثانیه
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # ثانیه
    
    @classmethod
    def ensure_directories_exist(cls):
        """ایجاد پوشه‌های مورد نیاز"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.BACKUPS_DIR,
            cls.REPORTS_DIR,
            cls.CONFIG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> Dict[str, List[str]]:
        """اعتبارسنجی تنظیمات"""
        errors = []
        warnings = []
        
        # بررسی متغیرهای ضروری
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if cls.ADMIN_USER_ID == 0:
            warnings.append("ADMIN_USER_ID not set")
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-here":
            warnings.append("SECRET_KEY should be changed from default")
        
        # بررسی پوشه‌ها
        try:
            cls.ensure_directories_exist()
        except Exception as e:
            errors.append(f"Cannot create directories: {e}")
        
        # بررسی فایل config
        config_file = cls.CONFIG_DIR / "api_servers_config.json"
        if not config_file.exists():
            warnings.append("API servers config file not found")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0
        }
    
    @classmethod
    def get_database_url(cls) -> str:
        """دریافت URL پایگاه داده"""
        return f"sqlite:///{cls.DATABASE_FILE}"
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """بررسی مدیر بودن کاربر"""
        return user_id == cls.ADMIN_USER_ID
    
    @classmethod
    def get_package_price(cls, package_name: str) -> int:
        """دریافت قیمت پکیج"""
        return cls.PACKAGE_PRICES.get(package_name, 0)
    
    @classmethod
    def get_package_duration(cls, package_name: str) -> int:
        """دریافت مدت اعتبار پکیج (روز)"""
        return cls.PACKAGE_DURATIONS.get(package_name, 30)
    
    @classmethod
    def get_max_requests_for_package(cls, package_name: str) -> int:
        """دریافت حداکثر درخواست برای پکیج"""
        return cls.PACKAGE_HIERARCHY.get(package_name, {}).get("max_requests_per_minute", cls.MAX_REQUESTS_PER_MINUTE)
    
    @classmethod
    def get_package_strategies(cls, package_name: str) -> List[str]:
        """دریافت استراتژی‌های مجاز برای پکیج"""
        return cls.PACKAGE_HIERARCHY.get(package_name, {}).get("strategies", [])
    
    @classmethod
    def is_strategy_allowed_for_package(cls, strategy: str, package_name: str) -> bool:
        """بررسی مجاز بودن استراتژی برای پکیج"""
        allowed_strategies = cls.get_package_strategies(package_name)
        return strategy in allowed_strategies
    
    @classmethod
    def get_strategy_name(cls, strategy_key: str) -> str:
        """دریافت نام فارسی استراتژی"""
        return cls.STRATEGY_NAMES.get(strategy_key, strategy_key)
    
    @classmethod
    def get_strategy_description(cls, strategy_key: str) -> str:
        """دریافت توضیحات استراتژی"""
        return cls.STRATEGY_DESCRIPTIONS.get(strategy_key, "")
    
    @classmethod
    def get_timeframe_name(cls, timeframe: str) -> str:
        """دریافت نام فارسی تایم‌فریم"""
        return cls.TIMEFRAME_NAMES.get(timeframe, timeframe)
    
    @classmethod
    def load_from_env(cls):
        """بارگذاری تنظیمات از متغیرهای محیطی"""
        # این متد می‌تواند برای بارگذاری تنظیمات اضافی استفاده شود
        pass


# ایجاد پوشه‌های مورد نیاز هنگام import
Config.ensure_directories_exist()