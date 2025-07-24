"""
مدیریت پشتیبان‌گیری و بازیابی MrTrader Bot
"""
import os
import shutil
import sqlite3
import gzip
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from pathlib import Path

from core.config import Config
from utils.logger import logger
from database.database_manager import DatabaseManager
from core.cache import cache


@dataclass
class BackupInfo:
    """اطلاعات بکاپ"""
    filename: str
    size: int
    created_at: datetime
    backup_type: str  # 'full', 'incremental', 'differential'
    checksum: str
    description: str = ''
    is_compressed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'filename': self.filename,
            'size': self.size,
            'created_at': self.created_at.isoformat(),
            'backup_type': self.backup_type,
            'checksum': self.checksum,
            'description': self.description,
            'is_compressed': self.is_compressed
        }


class BackupManager:
    """مدیریت پشتیبان‌گیری و بازیابی"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.backup_dir = Path(Config.BACKUPS_DIR)
        self.backup_schedule = {
            'daily': True,
            'weekly': True,
            'monthly': True
        }
        self._initialize_backup_system()
    
    def _initialize_backup_system(self):
        """مقداردهی اولیه سیستم بکاپ"""
        try:
            # ایجاد دایرکتوری بکاپ
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # ایجاد زیرپوشه‌ها
            for subdir in ['daily', 'weekly', 'monthly', 'manual']:
                (self.backup_dir / subdir).mkdir(exist_ok=True)
            
            # ایجاد جدول تاریخچه بکاپ
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS backup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    is_compressed BOOLEAN DEFAULT 1,
                    restoration_count INTEGER DEFAULT 0,
                    last_verified TIMESTAMP
                )
            """)
            
            # ایجاد جدول برنامه‌ریزی بکاپ
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS backup_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_type TEXT NOT NULL,
                    schedule_pattern TEXT NOT NULL,
                    last_backup TIMESTAMP,
                    next_backup TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    retention_days INTEGER DEFAULT 30,
                    max_backups INTEGER DEFAULT 10
                )
            """)
            
            # ایجاد جدول نظارت بر فضای ذخیره‌سازی
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS storage_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_space INTEGER,
                    used_space INTEGER,
                    backup_space INTEGER,
                    free_space INTEGER,
                    warning_threshold INTEGER DEFAULT 85
                )
            """)
            
            logger.info("Backup system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing backup system: {e}")
    
    async def create_full_backup(self, description: str = '') -> Optional[BackupInfo]:
        """ایجاد بکاپ کامل"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"mrtrader_full_{timestamp}.sql.gz"
            backup_path = self.backup_dir / 'manual' / backup_filename
            
            logger.info(f"Starting full backup: {backup_filename}")
            
            # بکاپ دیتابیس اصلی
            db_backup_success = await self._backup_database(backup_path)
            if not db_backup_success:
                logger.error("Database backup failed")
                return None
            
            # بکاپ فایل‌های کانفیگ
            await self._backup_config_files(backup_path.parent / f"config_{timestamp}")
            
            # بکاپ لاگ‌ها (اختیاری)
            await self._backup_logs(backup_path.parent / f"logs_{timestamp}")
            
            # محاسبه checksum
            checksum = self._calculate_file_checksum(backup_path)
            
            # دریافت اندازه فایل
            file_size = backup_path.stat().st_size
            
            # ساخت اطلاعات بکاپ
            backup_info = BackupInfo(
                filename=backup_filename,
                size=file_size,
                created_at=datetime.now(),
                backup_type='full',
                checksum=checksum,
                description=description or f"Full backup - {timestamp}",
                is_compressed=True
            )
            
            # ثبت در تاریخچه
            await self._save_backup_info(backup_info)
            
            logger.info(f"Full backup completed: {backup_filename} ({file_size / 1024 / 1024:.2f} MB)")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            return None
    
    async def create_incremental_backup(self, last_backup_date: datetime = None) -> Optional[BackupInfo]:
        """ایجاد بکاپ افزایشی"""
        try:
            if last_backup_date is None:
                # یافتن آخرین بکاپ
                last_backup = self.db.fetch_one("""
                    SELECT created_at FROM backup_history 
                    WHERE backup_type IN ('full', 'incremental')
                    ORDER BY created_at DESC LIMIT 1
                """)
                
                if last_backup:
                    last_backup_date = datetime.fromisoformat(last_backup['created_at'])
                else:
                    # اگر بکاپ قبلی نداریم، full backup بگیر
                    return await self.create_full_backup("Auto full backup - no previous backup found")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"mrtrader_inc_{timestamp}.sql.gz"
            backup_path = self.backup_dir / 'daily' / backup_filename
            
            logger.info(f"Starting incremental backup since {last_backup_date}")
            
            # بکاپ تغییرات از آخرین بکاپ
            changes_backed_up = await self._backup_changes_since(backup_path, last_backup_date)
            
            if not changes_backed_up:
                logger.info("No changes since last backup")
                return None
            
            # محاسبه checksum و اندازه
            checksum = self._calculate_file_checksum(backup_path)
            file_size = backup_path.stat().st_size
            
            backup_info = BackupInfo(
                filename=backup_filename,
                size=file_size,
                created_at=datetime.now(),
                backup_type='incremental',
                checksum=checksum,
                description=f"Incremental backup since {last_backup_date.strftime('%Y-%m-%d %H:%M')}",
                is_compressed=True
            )
            
            await self._save_backup_info(backup_info)
            
            logger.info(f"Incremental backup completed: {backup_filename}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            return None
    
    async def _backup_database(self, backup_path: Path) -> bool:
        """بکاپ دیتابیس"""
        try:
            db_path = Path(Config.DATABASE_FILE)
            
            if not db_path.exists():
                logger.error(f"Database file not found: {db_path}")
                return False
            
            # ایجاد dump از دیتابیس
            with sqlite3.connect(str(db_path)) as conn:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as backup_file:
                    # نوشتن header
                    backup_file.write(f"-- MrTrader Database Backup\n")
                    backup_file.write(f"-- Created: {datetime.now().isoformat()}\n")
                    backup_file.write(f"-- Database: {db_path}\n\n")
                    
                    # dump کامل دیتابیس
                    for line in conn.iterdump():
                        backup_file.write(f"{line}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False
    
    async def _backup_config_files(self, config_backup_dir: Path):
        """بکاپ فایل‌های کانفیگ"""
        try:
            config_backup_dir.mkdir(exist_ok=True)
            
            # فایل‌های کانفیگ برای بکاپ
            config_files = [
                'config.py',
                'requirements.txt',
                '.env'  # اگر وجود داشته باشد
            ]
            
            for config_file in config_files:
                source_path = Path(config_file)
                if source_path.exists():
                    dest_path = config_backup_dir / config_file
                    shutil.copy2(source_path, dest_path)
                    logger.debug(f"Backed up config file: {config_file}")
            
        except Exception as e:
            logger.error(f"Error backing up config files: {e}")
    
    async def _backup_logs(self, logs_backup_dir: Path):
        """بکاپ فایل‌های لاگ"""
        try:
            logs_backup_dir.mkdir(exist_ok=True)
            
            logs_dir = Path(Config.LOGS_DIRECTORY)
            if logs_dir.exists():
                # بکاپ لاگ‌های اخیر (7 روز گذشته)
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for log_file in logs_dir.glob('*.log*'):
                    if log_file.stat().st_mtime > cutoff_date.timestamp():
                        dest_path = logs_backup_dir / log_file.name
                        shutil.copy2(log_file, dest_path)
                        logger.debug(f"Backed up log file: {log_file.name}")
            
        except Exception as e:
            logger.error(f"Error backing up logs: {e}")
    
    async def _backup_changes_since(self, backup_path: Path, since_date: datetime) -> bool:
        """بکاپ تغییرات از تاریخ مشخص"""
        try:
            # برای بکاپ افزایشی، فقط رکوردهای تغییر یافته را backup می‌کنیم
            # این یک پیاده‌سازی ساده است و در production باید دقیق‌تر باشد
            
            tables_with_timestamps = [
                ('users', 'registration_date'),
                ('payments', 'payment_date'),
                ('user_activity', 'activity_date'),
                ('signals', 'created_at'),
                ('referrals', 'signup_date')
            ]
            
            has_changes = False
            
            with gzip.open(backup_path, 'wt', encoding='utf-8') as backup_file:
                backup_file.write(f"-- MrTrader Incremental Backup\n")
                backup_file.write(f"-- Since: {since_date.isoformat()}\n")
                backup_file.write(f"-- Created: {datetime.now().isoformat()}\n\n")
                
                for table_name, timestamp_column in tables_with_timestamps:
                    try:
                        # دریافت رکوردهای جدید/تغییر یافته
                        records = self.db.fetch_all(f"""
                            SELECT * FROM {table_name} 
                            WHERE {timestamp_column} > ?
                        """, (since_date.isoformat(),))
                        
                        if records:
                            has_changes = True
                            backup_file.write(f"-- Changes in {table_name}\n")
                            
                            # اطلاعات ساختار جدول
                            table_info = self.db.fetch_all(f"PRAGMA table_info({table_name})")
                            columns = [col['name'] for col in table_info]
                            
                            for record in records:
                                values = [str(record[col]) if record[col] is not None else 'NULL' for col in columns]
                                values_str = ', '.join([f"'{v}'" if v != 'NULL' else 'NULL' for v in values])
                                backup_file.write(f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({values_str});\n")
                            
                            backup_file.write(f"\n")
                            
                    except Exception as table_error:
                        logger.warning(f"Error backing up table {table_name}: {table_error}")
                        continue
            
            return has_changes
            
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            return False
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """محاسبه checksum فایل"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    async def _save_backup_info(self, backup_info: BackupInfo):
        """ذخیره اطلاعات بکاپ در دیتابیس"""
        try:
            self.db.execute_query("""
                INSERT INTO backup_history 
                (filename, backup_type, size, checksum, created_at, description, is_compressed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                backup_info.filename,
                backup_info.backup_type,
                backup_info.size,
                backup_info.checksum,
                backup_info.created_at.isoformat(),
                backup_info.description,
                backup_info.is_compressed
            ))
            
        except Exception as e:
            logger.error(f"Error saving backup info: {e}")
    
    async def restore_backup(self, backup_filename: str, verify_checksum: bool = True) -> bool:
        """بازیابی از بکاپ"""
        try:
            # یافتن فایل بکاپ
            backup_path = self._find_backup_file(backup_filename)
            if not backup_path:
                logger.error(f"Backup file not found: {backup_filename}")
                return False
            
            # دریافت اطلاعات بکاپ از دیتابیس
            backup_info = self.db.fetch_one("""
                SELECT * FROM backup_history WHERE filename = ?
            """, (backup_filename,))
            
            if not backup_info:
                logger.error(f"Backup info not found in database: {backup_filename}")
                return False
            
            # تأیید checksum
            if verify_checksum:
                current_checksum = self._calculate_file_checksum(backup_path)
                if current_checksum != backup_info['checksum']:
                    logger.error(f"Checksum mismatch for {backup_filename}")
                    return False
            
            logger.info(f"Starting restoration from {backup_filename}")
            
            # بکاپ فعلی قبل از بازیابی
            await self.create_full_backup(f"Pre-restoration backup - {datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # بازیابی دیتابیس
            restoration_success = await self._restore_database(backup_path, backup_info['is_compressed'])
            
            if restoration_success:
                # بروزرسانی شمارش بازیابی
                self.db.execute_query("""
                    UPDATE backup_history 
                    SET restoration_count = restoration_count + 1
                    WHERE filename = ?
                """, (backup_filename,))
                
                logger.info(f"Successfully restored from {backup_filename}")
                return True
            else:
                logger.error(f"Failed to restore from {backup_filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup {backup_filename}: {e}")
            return False
    
    def _find_backup_file(self, filename: str) -> Optional[Path]:
        """یافتن فایل بکاپ"""
        try:
            # جستجو در تمام زیرپوشه‌ها
            for subdir in ['daily', 'weekly', 'monthly', 'manual']:
                backup_path = self.backup_dir / subdir / filename
                if backup_path.exists():
                    return backup_path
            
            # جستجو در پوشه اصلی
            backup_path = self.backup_dir / filename
            if backup_path.exists():
                return backup_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding backup file {filename}: {e}")
            return None
    
    async def _restore_database(self, backup_path: Path, is_compressed: bool) -> bool:
        """بازیابی دیتابیس از بکاپ"""
        try:
            db_path = Path(Config.DATABASE_FILE)
            
            # بستن اتصال فعلی دیتابیس
            self.db.close_connection()
            
            # بکاپ امنیتی فایل دیتابیس فعلی
            if db_path.exists():
                backup_current = db_path.with_suffix('.bak')
                shutil.copy2(db_path, backup_current)
            
            # بازیابی از فایل بکاپ
            if is_compressed:
                with gzip.open(backup_path, 'rt', encoding='utf-8') as backup_file:
                    sql_content = backup_file.read()
            else:
                with open(backup_path, 'r', encoding='utf-8') as backup_file:
                    sql_content = backup_file.read()
            
            # ایجاد دیتابیس جدید
            if db_path.exists():
                db_path.unlink()
            
            with sqlite3.connect(str(db_path)) as conn:
                conn.executescript(sql_content)
                conn.commit()
            
            # بازاتصال DatabaseManager
            self.db = DatabaseManager()
            
            logger.info("Database restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            # بازگردانی فایل قبلی در صورت خطا
            try:
                backup_current = db_path.with_suffix('.bak')
                if backup_current.exists():
                    shutil.copy2(backup_current, db_path)
                    self.db = DatabaseManager()
            except:
                pass
            return False
    
    def list_backups(self, backup_type: str = None) -> List[Dict[str, Any]]:
        """لیست بکاپ‌ها"""
        try:
            if backup_type:
                backups = self.db.fetch_all("""
                    SELECT * FROM backup_history 
                    WHERE backup_type = ?
                    ORDER BY created_at DESC
                """, (backup_type,))
            else:
                backups = self.db.fetch_all("""
                    SELECT * FROM backup_history 
                    ORDER BY created_at DESC
                """)
            
            return [dict(row) for row in backups] if backups else []
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    async def verify_backup_integrity(self, backup_filename: str) -> Dict[str, Any]:
        """بررسی یکپارچگی بکاپ"""
        try:
            backup_path = self._find_backup_file(backup_filename)
            if not backup_path:
                return {'valid': False, 'error': 'Backup file not found'}
            
            # دریافت اطلاعات از دیتابیس
            backup_info = self.db.fetch_one("""
                SELECT * FROM backup_history WHERE filename = ?
            """, (backup_filename,))
            
            if not backup_info:
                return {'valid': False, 'error': 'Backup info not found in database'}
            
            # بررسی اندازه فایل
            current_size = backup_path.stat().st_size
            if current_size != backup_info['size']:
                return {
                    'valid': False, 
                    'error': f"Size mismatch: expected {backup_info['size']}, got {current_size}"
                }
            
            # بررسی checksum
            current_checksum = self._calculate_file_checksum(backup_path)
            if current_checksum != backup_info['checksum']:
                return {
                    'valid': False,
                    'error': f"Checksum mismatch: expected {backup_info['checksum']}, got {current_checksum}"
                }
            
            # تست بازیابی (بدون اعمال تغییرات)
            restoration_test = await self._test_restoration(backup_path, backup_info['is_compressed'])
            
            # بروزرسانی تاریخ تأیید
            self.db.execute_query("""
                UPDATE backup_history 
                SET last_verified = ?
                WHERE filename = ?
            """, (datetime.now().isoformat(), backup_filename))
            
            return {
                'valid': True,
                'size_check': True,
                'checksum_check': True,
                'restoration_test': restoration_test,
                'verified_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def _test_restoration(self, backup_path: Path, is_compressed: bool) -> bool:
        """تست بازیابی بدون اعمال تغییرات"""
        try:
            # ایجاد دیتابیس موقت برای تست
            test_db_path = backup_path.parent / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            try:
                # بازیابی در دیتابیس موقت
                if is_compressed:
                    with gzip.open(backup_path, 'rt', encoding='utf-8') as backup_file:
                        sql_content = backup_file.read()
                else:
                    with open(backup_path, 'r', encoding='utf-8') as backup_file:
                        sql_content = backup_file.read()
                
                with sqlite3.connect(str(test_db_path)) as conn:
                    conn.executescript(sql_content)
                    # تست ساده - شمارش جداول
                    tables = conn.execute("""
                        SELECT name FROM sqlite_master WHERE type='table'
                    """).fetchall()
                    
                    if len(tables) == 0:
                        return False
                
                return True
                
            finally:
                # حذف فایل موقت
                if test_db_path.exists():
                    test_db_path.unlink()
            
        except Exception as e:
            logger.error(f"Error testing restoration: {e}")
            return False
    
    async def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """پاکسازی بکاپ‌های قدیمی"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # یافتن بکاپ‌های قدیمی
            old_backups = self.db.fetch_all("""
                SELECT filename FROM backup_history 
                WHERE created_at < ? AND backup_type != 'full'
                ORDER BY created_at ASC
            """, (cutoff_date.isoformat(),))
            
            cleaned_count = 0
            freed_space = 0
            
            for backup in old_backups:
                filename = backup['filename']
                backup_path = self._find_backup_file(filename)
                
                if backup_path and backup_path.exists():
                    file_size = backup_path.stat().st_size
                    backup_path.unlink()
                    freed_space += file_size
                    cleaned_count += 1
                    
                    # حذف از دیتابیس
                    self.db.execute_query("""
                        DELETE FROM backup_history WHERE filename = ?
                    """, (filename,))
                    
                    logger.info(f"Cleaned up old backup: {filename}")
            
            result = {
                'cleaned_count': cleaned_count,
                'freed_space_mb': round(freed_space / 1024 / 1024, 2),
                'retention_days': retention_days
            }
            
            logger.info(f"Cleanup completed: {cleaned_count} backups removed, {result['freed_space_mb']} MB freed")
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return {'cleaned_count': 0, 'freed_space_mb': 0, 'error': str(e)}
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """آمار بکاپ‌ها"""
        try:
            # آمار کلی
            stats = self.db.fetch_one("""
                SELECT 
                    COUNT(*) as total_backups,
                    SUM(size) as total_size,
                    AVG(size) as avg_size,
                    MIN(created_at) as first_backup,
                    MAX(created_at) as latest_backup
                FROM backup_history
            """)
            
            # آمار بر اساس نوع
            type_stats = self.db.fetch_all("""
                SELECT 
                    backup_type,
                    COUNT(*) as count,
                    SUM(size) as total_size
                FROM backup_history
                GROUP BY backup_type
            """)
            
            # فضای دیسک
            disk_usage = self._get_disk_usage()
            
            return {
                'total_backups': stats['total_backups'] if stats else 0,
                'total_size_mb': round((stats['total_size'] or 0) / 1024 / 1024, 2),
                'average_size_mb': round((stats['avg_size'] or 0) / 1024 / 1024, 2),
                'first_backup': stats['first_backup'] if stats else None,
                'latest_backup': stats['latest_backup'] if stats else None,
                'type_breakdown': [dict(row) for row in type_stats] if type_stats else [],
                'disk_usage': disk_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting backup statistics: {e}")
            return {}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """محاسبه استفاده از فضای دیسک"""
        try:
            backup_size = sum(
                f.stat().st_size 
                for f in self.backup_dir.rglob('*') 
                if f.is_file()
            )
            
            # فضای کل دیسک
            disk_usage = shutil.disk_usage(self.backup_dir)
            
            return {
                'backup_directory_size_mb': round(backup_size / 1024 / 1024, 2),
                'total_disk_space_gb': round(disk_usage.total / 1024 / 1024 / 1024, 2),
                'free_disk_space_gb': round(disk_usage.free / 1024 / 1024 / 1024, 2),
                'used_disk_space_gb': round((disk_usage.total - disk_usage.free) / 1024 / 1024 / 1024, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating disk usage: {e}")
            return {}
    
    async def schedule_automatic_backups(self):
        """برنامه‌ریزی بکاپ‌های خودکار"""
        try:
            now = datetime.now()
            
            # بررسی نیاز به بکاپ روزانه
            last_daily = self.db.fetch_one("""
                SELECT MAX(created_at) as last_backup FROM backup_history 
                WHERE backup_type = 'incremental'
            """)
            
            if not last_daily or datetime.fromisoformat(last_daily['last_backup']) < now - timedelta(days=1):
                await self.create_incremental_backup()
                logger.info("Scheduled daily incremental backup completed")
            
            # بررسی نیاز به بکاپ هفتگی
            last_weekly = self.db.fetch_one("""
                SELECT MAX(created_at) as last_backup FROM backup_history 
                WHERE backup_type = 'full' AND description LIKE '%weekly%'
            """)
            
            if not last_weekly or datetime.fromisoformat(last_weekly['last_backup']) < now - timedelta(days=7):
                await self.create_full_backup("Weekly scheduled backup")
                logger.info("Scheduled weekly full backup completed")
            
            # پاکسازی بکاپ‌های قدیمی
            await self.cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Error in scheduled backup process: {e}")


# Export
__all__ = ['BackupManager', 'BackupInfo']