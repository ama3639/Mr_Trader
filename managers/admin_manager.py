"""
مدیریت ادمین‌ها و سطوح دسترسی MrTrader Bot
"""
from typing import List, Dict, Tuple , Optional, Set
from datetime import datetime

# **[اصلاح شد]** Config به درستی وارد شد
from core.config import Config
from utils.logger import logger, log_admin_action
from utils.time_manager import TimeManager
from database.database_manager import database_manager
from managers.csv_manager import CSVManager
from core.cache import cache

class AdminManager:
    """کلاس مدیریت ادمین‌ها و سطوح دسترسی"""
    
    # کش سطوح دسترسی ادمین‌ها
    _admin_cache = {}
    _manager_ids = set()
    
    @classmethod
    def initialize_managers(cls, manager_ids: List[int]):
        """مقداردهی اولیه مدیران اصلی"""
        cls._manager_ids = set(manager_ids)
        logger.info(f"Initialized {len(manager_ids)} main managers")
    
    @classmethod
    def is_manager(cls, telegram_id: int) -> bool:
        """بررسی مدیر اصلی بودن"""
        return telegram_id in cls._manager_ids
    
    @classmethod
    def is_admin(cls, telegram_id: int) -> bool:
        """
        **[اصلاح شد]**
        بررسی ادمین بودن کاربر به صورت مستقیم از لیست ادمین‌ها در فایل Config.
        این روش یک منبع حقیقت واحد (Single Source of Truth) ایجاد می‌کند و از پیچیدگی جلوگیری می‌کند.
        """
        try:
            # بررسی مستقیم از لیست ADMINS که از فایل .env خوانده شده است
            return telegram_id in Config.ADMINS
        except Exception as e:
            logger.error(f"Error checking admin status for {telegram_id}: {e}")
            return False
    
    @classmethod
    def get_admin_level(cls, telegram_id: int) -> int:
        """دریافت سطح دسترسی ادمین"""
        try:
            if cls.is_manager(telegram_id):
                return 4
            
            if not cls.is_admin(telegram_id):
                return 0

            cache_key = f"admin_level_{telegram_id}"
            cached_level = cache.get(cache_key)
            if cached_level is not None:
                return int(cached_level)
            
            level = database_manager.get_admin_level(telegram_id)
            
            if level == 0:
                admin_data = CSVManager.get_admin_data_from_csv(telegram_id)
                if admin_data:
                    level = int(admin_data.get('level', 1))
            
            cache.set(cache_key, level, 300)
            return level
            
        except Exception as e:
            logger.error(f"Error getting admin level for {telegram_id}: {e}")
            return 0
    
    @classmethod
    def add_admin(cls, telegram_id: int, level: int = 1, added_by: int = None) -> bool:
        """افزودن ادمین جدید
        
        Args:
            telegram_id: شناسه تلگرام ادمین جدید
            level: سطح دسترسی (1-3)
            added_by: شناسه تلگرام ادمین اضافه‌کننده
            
        Returns:
            موفقیت عملیات
        """
        try:
            if level < 1 or level > 3:
                logger.error(f"Invalid admin level: {level}")
                return False
            
            # افزودن به دیتابیس
            db_success = database_manager.add_admin(telegram_id, level, added_by)
            
            # افزودن به CSV
            admin_data = {
                'telegram_id': telegram_id,
                'level': level,
                'permissions': cls._get_permissions_for_level(level),
                'added_by': added_by,
                'added_date': TimeManager.get_current_shamsi(),
                'is_active': 1,
                'last_login': ''
            }
            
            csv_success = CSVManager.add_admin_to_csv(admin_data)
            
            if db_success or csv_success:
                # پاکسازی کش
                cls._clear_admin_cache(telegram_id)
                
                log_admin_action(
                    added_by or 0, 
                    "admin_added", 
                    str(telegram_id), 
                    f"Level: {level}"
                )
                
                logger.info(f"Added admin {telegram_id} with level {level}")
                return True
            else:
                logger.error(f"Failed to add admin {telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding admin {telegram_id}: {e}")
            return False
    
    @classmethod
    def remove_admin(cls, telegram_id: int, removed_by: int = None) -> bool:
        """حذف ادمین
        
        Args:
            telegram_id: شناسه تلگرام ادمین
            removed_by: شناسه تلگرام حذف‌کننده
            
        Returns:
            موفقیت عملیات
        """
        try:
            # مدیران اصلی قابل حذف نیستند
            if cls.is_manager(telegram_id):
                logger.warning(f"Cannot remove main manager: {telegram_id}")
                return False
            
            # غیرفعال کردن در دیتابیس
            db_success = database_manager.update_user(
                telegram_id, 
                is_active=False
            )
            
            # غیرفعال کردن در CSV
            csv_success = CSVManager.update_admin_in_csv(
                telegram_id, 
                {'is_active': 0}
            )
            
            if db_success or csv_success:
                # پاکسازی کش
                cls._clear_admin_cache(telegram_id)
                
                log_admin_action(
                    removed_by or 0, 
                    "admin_removed", 
                    str(telegram_id)
                )
                
                logger.info(f"Removed admin {telegram_id}")
                return True
            else:
                logger.error(f"Failed to remove admin {telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing admin {telegram_id}: {e}")
            return False
    
    @classmethod
    def update_admin_level(cls, telegram_id: int, new_level: int, updated_by: int = None) -> bool:
        """به‌روزرسانی سطح دسترسی ادمین
        
        Args:
            telegram_id: شناسه تلگرام ادمین
            new_level: سطح دسترسی جدید
            updated_by: شناسه تلگرام به‌روزرسان
            
        Returns:
            موفقیت عملیات
        """
        try:
            if new_level < 1 or new_level > 3:
                logger.error(f"Invalid admin level: {new_level}")
                return False
            
            # مدیران اصلی قابل تغییر نیستند
            if cls.is_manager(telegram_id):
                logger.warning(f"Cannot change main manager level: {telegram_id}")
                return False
            
            old_level = cls.get_admin_level(telegram_id)
            
            # به‌روزرسانی در دیتابیس
            db_success = database_manager.execute_query(
                "UPDATE admins SET level = ? WHERE telegram_id = ?",
                (new_level, telegram_id)
            )
            
            # به‌روزرسانی در CSV
            csv_success = CSVManager.update_admin_in_csv(
                telegram_id, 
                {
                    'level': new_level,
                    'permissions': cls._get_permissions_for_level(new_level)
                }
            )
            
            if db_success or csv_success:
                # پاکسازی کش
                cls._clear_admin_cache(telegram_id)
                
                log_admin_action(
                    updated_by or 0, 
                    "admin_level_updated", 
                    str(telegram_id), 
                    f"Old level: {old_level}, New level: {new_level}"
                )
                
                logger.info(f"Updated admin {telegram_id} level from {old_level} to {new_level}")
                return True
            else:
                logger.error(f"Failed to update admin {telegram_id} level")
                return False
                
        except Exception as e:
            logger.error(f"Error updating admin level for {telegram_id}: {e}")
            return False
    
    @classmethod
    def get_all_admins(cls) -> List[Dict]:
        """دریافت تمام ادمین‌ها
        
        Returns:
            لیست اطلاعات ادمین‌ها
        """
        try:
            # دریافت از CSV
            csv_admins = CSVManager.get_all_admins_from_csv()
            
            # افزودن مدیران اصلی
            all_admins = []
            
            for manager_id in cls._manager_ids:
                all_admins.append({
                    'telegram_id': manager_id,
                    'level': 4,
                    'permissions': 'all',
                    'added_by': 'system',
                    'added_date': 'system',
                    'is_active': True,
                    'last_login': '',
                    'type': 'main_manager'
                })
            
            # افزودن ادمین‌های عادی
            for admin in csv_admins:
                admin['type'] = 'admin'
                all_admins.append(admin)
            
            return all_admins
            
        except Exception as e:
            logger.error(f"Error getting all admins: {e}")
            return []
    
    @classmethod
    def has_permission(cls, telegram_id: int, permission: str) -> bool:
        """بررسی دسترسی ادمین به عملیات خاص
        
        Args:
            telegram_id: شناسه تلگرام
            permission: نوع دسترسی
            
        Returns:
            آیا دسترسی دارد
        """
        try:
            level = cls.get_admin_level(telegram_id)
            
            if level == 0:
                return False
            
            # مدیران اصلی به همه چیز دسترسی دارند
            if level == 4:
                return True
            
            # نقشه دسترسی‌ها
            permissions_map = {
                1: ['view_users', 'view_reports', 'basic_support'],
                2: ['view_users', 'view_reports', 'basic_support', 'manage_payments', 'user_management'],
                3: ['view_users', 'view_reports', 'basic_support', 'manage_payments', 'user_management', 'admin_management', 'system_settings']
            }
            
            level_permissions = permissions_map.get(level, [])
            return permission in level_permissions
            
        except Exception as e:
            logger.error(f"Error checking permission {permission} for {telegram_id}: {e}")
            return False
    
    @classmethod
    def update_last_login(cls, telegram_id: int) -> bool:
        """به‌روزرسانی آخرین ورود ادمین
        
        Args:
            telegram_id: شناسه تلگرام
            
        Returns:
            موفقیت عملیات
        """
        try:
            if not cls.is_admin(telegram_id):
                return False
            
            current_time = TimeManager.get_current_shamsi()
            
            # به‌روزرسانی در CSV (مدیران اصلی در CSV نیستند)
            if not cls.is_manager(telegram_id):
                CSVManager.update_admin_in_csv(
                    telegram_id, 
                    {'last_login': current_time}
                )
            
            # به‌روزرسانی در دیتابیس
            database_manager.execute_query(
                "UPDATE admins SET last_login = ? WHERE telegram_id = ?",
                (current_time, telegram_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating last login for admin {telegram_id}: {e}")
            return False
    
    @classmethod
    def get_admin_statistics(cls) -> Dict:
        """آمار ادمین‌ها
        
        Returns:
            آمار کلی ادمین‌ها
        """
        try:
            all_admins = cls.get_all_admins()
            
            stats = {
                'total_admins': len(all_admins),
                'main_managers': len(cls._manager_ids),
                'active_admins': len([a for a in all_admins if a.get('is_active', True)]),
                'levels': {1: 0, 2: 0, 3: 0, 4: 0}
            }
            
            for admin in all_admins:
                level = int(admin.get('level', 1))
                if level in stats['levels']:
                    stats['levels'][level] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting admin statistics: {e}")
            return {}
    
    @classmethod
    def search_admins(cls, query: str) -> List[Dict]:
        """جستجوی ادمین‌ها
        
        Args:
            query: عبارت جستجو
            
        Returns:
            لیست ادمین‌های یافت شده
        """
        try:
            all_admins = cls.get_all_admins()
            results = []
            
            query = query.lower()
            
            for admin in all_admins:
                if (query in str(admin.get('telegram_id', '')).lower() or
                    query in str(admin.get('level', '')).lower()):
                    results.append(admin)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching admins: {e}")
            return []
    
    @classmethod
    def _get_permissions_for_level(cls, level: int) -> str:
        """دریافت دسترسی‌های سطح مشخص
        
        Args:
            level: سطح دسترسی
            
        Returns:
            رشته دسترسی‌ها
        """
        permissions_map = {
            1: "view_users,view_reports,basic_support",
            2: "view_users,view_reports,basic_support,manage_payments,user_management",
            3: "view_users,view_reports,basic_support,manage_payments,user_management,admin_management,system_settings"
        }
        
        return permissions_map.get(level, "")
    
    @classmethod
    def _clear_admin_cache(cls, telegram_id: int):
        """پاکسازی کش ادمین
        
        Args:
            telegram_id: شناسه تلگرام
        """
        try:
            # پاکسازی کش داخلی
            if telegram_id in cls._admin_cache:
                del cls._admin_cache[telegram_id]
            
            # پاکسازی کش اصلی
            cache_key = f"admin_level_{telegram_id}"
            cache.delete(cache_key)
            
        except Exception as e:
            logger.error(f"Error clearing admin cache for {telegram_id}: {e}")
    
    @classmethod
    def validate_admin_action(cls, admin_id: int, target_id: int, action: str) -> Tuple[bool, str]:
        """اعتبارسنجی عملیات ادمین
        
        Args:
            admin_id: شناسه ادمین
            target_id: شناسه هدف
            action: نوع عملیات
            
        Returns:
            (مجاز بودن، پیام خطا)
        """
        try:
            admin_level = cls.get_admin_level(admin_id)
            target_level = cls.get_admin_level(target_id)
            
            # غیرادمین‌ها نمی‌توانند عملیات ادمین انجام دهند
            if admin_level == 0:
                return False, "شما سطح دسترسی کافی ندارید."
            
            # مدیران اصلی به همه چیز دسترسی دارند
            if admin_level == 4:
                return True, ""
            
            # ادمین‌ها نمی‌توانند روی ادمین‌های بالاتر عملیات انجام دهند
            if target_level >= admin_level and target_id != admin_id:
                return False, "شما نمی‌توانید روی ادمین‌های هم‌سطح یا بالاتر عملیات انجام دهید."
            
            # بررسی دسترسی‌های خاص
            required_permissions = {
                'block_user': 2,
                'manage_payments': 2,
                'add_admin': 3,
                'remove_admin': 3,
                'system_settings': 3
            }
            
            required_level = required_permissions.get(action, 1)
            if admin_level < required_level:
                return False, f"این عملیات نیاز به سطح دسترسی {required_level} دارد."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating admin action: {e}")
            return False, "خطا در بررسی دسترسی."
    
    @classmethod
    def log_admin_activity(cls, admin_id: int, activity: str, details: str = ""):
        """ثبت فعالیت ادمین
        
        Args:
            admin_id: شناسه ادمین
            activity: نوع فعالیت
            details: جزئیات
        """
        try:
            log_admin_action(admin_id, activity, "", details)
            
            # ثبت در دیتابیس برای پیگیری بهتر
            database_manager.add_user_log(
                admin_id, 
                f"admin_{activity}", 
                details
            )
            
        except Exception as e:
            logger.error(f"Error logging admin activity: {e}")

    @classmethod
    def grant_package_to_user(cls, admin_id: int, target_user_id: int, package_type: str, 
                              duration: str, expiry_date: datetime) -> bool:
        """
        پکیج را به کاربر اعطا می‌کند (با استفاده از تابع متمرکز).
        پارامتر expiry_date دیگر مستقیماً استفاده نمی‌شود و محاسبه آن به تابع مرکزی سپرده می‌شود.
        """
        try:
            # محاسبه duration_days از روی duration string
            duration_map = {
                'monthly': 30,
                'quarterly': 90,
                'yearly': 365,
                'lifetime': 365 * 100
            }
            duration_days = duration_map.get(duration, 30)

            # فراخوانی تابع متمرکز جدید
            from managers.user_manager import UserManager
            success = UserManager.set_user_package(
                target_user_id,
                package_type,
                duration_days
            )

            if success:
                log_admin_action(
                    admin_id, 
                    "package_granted",
                    str(target_user_id),
                    f"Package: {package_type}, Duration: {duration}"
                )
                logger.info(f"Admin {admin_id} granted package {package_type} to user {target_user_id}.")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in grant_package_to_user for user {target_user_id}: {e}", exc_info=True)
            return False
        
# توابع کمکی برای سازگاری با کد قبلی
def is_admin(telegram_id: int) -> bool:
    """بررسی ادمین بودن (تابع کمکی)"""
    return AdminManager.is_admin(telegram_id)


def is_manager(telegram_id: int) -> bool:
    """بررسی مدیر اصلی بودن (تابع کمکی)"""
    return AdminManager.is_manager(telegram_id)


def get_admin_level(telegram_id: int) -> int:
    """دریافت سطح ادمین (تابع کمکی)"""
    return AdminManager.get_admin_level(telegram_id)


# Export برای استفاده آسان‌تر
__all__ = [
    'AdminManager',
    'is_admin',
    'is_manager', 
    'get_admin_level'
]
