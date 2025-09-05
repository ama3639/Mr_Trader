"""
مدیریت کاربران MrTrader Bot - Fixed Recursion Issues
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
            # ✅ بررسی وجود کاربر بدون recursion
            existing_user = UserManager._check_user_exists(telegram_id)
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
                'package': 'demo',
                'expiry_date': '',
                'balance': 0.0,
                'referral_code': referral_code,
                'referred_by': referred_by or '',
                'is_blocked': 0,
                'entry_date': TimeManager.get_current_shamsi(),
                'last_activity': TimeManager.get_current_shamsi(),
                'api_calls_count': 0,
                'daily_limit': 5,
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
    def _check_user_exists(telegram_id: int) -> bool:
        """بررسی وجود کاربر بدون recursion - ✅ متد helper"""
        try:
            # بررسی در دیتابیس
            try:
                if hasattr(database_manager, 'get_user_by_telegram_id'):
                    db_user = database_manager.get_user_by_telegram_id(telegram_id)
                    if db_user:
                        return True
            except Exception:
                pass
            
            # بررسی در CSV
            try:
                if hasattr(CSVManager, 'get_user_data_from_csv'):
                    csv_user = CSVManager.get_user_data_from_csv(telegram_id)
                    if csv_user:
                        return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user exists {telegram_id}: {e}")
            return False
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """دریافت کاربر با شناسه تلگرام - ✅ Fixed Recursion
        
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
            
            # ✅ کاربر وجود ندارد - بازگشت None به جای ایجاد خودکار
            logger.info(f"User {telegram_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            return None
    
    @staticmethod
    def get_or_create_user(telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """دریافت یا ایجاد کاربر - ✅ جداگانه از get_user
        
        Args:
            telegram_id: شناسه تلگرام
            username: نام کاربری
            first_name: نام
            last_name: نام خانوادگی
            
        Returns:
            اطلاعات کاربر
        """
        try:
            # ابتدا سعی کن کاربر را پیدا کنی
            user = UserManager.get_user_by_telegram_id(telegram_id)
            if user:
                return user
            
            # اگر وجود ندارد، ایجاد کن
            logger.info(f"User {telegram_id} not found, creating new user")
            
            # ایجاد کاربر جدید
            created = UserManager.create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            if created:
                # بازگشت کاربر ایجاد شده
                user = UserManager.get_user_by_telegram_id(telegram_id)
                if user:
                    return user
            
            # اگر ایجاد ناموفق بود، کاربر پیش‌فرض برگردان
            return UserManager._create_default_user(telegram_id)
            
        except Exception as e:
            logger.error(f"Error getting or creating user {telegram_id}: {e}")
            return UserManager._create_default_user(telegram_id)
    
    @staticmethod
    def _create_default_user(telegram_id: int) -> Dict[str, Any]:
        """ایجاد کاربر پیش‌فرض - ✅ فقط return, بدون recursion
        
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
            
            # ✅ فقط return کن، ایجاد نکن تا recursion نشود
            logger.info(f"Returning default user for {telegram_id}")
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
                'package': csv_data.get('package', 'demo'),
                'package_expiry': csv_data.get('expiry_date', ''),
                'balance': float(csv_data.get('balance', 0)),
                'referral_code': csv_data.get('referral_code', ''),
                'referred_by': int(csv_data.get('referred_by', 0)) if csv_data.get('referred_by') else None,
                'is_blocked': csv_data.get('is_blocked', '0') == '1',
                'entry_date': csv_data.get('entry_date', ''),
                'last_activity': csv_data.get('last_activity', ''),
                'api_calls_count': int(csv_data.get('api_calls_count', 0)),
                'daily_limit': int(csv_data.get('daily_limit', 5)),
                'security_token': csv_data.get('security_token', '')
            }
        except Exception as e:
            logger.error(f"Error processing CSV user data: {e}")
            # ✅ بازگشت داده‌های خام در صورت خطا
            return csv_data if isinstance(csv_data, dict) else {}
    
    @staticmethod
    def update_user(telegram_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات کاربر در دیتابیس و CSV"""
        try:
            db_success = False
            if hasattr(database_manager, 'update_user'):
                try:
                    db_success = database_manager.update_user(telegram_id, **kwargs)
                except Exception as db_error:
                    logger.warning(f"Database update failed for user {telegram_id}: {db_error}")

            csv_success = False
            if hasattr(CSVManager, 'update_user_in_csv'):
                try:
                    # **[منطق جدید]** ابتدا چک می‌کنیم کاربر در CSV هست یا نه
                    if CSVManager.get_user_data_from_csv(telegram_id):
                        csv_success = CSVManager.update_user_in_csv(telegram_id, kwargs)
                    else:
                        # اگر کاربر در CSV نبود، هشدار نمی‌دهیم چون انتظار می‌رود در دیتابیس باشد
                        csv_success = True # عملیات را موفق در نظر می‌گیریم
                except Exception as csv_error:
                    logger.warning(f"CSV update failed for user {telegram_id}: {csv_error}")
            
            if db_success: # اولویت با موفقیت در دیتابیس است
                log_user_action(telegram_id, "user_updated", f"Fields: {list(kwargs.keys())}")
                return True
            
            # اگر دیتابیس ناموفق بود ولی CSV موفق بود
            if csv_success:
                log_user_action(telegram_id, "user_updated", f"Fields: {list(kwargs.keys())} (CSV only)")
                return True

            logger.error(f"Failed to update user {telegram_id} in any data source.")
            return False
                
        except Exception as e:
            logger.error(f"Critical error during user update for {telegram_id}: {e}", exc_info=True)
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
                return False, 999  # ✅ کاربر وجود ندارد، demo در نظر بگیر
            
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
                return False  # ✅ کاربر جدید مسدود نیست
            
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
            
            # اعطای پاداش رفرال
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
            
            return UserManager.update_user(telegram_id, balance=new_balance)
            
        except Exception as e:
            logger.error(f"Error adding balance for user {telegram_id}: {e}")
            return False
    
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
    def count_all_users() -> int:
        """تعداد کل کاربران را شمارش می‌کند."""
        try:
            # این تابع باید در database_manager شما پیاده‌سازی شود
            if hasattr(database_manager, 'count_users'):
                return database_manager.count_users()
            # اگر تابع بالا نبود، از CSV به عنوان جایگزین استفاده می‌کند
            if hasattr(CSVManager, 'count_users_in_csv'):
                return CSVManager.count_users_in_csv()
            logger.warning("No method found to count users.")
            return 0
        except Exception as e:
            logger.error(f"Error counting all users: {e}")
            return 0

    @staticmethod
    def get_all_users_paginated(page: int = 1, per_page: int = 5) -> List[Dict[str, Any]]:
        """لیستی از کاربران را به صورت صفحه‌بندی شده برمی‌گرداند."""
        try:
            # این تابع باید در database_manager شما پیاده‌سازی شود
            if hasattr(database_manager, 'get_users_paginated'):
                return database_manager.get_users_paginated(page, per_page)
            # اگر تابع بالا نبود، از CSV به عنوان جایگزین استفاده می‌کند
            if hasattr(CSVManager, 'get_users_from_csv'):
                return CSVManager.get_users_from_csv(page, per_page)
            logger.warning("No method found to get paginated users.")
            return []
        except Exception as e:
            logger.error(f"Error getting paginated users: {e}")
            return []        

    @staticmethod
    def block_user(telegram_id: int) -> bool:
        """یک کاربر را مسدود می‌کند."""
        try:
            # عدد 1 در دیتابیس معادل True برای فیلد is_blocked است
            success = UserManager.update_user(telegram_id, is_blocked=1)
            if success:
                log_user_action(telegram_id, "user_blocked", "User access has been revoked by an admin.")
            return success
        except Exception as e:
            logger.error(f"Error blocking user {telegram_id}: {e}")
            return False

    @staticmethod
    def unblock_user(telegram_id: int) -> bool:
        """یک کاربر را از حالت مسدود خارج می‌کند."""
        try:
            # عدد 0 در دیتابیس معادل False برای فیلد is_blocked است
            success = UserManager.update_user(telegram_id, is_blocked=0)
            if success:
                log_user_action(telegram_id, "user_unblocked", "User access has been restored by an admin.")
            return success
        except Exception as e:
            logger.error(f"Error unblocking user {telegram_id}: {e}")
            return False

# Export برای استفاده آسان‌تر
__all__ = ['UserManager']