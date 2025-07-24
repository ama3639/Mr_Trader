"""
مدل کاربر برای MrTrader Bot
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class UserStatus(Enum):
    """وضعیت کاربر"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"


class PackageType(Enum):
    """نوع پکیج کاربر"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"


@dataclass
class UserModel:
    """کلاس مدل کاربر"""
    
    # اطلاعات اصلی
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # وضعیت حساب
    status: UserStatus = UserStatus.ACTIVE
    package_type: PackageType = PackageType.FREE
    registration_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    # امتیازات و آمار
    user_points: int = 0
    total_signals_received: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    
    # تنظیمات کاربر
    language: str = "fa"
    timezone: str = "Asia/Tehran"
    notifications_enabled: bool = True
    
    # اطلاعات رفرال
    referrer_id: Optional[int] = None
    referral_code: Optional[str] = None
    referral_count: int = 0
    referral_earnings: float = 0.0
    
    # تنظیمات تحلیل
    preferred_strategies: Optional[str] = None  # JSON string
    risk_tolerance: str = "medium"  # low, medium, high
    max_signals_per_day: int = 10
    
    # اطلاعات اضافی
    phone_number: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # آمار عملکرد
    total_profit: float = 0.0
    total_loss: float = 0.0
    win_rate: float = 0.0
    average_profit: float = 0.0
    
    # محدودیت‌ها
    daily_requests: int = 0
    daily_limit: int = 100
    is_vip: bool = False
    is_blocked: bool = False
    
    def __post_init__(self):
        """تنظیمات پس از ایجاد شیء"""
        if self.registration_date is None:
            self.registration_date = datetime.now()
        
        if self.last_activity is None:
            self.last_activity = datetime.now()
    
    @property
    def full_name(self) -> str:
        """نام کامل کاربر"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User_{self.telegram_id}"
    
    @property
    def display_name(self) -> str:
        """نام نمایشی کاربر"""
        if self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User_{self.telegram_id}"
    
    @property
    def is_premium(self) -> bool:
        """بررسی پکیج پریمیوم"""
        return self.package_type in [PackageType.PREMIUM, PackageType.VIP, PackageType.GHOST]
    
    @property
    def is_expired(self) -> bool:
        """بررسی انقضای پکیج"""
        if self.expiry_date is None:
            return False
        return datetime.now() > self.expiry_date
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """روزهای باقیمانده تا انقضا"""
        if self.expiry_date is None:
            return None
        delta = self.expiry_date - datetime.now()
        return max(0, delta.days)
    
    def calculate_win_rate(self) -> float:
        """محاسبه نرخ موفقیت"""
        total_trades = self.successful_trades + self.failed_trades
        if total_trades == 0:
            return 0.0
        return (self.successful_trades / total_trades) * 100
    
    def update_stats(self, profit: float, is_successful: bool):
        """بروزرسانی آمار معاملات"""
        if is_successful:
            self.successful_trades += 1
            self.total_profit += profit
        else:
            self.failed_trades += 1
            self.total_loss += abs(profit)
        
        self.win_rate = self.calculate_win_rate()
        total_trades = self.successful_trades + self.failed_trades
        if total_trades > 0:
            self.average_profit = (self.total_profit - self.total_loss) / total_trades
    
    def add_points(self, points: int, reason: str = ""):
        """اضافه کردن امتیاز"""
        self.user_points += points
    
    def deduct_points(self, points: int, reason: str = "") -> bool:
        """کم کردن امتیاز"""
        if self.user_points >= points:
            self.user_points -= points
            return True
        return False
    
    def has_access_to_strategy(self, strategy_name: str) -> bool:
        """بررسی دسترسی به استراتژی"""
        # نمونه لاجیک دسترسی
        free_strategies = ['basic_rsi', 'simple_ma']
        premium_strategies = ['advanced_rsi', 'bollinger_bands', 'macd']
        vip_strategies = ['composite_signals', 'ai_prediction']
        
        if self.package_type == PackageType.FREE:
            return strategy_name in free_strategies
        elif self.package_type == PackageType.BASIC:
            return strategy_name in free_strategies + ['basic_trend']
        elif self.package_type == PackageType.PREMIUM:
            return strategy_name in free_strategies + premium_strategies
        elif self.package_type in [PackageType.VIP, PackageType.GHOST]:
            return True
        
        return False
    
    def can_receive_signals(self) -> bool:
        """بررسی امکان دریافت سیگنال"""
        if self.is_blocked or self.status != UserStatus.ACTIVE:
            return False
        
        if self.is_expired and self.package_type != PackageType.FREE:
            return False
        
        if self.daily_requests >= self.daily_limit:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'status': self.status.value,
            'package_type': self.package_type.value,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'user_points': self.user_points,
            'total_signals_received': self.total_signals_received,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'language': self.language,
            'timezone': self.timezone,
            'notifications_enabled': self.notifications_enabled,
            'referrer_id': self.referrer_id,
            'referral_code': self.referral_code,
            'referral_count': self.referral_count,
            'referral_earnings': self.referral_earnings,
            'preferred_strategies': self.preferred_strategies,
            'risk_tolerance': self.risk_tolerance,
            'max_signals_per_day': self.max_signals_per_day,
            'phone_number': self.phone_number,
            'email': self.email,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'win_rate': self.win_rate,
            'average_profit': self.average_profit,
            'daily_requests': self.daily_requests,
            'daily_limit': self.daily_limit,
            'is_vip': self.is_vip,
            'is_blocked': self.is_blocked
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserModel':
        """ایجاد از dictionary"""
        # تبدیل تاریخ‌ها
        for date_field in ['registration_date', 'last_activity', 'expiry_date']:
            if data.get(date_field):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # تبدیل enum ها
        if 'status' in data:
            data['status'] = UserStatus(data['status'])
        if 'package_type' in data:
            data['package_type'] = PackageType(data['package_type'])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """نمایش رشته‌ای"""
        return f"User({self.telegram_id}, {self.display_name}, {self.package_type.value})"
    
    def __repr__(self) -> str:
        """نمایش تفصیلی"""
        return f"UserModel(telegram_id={self.telegram_id}, name='{self.display_name}', package='{self.package_type.value}')"


# نمونه کارخانه برای ایجاد کاربر
class UserFactory:
    """کارخانه ایجاد کاربر"""
    
    @staticmethod
    def create_new_user(telegram_id: int, username: str = None, first_name: str = None, 
                       last_name: str = None, referrer_id: int = None) -> UserModel:
        """ایجاد کاربر جدید"""
        return UserModel(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            referrer_id=referrer_id,
            registration_date=datetime.now(),
            last_activity=datetime.now()
        )
    
    @staticmethod
    def create_premium_user(telegram_id: int, package_type: PackageType, 
                           days: int = 30) -> UserModel:
        """ایجاد کاربر پریمیوم"""
        expiry_date = datetime.now().replace(hour=23, minute=59, second=59) + \
                     datetime.timedelta(days=days)
        
        return UserModel(
            telegram_id=telegram_id,
            package_type=package_type,
            expiry_date=expiry_date,
            daily_limit=200 if package_type == PackageType.VIP else 150
        )


# Export
__all__ = ['UserModel', 'UserStatus', 'PackageType', 'UserFactory']