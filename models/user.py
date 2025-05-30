"""
مدل کاربر - مدیریت اطلاعات و وضعیت کاربران
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
import json

class UserStatus(Enum):
    """وضعیت کاربر"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    DELETED = "deleted"

class PackageType(Enum):
    """نوع پکیج کاربر"""
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"
    FREE = "free"

@dataclass
class UserPackage:
    """اطلاعات پکیج کاربر"""
    package_type: PackageType
    purchase_date: datetime
    expiry_date: datetime
    is_active: bool = True
    auto_renew: bool = False
    price_paid: float = 0.0
    transaction_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """بررسی انقضای پکیج"""
        return datetime.now() > self.expiry_date
    
    def days_remaining(self) -> int:
        """روزهای باقی‌مانده تا انقضا"""
        if self.is_expired():
            return 0
        return (self.expiry_date - datetime.now()).days
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "package_type": self.package_type.value,
            "purchase_date": self.purchase_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat(),
            "is_active": self.is_active,
            "auto_renew": self.auto_renew,
            "price_paid": self.price_paid,
            "transaction_id": self.transaction_id,
            "days_remaining": self.days_remaining()
        }

@dataclass
class UserStats:
    """آمار استفاده کاربر"""
    total_signals_requested: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    last_activity: Optional[datetime] = None
    favorite_strategies: List[str] = field(default_factory=list)
    favorite_symbols: List[str] = field(default_factory=list)
    total_reports_generated: int = 0
    
    def success_rate(self) -> float:
        """نرخ موفقیت تحلیل‌ها"""
        total = self.successful_analyses + self.failed_analyses
        if total == 0:
            return 0.0
        return (self.successful_analyses / total) * 100

@dataclass
class UserSettings:
    """تنظیمات شخصی کاربر"""
    language: str = "fa"
    timezone: str = "Asia/Tehran"
    notifications_enabled: bool = True
    email_reports: bool = False
    telegram_notifications: bool = True
    preferred_currency: str = "USDT"
    default_timeframe: str = "1h"
    risk_tolerance: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "language": self.language,
            "timezone": self.timezone,
            "notifications_enabled": self.notifications_enabled,
            "email_reports": self.email_reports,
            "telegram_notifications": self.telegram_notifications,
            "preferred_currency": self.preferred_currency,
            "default_timeframe": self.default_timeframe,
            "risk_tolerance": self.risk_tolerance
        }

@dataclass
class User:
    """مدل کامل کاربر"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    registration_date: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    status: UserStatus = UserStatus.ACTIVE
    is_admin: bool = False
    is_vip: bool = False
    referred_by: Optional[int] = None
    referral_code: Optional[str] = None
    current_package: Optional[UserPackage] = None
    stats: UserStats = field(default_factory=UserStats)
    settings: UserSettings = field(default_factory=UserSettings)
    notes: str = ""
    
    def __post_init__(self):
        """پردازش پس از ایجاد"""
        if not self.current_package:
            # پکیج رایگان پیش‌فرض
            self.current_package = UserPackage(
                package_type=PackageType.FREE,
                purchase_date=self.registration_date,
                expiry_date=self.registration_date + timedelta(days=30),
                price_paid=0.0
            )
    
    def get_full_name(self) -> str:
        """نام کامل کاربر"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User_{self.user_id}"
    
    def has_access_to_strategy(self, strategy: str) -> bool:
        """بررسی دسترسی به استراتژی"""
        if not self.current_package or self.current_package.is_expired():
            return strategy in ["basic_demo"]  # فقط دمو
        
        package_type = self.current_package.package_type
        
        # استراتژی‌های هر پکیج
        strategy_access = {
            PackageType.FREE: ["basic_demo"],
            PackageType.BASIC: ["price_action", "simple_ma", "rsi_basic"],
            PackageType.PREMIUM: ["price_action", "simple_ma", "rsi_basic", "ichimoku", "fibonacci"],
            PackageType.VIP: ["price_action", "simple_ma", "rsi_basic", "ichimoku", "fibonacci", "elliott_wave", "harmonic"],
            PackageType.GHOST: ["all"]  # دسترسی به همه
        }
        
        allowed_strategies = strategy_access.get(package_type, [])
        return strategy in allowed_strategies or "all" in allowed_strategies
    
    def get_package_level(self) -> int:
        """سطح پکیج کاربر (برای مقایسه)"""
        if not self.current_package:
            return 0
        
        levels = {
            PackageType.FREE: 0,
            PackageType.BASIC: 1,
            PackageType.PREMIUM: 2,
            PackageType.VIP: 3,
            PackageType.GHOST: 4
        }
        return levels.get(self.current_package.package_type, 0)
    
    def update_activity(self):
        """به‌روزرسانی آخرین فعالیت"""
        self.last_login = datetime.now()
        if self.stats.last_activity is None:
            self.stats.last_activity = datetime.now()
    
    def add_strategy_usage(self, strategy: str, success: bool = True):
        """ثبت استفاده از استراتژی"""
        self.stats.total_signals_requested += 1
        
        if success:
            self.stats.successful_analyses += 1
        else:
            self.stats.failed_analyses += 1
        
        # اضافه کردن به استراتژی‌های مورد علاقه
        if strategy not in self.stats.favorite_strategies:
            self.stats.favorite_strategies.append(strategy)
        
        # محدود کردن به 10 استراتژی برتر
        if len(self.stats.favorite_strategies) > 10:
            self.stats.favorite_strategies = self.stats.favorite_strategies[-10:]
    
    def add_symbol_usage(self, symbol: str):
        """ثبت استفاده از نماد"""
        if symbol not in self.stats.favorite_symbols:
            self.stats.favorite_symbols.append(symbol)
        
        # محدود کردن به 20 نماد برتر
        if len(self.stats.favorite_symbols) > 20:
            self.stats.favorite_symbols = self.stats.favorite_symbols[-20:]
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "registration_date": self.registration_date.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "status": self.status.value,
            "is_admin": self.is_admin,
            "is_vip": self.is_vip,
            "referred_by": self.referred_by,
            "referral_code": self.referral_code,
            "current_package": self.current_package.to_dict() if self.current_package else None,
            "stats": {
                "total_signals_requested": self.stats.total_signals_requested,
                "successful_analyses": self.stats.successful_analyses,
                "failed_analyses": self.stats.failed_analyses,
                "success_rate": self.stats.success_rate(),
                "last_activity": self.stats.last_activity.isoformat() if self.stats.last_activity else None,
                "favorite_strategies": self.stats.favorite_strategies,
                "favorite_symbols": self.stats.favorite_symbols,
                "total_reports_generated": self.stats.total_reports_generated
            },
            "settings": self.settings.to_dict(),
            "notes": self.notes,
            "full_name": self.get_full_name(),
            "package_level": self.get_package_level()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """ایجاد از دیکشنری"""
        # پردازش package
        package_data = data.get("current_package")
        current_package = None
        if package_data:
            current_package = UserPackage(
                package_type=PackageType(package_data["package_type"]),
                purchase_date=datetime.fromisoformat(package_data["purchase_date"]),
                expiry_date=datetime.fromisoformat(package_data["expiry_date"]),
                is_active=package_data.get("is_active", True),
                auto_renew=package_data.get("auto_renew", False),
                price_paid=package_data.get("price_paid", 0.0),
                transaction_id=package_data.get("transaction_id")
            )
        
        # پردازش stats
        stats_data = data.get("stats", {})
        stats = UserStats(
            total_signals_requested=stats_data.get("total_signals_requested", 0),
            successful_analyses=stats_data.get("successful_analyses", 0),
            failed_analyses=stats_data.get("failed_analyses", 0),
            last_activity=datetime.fromisoformat(stats_data["last_activity"]) if stats_data.get("last_activity") else None,
            favorite_strategies=stats_data.get("favorite_strategies", []),
            favorite_symbols=stats_data.get("favorite_symbols", []),
            total_reports_generated=stats_data.get("total_reports_generated", 0)
        )
        
        # پردازش settings
        settings_data = data.get("settings", {})
        settings = UserSettings(
            language=settings_data.get("language", "fa"),
            timezone=settings_data.get("timezone", "Asia/Tehran"),
            notifications_enabled=settings_data.get("notifications_enabled", True),
            email_reports=settings_data.get("email_reports", False),
            telegram_notifications=settings_data.get("telegram_notifications", True),
            preferred_currency=settings_data.get("preferred_currency", "USDT"),
            default_timeframe=settings_data.get("default_timeframe", "1h"),
            risk_tolerance=settings_data.get("risk_tolerance", "medium")
        )
        
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            registration_date=datetime.fromisoformat(data["registration_date"]),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            status=UserStatus(data.get("status", "active")),
            is_admin=data.get("is_admin", False),
            is_vip=data.get("is_vip", False),
            referred_by=data.get("referred_by"),
            referral_code=data.get("referral_code"),
            current_package=current_package,
            stats=stats,
            settings=settings,
            notes=data.get("notes", "")
        )

class UserRepository:
    """مخزن کاربران - برای استفاده در DatabaseManager"""
    
    @staticmethod
    def create_user_schema() -> str:
        """ایجاد جدول کاربران"""
        return """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            registration_date TEXT NOT NULL,
            last_login TEXT,
            status TEXT DEFAULT 'active',
            is_admin BOOLEAN DEFAULT 0,
            is_vip BOOLEAN DEFAULT 0,
            referred_by INTEGER,
            referral_code TEXT,
            current_package TEXT,
            stats TEXT,
            settings TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
        CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code);
        """
    
    @staticmethod
    def user_to_db_row(user: User) -> Dict[str, Any]:
        """تبدیل User به سطر دیتابیس"""
        return {
            "user_id": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "registration_date": user.registration_date.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "status": user.status.value,
            "is_admin": user.is_admin,
            "is_vip": user.is_vip,
            "referred_by": user.referred_by,
            "referral_code": user.referral_code,
            "current_package": json.dumps(user.current_package.to_dict()) if user.current_package else None,
            "stats": json.dumps(user.stats.__dict__, default=str),
            "settings": json.dumps(user.settings.to_dict()),
            "notes": user.notes
        }
    
    @staticmethod
    def db_row_to_user(row: Dict[str, Any]) -> User:
        """تبدیل سطر دیتابیس به User"""
        # پردازش package
        current_package = None
        if row.get("current_package"):
            package_data = json.loads(row["current_package"])
            current_package = UserPackage(
                package_type=PackageType(package_data["package_type"]),
                purchase_date=datetime.fromisoformat(package_data["purchase_date"]),
                expiry_date=datetime.fromisoformat(package_data["expiry_date"]),
                is_active=package_data.get("is_active", True),
                auto_renew=package_data.get("auto_renew", False),
                price_paid=package_data.get("price_paid", 0.0),
                transaction_id=package_data.get("transaction_id")
            )
        
        # پردازش stats
        stats_data = json.loads(row.get("stats", "{}"))
        stats = UserStats(
            total_signals_requested=stats_data.get("total_signals_requested", 0),
            successful_analyses=stats_data.get("successful_analyses", 0),
            failed_analyses=stats_data.get("failed_analyses", 0),
            last_activity=datetime.fromisoformat(stats_data["last_activity"]) if stats_data.get("last_activity") else None,
            favorite_strategies=stats_data.get("favorite_strategies", []),
            favorite_symbols=stats_data.get("favorite_symbols", []),
            total_reports_generated=stats_data.get("total_reports_generated", 0)
        )
        
        # پردازش settings
        settings_data = json.loads(row.get("settings", "{}"))
        settings = UserSettings(
            language=settings_data.get("language", "fa"),
            timezone=settings_data.get("timezone", "Asia/Tehran"),
            notifications_enabled=settings_data.get("notifications_enabled", True),
            email_reports=settings_data.get("email_reports", False),
            telegram_notifications=settings_data.get("telegram_notifications", True),
            preferred_currency=settings_data.get("preferred_currency", "USDT"),
            default_timeframe=settings_data.get("default_timeframe", "1h"),
            risk_tolerance=settings_data.get("risk_tolerance", "medium")
        )
        
        return User(
            user_id=row["user_id"],
            username=row.get("username"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            phone=row.get("phone"),
            registration_date=datetime.fromisoformat(row["registration_date"]),
            last_login=datetime.fromisoformat(row["last_login"]) if row.get("last_login") else None,
            status=UserStatus(row.get("status", "active")),
            is_admin=bool(row.get("is_admin", False)),
            is_vip=bool(row.get("is_vip", False)),
            referred_by=row.get("referred_by"),
            referral_code=row.get("referral_code"),
            current_package=current_package,
            stats=stats,
            settings=settings,
            notes=row.get("notes", "")
        )
