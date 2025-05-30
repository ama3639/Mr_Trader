"""
مدیریت کاربران MrTrader Bot
"""
import uuid
import random
import string
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from core.config import Config
from utils.logger import logger, log_user_action
from utils.time_manager import TimeManager
from database.database_manager import database_manager
from managers.csv_manager import CSVManager


class UserManager:
    """کلاس مدیریت کاربران"""
    
    @staticmethod
    def create_user(telegram_id: int, username: str = None, first_name: str = None, 
                   last_name: str = None, phone_number: str = None, 
                   referred_by: int = None) -> bool:
        """ایجاد کاربر جدید
        
        Args:
            telegram_id: شناسه تلگرام
            username: نام کاربری
            first_name: نام
            last_name: نام خانوادگی
            phone_number: شماره تلفن
            referred_by: معرف
            
        Returns:
            موفقیت عملیات
        """
        try:
            # بررسی وجود کاربر
            existing_user = UserManager.get_user_by_telegram_id(telegram_id)
            if existing_user:
                logger.warning(f"User {telegram_id} already exists")
                return False
            
            # تولید کد رفرال منحصربه‌فرد
            referral_code = UserManager.generate_referral_code()
            
            # ایجاد در دیتابیس
            db_success = database_manager.create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referral_code=referral_code
            )
            
            # ایجاد در CSV
            user_data = {
                'telegram_id': telegram_id,
                'username': username or '',
                'first_name': first_name or '',
                'last_name': last_name or '',
                'phone_number': phone_number or '',
                'package': 'none',
                'expiry_date': '',
                'balance': 0.0,
                'referral_code': referral_code,
                'referred_by': referred_by or '',
                'is_blocked': 0,
                'entry_date': TimeManager.get_current_shamsi(),
                'last_activity': TimeManager.get_current_shamsi(),
                'api_calls_count': 0,
                'daily_limit': 10,
                'security_token': ''
            }
            
            csv_success = CSVManager.add_user_to_csv(user_data)
            
            if db_success and csv_success:
                # پردازش رفرال
                if referred_by:
                    UserManager.process_referral(referred_by, telegram_id)
                
                log_user_action(telegram_id, "user_created", f"Username: {username}")
                logger.info(f"Created new user: {telegram_id}")
                return True
            else:
                logger.error(f"Failed to create user {telegram_id} in database or CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """دریافت کاربر با شناسه تلگرام
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            اطلاعات کاربر یا None
        """
        try:
            # ابتدا از دیتابیس
            db_user = database_manager.get_user_by_telegram_id(telegram_id)
            if db_user:
                return db_user
            
            # در صورت عدم وجود، از CSV
            csv_user = CSVManager.get_user_data_from_csv(telegram_id)
            if csv_user:
                # تبدیل string ها به نوع مناسب
                processed_user = UserManager._process_csv_user_data(csv_user)
                return processed_user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            return None
    
    @staticmethod
    def _process_csv_user_data(csv_data: Dict[str, str]) -> Dict[str, Any]:
        """پردازش داده‌های CSV کاربر
        
        Args:
            csv_data: داده‌های خام CSV
            
        Returns:
            داده‌های پردازش شده
        """
        try:
            return {
                'telegram_id': int(csv_data.get('telegram_id', 0)),
                'username': csv_data.get('username', ''),
                'first_name': csv_data.get('first_name', ''),
                'last_name': csv_data.get('last_name', ''),
                'phone_number': csv_data.get('phone_number', ''),
                'package': csv_data.get('package', 'none'),
                'package_expiry': csv_data.get('expiry_date', ''),
                'balance': float(csv_data.get('balance', 0)),
                'referral_code': csv_data.get('referral_code', ''),
                'referred_by': int(csv_data.get('referred_by', 0)) if csv_data.get('referred_by') else None,
                'is_blocked': csv_data.get('is_blocked', '0') == '1',
                'entry_date': csv_data.get('entry_date', ''),
                'last_activity': csv_data.get('last_activity', ''),
                'api_calls_count': int(csv_data.get('api_calls_count', 0)),
                'daily_limit': int(csv_data.get('daily_limit', 10)),
                'security_token': csv_data.get('security_token', '')
            }
        except Exception as e:
            logger.error(f"Error processing CSV user data: {e}")
            return csv_data
    
    @staticmethod
    def update_user(telegram_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            **kwargs: فیلدهای به‌روزرسانی
            
        Returns:
            موفقیت عملیات
        """
        try:
            # به‌روزرسانی در دیتابیس
            db_success = database_manager.update_user(telegram_id, **kwargs)
            
            # به‌روزرسانی در CSV
            csv_success = CSVManager.update_user_in_csv(telegram_id, kwargs)
            
            if db_success or csv_success:
                log_user_action(telegram_id, "user_updated", f"Fields: {list(kwargs.keys())}")
                return True
            else:
                logger.warning(f"Failed to update user {telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def update_user_balance(telegram_id: int, new_balance: float) -> bool:
        """به‌روزرسانی موجودی کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            new_balance: موجودی جدید
            
        Returns:
            موفقیت عملیات
        """
        try:
            success = UserManager.update_user(telegram_id, balance=new_balance)
            if success:
                log_user_action(telegram_id, "balance_updated", f"New balance: {new_balance}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating balance for user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def add_balance(telegram_id: int, amount: float) -> bool:
        """افزایش موجودی کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            amount: مبلغ افزایش
            
        Returns:
            موفقیت عملیات
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False
            
            current_balance = float(user.get('balance', 0))
            new_balance = current_balance + amount
            
            return UserManager.update_user_balance(telegram_id, new_balance)
            
        except Exception as e:
            logger.error(f"Error adding balance for user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def subtract_balance(telegram_id: int, amount: float) -> bool:
        """کاهش موجودی کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            amount: مبلغ کاهش
            
        Returns:
            موفقیت عملیات
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False
            
            current_balance = float(user.get('balance', 0))
            if current_balance < amount:
                logger.warning(f"Insufficient balance for user {telegram_id}")
                return False
            
            new_balance = current_balance - amount
            return UserManager.update_user_balance(telegram_id, new_balance)
            
        except Exception as e:
            logger.error(f"Error subtracting balance for user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def set_user_package(telegram_id: int, package: str, duration_days: int = 30) -> bool:
        """تنظیم پکیج کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            package: نوع پکیج
            duration_days: مدت اعتبار به روز
            
        Returns:
            موفقیت عملیات
        """
        try:
            # محاسبه تاریخ انقضا
            expiry_date = TimeManager.create_expiry_date(duration_days)
            
            # به‌روزرسانی پکیج
            success = UserManager.update_user(
                telegram_id,
                package=package,
                package_expiry=expiry_date
            )
            
            if success:
                log_user_action(telegram_id, "package_set", f"Package: {package}, Duration: {duration_days} days")
                logger.info(f"Set package {package} for user {telegram_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting package for user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def extend_user_package(telegram_id: int, additional_days: int) -> bool:
        """تمدید پکیج کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            additional_days: روزهای اضافی
            
        Returns:
            موفقیت عملیات
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False
            
            current_expiry = user.get('package_expiry', '')
            
            # اگر پکیج منقضی شده، از امروز شروع کن
            if not current_expiry or TimeManager.is_expired(current_expiry):
                new_expiry = TimeManager.create_expiry_date(additional_days)
            else:
                # اضافه کردن به تاریخ موجود
                new_expiry = TimeManager.add_shamsi_days(current_expiry, additional_days)
            
            success = UserManager.update_user(telegram_id, package_expiry=new_expiry)
            
            if success:
                log_user_action(telegram_id, "package_extended", f"Additional days: {additional_days}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error extending package for user {telegram_id}: {e}")
            return False
    
    @staticmethod
    async def is_package_expired(telegram_id: int) -> Tuple[bool, int]:
        """بررسی انقضای پکیج کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            (آیا منقضی شده، روزهای باقیمانده)
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return True, 0
            
            package = user.get('package', 'none')
            if package == 'none':
                return True, 0
            
            expiry_date = user.get('package_expiry', '')
            if not expiry_date:
                return True, 0
            
            is_expired = TimeManager.is_expired(expiry_date)
            
            if is_expired:
                return True, 0
            
            # محاسبه روزهای باقیمانده
            days_left = TimeManager.days_difference(
                TimeManager.get_current_shamsi(), 
                expiry_date
            )
            
            return False, max(0, days_left)
            
        except Exception as e:
            logger.error(f"Error checking package expiry for user {telegram_id}: {e}")
            return True, 0
    
    @staticmethod
    def block_user(telegram_id: int, reason: str = "") -> bool:
        """مسدود کردن کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            reason: دلیل مسدودیت
            
        Returns:
            موفقیت عملیات
        """
        try:
            success = UserManager.update_user(telegram_id, is_blocked=True)
            
            if success:
                log_user_action(telegram_id, "user_blocked", f"Reason: {reason}")
                logger.info(f"Blocked user {telegram_id}: {reason}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error blocking user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def unblock_user(telegram_id: int) -> bool:
        """رفع مسدودیت کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            موفقیت عملیات
        """
        try:
            success = UserManager.update_user(telegram_id, is_blocked=False)
            
            if success:
                log_user_action(telegram_id, "user_unblocked")
                logger.info(f"Unblocked user {telegram_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error unblocking user {telegram_id}: {e}")
            return False
    
    @staticmethod
    def is_user_blocked(telegram_id: int) -> bool:
        """بررسی مسدودیت کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            آیا کاربر مسدود است
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return True  # کاربر وجود ندارد = مسدود
            
            return user.get('is_blocked', False)
            
        except Exception as e:
            logger.error(f"Error checking if user {telegram_id} is blocked: {e}")
            return True
    
    @staticmethod
    def generate_referral_code() -> str:
        """تولید کد رفرال منحصربه‌فرد
        
        Returns:
            کد رفرال 8 کاراکتری
        """
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # بررسی یکتا بودن
            existing_user = CSVManager.find_user_by_referral_code(code)
            if not existing_user:
                return code
    
    @staticmethod
    def process_referral(referrer_id: int, referred_id: int) -> bool:
        """پردازش رفرال
        
        Args:
            referrer_id: شناسه معرف
            referred_id: شناسه معرفی شده
            
        Returns:
            موفقیت عملیات
        """
        try:
            # بررسی وجود معرف
            referrer = UserManager.get_user_by_telegram_id(referrer_id)
            if not referrer:
                logger.warning(f"Referrer {referrer_id} not found")
                return False
            
            # اعطای پاداش رفرال (مثلاً افزایش موجودی)
            referral_bonus = 50000  # 50 هزار تومان
            success = UserManager.add_balance(referrer_id, referral_bonus)
            
            if success:
                log_user_action(referrer_id, "referral_bonus", f"Referred user: {referred_id}, Bonus: {referral_bonus}")
                log_user_action(referred_id, "referred_by", f"Referrer: {referrer_id}")
                logger.info(f"Processed referral: {referrer_id} -> {referred_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing referral {referrer_id} -> {referred_id}: {e}")
            return False
    
    @staticmethod
    def get_user_statistics() -> Dict[str, Any]:
        """آمار کاربران
        
        Returns:
            آمار کلی کاربران
        """
        try:
            users = CSVManager.get_all_users_from_csv()
            
            stats = {
                'total_users': len(users),
                'active_users': 0,
                'blocked_users': 0,
                'premium_users': 0,
                'packages': {'none': 0, 'guest': 0, 'basic': 0, 'premium': 0, 'vip': 0},
                'total_balance': 0.0,
                'referrals_count': 0
            }
            
            for user in users:
                # وضعیت فعالیت
                if user.get('is_blocked', '0') == '1':
                    stats['blocked_users'] += 1
                else:
                    stats['active_users'] += 1
                
                # نوع پکیج
                package = user.get('package', 'none')
                if package in stats['packages']:
                    stats['packages'][package] += 1
                
                if package != 'none':
                    stats['premium_users'] += 1
                
                # موجودی کل
                balance = float(user.get('balance', 0))
                stats['total_balance'] += balance
                
                # تعداد رفرال‌ها
                if user.get('referred_by'):
                    stats['referrals_count'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    @staticmethod
    def search_users(query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """جستجوی کاربران
        
        Args:
            query: عبارت جستجو
            limit: حداکثر نتایج
            
        Returns:
            لیست کاربران یافت شده
        """
        try:
            users = CSVManager.get_all_users_from_csv()
            results = []
            
            query = query.lower()
            
            for user in users:
                # جستجو در فیلدهای مختلف
                if (query in str(user.get('telegram_id', '')).lower() or
                    query in user.get('username', '').lower() or
                    query in user.get('first_name', '').lower() or
                    query in user.get('last_name', '').lower() or
                    query in user.get('referral_code', '').lower()):
                    
                    results.append(UserManager._process_csv_user_data(user))
                    
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    @staticmethod
    def get_users_by_package_type(package: str) -> List[Dict[str, Any]]:
        """دریافت کاربران بر اساس نوع پکیج
        
        Args:
            package: نوع پکیج
            
        Returns:
            لیست کاربران با پکیج مشخص
        """
        try:
            users = CSVManager.get_users_by_package(package)
            return [UserManager._process_csv_user_data(user) for user in users]
            
        except Exception as e:
            logger.error(f"Error getting users by package {package}: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_packages() -> int:
        """پاکسازی پکیج‌های منقضی شده
        
        Returns:
            تعداد پکیج‌های پاکسازی شده
        """
        try:
            users = CSVManager.get_all_users_from_csv()
            cleaned_count = 0
            
            for user in users:
                telegram_id = int(user.get('telegram_id', 0))
                package = user.get('package', 'none')
                expiry_date = user.get('expiry_date', '')
                
                if package != 'none' and expiry_date and TimeManager.is_expired(expiry_date):
                    # تنظیم پکیج به none
                    success = UserManager.update_user(
                        telegram_id,
                        package='none',
                        package_expiry=''
                    )
                    
                    if success:
                        cleaned_count += 1
                        log_user_action(telegram_id, "package_expired", f"Previous package: {package}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired packages")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired packages: {e}")
            return 0
    
    # تابع wrapper برای سازگاری با کد قبلی
    @staticmethod
    def to_shamsi(dt: datetime) -> str:
        """تبدیل تاریخ به شمسی (wrapper)"""
        return TimeManager.to_shamsi(dt)


# Export برای استفاده آسان‌تر
__all__ = ['UserManager']
