"""
مدیریت فایل‌های CSV برای MrTrader Bot
"""
import csv
import os
from typing import Dict, List, Optional, Any, Union
from threading import Lock
from datetime import datetime

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
                Config.DATA_DIR.mkdir(exist_ok=True)
                
                headers = [
                    'telegram_id', 'username', 'first_name', 'last_name', 'phone_number',
                    'package', 'expiry_date', 'balance', 'referral_code', 'referred_by',
                    'is_blocked', 'entry_date', 'last_activity', 'api_calls_count',
                    'daily_limit', 'security_token'
                ]
                
                with open(Config.USER_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
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
                Config.DATA_DIR.mkdir(exist_ok=True)
                
                headers = [
                    'telegram_id', 'level', 'permissions', 'added_by', 
                    'added_date', 'is_active', 'last_login'
                ]
                
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                
                logger.info(f"Created admin CSV file: {Config.ADMIN_CSV_FILE}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring admin CSV exists: {e}")
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
                
                with open(Config.USER_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
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
                
                # آماده‌سازی داده‌ها
                current_time = TimeManager.get_current_shamsi()
                csv_row = {
                    'telegram_id': str(user_data.get('telegram_id', '')),
                    'username': user_data.get('username', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'phone_number': user_data.get('phone_number', ''),
                    'package': user_data.get('package', 'none'),
                    'expiry_date': user_data.get('expiry_date', ''),
                    'balance': str(user_data.get('balance', 0)),
                    'referral_code': user_data.get('referral_code', ''),
                    'referred_by': str(user_data.get('referred_by', '')),
                    'is_blocked': str(user_data.get('is_blocked', 0)),
                    'entry_date': user_data.get('entry_date', current_time),
                    'last_activity': user_data.get('last_activity', current_time),
                    'api_calls_count': str(user_data.get('api_calls_count', 0)),
                    'daily_limit': str(user_data.get('daily_limit', 10)),
                    'security_token': user_data.get('security_token', '')
                }
                
                # خواندن فایل موجود
                rows = []
                with open(Config.USER_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    headers = reader.fieldnames
                    rows = list(reader)
                
                # افزودن ردیف جدید
                rows.append(csv_row)
                
                # نوشتن به فایل
                with open(Config.USER_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
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
                
                # خواندن فایل
                rows = []
                user_found = False
                
                with open(Config.USER_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
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
                with open(Config.USER_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
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
                
                with open(Config.USER_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
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
                
                with open(Config.ADMIN_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
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
                
                # آماده‌سازی داده‌ها
                current_time = TimeManager.get_current_shamsi()
                csv_row = {
                    'telegram_id': telegram_id,
                    'level': str(admin_data.get('level', 1)),
                    'permissions': admin_data.get('permissions', ''),
                    'added_by': str(admin_data.get('added_by', '')),
                    'added_date': admin_data.get('added_date', current_time),
                    'is_active': str(admin_data.get('is_active', 1)),
                    'last_login': admin_data.get('last_login', '')
                }
                
                # خواندن فایل موجود
                rows = []
                with open(Config.ADMIN_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    headers = reader.fieldnames
                    rows = list(reader)
                
                # افزودن ردیف جدید
                rows.append(csv_row)
                
                # نوشتن به فایل
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
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
                
                # خواندن فایل
                rows = []
                admin_found = False
                
                with open(Config.ADMIN_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
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
                with open(Config.ADMIN_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
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
                
                with open(Config.ADMIN_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    return [row for row in reader if row.get('is_active', '1') == '1']
                    
        except Exception as e:
            logger.error(f"Error getting all admins from CSV: {e}")
            return []
    
    @classmethod
    def backup_csv_files(cls, backup_dir: str) -> bool:
        """پشتیبان‌گیری از فایل‌های CSV
        
        Args:
            backup_dir: مسیر پشتیبان‌گیری
            
        Returns:
            موفقیت عملیات
        """
        try:
            import shutil
            
            os.makedirs(backup_dir, exist_ok=True)
            
            csv_files = [
                Config.USER_CSV_FILE,
                Config.ADMIN_CSV_FILE,
                Config.PENDING_PAYMENTS_CSV,
                Config.PAYMENT_LOG_CSV,
                Config.SETTINGS_CSV_FILE
            ]
            
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    backup_file = os.path.join(backup_dir, os.path.basename(csv_file))
                    shutil.copy2(csv_file, backup_file)
                    logger.info(f"Backed up {csv_file} to {backup_file}")
            
            return True
            
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
            stats['premium_users'] = len([u for u in users if u.get('package', 'none') != 'none'])
            
            # آمار ادمین‌ها
            admins = cls.get_all_admins_from_csv()
            stats['total_admins'] = len(admins)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting CSV statistics: {e}")
            return {}


# Export برای استفاده آسان‌تر
__all__ = ['CSVManager']
