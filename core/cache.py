"""
سیستم کش برای مدیریت سیگنال‌ها و داده‌های API
"""

import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from utils.logger import logger


@dataclass
class CacheEntry:
    """ورودی کش"""
    data: Any
    created_at: datetime
    expires_at: datetime
    strategy: str
    symbol: str
    currency: str
    timeframe: str


class Cache:
    """مدیریت کش سیگنال‌ها و داده‌های API"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._signal_cache_duration = 60  # ثانیه (1 دقیقه)
        self._price_cache_duration = 30   # ثانیه (30 ثانیه)
        self._default_cache_duration = 300  # ثانیه (5 دقیقه)
    
    def _generate_cache_key(self, strategy: str, symbol: str, currency: str, timeframe: str, cache_type: str = "signal") -> str:
        """تولید کلید یکتا برای کش"""
        try:
            # ترکیب پارامترها برای ایجاد کلید یکتا
            key_data = f"{cache_type}:{strategy}:{symbol}:{currency}:{timeframe}"
            
            # ایجاد hash برای کلید کوتاه‌تر و یکتا
            return hashlib.md5(key_data.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"{cache_type}_{strategy}_{symbol}_{currency}_{timeframe}"
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """بررسی انقضای ورودی کش"""
        return datetime.now() > entry.expires_at
    
    def _cleanup_expired_entries(self):
        """پاک‌سازی ورودی‌های منقضی شده"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items() 
                if current_time > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def set_signal(
        self, 
        strategy: str, 
        symbol: str, 
        currency: str, 
        timeframe: str, 
        data: Any,
        custom_duration: Optional[int] = None
    ) -> str:
        """
        ذخیره سیگنال در کش
        
        Args:
            strategy: نام استراتژی
            symbol: نماد ارز
            currency: ارز مرجع
            timeframe: تایم‌فریم
            data: داده‌های سیگنال
            custom_duration: مدت نگهداری کش (ثانیه)
            
        Returns:
            str: کلید کش
        """
        try:
            cache_key = self._generate_cache_key(strategy, symbol, currency, timeframe, "signal")
            duration = custom_duration or self._signal_cache_duration
            
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=duration)
            
            entry = CacheEntry(
                data=data,
                created_at=created_at,
                expires_at=expires_at,
                strategy=strategy,
                symbol=symbol,
                currency=currency,
                timeframe=timeframe
            )
            
            self._cache[cache_key] = entry
            
            logger.info(f"Signal cached: {strategy} {symbol}/{currency} @ {timeframe} for {duration}s")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error setting signal cache: {e}")
            return ""
    
    def get_signal(
        self, 
        strategy: str, 
        symbol: str, 
        currency: str, 
        timeframe: str
    ) -> Optional[Any]:
        """
        دریافت سیگنال از کش
        
        Args:
            strategy: نام استراتژی
            symbol: نماد ارز
            currency: ارز مرجع
            timeframe: تایم‌فریم
            
        Returns:
            Optional[Any]: داده‌های سیگنال یا None
        """
        try:
            # پاک‌سازی ورودی‌های منقضی شده
            self._cleanup_expired_entries()
            
            cache_key = self._generate_cache_key(strategy, symbol, currency, timeframe, "signal")
            
            entry = self._cache.get(cache_key)
            if not entry:
                logger.debug(f"Signal cache miss: {strategy} {symbol}/{currency} @ {timeframe}")
                return None
            
            if self._is_expired(entry):
                del self._cache[cache_key]
                logger.debug(f"Signal cache expired: {strategy} {symbol}/{currency} @ {timeframe}")
                return None
            
            logger.info(f"Signal cache hit: {strategy} {symbol}/{currency} @ {timeframe}")
            return entry.data
            
        except Exception as e:
            logger.error(f"Error getting signal cache: {e}")
            return None
    
    def set_price(self, symbol: str, currency: str, price: float) -> str:
        """ذخیره قیمت زنده در کش"""
        try:
            cache_key = self._generate_cache_key("live_price", symbol, currency, "current", "price")
            
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=self._price_cache_duration)
            
            entry = CacheEntry(
                data={"price": price, "timestamp": created_at.isoformat()},
                created_at=created_at,
                expires_at=expires_at,
                strategy="live_price",
                symbol=symbol,
                currency=currency,
                timeframe="current"
            )
            
            self._cache[cache_key] = entry
            
            logger.debug(f"Price cached: {symbol}/{currency} = {price}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error setting price cache: {e}")
            return ""
    
    def get_price(self, symbol: str, currency: str) -> Optional[float]:
        """دریافت قیمت زنده از کش"""
        try:
            self._cleanup_expired_entries()
            
            cache_key = self._generate_cache_key("live_price", symbol, currency, "current", "price")
            
            entry = self._cache.get(cache_key)
            if not entry or self._is_expired(entry):
                return None
            
            price_data = entry.data
            if isinstance(price_data, dict) and "price" in price_data:
                return price_data["price"]
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting price cache: {e}")
            return None
    
    def invalidate_signal(self, strategy: str, symbol: str, currency: str, timeframe: str):
        """حذف سیگنال مشخص از کش"""
        try:
            cache_key = self._generate_cache_key(strategy, symbol, currency, timeframe, "signal")
            
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.info(f"Signal cache invalidated: {strategy} {symbol}/{currency} @ {timeframe}")
                
        except Exception as e:
            logger.error(f"Error invalidating signal cache: {e}")
    
    def invalidate_user_signals(self, user_id: int):
        """حذف تمام سیگنال‌های کاربر (در صورت نیاز)"""
        try:
            # این متد می‌تواند برای حذف کش‌های مربوط به کاربر خاص استفاده شود
            # فعلاً پیاده‌سازی نشده چون کش بر اساس کاربر نیست
            pass
            
        except Exception as e:
            logger.error(f"Error invalidating user signals: {e}")
    
    def clear_all(self):
        """پاک کردن تمام کش"""
        try:
            self._cache.clear()
            logger.info("All cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """دریافت آمار کش"""
        try:
            current_time = datetime.now()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values() 
                if current_time > entry.expires_at
            )
            active_entries = total_entries - expired_entries
            
            # آمار بر اساس نوع
            signal_entries = sum(
                1 for key in self._cache.keys() 
                if key.startswith(hashlib.md5("signal:".encode()).hexdigest()[:8])
            )
            price_entries = sum(
                1 for key in self._cache.keys() 
                if key.startswith(hashlib.md5("price:".encode()).hexdigest()[:8])
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "signal_entries": signal_entries,
                "price_entries": price_entries,
                "cache_hit_rate": getattr(self, '_hit_rate', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def is_signal_fresh(self, strategy: str, symbol: str, currency: str, timeframe: str) -> bool:
        """بررسی تازگی سیگنال (کمتر از 1 دقیقه)"""
        try:
            cache_key = self._generate_cache_key(strategy, symbol, currency, timeframe, "signal")
            entry = self._cache.get(cache_key)
            
            if not entry:
                return False
            
            # بررسی اینکه سیگنال کمتر از 1 دقیقه قدیمی باشد
            age_seconds = (datetime.now() - entry.created_at).total_seconds()
            return age_seconds < 60 and not self._is_expired(entry)
            
        except Exception as e:
            logger.error(f"Error checking signal freshness: {e}")
            return False


# ایجاد نمونه سراسری کش
cache = Cache()
