"""
تنظیمات و پیکربندی سیستم MrTrader Bot - Fixed Version
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
    BACKUP_DIRECTORY = BASE_DIR / "backups"  # ✅ اضافه شده برای رفع خطا
    REPORTS_DIR = BASE_DIR / "reports"
    CONFIG_DIR = BASE_DIR / "config"
    
    # ✅ مسیرهای فایل‌های CSV (کامل شده برای رفع خطا)
    USER_CSV_FILE = str(DATA_DIR / "users.csv")
    ADMIN_CSV_FILE = str(DATA_DIR / "admins.csv")
    TRANSACTIONS_CSV_FILE = str(DATA_DIR / "transactions.csv")
    PACKAGES_CSV_FILE = str(DATA_DIR / "packages.csv")
    REFERRALS_CSV_FILE = str(DATA_DIR / "referrals.csv")
    USAGE_CSV_FILE = str(DATA_DIR / "usage_stats.csv")
    PENDING_PAYMENTS_CSV = str(DATA_DIR / "pending_payments.csv")  # ✅ اضافه شده
    PAYMENT_LOG_CSV = str(DATA_DIR / "payment_log.csv")  # ✅ اضافه شده
    SETTINGS_CSV_FILE = str(DATA_DIR / "settings.csv")  # ✅ اضافه شده
    ANALYTICS_CSV_FILE = str(DATA_DIR / "analytics.csv")  # ✅ اضافه شده
    
    # تنظیمات پایگاه داده
    DATABASE_FILE = str(DATA_DIR / "mrtrader.db")
    
    # تنظیمات ربات تلگرام
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
    
    # ✅ لیست ادمین‌ها (اضافه شده برای compatibility)
    ADMINS = [
        ADMIN_USER_ID if ADMIN_USER_ID > 0 else 123456789,  # ادمین اصلی
        # سایر ادمین‌ها
    ]
    
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
    
    # ✅ تنظیمات لاگ (اضافه شده)
    ERROR_LOG_FILE = str(LOGS_DIR / "errors.log")
    MAIN_LOG_FILE = str(LOGS_DIR / "mrtrader.log")
    USER_ACTIONS_LOG = str(LOGS_DIR / "user_actions.log")
    API_LOG_FILE = str(LOGS_DIR / "api.log")
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    
    # ✅ API Keys (اضافه شده)
    COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "your_api_key_here")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "your_api_key_here")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "your_api_key_here")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "your_secret_key_here")
    
    # ✅ تنظیمات API (اضافه شده)
    API_TIMEOUTS = {
        'connect': 10,
        'read': 30,
        'total': 60
    }
    
    API_RATE_LIMITS = {
        'coinmarketcap': 10000,  # requests per month
        'coingecko': 100,        # requests per minute
        'binance': 1200          # requests per minute
    }
    
    # تنظیمات کش
    CACHE_ENABLED = True
    SIGNAL_CACHE_DURATION = 60  # ثانیه (1 دقیقه)
    PRICE_CACHE_DURATION = 30   # ثانیه (30 ثانیه)
    DEFAULT_CACHE_DURATION = 300  # ثانیه (5 دقیقه)
    
    # تنظیمات rate limiting
    RATE_LIMIT_ENABLED = True
    MAX_REQUESTS_PER_MINUTE = 10
    BASIC_MAX_REQUESTS_PER_MINUTE = 10
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
    
    # ✅ تنظیمات پکیج‌ها (بروزرسانی شده - format جدید)
    PACKAGES = {
        'demo': {
            'name': 'دمو',
            'price': 0,
            'duration_days': 9999,  # بی‌نهایت
            'daily_limit': 5,
            'features': ['تحلیل ساده', 'سیگنال‌های پایه', 'نمودار قیمت']
        },
        'basic': {
            'name': 'پایه',
            'price': 99000,
            'duration_days': 30,
            'daily_limit': 20,
            'features': ['تحلیل کامل', 'سیگنال‌های پیشرفته', 'آلارم قیمت']
        },
        'premium': {
            'name': 'ویژه',
            'price': 199000,
            'duration_days': 30,
            'daily_limit': 50,
            'features': ['تحلیل هوش مصنوعی', 'سیگنال‌های VIP', 'مشاوره تخصصی']
        },
        'vip': {
            'name': 'VIP',
            'price': 399000,
            'duration_days': 30,
            'daily_limit': 100,
            'features': ['دسترسی کامل', 'سیگنال‌های انحصاری', 'مشاوره شخصی']
        }
    }
    
    # سطح‌بندی پکیج‌ها و دسترسی‌ها (بروزرسانی شده مطابق مستندات جدید)
    PACKAGE_HIERARCHY = {
        "demo": {
            "level": 0,
            "max_requests_per_minute": 1,
            "daily_limit": 5,
            "strategies": ["demo_price_action", "demo_rsi"]
        },
        "basic": {
            "level": 1,
            "max_requests_per_minute": 5,
            "daily_limit": 50,
            "strategies": [
                "demo_price_action", "demo_rsi",  # دمو ها همیشه در دسترس
                "cci_analysis", "ema_analysis", "ichimoku", "macd", 
                "price_action_pandas_ta", "rsi", "williams_r_analysis",
                "project_price_live_binance", "ichimoku_low_signal"
            ]
        },
        "premium": {
            "level": 2,
            "max_requests_per_minute": 10,
            "daily_limit": 200,
            "strategies": [
                # همه استراتژی‌های basic
                "demo_price_action", "demo_rsi", "cci_analysis", "ema_analysis", 
                "ichimoku", "macd", "price_action_pandas_ta", "rsi", "williams_r_analysis",
                "project_price_live_binance", "ichimoku_low_signal",
                # استراتژی‌های premium اضافی
                "a_candlestick", "bollinger_bands", "stochastic", "macd_divergence",
                "b_pivot", "c_trend_lines", "fibonacci_strategy", "double_top_pattern",
                "triangle_pattern", "wedge_pattern", "momentum", "martingale_low",
                "heikin_ashi", "stoch_rsi", "williams_alligator", "parabolic_sar",
                "support_resistance"
            ]
        },
        "vip": {
            "level": 3,
            "max_requests_per_minute": 20,
            "daily_limit": 500,
            "strategies": [
                # همه استراتژی‌های premium
                "demo_price_action", "demo_rsi", "cci_analysis", "ema_analysis", 
                "ichimoku", "macd", "price_action_pandas_ta", "rsi", "williams_r_analysis",
                "project_price_live_binance", "ichimoku_low_signal", "a_candlestick", 
                "bollinger_bands", "stochastic", "macd_divergence", "b_pivot", 
                "c_trend_lines", "fibonacci_strategy", "double_top_pattern",
                "triangle_pattern", "wedge_pattern", "momentum", "martingale_low",
                "heikin_ashi", "stoch_rsi", "williams_alligator", "parabolic_sar",
                "support_resistance",
                # استراتژی‌های vip اضافی
                "atr", "sma_advanced", "volume_profile", "vwap", "diamond_pattern",
                "crt", "p3", "rtm", "multi_resistance"
            ]
        }
    }
    
    # برای backward compatibility
    PACKAGE_HIERARCHY["free"] = PACKAGE_HIERARCHY["demo"]
    
    # تنظیمات استراتژی‌ها - نام‌های فارسی (بروزرسانی شده)
    STRATEGY_NAMES = {
        # استراتژی‌های دمو
        "demo_price_action": "🎯 دمو پرایس اکشن",
        "demo_rsi": "📈 دمو RSI",
        
        # استراتژی‌های BASIC Package
        "cci_analysis": "📊 تحلیل CCI",
        "ema_analysis": "📈 تحلیل EMA", 
        "ichimoku": "☁️ ابر ایچیموکو",
        "macd": "🌊 تحلیل MACD",
        "price_action_pandas_ta": "🎯 پرایس اکشن TA",
        "rsi": "📊 تحلیل RSI",
        "williams_r_analysis": "📉 تحلیل Williams R",
        "project_price_live_binance": "🔴 قیمت زنده بایننس",
        "ichimoku_low_signal": "☁️ ایچیموکو سیگنال پایین",
        
        # استراتژی‌های PREMIUM Package
        "a_candlestick": "🕯️ تحلیل کندل استیک",
        "bollinger_bands": "📊 باندهای بولینگر",
        "stochastic": "📈 تحلیل استوکاستیک",
        "macd_divergence": "🌊 واگرایی MACD",
        "b_pivot": "🎯 نقاط محوری",
        "c_trend_lines": "📐 خطوط روند",
        "fibonacci_strategy": "🌀 استراتژی فیبوناچی",
        "double_top_pattern": "⛰️ الگوی دو قله",
        "triangle_pattern": "📐 الگوی مثلث",
        "wedge_pattern": "📊 الگوی گوه",
        "momentum": "🚀 تحلیل مومنتوم",
        "martingale_low": "🎰 مارتینگل پایین",
        "heikin_ashi": "🕯️ کندل هایکن آشی",
        "stoch_rsi": "📊 استوکاستیک RSI",
        "williams_alligator": "🐊 تمساح ویلیامز",
        "parabolic_sar": "📈 سار پارابولیک",
        "support_resistance": "🛡️ حمایت و مقاومت",
        
        # استراتژی‌های VIP Package
        "atr": "📊 تحلیل ATR",
        "sma_advanced": "📈 SMA پیشرفته",
        "volume_profile": "📊 پروفایل حجم",
        "vwap": "💎 تحلیل VWAP",
        "diamond_pattern": "💎 الگوی الماس",
        "crt": "🎯 تحلیل CRT",
        "p3": "🎯 سیستم P3",
        "rtm": "🔄 تحلیل RTM",
        "multi_resistance": "🛡️ مقاومت چندگانه"
    }
    
    # توضیحات تفصیلی استراتژی‌ها (بروزرسانی شده)
    STRATEGY_DESCRIPTIONS = {
        # استراتژی‌های دمو
        "demo_price_action": "نسخه دمو تحلیل حرکت قیمت - محدود به 5 تحلیل در روز",
        "demo_rsi": "نسخه دمو شاخص قدرت نسبی - محدود به 5 تحلیل در روز",
        
        # استراتژی‌های BASIC Package
        "cci_analysis": "شاخص کانال کالا برای تشخیص نقاط اشباع خرید و فروش",
        "ema_analysis": "میانگین متحرک نمایی برای تشخیص روند و نقاط ورود",
        "ichimoku": "سیستم جامع تحلیل ژاپنی با ابر ایچیموکو",
        "macd": "واگرایی همگرایی میانگین متحرک برای تشخیص تغییر روند",
        "price_action_pandas_ta": "تحلیل حرکت قیمت با کتابخانه pandas و اندیکاتورهای تکنیکال",
        "rsi": "شاخص قدرت نسبی برای شناسایی شرایط اشباع",
        "williams_r_analysis": "اندیکاتور Williams %R برای تشخیص نقاط برگشت",
        "project_price_live_binance": "دریافت قیمت‌های زنده و تحلیل آنی از صرافی بایننس",
        "ichimoku_low_signal": "سیگنال‌های کم ریسک و محافظه‌کارانه ایچیموکو",
        
        # استراتژی‌های PREMIUM Package
        "a_candlestick": "تشخیص و تحلیل الگوهای کندل استیک ژاپنی",
        "bollinger_bands": "باندهای بولینگر برای تحلیل نوسانات و نقاط ورود",
        "stochastic": "نوسان‌گر استوکاستیک برای تشخیص اشباع و نقاط برگشت",
        "macd_divergence": "تشخیص واگرایی‌های MACD برای پیش‌بینی تغییر روند",
        "b_pivot": "محاسبه و تحلیل نقاط محوری حمایت و مقاومت",
        "c_trend_lines": "ترسیم و تحلیل خطوط روند و کانال‌های قیمتی",
        "fibonacci_strategy": "استفاده از سطوح فیبوناچی ریتریسمنت برای نقاط ورود",
        "double_top_pattern": "تشخیص الگوهای دو قله و دو کف برای پیش‌بینی برگشت روند",
        "triangle_pattern": "تشخیص انواع الگوهای مثلث صعودی، نزولی و متقارن",
        "wedge_pattern": "تحلیل الگوهای گوه صعودی و نزولی",
        "momentum": "تحلیل قدرت و مومنتوم حرکت قیمت",
        "martingale_low": "استراتژی مارتینگل با ریسک پایین و مدیریت سرمایه",
        "heikin_ashi": "تحلیل با کندل‌های هایکن آشی برای تشخیص روند",
        "stoch_rsi": "ترکیب استوکاستیک و RSI برای دقت بیشتر",
        "williams_alligator": "سیستم تمساح ویلیامز برای تشخیص روند",
        "parabolic_sar": "سیستم سار پارابولیک برای تعیین نقاط توقف",
        "support_resistance": "تشخیص خودکار سطوح حمایت و مقاومت",
        
        # استراتژی‌های VIP Package
        "atr": "میانگین دامنه واقعی برای محاسبه نوسانات و تنظیم stop loss",
        "sma_advanced": "میانگین متحرک ساده با تحلیل‌های پیشرفته و چندتایم‌فریمه",
        "volume_profile": "تحلیل پروفایل حجم معاملات برای شناسایی نواحی مهم",
        "vwap": "میانگین موزون حجمی برای شناسایی قیمت منصفانه",
        "diamond_pattern": "تشخیص الگوی نادر و قوی الماس",
        "crt": "سیستم تحلیل CRT پیشرفته برای شناسایی روندها",
        "p3": "سیستم تحلیل P3 برای پیش‌بینی نقاط عطف",
        "rtm": "سیستم RTM پیشرفته برای تحلیل ریسک و بازده",
        "multi_resistance": "تحلیل چند سطحی حمایت و مقاومت با دقت بالا"
    }
    
    # دسته‌بندی استراتژی‌ها بر اساس نوع (بروزرسانی شده)
    STRATEGY_CATEGORIES = {
        "demo": ["demo_price_action", "demo_rsi"],
        "technical_indicators": [
            "cci_analysis", "ema_analysis", "macd", "rsi", "williams_r_analysis",
            "bollinger_bands", "stochastic", "atr", "sma_advanced", "vwap",
            "stoch_rsi", "williams_alligator", "parabolic_sar"
        ],
        "pattern_recognition": [
            "double_top_pattern", "triangle_pattern", "wedge_pattern", "diamond_pattern"
        ],
        "price_action": [
            "price_action_pandas_ta", "a_candlestick", "heikin_ashi"
        ],
        "trend_analysis": [
            "ichimoku", "ichimoku_low_signal", "c_trend_lines",
            "fibonacci_strategy", "b_pivot", "support_resistance"
        ],
        "volume_analysis": [
            "volume_profile", "project_price_live_binance"
        ],
        "advanced_systems": [
            "momentum", "martingale_low", "crt", "p3", "rtm", "multi_resistance"
        ],
        "divergence_analysis": [
            "macd_divergence"
        ]
    }
    
    # تنظیمات ارزها و جفت ارزها
    SUPPORTED_SYMBOLS = [
        "BTC", "ETH", "BNB", "ADA", "XRP", "DOT", "LINK", "LTC", 
        "UNI", "AAVE", "SUSHI", "COMP", "MKR", "YFI", "SNX", "CRV",
        "SOL", "AVAX", "MATIC", "ALGO", "ATOM", "LUNA", "NEAR", "FTM",
        "SHIB", "DOGE", "ICP", "VET", "THETA", "FIL", "TRX", "EOS"
    ]
    
    SUPPORTED_CURRENCIES = ["USDT", "BUSD", "USD", "EUR", "BTC", "ETH", "BNB", "USDC"]
    
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
    
    # محدودیت‌های تایم‌فریم بر اساس پکیج (بروزرسانی شده)
    PACKAGE_TIMEFRAME_LIMITS = {
        "demo": ["1h", "4h", "1d"],
        "basic": ["15m", "30m", "1h", "4h", "1d", "1w"],
        "premium": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
        "vip": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    }
    
    # برای backward compatibility
    PACKAGE_TIMEFRAME_LIMITS["free"] = PACKAGE_TIMEFRAME_LIMITS["demo"]
    
    # تنظیمات رفرال
    REFERRAL_ENABLED = True
    REFERRAL_COMMISSION_PERCENT = 10  # درصد
    MIN_REFERRAL_PAYOUT = 50000      # تومان
    WELCOME_BONUS = 1000             # امتیاز
    FREE_TRIAL_DAYS = 3              # روز
    
    # ✅ تنظیمات رفرال (اضافه شده)
    REFERRAL_SETTINGS = {
        'bonus_amount': 50000,  # 50 هزار تومان
        'min_withdraw': 100000,  # 100 هزار تومان
        'commission_percentage': 0.1,  # 10%
        'max_levels': 3
    }
    
    # تنظیمات بکاپ
    AUTO_BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 24
    MAX_BACKUP_FILES = 7
    
    # ✅ تنظیمات بکاپ (اضافه شده)
    BACKUP_SETTINGS = {
        'auto_backup': True,
        'backup_interval': 3600,  # 1 hour
        'backup_retention': 30,   # 30 days
        'backup_compression': True
    }
    
    # ✅ تنظیمات CSV (کامل شده برای رفع خطا)
    CSV_SETTINGS = {
        "encoding": "utf-8-sig",
        "delimiter": ",",
        "quotechar": '"',
        "create_backup": True,
        "backup_on_write": True,
        "headers": {
            "users": [
                "telegram_id", "username", "first_name", "last_name", "phone_number",
                "package", "expiry_date", "balance", "referral_code", "referred_by",
                "is_blocked", "entry_date", "last_activity", "api_calls_count",
                "daily_limit", "security_token"
            ],
            "admins": [
                "telegram_id", "username", "first_name", "last_name", "role",
                "permissions", "entry_date", "last_activity", "is_active"
            ],
            "transactions": [
                "id", "user_id", "transaction_type", "amount", "currency",
                "status", "payment_method", "gateway_ref", "date", "description"
            ],
            "pending_payments": [  # ✅ اضافه شده
                "id", "user_id", "amount", "package", "payment_method",
                "status", "created_at", "gateway_ref", "callback_data"
            ],
            "payment_log": [  # ✅ اضافه شده
                "id", "user_id", "amount", "status", "gateway", "ref_id",
                "created_at", "completed_at", "description"
            ],
            "settings": [  # ✅ اضافه شده
                "key", "value", "description", "updated_at"
            ]
        }
    }
    
    # ✅ تنظیمات امنیتی (اضافه شده)
    SECURITY_SETTINGS = {
        'max_login_attempts': 5,
        'lockout_duration': 3600,  # 1 hour
        'session_timeout': 86400,  # 24 hours
        'require_phone_verification': False,
        'enable_2fa': False
    }
    
    # ✅ کانال‌ها و گروه‌ها (اضافه شده)
    CHANNELS = {
        'main_channel': '@mrtrader_channel',
        'support_group': '@mrtrader_support',
        'announcements': '@mrtrader_news'
    }
    
    # ✅ تنظیمات پرداخت (اضافه شده)
    PAYMENT_SETTINGS = {
        'zarinpal_merchant': 'your_zarinpal_merchant_id',
        'idpay_api_key': 'your_idpay_api_key',
        'callback_url': 'https://yoursite.com/callback',
        'currency': 'IRT',  # Iranian Toman
        'min_payment': 10000,
        'max_payment': 10000000
    }
    
    # ✅ تنظیمات کش (اضافه شده)
    CACHE_SETTINGS = {
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0,
        'cache_ttl': 300,  # 5 minutes
        'max_cache_size': 1000
    }
    
    # ✅ تنظیمات نوتیفیکیشن (اضافه شده)
    NOTIFICATION_SETTINGS = {
        'enable_email': False,
        'enable_sms': False,
        'enable_telegram': True,
        'admin_notifications': True
    }
    
    # ✅ تنظیمات monitoring (اضافه شده)
    MONITORING = {
        'enable_metrics': True,
        'metrics_interval': 60,  # 1 minute
        'alert_threshold': 0.9,
        'health_check_interval': 30
    }
    
    # ✅ تنظیمات پیام‌ها (اضافه شده)
    MESSAGE_SETTINGS = {
        'max_message_length': 4096,
        'typing_delay': 0.5,
        'delete_after_seconds': 300,
        'enable_markdown': True
    }
    
    # پیام‌های سیستم (بروزرسانی شده)
    MESSAGES = {
        "welcome": (
            "🤖 **به ربات MrTrader خوش آمدید!**\n\n"
            "من یک ربات هوشمند برای تحلیل بازار ارزهای دیجیتال هستم.\n"
            "35 استراتژی پیشرفته در اختیار شما قرار دارم.\n\n"
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
            "🥉 Basic: {basic_price:,} تومان (9 استراتژی)\n"
            "🥈 Premium: {premium_price:,} تومان (26 استراتژی)\n"
            "👑 VIP: {vip_price:,} تومان (35 استراتژی)"
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
            "💾 نتیجه از کش (آخرین بروزرسانی: {time})"
        ),
        "fresh_result": (
            "🔄 تحلیل جدید انجام شد"
        ),
        "maintenance": (
            "🔧 سیستم در حال تعمیر و نگهداری است.\n"
            "لطفاً کمی بعد مراجعه کنید."
        ),
        "demo_limit": (
            "🆓 محدودیت دمو: {used}/{limit} تحلیل استفاده شده.\n"
            "برای دسترسی نامحدود، پکیج خود را ارتقا دهید."
        ),
        "api_error": (
            "⚠️ خطا در دریافت داده‌ها از سرور.\n"
            "لطفاً کمی بعد دوباره تلاش کنید."
        ),
        "invalid_input": (
            "❌ داده‌های ورودی نامعتبر است.\n"
            "لطفاً پارامترهای صحیح را انتخاب کنید."
        ),
        "csv_error": (
            "❌ خطا در دسترسی به فایل CSV.\n"
            "لطفاً با پشتیبانی تماس بگیرید."
        ),
        "user_not_found": (
            "❌ کاربر یافت نشد.\n"
            "لطفاً ابتدا دستور /start را ارسال کنید."
        )
    }
    
    # تنظیمات شبکه
    REQUEST_TIMEOUT = 30  # ثانیه
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # ثانیه
    
    # تنظیمات محدودیت دمو
    DEMO_DAILY_LIMIT = 5
    DEMO_MONTHLY_LIMIT = 50
    
    @classmethod
    def ensure_directories_exist(cls):
        """ایجاد پوشه‌ها و فایل‌های مورد نیاز"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.BACKUPS_DIR,
            cls.BACKUP_DIRECTORY,  # ✅ اضافه شده
            cls.REPORTS_DIR,
            cls.CONFIG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # ✅ ایجاد فایل‌های CSV در صورت عدم وجود
        cls.ensure_csv_files_exist()
    
    @classmethod
    def ensure_csv_files_exist(cls):
        """ایجاد فایل‌های CSV با header های مناسب در صورت عدم وجود - ✅ کامل شده"""
        csv_files = {
            cls.USER_CSV_FILE: cls.CSV_SETTINGS["headers"]["users"],
            cls.ADMIN_CSV_FILE: cls.CSV_SETTINGS["headers"]["admins"], 
            cls.TRANSACTIONS_CSV_FILE: cls.CSV_SETTINGS["headers"]["transactions"],
            cls.PENDING_PAYMENTS_CSV: cls.CSV_SETTINGS["headers"]["pending_payments"],  # ✅ اضافه شده
            cls.PAYMENT_LOG_CSV: cls.CSV_SETTINGS["headers"]["payment_log"],  # ✅ اضافه شده
            cls.SETTINGS_CSV_FILE: cls.CSV_SETTINGS["headers"]["settings"]  # ✅ اضافه شده
        }
        
        import csv
        
        for file_path, headers in csv_files.items():
            file_obj = Path(file_path)
            if not file_obj.exists():
                try:
                    with open(file_path, 'w', newline='', encoding=cls.CSV_SETTINGS["encoding"]) as f:
                        writer = csv.writer(f, delimiter=cls.CSV_SETTINGS["delimiter"])
                        writer.writerow(headers)
                    print(f"✅ Created CSV file: {file_path}")
                except Exception as e:
                    print(f"❌ Error creating CSV file {file_path}: {e}")
    
    @classmethod
    def validate_config(cls) -> bool:  # ✅ تغییر از Dict به bool
        """اعتبارسنجی تنظیمات - ✅ Fixed return type"""
        try:
            errors = []
            warnings = []
            
            # بررسی متغیرهای ضروری
            if not cls.BOT_TOKEN:
                errors.append("BOT_TOKEN is required")
            
            if cls.ADMIN_USER_ID == 0:
                warnings.append("ADMIN_USER_ID not set")
            
            if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-here":
                warnings.append("SECRET_KEY should be changed from default")
            
            # بررسی پوشه‌ها و فایل‌ها
            try:
                cls.ensure_directories_exist()
            except Exception as e:
                errors.append(f"Cannot create directories: {e}")
            
            # بررسی فایل config
            config_file = cls.CONFIG_DIR / "api_servers_config.json"
            if not config_file.exists():
                warnings.append("API servers config file not found")
            
            # ✅ بررسی فایل‌های CSV
            csv_files = [cls.USER_CSV_FILE, cls.ADMIN_CSV_FILE, cls.TRANSACTIONS_CSV_FILE]
            for csv_file in csv_files:
                if not Path(csv_file).exists():
                    warnings.append(f"CSV file not found: {csv_file}")
            
            # نمایش warnings
            if warnings:
                for warning in warnings:
                    print(f"⚠️ Warning: {warning}")
            
            # نمایش errors
            if errors:
                for error in errors:
                    print(f"❌ Error: {error}")
                return False
            
            print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    @classmethod
    def get_database_url(cls) -> str:
        """دریافت URL پایگاه داده"""
        return f"sqlite:///{cls.DATABASE_FILE}"
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """بررسی مدیر بودن کاربر"""
        return user_id == cls.ADMIN_USER_ID or user_id in cls.ADMINS
    
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
    def get_strategy_category(cls, strategy: str) -> str:
        """دریافت دسته‌بندی استراتژی"""
        for category, strategies in cls.STRATEGY_CATEGORIES.items():
            if strategy in strategies:
                return category
        return "general"
    
    @classmethod
    def get_package_timeframes(cls, package_name: str) -> List[str]:
        """دریافت تایم‌فریم‌های مجاز برای پکیج"""
        return cls.PACKAGE_TIMEFRAME_LIMITS.get(package_name, cls.SUPPORTED_TIMEFRAMES)
    
    @classmethod
    def is_timeframe_allowed_for_package(cls, timeframe: str, package_name: str) -> bool:
        """بررسی مجاز بودن تایم‌فریم برای پکیج"""
        allowed_timeframes = cls.get_package_timeframes(package_name)
        return timeframe in allowed_timeframes
    
    @classmethod
    def get_all_strategies(cls) -> List[str]:
        """دریافت لیست همه استراتژی‌ها"""
        all_strategies = set()
        for package_strategies in cls.PACKAGE_HIERARCHY.values():
            all_strategies.update(package_strategies.get("strategies", []))
        return sorted(list(all_strategies))
    
    @classmethod
    def get_strategy_package_level(cls, strategy: str) -> str:
        """دریافت کمترین سطح پکیج مورد نیاز برای استراتژی"""
        # ترتیب اولویت از پایین‌ترین سطح
        package_order = ["demo", "basic", "premium", "vip"]
        
        for package_name in package_order:
            if strategy in cls.get_package_strategies(package_name):
                return package_name
        
        return "premium"  # پیش‌فرض
    
    @classmethod
    def get_demo_strategies(cls) -> List[str]:
        """دریافت استراتژی‌های دمو"""
        return cls.PACKAGE_HIERARCHY.get("demo", {}).get("strategies", [])
    
    @classmethod
    def is_demo_strategy(cls, strategy: str) -> bool:
        """بررسی دمو بودن استراتژی"""
        return strategy in cls.get_demo_strategies()
    
    @classmethod
    def get_package_daily_limit(cls, package_name: str) -> int:
        """دریافت محدودیت روزانه پکیج"""
        return cls.PACKAGE_HIERARCHY.get(package_name, {}).get("daily_limit", 5)
    
    @classmethod
    def get_package_info(cls, package_name: str) -> Dict[str, any]:  # ✅ اضافه شده
        """دریافت اطلاعات کامل پکیج"""
        return cls.PACKAGES.get(package_name, cls.PACKAGES['demo'])
    
    @classmethod
    def load_from_env(cls):
        """بارگذاری تنظیمات از متغیرهای محیطی"""
        # این متد می‌تواند برای بارگذاری تنظیمات اضافی استفاده شود
        pass


# ایجاد پوشه‌ها و فایل‌های مورد نیاز هنگام import
Config.ensure_directories_exist()

# ✅ Export برای استفاده آسان‌تر
__all__ = ['Config']