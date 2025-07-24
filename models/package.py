"""
مدل پکیج - مدیریت اطلاعات پکیج‌های کاربران
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
import json

class PackageType(Enum):
    """نوع پکیج"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    GHOST = "ghost"

class PackageStatus(Enum):
    """وضعیت پکیج"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class SubscriptionType(Enum):
    """نوع اشتراک"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

@dataclass
class PackageFeatures:
    """ویژگی‌های پکیج"""
    strategies: List[str] = field(default_factory=list)
    max_daily_requests: int = 0
    max_monthly_requests: int = 0
    has_live_support: bool = False
    has_priority_support: bool = False
    has_advanced_analytics: bool = False
    has_portfolio_tracking: bool = False
    has_custom_alerts: bool = False
    has_api_access: bool = False
    concurrent_analyses: int = 1
    history_retention_days: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "strategies": self.strategies,
            "max_daily_requests": self.max_daily_requests,
            "max_monthly_requests": self.max_monthly_requests,
            "has_live_support": self.has_live_support,
            "has_priority_support": self.has_priority_support,
            "has_advanced_analytics": self.has_advanced_analytics,
            "has_portfolio_tracking": self.has_portfolio_tracking,
            "has_custom_alerts": self.has_custom_alerts,
            "has_api_access": self.has_api_access,
            "concurrent_analyses": self.concurrent_analyses,
            "history_retention_days": self.history_retention_days
        }

@dataclass
class PackagePricing:
    """قیمت‌گذاری پکیج"""
    monthly_price: float = 0.0
    quarterly_price: float = 0.0
    yearly_price: float = 0.0
    lifetime_price: float = 0.0
    currency: str = "USD"
    discount_percentage: float = 0.0
    promotional_price: Optional[float] = None
    promotional_expires: Optional[datetime] = None
    
    def get_effective_price(self, subscription_type: SubscriptionType) -> float:
        """دریافت قیمت مؤثر"""
        base_prices = {
            SubscriptionType.MONTHLY: self.monthly_price,
            SubscriptionType.QUARTERLY: self.quarterly_price,
            SubscriptionType.YEARLY: self.yearly_price,
            SubscriptionType.LIFETIME: self.lifetime_price
        }
        
        base_price = base_prices.get(subscription_type, 0.0)
        
        # بررسی قیمت تبلیغاتی
        if (self.promotional_price and 
            self.promotional_expires and 
            datetime.now() < self.promotional_expires):
            return self.promotional_price
        
        # اعمال تخفیف
        if self.discount_percentage > 0:
            return base_price * (1 - self.discount_percentage / 100)
        
        return base_price
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "monthly_price": self.monthly_price,
            "quarterly_price": self.quarterly_price,
            "yearly_price": self.yearly_price,
            "lifetime_price": self.lifetime_price,
            "currency": self.currency,
            "discount_percentage": self.discount_percentage,
            "promotional_price": self.promotional_price,
            "promotional_expires": self.promotional_expires.isoformat() if self.promotional_expires else None
        }

@dataclass
class Package:
    """مدل کامل پکیج"""
    package_id: str
    name: str
    package_type: PackageType
    title: str
    description: str
    features: PackageFeatures
    pricing: PackagePricing
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """پردازش پس از ایجاد"""
        # ویژگی‌های پیش‌فرض بر اساس نوع پکیج
        if not self.features.strategies:
            self.features.strategies = self._get_default_strategies()
        
        if self.features.max_daily_requests == 0:
            self.features.max_daily_requests = self._get_default_daily_requests()
    
    def _get_default_strategies(self) -> List[str]:
        """استراتژی‌های پیش‌فرض هر پکیج"""
        strategy_map = {
            PackageType.FREE: ["basic_demo"],
            PackageType.BASIC: ["price_action", "simple_ma", "rsi_basic"],
            PackageType.PREMIUM: [
                "price_action", "simple_ma", "rsi_basic", 
                "ichimoku", "fibonacci", "macd", "bollinger_bands"
            ],
            PackageType.VIP: [
                "price_action", "simple_ma", "rsi_basic", 
                "ichimoku", "fibonacci", "macd", "bollinger_bands",
                "elliott_wave", "harmonic_patterns", "volume_analysis"
            ],
            PackageType.GHOST: [
                "all_strategies", "ai_predictions", "market_sentiment",
                "whale_tracking", "institutional_flow", "dark_pool_analysis"
            ]
        }
        return strategy_map.get(self.package_type, [])
    
    def _get_default_daily_requests(self) -> int:
        """محدودیت درخواست روزانه پیش‌فرض"""
        request_limits = {
            PackageType.FREE: 5,
            PackageType.BASIC: 50,
            PackageType.PREMIUM: 200,
            PackageType.VIP: 500,
            PackageType.GHOST: 9999  # نامحدود
        }
        return request_limits.get(self.package_type, 0)
    
    def has_strategy(self, strategy: str) -> bool:
        """بررسی دسترسی به استراتژی"""
        return (strategy in self.features.strategies or 
                "all_strategies" in self.features.strategies)
    
    def get_duration_days(self, subscription_type: SubscriptionType) -> int:
        """دریافت مدت زمان بر حسب روز"""
        duration_map = {
            SubscriptionType.MONTHLY: 30,
            SubscriptionType.QUARTERLY: 90,
            SubscriptionType.YEARLY: 365,
            SubscriptionType.LIFETIME: 365 * 100  # 100 سال
        }
        return duration_map.get(subscription_type, 30)
    
    def calculate_expiry_date(self, 
                            start_date: datetime, 
                            subscription_type: SubscriptionType) -> datetime:
        """محاسبه تاریخ انقضا"""
        duration_days = self.get_duration_days(subscription_type)
        return start_date + timedelta(days=duration_days)
    
    def get_package_level(self) -> int:
        """سطح پکیج (برای مقایسه)"""
        levels = {
            PackageType.FREE: 0,
            PackageType.BASIC: 1,
            PackageType.PREMIUM: 2,
            PackageType.VIP: 3,
            PackageType.GHOST: 4
        }
        return levels.get(self.package_type, 0)
    
    def can_upgrade_to(self, target_package: 'Package') -> bool:
        """بررسی امکان ارتقا به پکیج دیگر"""
        return target_package.get_package_level() > self.get_package_level()
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "package_id": self.package_id,
            "name": self.name,
            "package_type": self.package_type.value,
            "title": self.title,
            "description": self.description,
            "features": self.features.to_dict(),
            "pricing": self.pricing.to_dict(),
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "sort_order": self.sort_order,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
            "package_level": self.get_package_level()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Package':
        """ایجاد از دیکشنری"""
        # پردازش features
        features_data = data.get("features", {})
        features = PackageFeatures(
            strategies=features_data.get("strategies", []),
            max_daily_requests=features_data.get("max_daily_requests", 0),
            max_monthly_requests=features_data.get("max_monthly_requests", 0),
            has_live_support=features_data.get("has_live_support", False),
            has_priority_support=features_data.get("has_priority_support", False),
            has_advanced_analytics=features_data.get("has_advanced_analytics", False),
            has_portfolio_tracking=features_data.get("has_portfolio_tracking", False),
            has_custom_alerts=features_data.get("has_custom_alerts", False),
            has_api_access=features_data.get("has_api_access", False),
            concurrent_analyses=features_data.get("concurrent_analyses", 1),
            history_retention_days=features_data.get("history_retention_days", 30)
        )
        
        # پردازش pricing
        pricing_data = data.get("pricing", {})
        pricing = PackagePricing(
            monthly_price=pricing_data.get("monthly_price", 0.0),
            quarterly_price=pricing_data.get("quarterly_price", 0.0),
            yearly_price=pricing_data.get("yearly_price", 0.0),
            lifetime_price=pricing_data.get("lifetime_price", 0.0),
            currency=pricing_data.get("currency", "USD"),
            discount_percentage=pricing_data.get("discount_percentage", 0.0),
            promotional_price=pricing_data.get("promotional_price"),
            promotional_expires=datetime.fromisoformat(pricing_data["promotional_expires"]) if pricing_data.get("promotional_expires") else None
        )
        
        return cls(
            package_id=data["package_id"],
            name=data["name"],
            package_type=PackageType(data["package_type"]),
            title=data["title"],
            description=data["description"],
            features=features,
            pricing=pricing,
            is_active=data.get("is_active", True),
            is_featured=data.get("is_featured", False),
            sort_order=data.get("sort_order", 0),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"])
        )

class PackageManager:
    """مدیریت پکیج‌ها"""
    
    @staticmethod
    def get_default_packages() -> List[Package]:
        """دریافت پکیج‌های پیش‌فرض"""
        packages = []
        
        # پکیج رایگان
        free_package = Package(
            package_id="free",
            name="Free",
            package_type=PackageType.FREE,
            title="پکیج رایگان",
            description="دسترسی محدود به امکانات پایه",
            features=PackageFeatures(
                strategies=["basic_demo"],
                max_daily_requests=5,
                max_monthly_requests=50,
                concurrent_analyses=1,
                history_retention_days=7
            ),
            pricing=PackagePricing(
                monthly_price=0.0,
                quarterly_price=0.0,
                yearly_price=0.0,
                lifetime_price=0.0
            ),
            sort_order=1
        )
        packages.append(free_package)
        
        # پکیج پایه
        basic_package = Package(
            package_id="basic",
            name="Basic",
            package_type=PackageType.BASIC,
            title="پکیج پایه",
            description="دسترسی به استراتژی‌های پایه و تحلیل‌های ساده",
            features=PackageFeatures(
                strategies=["price_action", "simple_ma", "rsi_basic"],
                max_daily_requests=50,
                max_monthly_requests=1000,
                concurrent_analyses=2,
                history_retention_days=30
            ),
            pricing=PackagePricing(
                monthly_price=29.99,
                quarterly_price=79.99,
                yearly_price=299.99,
                currency="USD"
            ),
            sort_order=2
        )
        packages.append(basic_package)
        
        # پکیج ویژه
        premium_package = Package(
            package_id="premium",
            name="Premium",
            package_type=PackageType.PREMIUM,
            title="پکیج ویژه",
            description="دسترسی به استراتژی‌های پیشرفته و تحلیل‌های حرفه‌ای",
            features=PackageFeatures(
                strategies=[
                    "price_action", "simple_ma", "rsi_basic", 
                    "ichimoku", "fibonacci", "macd", "bollinger_bands"
                ],
                max_daily_requests=200,
                max_monthly_requests=5000,
                has_live_support=True,
                has_advanced_analytics=True,
                concurrent_analyses=5,
                history_retention_days=90
            ),
            pricing=PackagePricing(
                monthly_price=79.99,
                quarterly_price=199.99,
                yearly_price=799.99,
                currency="USD"
            ),
            is_featured=True,
            sort_order=3
        )
        packages.append(premium_package)
        
        # پکیج VIP
        vip_package = Package(
            package_id="vip",
            name="VIP",
            package_type=PackageType.VIP,
            title="پکیج VIP",
            description="دسترسی کامل به تمام استراتژی‌ها و پشتیبانی اولویت‌دار",
            features=PackageFeatures(
                strategies=[
                    "price_action", "simple_ma", "rsi_basic", 
                    "ichimoku", "fibonacci", "macd", "bollinger_bands",
                    "elliott_wave", "harmonic_patterns", "volume_analysis"
                ],
                max_daily_requests=500,
                max_monthly_requests=10000,
                has_live_support=True,
                has_priority_support=True,
                has_advanced_analytics=True,
                has_portfolio_tracking=True,
                has_custom_alerts=True,
                concurrent_analyses=10,
                history_retention_days=365
            ),
            pricing=PackagePricing(
                monthly_price=199.99,
                quarterly_price=499.99,
                yearly_price=1999.99,
                currency="USD"
            ),
            sort_order=4
        )
        packages.append(vip_package)
        
        # پکیج شبح
        ghost_package = Package(
            package_id="ghost",
            name="Ghost",
            package_type=PackageType.GHOST,
            title="پکیج شبح",
            description="دسترسی نامحدود به تمام امکانات و تحلیل‌های پیشرفته",
            features=PackageFeatures(
                strategies=[
                    "all_strategies", "ai_predictions", "market_sentiment",
                    "whale_tracking", "institutional_flow", "dark_pool_analysis"
                ],
                max_daily_requests=9999,
                max_monthly_requests=99999,
                has_live_support=True,
                has_priority_support=True,
                has_advanced_analytics=True,
                has_portfolio_tracking=True,
                has_custom_alerts=True,
                has_api_access=True,
                concurrent_analyses=99,
                history_retention_days=9999
            ),
            pricing=PackagePricing(
                monthly_price=999.99,
                quarterly_price=2499.99,
                yearly_price=9999.99,
                lifetime_price=49999.99,
                currency="USD"
            ),
            sort_order=5
        )
        packages.append(ghost_package)
        
        return packages
    
    @staticmethod
    def get_package_by_type(package_type: PackageType) -> Optional[Package]:
        """دریافت پکیج بر اساس نوع"""
        packages = PackageManager.get_default_packages()
        for package in packages:
            if package.package_type == package_type:
                return package
        return None
    
    @staticmethod
    def get_available_packages() -> List[Package]:
        """دریافت پکیج‌های فعال"""
        packages = PackageManager.get_default_packages()
        return [p for p in packages if p.is_active]
    
    @staticmethod
    def calculate_upgrade_price(from_package: Package, 
                              to_package: Package, 
                              subscription_type: SubscriptionType,
                              remaining_days: int) -> float:
        """محاسبه قیمت ارتقا"""
        if not from_package.can_upgrade_to(to_package):
            return 0.0
        
        # قیمت پکیج جدید
        new_price = to_package.pricing.get_effective_price(subscription_type)
        
        # قیمت پکیج فعلی
        current_price = from_package.pricing.get_effective_price(subscription_type)
        
        # محاسبه قیمت بر اساس روزهای باقی‌مانده
        total_days = to_package.get_duration_days(subscription_type)
        daily_rate_diff = (new_price - current_price) / total_days
        
        return max(0, daily_rate_diff * remaining_days)

class PackageRepository:
    """مخزن پکیج‌ها - برای استفاده در DatabaseManager"""
    
    @staticmethod
    def create_package_schema() -> str:
        """ایجاد جدول پکیج‌ها"""
        return """
        CREATE TABLE IF NOT EXISTS packages (
            package_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            package_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            features TEXT NOT NULL,
            pricing TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_featured BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_packages_type ON packages(package_type);
        CREATE INDEX IF NOT EXISTS idx_packages_active ON packages(is_active);
        CREATE INDEX IF NOT EXISTS idx_packages_featured ON packages(is_featured);
        """
    
    @staticmethod
    def package_to_db_row(package: Package) -> Dict[str, Any]:
        """تبدیل Package به سطر دیتابیس"""
        return {
            "package_id": package.package_id,
            "name": package.name,
            "package_type": package.package_type.value,
            "title": package.title,
            "description": package.description,
            "features": json.dumps(package.features.to_dict()),
            "pricing": json.dumps(package.pricing.to_dict()),
            "is_active": package.is_active,
            "is_featured": package.is_featured,
            "sort_order": package.sort_order,
            "created_date": package.created_date.isoformat(),
            "updated_date": package.updated_date.isoformat()
        }
    
    @staticmethod
    def db_row_to_package(row: Dict[str, Any]) -> Package:
        """تبدیل سطر دیتابیس به Package"""
        features_data = json.loads(row["features"])
        features = PackageFeatures(
            strategies=features_data.get("strategies", []),
            max_daily_requests=features_data.get("max_daily_requests", 0),
            max_monthly_requests=features_data.get("max_monthly_requests", 0),
            has_live_support=features_data.get("has_live_support", False),
            has_priority_support=features_data.get("has_priority_support", False),
            has_advanced_analytics=features_data.get("has_advanced_analytics", False),
            has_portfolio_tracking=features_data.get("has_portfolio_tracking", False),
            has_custom_alerts=features_data.get("has_custom_alerts", False),
            has_api_access=features_data.get("has_api_access", False),
            concurrent_analyses=features_data.get("concurrent_analyses", 1),
            history_retention_days=features_data.get("history_retention_days", 30)
        )
        
        pricing_data = json.loads(row["pricing"])
        pricing = PackagePricing(
            monthly_price=pricing_data.get("monthly_price", 0.0),
            quarterly_price=pricing_data.get("quarterly_price", 0.0),
            yearly_price=pricing_data.get("yearly_price", 0.0),
            lifetime_price=pricing_data.get("lifetime_price", 0.0),
            currency=pricing_data.get("currency", "USD"),
            discount_percentage=pricing_data.get("discount_percentage", 0.0),
            promotional_price=pricing_data.get("promotional_price"),
            promotional_expires=datetime.fromisoformat(pricing_data["promotional_expires"]) if pricing_data.get("promotional_expires") else None
        )
        
        return Package(
            package_id=row["package_id"],
            name=row["name"],
            package_type=PackageType(row["package_type"]),
            title=row["title"],
            description=row["description"],
            features=features,
            pricing=pricing,
            is_active=bool(row["is_active"]),
            is_featured=bool(row["is_featured"]),
            sort_order=row["sort_order"],
            created_date=datetime.fromisoformat(row["created_date"]),
            updated_date=datetime.fromisoformat(row["updated_date"])
        )
