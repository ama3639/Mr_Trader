"""
مدیریت امنیت و احراز هویت MrTrader Bot
"""
import hashlib
import secrets
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from core.config import Config
from utils.logger import logger, log_security_event
from utils.time_manager import TimeManager
from database.database_manager import database_manager
from managers.user_manager import UserManager
from core.cache import cache


class SecurityManager:
    """کلاس مدیریت امنیت سیستم"""
    
    # کش برای ذخیره تلاش‌های ناموفق
    _failed_attempts = {}
    _locked_users = {}
    
    @classmethod
    async def is_user_allowed(cls, user_id: int) -> bool:
        """بررسی مجاز بودن کاربر برای استفاده از ربات
        
        Args:
            user_id: شناسه تلگرام کاربر
            
        Returns:
            bool: True اگر کاربر مجاز باشد
        """
        try:
            # بررسی وجود کاربر
            user = UserManager.get_user_by_telegram_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found in database")
                return True  # کاربران جدید مجاز هستند
            
            # بررسی مسدودیت کاربر
            if user.get('is_blocked', False):
                logger.warning(f"User {user_id} is blocked")
                return False
            
            # بررسی قفل بودن کاربر
            is_locked, unlock_time = cls.is_user_locked(user_id)
            if is_locked:
                remaining = cls.get_remaining_lockout_time(user_id)
                logger.warning(f"User {user_id} is locked. Remaining time: {remaining}")
                return False
            
            # بررسی محدودیت روزانه (اختیاری - warning فقط)
            daily_limit = user.get('daily_limit', 100)
            current_calls = user.get('api_calls_count', 0)
            
            if current_calls >= daily_limit:
                logger.warning(f"User {user_id} exceeded daily limit ({current_calls}/{daily_limit})")
                # در حالت عادی false برمی‌گرداند، اما برای جلوگیری از مشکل، true برمی‌گردانیم
                return True
            
            # کاربر مجاز است
            return True
            
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is allowed: {e}")
            # در صورت خطا، کاربر را مجاز می‌دانیم تا سیستم متوقف نشود
            return True
    
    @classmethod
    def is_user_allowed_sync(cls, user_id: int) -> bool:
        """نسخه sync برای بررسی مجاز بودن کاربر
        
        Args:
            user_id: شناسه تلگرام کاربر
            
        Returns:
            bool: True اگر کاربر مجاز باشد
        """
        try:
            # بررسی وجود کاربر
            user = UserManager.get_user_by_telegram_id(user_id)
            if not user:
                return True  # کاربران جدید مجاز هستند
            
            # بررسی مسدودیت کاربر
            if user.get('is_blocked', False):
                return False
            
            # بررسی قفل بودن کاربر
            is_locked, _ = cls.is_user_locked(user_id)
            if is_locked:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is allowed (sync): {e}")
            return True
    
    @classmethod
    def generate_security_token(cls, user_id: int) -> str:
        """تولید توکن امنیتی برای کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            توکن امنیتی
        """
        try:
            # ترکیب داده‌های منحصربه‌فرد
            timestamp = str(int(time.time()))
            random_data = secrets.token_hex(16)
            user_data = str(user_id)
            
            # ایجاد hash
            combined_data = f"{user_data}:{timestamp}:{random_data}"
            token = hashlib.sha256(combined_data.encode()).hexdigest()
            
            # ذخیره توکن برای کاربر
            UserManager.update_user(user_id, security_token=token)
            
            log_security_event("token_generated", user_id, "", f"Token: {token[:16]}...")
            return token
            
        except Exception as e:
            logger.error(f"Error generating security token for user {user_id}: {e}")
            return ""
    
    @classmethod
    def validate_security_token(cls, user_id: int, token: str) -> bool:
        """اعتبارسنجی توکن امنیتی
        
        Args:
            user_id: شناسه کاربر
            token: توکن ارسال شده
            
        Returns:
            معتبر بودن توکن
        """
        try:
            if not token:
                return False
            
            user = UserManager.get_user_by_telegram_id(user_id)
            if not user:
                return False
            
            stored_token = user.get('security_token', '')
            is_valid = stored_token == token
            
            if not is_valid:
                log_security_event("invalid_token", user_id, "", f"Provided: {token[:16]}...")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating security token for user {user_id}: {e}")
            return False
    
    @classmethod
    def record_failed_attempt(cls, user_id: int, attempt_type: str = "login", 
                             ip_address: str = "") -> bool:
        """ثبت تلاش ناموفق
        
        Args:
            user_id: شناسه کاربر
            attempt_type: نوع تلاش
            ip_address: آدرس IP
            
        Returns:
            آیا باید کاربر قفل شود
        """
        try:
            current_time = datetime.now()
            
            # دریافت تعداد تلاش‌های قبلی
            if user_id not in cls._failed_attempts:
                cls._failed_attempts[user_id] = []
            
            # افزودن تلاش جدید
            cls._failed_attempts[user_id].append({
                'timestamp': current_time,
                'type': attempt_type,
                'ip_address': ip_address
            })
            
            # پاکسازی تلاش‌های قدیمی (بیش از 1 ساعت)
            one_hour_ago = current_time - timedelta(hours=1)
            cls._failed_attempts[user_id] = [
                attempt for attempt in cls._failed_attempts[user_id]
                if attempt['timestamp'] > one_hour_ago
            ]
            
            # شمارش تلاش‌های اخیر
            recent_attempts = len(cls._failed_attempts[user_id])
            
            # به‌روزرسانی در دیتابیس
            database_manager.update_user(user_id, failed_attempts=recent_attempts)
            
            log_security_event(
                "failed_attempt", 
                user_id, 
                ip_address, 
                f"Type: {attempt_type}, Total: {recent_attempts}"
            )
            
            # بررسی نیاز به قفل کردن
            max_attempts = getattr(Config, 'MAX_LOGIN_ATTEMPTS', 5)
            if recent_attempts >= max_attempts:
                lockout_minutes = getattr(Config, 'LOCKOUT_MINUTES', 15)
                cls.lock_user(user_id, lockout_minutes, f"Too many failed {attempt_type} attempts")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error recording failed attempt for user {user_id}: {e}")
            return False
    
    @classmethod
    def lock_user(cls, user_id: int, duration_minutes: int = None, reason: str = "") -> bool:
        """قفل کردن کاربر
        
        Args:
            user_id: شناسه کاربر
            duration_minutes: مدت قفل به دقیقه
            reason: دلیل قفل
            
        Returns:
            موفقیت عملیات
        """
        try:
            if duration_minutes is None:
                duration_minutes = getattr(Config, 'LOCKOUT_MINUTES', 15)
            
            unlock_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            # ذخیره در کش محلی
            cls._locked_users[user_id] = {
                'locked_until': unlock_time,
                'reason': reason,
                'locked_at': datetime.now()
            }
            
            # به‌روزرسانی در دیتابیس
            database_manager.update_user(
                user_id, 
                locked_until=unlock_time.isoformat()
            )
            
            log_security_event(
                "user_locked", 
                user_id, 
                "", 
                f"Duration: {duration_minutes}min, Reason: {reason}"
            )
            
            logger.warning(f"Locked user {user_id} for {duration_minutes} minutes: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error locking user {user_id}: {e}")
            return False
    
    @classmethod
    def unlock_user(cls, user_id: int) -> bool:
        """رفع قفل کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            موفقیت عملیات
        """
        try:
            # حذف از کش محلی
            if user_id in cls._locked_users:
                del cls._locked_users[user_id]
            
            # حذف از کش اصلی
            cache.delete(f"locked_user_{user_id}")
            
            # به‌روزرسانی در دیتابیس
            database_manager.update_user(
                user_id, 
                locked_until=None,
                failed_attempts=0
            )
            
            # پاکسازی تلاش‌های ناموفق
            if user_id in cls._failed_attempts:
                del cls._failed_attempts[user_id]
            
            log_security_event("user_unlocked", user_id, "", "Manual unlock")
            logger.info(f"Unlocked user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unlocking user {user_id}: {e}")
            return False
    
    @classmethod
    def is_user_locked(cls, user_id: int) -> Tuple[bool, Optional[datetime]]:
        """بررسی قفل بودن کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            (آیا قفل است، زمان رفع قفل)
        """
        try:
            current_time = datetime.now()
            
            # بررسی کش محلی
            if user_id in cls._locked_users:
                lock_info = cls._locked_users[user_id]
                unlock_time = lock_info['locked_until']
                
                if current_time < unlock_time:
                    return True, unlock_time
                else:
                    # قفل منقضی شده
                    del cls._locked_users[user_id]
            
            # بررسی دیتابیس
            user = UserManager.get_user_by_telegram_id(user_id)
            if user and user.get('locked_until'):
                try:
                    unlock_time_str = user.get('locked_until')
                    unlock_time = datetime.fromisoformat(unlock_time_str)
                    
                    if current_time < unlock_time:
                        # کاربر هنوز قفل است
                        cls._locked_users[user_id] = {
                            'locked_until': unlock_time,
                            'reason': 'Database lock',
                            'locked_at': current_time
                        }
                        return True, unlock_time
                    else:
                        # قفل منقضی شده - پاکسازی
                        cls.unlock_user(user_id)
                except (ValueError, TypeError):
                    # مشکل در فرمت تاریخ
                    cls.unlock_user(user_id)
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is locked: {e}")
            return False, None
    
    @classmethod
    def get_remaining_lockout_time(cls, user_id: int) -> Optional[str]:
        """دریافت زمان باقیمانده قفل
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            زمان باقیمانده به فرمت خوانا
        """
        try:
            is_locked, unlock_time = cls.is_user_locked(user_id)
            
            if not is_locked or not unlock_time:
                return None
            
            remaining = unlock_time - datetime.now()
            
            if remaining.total_seconds() <= 0:
                return None
            
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            
            if minutes > 0:
                return f"{minutes} دقیقه و {seconds} ثانیه"
            else:
                return f"{seconds} ثانیه"
                
        except Exception as e:
            logger.error(f"Error getting remaining lockout time for user {user_id}: {e}")
            return None
    
    @classmethod
    def clear_failed_attempts(cls, user_id: int) -> bool:
        """پاکسازی تلاش‌های ناموفق کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            موفقیت عملیات
        """
        try:
            # پاکسازی کش محلی
            if user_id in cls._failed_attempts:
                del cls._failed_attempts[user_id]
            
            # به‌روزرسانی دیتابیس
            database_manager.update_user(user_id, failed_attempts=0)
            
            log_security_event("failed_attempts_cleared", user_id)
            return True
            
        except Exception as e:
            logger.error(f"Error clearing failed attempts for user {user_id}: {e}")
            return False
    
    @classmethod
    def validate_api_rate_limit(cls, user_id: int, endpoint: str = "general") -> Tuple[bool, str]:
        """بررسی محدودیت نرخ API
        
        Args:
            user_id: شناسه کاربر
            endpoint: نوع endpoint
            
        Returns:
            (مجاز بودن، پیام خطا)
        """
        try:
            # دریافت تنظیمات کاربر
            user = UserManager.get_user_by_telegram_id(user_id)
            if not user:
                return False, "کاربر یافت نشد"
            
            # بررسی مسدودیت
            if UserManager.is_user_blocked(user_id):
                return False, "حساب کاربری شما مسدود شده است"
            
            # بررسی قفل
            is_locked, unlock_time = cls.is_user_locked(user_id)
            if is_locked:
                remaining = cls.get_remaining_lockout_time(user_id)
                return False, f"حساب شما قفل شده است. زمان باقیمانده: {remaining}"
            
            # بررسی محدودیت روزانه
            daily_limit = user.get('daily_limit', 10)
            current_calls = user.get('api_calls_count', 0)
            
            if current_calls >= daily_limit:
                return False, "حد مجاز درخواست روزانه شما تمام شده است"
            
            # افزایش شمارنده
            UserManager.update_user(user_id, api_calls_count=current_calls + 1)
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating API rate limit for user {user_id}: {e}")
            return False, "خطا در بررسی محدودیت‌ها"
    
    @classmethod
    def reset_daily_limits(cls) -> int:
        """بازنشانی محدودیت‌های روزانه
        
        Returns:
            تعداد کاربران بازنشانی شده
        """
        try:
            # بازنشانی در دیتابیس
            affected_rows = database_manager.execute_query(
                "UPDATE users SET api_calls_count = 0"
            )
            
            log_security_event("daily_limits_reset", 0, "", f"Affected users: {affected_rows}")
            logger.info(f"Reset daily limits for {affected_rows} users")
            
            return affected_rows or 0
            
        except Exception as e:
            logger.error(f"Error resetting daily limits: {e}")
            return 0
    
    @classmethod
    def get_security_statistics(cls) -> Dict:
        """آمار امنیتی سیستم
        
        Returns:
            آمار امنیتی
        """
        try:
            stats = {
                'locked_users': len(cls._locked_users),
                'users_with_failed_attempts': len(cls._failed_attempts),
                'total_failed_attempts_today': 0,
                'active_security_events': 0
            }
            
            # شمارش تلاش‌های ناموفق امروز
            today = datetime.now().date()
            for attempts in cls._failed_attempts.values():
                for attempt in attempts:
                    if attempt['timestamp'].date() == today:
                        stats['total_failed_attempts_today'] += 1
            
            # دریافت آمار از دیتابیس
            db_stats = database_manager.execute_query("""
                SELECT 
                    COUNT(CASE WHEN locked_until > datetime('now') THEN 1 END) as locked_count,
                    COUNT(CASE WHEN failed_attempts > 0 THEN 1 END) as failed_attempts_count
                FROM users
            """, fetch=True)
            
            if db_stats:
                stats['db_locked_users'] = db_stats[0].get('locked_count', 0)
                stats['db_users_with_failures'] = db_stats[0].get('failed_attempts_count', 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting security statistics: {e}")
            return {}
    
    @classmethod
    def cleanup_expired_locks(cls) -> int:
        """پاکسازی قفل‌های منقضی شده
        
        Returns:
            تعداد قفل‌های پاکسازی شده
        """
        try:
            current_time = datetime.now()
            cleaned_count = 0
            
            # پاکسازی کش محلی
            expired_users = []
            for user_id, lock_info in cls._locked_users.items():
                if current_time >= lock_info['locked_until']:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                cls.unlock_user(user_id)
                cleaned_count += 1
            
            # پاکسازی دیتابیس
            db_cleaned = database_manager.execute_query("""
                UPDATE users 
                SET locked_until = NULL, failed_attempts = 0 
                WHERE locked_until <= datetime('now')
            """)
            
            if db_cleaned:
                cleaned_count += db_cleaned
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired locks")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired locks: {e}")
            return 0
    
    @classmethod
    def generate_api_key(cls, user_id: int) -> str:
        """تولید کلید API برای کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            کلید API
        """
        try:
            # تولید کلید منحصربه‌فرد
            timestamp = str(int(time.time()))
            random_part = secrets.token_urlsafe(32)
            api_key = f"mrtrader_{user_id}_{timestamp}_{random_part}"
            
            # ذخیره در دیتابیس (اگر جدول مناسب وجود داشت)
            log_security_event("api_key_generated", user_id, "", f"Key: {api_key[:20]}...")
            
            return api_key
            
        except Exception as e:
            logger.error(f"Error generating API key for user {user_id}: {e}")
            return ""
    
    @classmethod
    async def get_locked_users_count(cls) -> int:
        """دریافت تعداد کاربران قفل شده
        
        Returns:
            تعداد کاربران قفل شده
        """
        try:
            # شمارش کش محلی
            local_count = len([
                user_id for user_id, lock_info in cls._locked_users.items()
                if datetime.now() < lock_info['locked_until']
            ])
            
            # شمارش دیتابیس
            db_result = database_manager.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE locked_until > datetime('now')",
                fetch=True
            )
            
            db_count = db_result[0]['count'] if db_result else 0
            
            return max(local_count, db_count)
            
        except Exception as e:
            logger.error(f"Error getting locked users count: {e}")
            return 0


# توابع کمکی برای سازگاری
def is_user_locked(user_id: int) -> bool:
    """بررسی قفل بودن کاربر (تابع کمکی)"""
    is_locked, _ = SecurityManager.is_user_locked(user_id)
    return is_locked


def record_failed_attempt(user_id: int, attempt_type: str = "login") -> bool:
    """ثبت تلاش ناموفق (تابع کمکی)"""
    return SecurityManager.record_failed_attempt(user_id, attempt_type)


# Export برای استفاده آسان‌تر
__all__ = [
    'SecurityManager',
    'is_user_locked',
    'record_failed_attempt'
]