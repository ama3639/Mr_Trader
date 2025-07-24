"""
مدیریت فایل‌های CSV برای MrTrader Bot - Fixed Version
"""
import csv
import os
import shutil
from typing import Dict, List, Optional, Any, Union
from threading import Lock
from datetime import datetime
from pathlib import Path

from core.config import Config
from utils.logger import logger
from utils.time_manager import TimeManager


class CSVManager:
    """کلاس مدیریت فایل‌های CSV"""
    
    _lock = Lock()
    
    @classmethod
    def ensure_user_csv_exists(cls):
        """اطمینان از وجود فایل CSV کاربران"""
        try:
            if not os.path.exists(Config.USER_CSV_FILE):
                # ✅ ایجاد دیرکتوری در صورت عدم وجود
                Path(Config.USER_CSV_FILE).parent.mkdir(parents=True, exist_ok=True)
                
                # ✅ استفاده از headers از config
                headers = Config.CSV_SETTINGS["headers"]["users"]
                
                # ✅ استفاده از encoding از config
                with open(Config.USER_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.writer(csvfile, 
                                      delimiter=Config.CSV_SETTINGS["delimiter"],
                                      quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writerow(headers)
                
                logger.info(f"Created user CSV file: {Config.USER_CSV_FILE}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring user CSV exists: {e}")
            return False
    
    @classmethod
    def ensure_admin_csv_exists(cls):
        """اطمینان از وجود فایل CSV ادمین‌ها"""
        try:
            if not os.path.exists(Config.ADMIN_CSV_FILE):
                # ✅ ایجاد دیرکتوری در صورت عدم وجود
                Path(Config.ADMIN_CSV_FILE).parent.mkdir(parents=True, exist_ok=True)
                
                # ✅ استفاده از headers از config
                headers = Config.CSV_SETTINGS["headers"]["admins"]
                
                # ✅ استفاده از تنظیمات CSV از config
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.writer(csvfile,
                                      delimiter=Config.CSV_SETTINGS["delimiter"],
                                      quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writerow(headers)
                
                logger.info(f"Created admin CSV file: {Config.ADMIN_CSV_FILE}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring admin CSV exists: {e}")
            return False
    
    @classmethod
    def ensure_all_csv_files_exist(cls):
        """اطمینان از وجود همه فایل‌های CSV"""
        try:
            success = True
            
            # ✅ ایجاد همه فایل‌های CSV با headers مناسب
            csv_files_info = [
                (Config.USER_CSV_FILE, "users"),
                (Config.ADMIN_CSV_FILE, "admins"),
                (Config.TRANSACTIONS_CSV_FILE, "transactions")
            ]
            
            # ✅ فایل‌های اضافی اگر در config تعریف شده باشند
            if hasattr(Config, 'PENDING_PAYMENTS_CSV') and "pending_payments" in Config.CSV_SETTINGS["headers"]:
                csv_files_info.append((Config.PENDING_PAYMENTS_CSV, "pending_payments"))
            
            if hasattr(Config, 'PAYMENT_LOG_CSV') and "payment_log" in Config.CSV_SETTINGS["headers"]:
                csv_files_info.append((Config.PAYMENT_LOG_CSV, "payment_log"))
                
            if hasattr(Config, 'SETTINGS_CSV_FILE') and "settings" in Config.CSV_SETTINGS["headers"]:
                csv_files_info.append((Config.SETTINGS_CSV_FILE, "settings"))
            
            for file_path, header_key in csv_files_info:
                if not os.path.exists(file_path):
                    try:
                        # ایجاد دیرکتوری
                        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                        
                        # گرفتن headers
                        headers = Config.CSV_SETTINGS["headers"].get(header_key, [])
                        
                        if headers:
                            with open(file_path, 'w', newline='', 
                                     encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                                writer = csv.writer(csvfile,
                                                  delimiter=Config.CSV_SETTINGS["delimiter"],
                                                  quotechar=Config.CSV_SETTINGS["quotechar"])
                                writer.writerow(headers)
                            
                            logger.info(f"Created CSV file: {file_path}")
                        else:
                            logger.warning(f"No headers found for {header_key}")
                            
                    except Exception as file_error:
                        logger.error(f"Error creating {file_path}: {file_error}")
                        success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error ensuring all CSV files exist: {e}")
            return False
    
    @classmethod
    def get_user_data_from_csv(cls, telegram_id: Union[int, str]) -> Optional[Dict[str, str]]:
        """دریافت اطلاعات کاربر از فایل CSV
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            
        Returns:
            اطلاعات کاربر یا None
        """
        try:
            telegram_id = str(telegram_id)
            
            with cls._lock:
                if not os.path.exists(Config.USER_CSV_FILE):
                    cls.ensure_user_csv_exists()
                    return None
                
                # ✅ استفاده از تنظیمات CSV از config
                with open(Config.USER_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    for row in reader:
                        if row.get('telegram_id') == telegram_id:
                            return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user data from CSV for {telegram_id}: {e}")
            return None
    
    @classmethod
    def add_user_to_csv(cls, user_data: Dict[str, Any]) -> bool:
        """افزودن کاربر جدید به فایل CSV
        
        Args:
            user_data: اطلاعات کاربر
            
        Returns:
            موفقیت عملیات
        """
        try:
            with cls._lock:
                cls.ensure_user_csv_exists()
                
                # بررسی وجود کاربر
                existing_user = cls.get_user_data_from_csv(user_data.get('telegram_id'))
                if existing_user:
                    logger.warning(f"User {user_data.get('telegram_id')} already exists in CSV")
                    return False
                
                # ✅ بکاپ اختیاری
                if Config.CSV_SETTINGS.get("create_backup", False):
                    cls._create_backup(Config.USER_CSV_FILE)
                
                # آماده‌سازی داده‌ها
                current_time = TimeManager.get_current_shamsi()
                csv_row = {
                    'telegram_id': str(user_data.get('telegram_id', '')),
                    'username': user_data.get('username', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'phone_number': user_data.get('phone_number', ''),
                    'package': user_data.get('package', 'demo'),  # ✅ پیش‌فرض demo
                    'expiry_date': user_data.get('expiry_date', ''),
                    'balance': str(user_data.get('balance', 0)),
                    'referral_code': user_data.get('referral_code', ''),
                    'referred_by': str(user_data.get('referred_by', '')),
                    'is_blocked': str(user_data.get('is_blocked', 0)),
                    'entry_date': user_data.get('entry_date', current_time),
                    'last_activity': user_data.get('last_activity', current_time),
                    'api_calls_count': str(user_data.get('api_calls_count', 0)),
                    'daily_limit': str(user_data.get('daily_limit', 5)),  # ✅ پیش‌فرض 5
                    'security_token': user_data.get('security_token', '')
                }
                
                # خواندن فایل موجود
                rows = []
                with open(Config.USER_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    headers = reader.fieldnames
                    rows = list(reader)
                
                # افزودن ردیف جدید
                rows.append(csv_row)
                
                # نوشتن به فایل
                with open(Config.USER_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writeheader()
                    writer.writerows(rows)
                
                logger.info(f"Added user {user_data.get('telegram_id')} to CSV")
                return True
                
        except Exception as e:
            logger.error(f"Error adding user to CSV: {e}")
            return False
    
    @classmethod
    def update_user_in_csv(cls, telegram_id: Union[int, str], updates: Dict[str, Any]) -> bool:
        """به‌روزرسانی اطلاعات کاربر در فایل CSV
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            updates: اطلاعات جدید
            
        Returns:
            موفقیت عملیات
        """
        try:
            telegram_id = str(telegram_id)
            
            with cls._lock:
                if not os.path.exists(Config.USER_CSV_FILE):
                    logger.warning("User CSV file does not exist")
                    return False
                
                # ✅ بکاپ اختیاری
                if Config.CSV_SETTINGS.get("backup_on_write", False):
                    cls._create_backup(Config.USER_CSV_FILE)
                
                # خواندن فایل
                rows = []
                user_found = False
                
                with open(Config.USER_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    headers = reader.fieldnames
                    
                    for row in reader:
                        if row.get('telegram_id') == telegram_id:
                            # به‌روزرسانی اطلاعات
                            for key, value in updates.items():
                                if key in headers:
                                    row[key] = str(value)
                            
                            # به‌روزرسانی زمان آخرین فعالیت
                            row['last_activity'] = TimeManager.get_current_shamsi()
                            user_found = True
                        
                        rows.append(row)
                
                if not user_found:
                    logger.warning(f"User {telegram_id} not found in CSV")
                    return False
                
                # نوشتن به فایل
                with open(Config.USER_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writeheader()
                    writer.writerows(rows)
                
                logger.info(f"Updated user {telegram_id} in CSV")
                return True
                
        except Exception as e:
            logger.error(f"Error updating user in CSV: {e}")
            return False
    
    @classmethod
    def get_all_users_from_csv(cls) -> List[Dict[str, str]]:
        """دریافت تمام کاربران از فایل CSV
        
        Returns:
            لیست اطلاعات کاربران
        """
        try:
            with cls._lock:
                if not os.path.exists(Config.USER_CSV_FILE):
                    cls.ensure_user_csv_exists()
                    return []
                
                with open(Config.USER_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    return list(reader)
                    
        except Exception as e:
            logger.error(f"Error getting all users from CSV: {e}")
            return []
    
    @classmethod
    def find_user_by_referral_code(cls, referral_code: str) -> Optional[str]:
        """یافتن کاربر با کد رفرال
        
        Args:
            referral_code: کد رفرال
            
        Returns:
            telegram_id کاربر یا None
        """
        try:
            users = cls.get_all_users_from_csv()
            for user in users:
                if user.get('referral_code') == referral_code:
                    return user.get('telegram_id')
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by referral code: {e}")
            return None
    
    @classmethod
    def get_users_by_package(cls, package: str) -> List[Dict[str, str]]:
        """دریافت کاربران با پکیج مشخص
        
        Args:
            package: نوع پکیج
            
        Returns:
            لیست کاربران با پکیج مشخص
        """
        try:
            users = cls.get_all_users_from_csv()
            return [user for user in users if user.get('package') == package]
            
        except Exception as e:
            logger.error(f"Error getting users by package: {e}")
            return []
    
    @classmethod
    def get_active_users(cls) -> List[Dict[str, str]]:
        """دریافت کاربران فعال (غیر مسدود)
        
        Returns:
            لیست کاربران فعال
        """
        try:
            users = cls.get_all_users_from_csv()
            return [user for user in users if user.get('is_blocked', '0') != '1']
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    @classmethod
    def get_admin_data_from_csv(cls, telegram_id: Union[int, str]) -> Optional[Dict[str, str]]:
        """دریافت اطلاعات ادمین از فایل CSV
        
        Args:
            telegram_id: شناسه تلگرام ادمین
            
        Returns:
            اطلاعات ادمین یا None
        """
        try:
            telegram_id = str(telegram_id)
            
            with cls._lock:
                if not os.path.exists(Config.ADMIN_CSV_FILE):
                    cls.ensure_admin_csv_exists()
                    return None
                
                with open(Config.ADMIN_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    for row in reader:
                        if row.get('telegram_id') == telegram_id and row.get('is_active', '1') == '1':
                            return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting admin data from CSV for {telegram_id}: {e}")
            return None
    
    @classmethod
    def add_admin_to_csv(cls, admin_data: Dict[str, Any]) -> bool:
        """افزودن ادمین جدید به فایل CSV
        
        Args:
            admin_data: اطلاعات ادمین
            
        Returns:
            موفقیت عملیات
        """
        try:
            with cls._lock:
                cls.ensure_admin_csv_exists()
                
                telegram_id = str(admin_data.get('telegram_id', ''))
                
                # بررسی وجود ادمین
                existing_admin = cls.get_admin_data_from_csv(telegram_id)
                if existing_admin:
                    # به‌روزرسانی ادمین موجود
                    return cls.update_admin_in_csv(telegram_id, admin_data)
                
                # ✅ بکاپ اختیاری
                if Config.CSV_SETTINGS.get("create_backup", False):
                    cls._create_backup(Config.ADMIN_CSV_FILE)
                
                # آماده‌سازی داده‌ها
                current_time = TimeManager.get_current_shamsi()
                csv_row = {
                    'telegram_id': telegram_id,
                    'username': admin_data.get('username', ''),
                    'first_name': admin_data.get('first_name', ''),
                    'last_name': admin_data.get('last_name', ''),
                    'role': admin_data.get('role', 'admin'),
                    'permissions': admin_data.get('permissions', ''),
                    'entry_date': admin_data.get('entry_date', current_time),
                    'last_activity': admin_data.get('last_activity', ''),
                    'is_active': str(admin_data.get('is_active', 1))
                }
                
                # خواندن فایل موجود
                rows = []
                with open(Config.ADMIN_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    headers = reader.fieldnames
                    rows = list(reader)
                
                # افزودن ردیف جدید
                rows.append(csv_row)
                
                # نوشتن به فایل
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writeheader()
                    writer.writerows(rows)
                
                logger.info(f"Added admin {telegram_id} to CSV")
                return True
                
        except Exception as e:
            logger.error(f"Error adding admin to CSV: {e}")
            return False
    
    @classmethod
    def update_admin_in_csv(cls, telegram_id: Union[int, str], updates: Dict[str, Any]) -> bool:
        """به‌روزرسانی اطلاعات ادمین در فایل CSV
        
        Args:
            telegram_id: شناسه تلگرام ادمین
            updates: اطلاعات جدید
            
        Returns:
            موفقیت عملیات
        """
        try:
            telegram_id = str(telegram_id)
            
            with cls._lock:
                if not os.path.exists(Config.ADMIN_CSV_FILE):
                    logger.warning("Admin CSV file does not exist")
                    return False
                
                # ✅ بکاپ اختیاری
                if Config.CSV_SETTINGS.get("backup_on_write", False):
                    cls._create_backup(Config.ADMIN_CSV_FILE)
                
                # خواندن فایل
                rows = []
                admin_found = False
                
                with open(Config.ADMIN_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    headers = reader.fieldnames
                    
                    for row in reader:
                        if row.get('telegram_id') == telegram_id:
                            # به‌روزرسانی اطلاعات
                            for key, value in updates.items():
                                if key in headers:
                                    row[key] = str(value)
                            
                            admin_found = True
                        
                        rows.append(row)
                
                if not admin_found:
                    logger.warning(f"Admin {telegram_id} not found in CSV")
                    return False
                
                # نوشتن به فایل
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    writer.writeheader()
                    writer.writerows(rows)
                
                logger.info(f"Updated admin {telegram_id} in CSV")
                return True
                
        except Exception as e:
            logger.error(f"Error updating admin in CSV: {e}")
            return False
    
    @classmethod
    def get_all_admins_from_csv(cls) -> List[Dict[str, str]]:
        """دریافت تمام ادمین‌ها از فایل CSV
        
        Returns:
            لیست اطلاعات ادمین‌ها
        """
        try:
            with cls._lock:
                if not os.path.exists(Config.ADMIN_CSV_FILE):
                    cls.ensure_admin_csv_exists()
                    return []
                
                with open(Config.ADMIN_CSV_FILE, 'r', 
                         encoding=Config.CSV_SETTINGS["encoding"]) as csvfile:
                    reader = csv.DictReader(csvfile,
                                          delimiter=Config.CSV_SETTINGS["delimiter"],
                                          quotechar=Config.CSV_SETTINGS["quotechar"])
                    return [row for row in reader if row.get('is_active', '1') == '1']
                    
        except Exception as e:
            logger.error(f"Error getting all admins from CSV: {e}")
            return []
    
    @classmethod
    def _create_backup(cls, file_path: str) -> bool:
        """ایجاد بکاپ از فایل CSV
        
        Args:
            file_path: مسیر فایل اصلی
            
        Returns:
            موفقیت عملیات
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # ایجاد نام فایل بکاپ
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{file_name}"
            
            # ✅ استفاده از BACKUP_DIRECTORY از config
            backup_dir = getattr(Config, 'BACKUP_DIRECTORY', Config.BACKUPS_DIR)
            backup_path = os.path.join(backup_dir, backup_name)
            
            # ایجاد دیرکتوری بکاپ
            os.makedirs(backup_dir, exist_ok=True)
            
            # کپی فایل
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return False
    
    @classmethod
    def backup_csv_files(cls, backup_dir: str = None) -> bool:
        """پشتیبان‌گیری از فایل‌های CSV
        
        Args:
            backup_dir: مسیر پشتیبان‌گیری
            
        Returns:
            موفقیت عملیات
        """
        try:
            if backup_dir is None:
                backup_dir = getattr(Config, 'BACKUP_DIRECTORY', Config.BACKUPS_DIR)
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # ✅ فایل‌های CSV برای بکاپ
            csv_files = [
                Config.USER_CSV_FILE,
                Config.ADMIN_CSV_FILE,
                Config.TRANSACTIONS_CSV_FILE
            ]
            
            # ✅ فایل‌های اضافی اگر وجود داشته باشند
            additional_files = [
                getattr(Config, 'PENDING_PAYMENTS_CSV', None),
                getattr(Config, 'PAYMENT_LOG_CSV', None),
                getattr(Config, 'SETTINGS_CSV_FILE', None),
                getattr(Config, 'PACKAGES_CSV_FILE', None),
                getattr(Config, 'REFERRALS_CSV_FILE', None),
                getattr(Config, 'USAGE_CSV_FILE', None),
                getattr(Config, 'ANALYTICS_CSV_FILE', None)
            ]
            
            csv_files.extend([f for f in additional_files if f is not None])
            
            success_count = 0
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    if cls._create_backup(csv_file):
                        success_count += 1
                    else:
                        logger.warning(f"Failed to backup {csv_file}")
            
            logger.info(f"Backed up {success_count}/{len(csv_files)} CSV files")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error backing up CSV files: {e}")
            return False
    
    @classmethod
    def get_csv_statistics(cls) -> Dict[str, int]:
        """آمار فایل‌های CSV
        
        Returns:
            آمار تعداد ردیف‌ها در فایل‌های مختلف
        """
        try:
            stats = {}
            
            # آمار کاربران
            users = cls.get_all_users_from_csv()
            stats['total_users'] = len(users)
            stats['active_users'] = len([u for u in users if u.get('is_blocked', '0') != '1'])
            stats['premium_users'] = len([u for u in users if u.get('package', 'demo') not in ['demo', 'none']])
            
            # آمار ادمین‌ها
            admins = cls.get_all_admins_from_csv()
            stats['total_admins'] = len(admins)
            
            # آمار پکیج‌ها
            package_counts = {}
            for user in users:
                package = user.get('package', 'demo')
                package_counts[package] = package_counts.get(package, 0) + 1
            stats['package_distribution'] = package_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting CSV statistics: {e}")
            return {}
    
    @classmethod
    def validate_csv_integrity(cls) -> Dict[str, bool]:
        """بررسی یکپارچگی فایل‌های CSV
        
        Returns:
            وضعیت یکپارچگی هر فایل
        """
        try:
            results = {}
            
            # بررسی فایل کاربران
            try:
                users = cls.get_all_users_from_csv()
                telegram_ids = [user.get('telegram_id') for user in users]
                unique_ids = set(telegram_ids)
                
                results['users_file_exists'] = os.path.exists(Config.USER_CSV_FILE)
                results['users_readable'] = len(users) >= 0
                results['users_no_duplicates'] = len(telegram_ids) == len(unique_ids)
                results['users_valid_data'] = all(user.get('telegram_id') for user in users)
                
            except Exception:
                results.update({
                    'users_file_exists': False,
                    'users_readable': False,
                    'users_no_duplicates': False,
                    'users_valid_data': False
                })
            
            # بررسی فایل ادمین‌ها
            try:
                admins = cls.get_all_admins_from_csv()
                admin_ids = [admin.get('telegram_id') for admin in admins]
                unique_admin_ids = set(admin_ids)
                
                results['admins_file_exists'] = os.path.exists(Config.ADMIN_CSV_FILE)
                results['admins_readable'] = len(admins) >= 0
                results['admins_no_duplicates'] = len(admin_ids) == len(unique_admin_ids)
                results['admins_valid_data'] = all(admin.get('telegram_id') for admin in admins)
                
            except Exception:
                results.update({
                    'admins_file_exists': False,
                    'admins_readable': False,
                    'admins_no_duplicates': False,
                    'admins_valid_data': False
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating CSV integrity: {e}")
            return {}


# Export برای استفاده آسان‌تر
__all__ = ['CSVManager']