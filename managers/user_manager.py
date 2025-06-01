"""
مدیریت کاربران MrTrader Bot
"""
import uuid
import random
import string
import asyncio
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
            try:
                db_success = database_manager.create_user(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    referral_code=referral_code
                )
            except Exception as db_error:
                logger.warning(f"Database creation failed for user {telegram_id}: {db_error}")
                db_success = False
            
            # ایجاد در CSV
            user_data = {
                'telegram_id': telegram_id,
                'username': username or '',
                'first_name': first_name or '',
                'last_name': last_name or '',
                'phone_number': phone_number or '',
                'package': 'demo',  # ✅ تغییر از 'none' به 'demo'
                'expiry_date': '',
                'balance': 0.0,
                'referral_code': referral_code,
                'referred_by': referred_by or '',
                'is_blocked': 0,
                'entry_date': TimeManager.get_current_shamsi(),
                'last_activity': TimeManager.get_current_shamsi(),
                'api_calls_count': 0,
                'daily_limit': 5,  # ✅ محدودیت demo
                'security_token': ''
            }
            
            try:
                csv_success = CSVManager.add_user_to_csv(user_data)
            except Exception as csv_error:
                logger.warning(f"CSV creation failed for user {telegram_id}: {csv_error}")
                csv_success = False
            
            # اگر یکی موفق باشد، کافی است
            if db_success or csv_success:
                # پردازش رفرال
                if referred_by:
                    try:
                        UserManager.process_referral(referred_by, telegram_id)
                    except Exception as ref_error:
                        logger.warning(f"Referral processing failed: {ref_error}")
                
                log_user_action(telegram_id, "user_created", f"Username: {username}")
                logger.info(f"Created new user: {telegram_id}")
                return True
            else:
                logger.error(f"Failed to create user {telegram_id} in both database and CSV")
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
            try:
                if hasattr(database_manager, 'get_user_by_telegram_id'):
                    db_user = database_manager.get_user_by_telegram_id(telegram_id)
                    if db_user:
                        return db_user
            except Exception as db_error:
                logger.warning(f"Database query failed for user {telegram_id}: {db_error}")
            
            # در صورت عدم وجود، از CSV
            try:
                if hasattr(CSVManager, 'get_user_data_from_csv'):
                    csv_user = CSVManager.get_user_data_from_csv(telegram_id)
                    if csv_user:
                        # تبدیل string ها به نوع مناسب
                        processed_user = UserManager._process_csv_user_data(csv_user)
                        return processed_user
            except Exception as csv_error:
                logger.warning(f"CSV query failed for user {telegram_id}: {csv_error}")
            
            # اگر کاربر وجود ندارد، خودکار ایجاد کن
            logger.info(f"User {telegram_id} not found, creating new user")
            return UserManager._create_default_user(telegram_id)
            
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            # ✅ بازگشت کاربر پیش‌فرض به جای None
            return UserManager._create_default_user(telegram_id)
    
    @staticmethod
    def _create_default_user(telegram_id: int) -> Dict[str, Any]:
        """ایجاد کاربر پیش‌فرض در صورت عدم وجود
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            اطلاعات کاربر پیش‌فرض
        """
        try:
            default_user = {
                'telegram_id': telegram_id,
                'username': '',
                'first_name': '',
                'last_name': '',
                'phone_number': '',
                'package': 'demo',
                'package_expiry': '',
                'balance': 0.0,
                'referral_code': UserManager.generate_referral_code(),
                'referred_by': None,
                'is_blocked': False,
                'entry_date': TimeManager.get_current_shamsi(),
                'last_activity': TimeManager.get_current_shamsi(),
                'api_calls_count': 0,
                'daily_limit': 5,
                'security_token': ''
            }
            
            # تلاش برای ذخیره کاربر جدید
            try:
                UserManager.create_user(telegram_id)
            except Exception as create_error:
                logger.warning(f"Failed to create user {telegram_id}: {create_error}")
            
            return default_user
            
        except Exception as e:
            logger.error(f"Error creating default user {telegram_id}: {e}")
            # ✅ بازگشت حداقل ساختار در صورت هر خطا
            return {
                'telegram_id': telegram_id,
                'package': 'demo',
                'is_blocked': False,
                'daily_limit': 5,
                'api_calls_count': 0
            }
    
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
                'package': csv_data.get('package', 'demo'),  # ✅ پیش‌فرض demo
                'package_expiry': csv_data.get('expiry_date', ''),
                'balance': float(csv_data.get('balance', 0)),
                'referral_code': csv_data.get('referral_code', ''),
                'referred_by': int(csv_data.get('referred_by', 0)) if csv_data.get('referred_by') else None,
                'is_blocked': csv_data.get('is_blocked', '0') == '1',
                'entry_date': csv_data.get('entry_date', ''),
                'last_activity': csv_data.get('last_activity', ''),
                'api_calls_count': int(csv_data.get('api_calls_count', 0)),
                'daily_limit': int(csv_data.get('daily_limit', 5)),  # ✅ پیش‌فرض 5
                'security_token': csv_data.get('security_token', '')
            }
        except Exception as e:
            logger.error(f"Error processing CSV user data: {e}")
            # ✅ بازگشت داده‌های خام در صورت خطا
            return csv_data if isinstance(csv_data, dict) else {}
    
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
            db_success = False
            try:
                if hasattr(database_manager, 'update_user'):
                    db_success = database_manager.update_user(telegram_id, **kwargs)
            except Exception as db_error:
                logger.warning(f"Database update failed for user {telegram_id}: {db_error}")
            
            # به‌روزرسانی در CSV
            csv_success = False
            try:
                if hasattr(CSVManager, 'update_user_in_csv'):
                    csv_success = CSVManager.update_user_in_csv(telegram_id, kwargs)
            except Exception as csv_error:
                logger.warning(f"CSV update failed for user {telegram_id}: {csv_error}")
            
            # اگر یکی موفق باشد، کافی است
            if db_success or csv_success:
                log_user_action(telegram_id, "user_updated", f"Fields: {list(kwargs.keys())}")
                return True
            else:
                logger.warning(f"Failed to update user {telegram_id} in both database and CSV")
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
    def is_package_expired(telegram_id: int) -> Tuple[bool, int]:
        """بررسی انقضای پکیج کاربر - ✅ حذف async
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            (آیا منقضی شده، روزهای باقیمانده)
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return True, 0
            
            package = user.get('package', 'demo')
            if package == 'demo' or package == 'none':
                return False, 999  # ✅ دمو هیچوقت منقضی نمی‌شود
            
            expiry_date = user.get('package_expiry', '')
            if not expiry_date:
                return True, 0
            
            try:
                is_expired = TimeManager.is_expired(expiry_date)
                
                if is_expired:
                    return True, 0
                
                # محاسبه روزهای باقیمانده
                days_left = TimeManager.days_difference(
                    TimeManager.get_current_shamsi(), 
                    expiry_date
                )
                
                return False, max(0, days_left)
            except Exception as time_error:
                logger.warning(f"Time calculation error for user {telegram_id}: {time_error}")
                return False, 0  # ✅ در صورت خطا، منقضی نشده فرض کن
            
        except Exception as e:
            logger.error(f"Error checking package expiry for user {telegram_id}: {e}")
            return False, 0  # ✅ در صورت خطا، منقضی نشده فرض کن
    
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
                return False  # ✅ تغییر از True به False - کاربر جدید مسدود نیست
            
            return user.get('is_blocked', False)
            
        except Exception as e:
            logger.error(f"Error checking if user {telegram_id} is blocked: {e}")
            return False  # ✅ در صورت خطا، مسدود نیست
    
    @staticmethod
    def generate_referral_code() -> str:
        """تولید کد رفرال منحصربه‌فرد
        
        Returns:
            کد رفرال 8 کاراکتری
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                # بررسی یکتا بودن
                try:
                    if hasattr(CSVManager, 'find_user_by_referral_code'):
                        existing_user = CSVManager.find_user_by_referral_code(code)
                        if not existing_user:
                            return code
                except Exception as csv_error:
                    logger.warning(f"CSV referral check failed: {csv_error}")
                    # اگر CSV کار نکند، کد تولید شده را برگردان
                    return code
                    
            except Exception as e:
                logger.warning(f"Error generating referral code attempt {attempt + 1}: {e}")
        
        # اگر همه تلاش‌ها ناموفق بود، کد ساده تولید کن
        return f"REF{random.randint(10000, 99999)}"
    
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
            users = []
            try:
                if hasattr(CSVManager, 'get_all_users_from_csv'):
                    users = CSVManager.get_all_users_from_csv()
            except Exception as csv_error:
                logger.warning(f"CSV stats failed: {csv_error}")
            
            stats = {
                'total_users': len(users),
                'active_users': 0,
                'blocked_users': 0,
                'premium_users': 0,
                'packages': {'demo': 0, 'basic': 0, 'premium': 0, 'vip': 0},
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
                package = user.get('package', 'demo')
                if package in stats['packages']:
                    stats['packages'][package] += 1
                
                if package != 'demo' and package != 'none':
                    stats['premium_users'] += 1
                
                # موجودی کل
                try:
                    balance = float(user.get('balance', 0))
                    stats['total_balance'] += balance
                except (ValueError, TypeError):
                    pass
                
                # تعداد رفرال‌ها
                if user.get('referred_by'):
                    stats['referrals_count'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'blocked_users': 0,
                'premium_users': 0,
                'packages': {'demo': 0, 'basic': 0, 'premium': 0, 'vip': 0},
                'total_balance': 0.0,
                'referrals_count': 0
            }
    
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
            users = []
            try:
                if hasattr(CSVManager, 'get_all_users_from_csv'):
                    users = CSVManager.get_all_users_from_csv()
            except Exception as csv_error:
                logger.warning(f"CSV search failed: {csv_error}")
                return []
            
            results = []
            query = query.lower()
            
            for user in users:
                try:
                    # جستجو در فیلدهای مختلف
                    if (query in str(user.get('telegram_id', '')).lower() or
                        query in user.get('username', '').lower() or
                        query in user.get('first_name', '').lower() or
                        query in user.get('last_name', '').lower() or
                        query in user.get('referral_code', '').lower()):
                        
                        results.append(UserManager._process_csv_user_data(user))
                        
                        if len(results) >= limit:
                            break
                except Exception as user_error:
                    logger.warning(f"Error processing user in search: {user_error}")
                    continue
            
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
            users = []
            try:
                if hasattr(CSVManager, 'get_users_by_package'):
                    users = CSVManager.get_users_by_package(package)
                elif hasattr(CSVManager, 'get_all_users_from_csv'):
                    all_users = CSVManager.get_all_users_from_csv()
                    users = [u for u in all_users if u.get('package') == package]
            except Exception as csv_error:
                logger.warning(f"CSV package query failed: {csv_error}")
                return []
            
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
            users = []
            try:
                if hasattr(CSVManager, 'get_all_users_from_csv'):
                    users = CSVManager.get_all_users_from_csv()
            except Exception as csv_error:
                logger.warning(f"CSV cleanup failed: {csv_error}")
                return 0
            
            cleaned_count = 0
            
            for user in users:
                try:
                    telegram_id = int(user.get('telegram_id', 0))
                    package = user.get('package', 'demo')
                    expiry_date = user.get('expiry_date', '')
                    
                    if (package not in ['demo', 'none'] and 
                        expiry_date and 
                        TimeManager.is_expired(expiry_date)):
                        
                        # تنظیم پکیج به demo
                        success = UserManager.update_user(
                            telegram_id,
                            package='demo',
                            package_expiry=''
                        )
                        
                        if success:
                            cleaned_count += 1
                            log_user_action(telegram_id, "package_expired", f"Previous package: {package}")
                
                except Exception as user_error:
                    logger.warning(f"Error cleaning user package: {user_error}")
                    continue
            
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
    
    # ✅ متدهای کمکی اضافی برای error handling
    @staticmethod
    def safe_get_user(telegram_id: int) -> Dict[str, Any]:
        """دریافت امن کاربر - همیشه مقداری برمی‌گرداند
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            اطلاعات کاربر (حداقل ساختار)
        """
        try:
            user = UserManager.get_user_by_telegram_id(telegram_id)
            return user if user else UserManager._create_default_user(telegram_id)
        except Exception as e:
            logger.error(f"Safe get user failed for {telegram_id}: {e}")
            return {
                'telegram_id': telegram_id,
                'package': 'demo',
                'is_blocked': False,
                'daily_limit': 5,
                'api_calls_count': 0
            }
    
    @staticmethod
    def increment_api_calls(telegram_id: int) -> bool:
        """افزایش شمارنده تماس‌های API
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            موفقیت عملیات
        """
        try:
            user = UserManager.safe_get_user(telegram_id)
            current_calls = int(user.get('api_calls_count', 0))
            new_calls = current_calls + 1
            
            return UserManager.update_user(telegram_id, api_calls_count=new_calls)
            
        except Exception as e:
            logger.error(f"Error incrementing API calls for user {telegram_id}: {e}")
            return False


# Export برای استفاده آسان‌تر
__all__ = ['UserManager']