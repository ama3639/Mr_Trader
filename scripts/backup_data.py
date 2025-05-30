#!/usr/bin/env python3
"""
اسکریپت پشتیبان‌گیری از داده‌های MrTrader Bot
"""
import os
import sys
import shutil
import sqlite3
import zipfile
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import logging

# اضافه کردن پوشه پروژه به path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from utils.logger import logger


class BackupManager:
    """کلاس مدیریت بکاپ"""
    
    def __init__(self):
        self.project_root = project_root
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # تنظیم پوشه‌های بکاپ
        self.daily_dir = self.backup_dir / "daily"
        self.weekly_dir = self.backup_dir / "weekly"
        self.monthly_dir = self.backup_dir / "monthly"
        
        for dir_path in [self.daily_dir, self.weekly_dir, self.monthly_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def create_backup(self, backup_type="manual", include_logs=False):
        """ایجاد بکاپ کامل"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # تعیین پوشه بکاپ بر اساس نوع
            if backup_type == "daily":
                backup_folder = self.daily_dir
            elif backup_type == "weekly":
                backup_folder = self.weekly_dir
            elif backup_type == "monthly":
                backup_folder = self.monthly_dir
            else:
                backup_folder = self.backup_dir
            
            backup_name = f"mrtrader_backup_{backup_type}_{timestamp}"
            backup_path = backup_folder / f"{backup_name}.zip"
            
            print(f"🔄 شروع بکاپ {backup_type}...")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # بکاپ پایگاه داده
                self._backup_database(zipf)
                
                # بکاپ فایل‌های CSV
                self._backup_csv_files(zipf)
                
                # بکاپ فایل‌های تنظیمات
                self._backup_config_files(zipf)
                
                # بکاپ لاگ‌ها (در صورت درخواست)
                if include_logs:
                    self._backup_logs(zipf)
                
                # بکاپ فایل‌های مهم پروژه
                self._backup_project_files(zipf)
                
                # ایجاد manifest
                self._create_manifest(zipf, backup_type, timestamp)
            
            # ایجاد checksum
            checksum = self._calculate_checksum(backup_path)
            
            # ذخیره اطلاعات بکاپ
            backup_info = {
                'backup_name': backup_name,
                'backup_type': backup_type,
                'timestamp': timestamp,
                'file_path': str(backup_path),
                'file_size': backup_path.stat().st_size,
                'checksum': checksum,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_backup_info(backup_info)
            
            print(f"✅ بکاپ با موفقیت ایجاد شد: {backup_path}")
            print(f"📦 حجم فایل: {self._format_size(backup_path.stat().st_size)}")
            print(f"🔒 Checksum: {checksum}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            print(f"❌ خطا در ایجاد بکاپ: {e}")
            raise
    
    def _backup_database(self, zipf):
        """بکاپ پایگاه داده"""
        try:
            db_path = Config.DATABASE_PATH
            if db_path.exists():
                zipf.write(db_path, "database/mrtrader.db")
                print("✅ پایگاه داده بکاپ شد")
            
            # بکاپ WAL و SHM files اگر وجود دارند
            for ext in ['.wal', '.shm']:
                wal_file = Path(str(db_path) + ext)
                if wal_file.exists():
                    zipf.write(wal_file, f"database/{wal_file.name}")
                    
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            print(f"⚠️ خطا در بکاپ پایگاه داده: {e}")
    
    def _backup_csv_files(self, zipf):
        """بکاپ فایل‌های CSV"""
        try:
            data_dir = self.project_root / "data"
            if data_dir.exists():
                for csv_file in data_dir.glob("*.csv"):
                    zipf.write(csv_file, f"data/{csv_file.name}")
                print("✅ فایل‌های CSV بکاپ شدند")
        except Exception as e:
            logger.error(f"Error backing up CSV files: {e}")
            print(f"⚠️ خطا در بکاپ فایل‌های CSV: {e}")
    
    def _backup_config_files(self, zipf):
        """بکاپ فایل‌های تنظیمات"""
        try:
            config_dir = self.project_root / "config"
            if config_dir.exists():
                for config_file in config_dir.glob("*.json"):
                    zipf.write(config_file, f"config/{config_file.name}")
                print("✅ فایل‌های تنظیمات بکاپ شدند")
        except Exception as e:
            logger.error(f"Error backing up config files: {e}")
            print(f"⚠️ خطا در بکاپ فایل‌های تنظیمات: {e}")
    
    def _backup_logs(self, zipf):
        """بکاپ لاگ‌ها"""
        try:
            logs_dir = self.project_root / "logs"
            if logs_dir.exists():
                # فقط لاگ‌های 7 روز اخیر
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for log_file in logs_dir.glob("*.log"):
                    if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_date:
                        zipf.write(log_file, f"logs/{log_file.name}")
                print("✅ لاگ‌ها بکاپ شدند")
        except Exception as e:
            logger.error(f"Error backing up logs: {e}")
            print(f"⚠️ خطا در بکاپ لاگ‌ها: {e}")
    
    def _backup_project_files(self, zipf):
        """بکاپ فایل‌های مهم پروژه"""
        try:
            important_files = [
                "requirements.txt",
                "main.py",
                ".env.example"
            ]
            
            for file_name in important_files:
                file_path = self.project_root / file_name
                if file_path.exists():
                    zipf.write(file_path, f"project/{file_name}")
            
            print("✅ فایل‌های مهم پروژه بکاپ شدند")
        except Exception as e:
            logger.error(f"Error backing up project files: {e}")
            print(f"⚠️ خطا در بکاپ فایل‌های پروژه: {e}")
    
    def _create_manifest(self, zipf, backup_type, timestamp):
        """ایجاد manifest بکاپ"""
        try:
            manifest = {
                'backup_info': {
                    'type': backup_type,
                    'timestamp': timestamp,
                    'created_at': datetime.now().isoformat(),
                    'version': getattr(Config, 'BOT_VERSION', '1.0.0')
                },
                'contents': {
                    'database': 'database/mrtrader.db',
                    'csv_files': 'data/',
                    'config_files': 'config/',
                    'project_files': 'project/'
                },
                'restore_instructions': [
                    '1. استخراج فایل‌ها در پوشه مناسب',
                    '2. بازیابی پایگاه داده از database/mrtrader.db',
                    '3. کپی فایل‌های CSV به پوشه data/',
                    '4. بازگرداندن تنظیمات از config/',
                    '5. راه‌اندازی مجدد ربات'
                ]
            }
            
            manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
            zipf.writestr("MANIFEST.json", manifest_json)
            
        except Exception as e:
            logger.error(f"Error creating manifest: {e}")
    
    def _calculate_checksum(self, file_path):
        """محاسبه checksum فایل"""
        try:
            import hashlib
            
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return None
    
    def _save_backup_info(self, backup_info):
        """ذخیره اطلاعات بکاپ"""
        try:
            backup_log_file = self.backup_dir / "backup_log.json"
            
            # بارگذاری لاگ موجود
            if backup_log_file.exists():
                with open(backup_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # اضافه کردن بکاپ جدید
            logs.append(backup_info)
            
            # حفظ فقط 50 رکورد آخر
            logs = logs[-50:]
            
            # ذخیره
            with open(backup_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving backup info: {e}")
    
    def _format_size(self, size_bytes):
        """فرمت‌بندی اندازه فایل"""
        if size_bytes >= 1024**3:
            return f"{size_bytes / (1024**3):.2f} GB"
        elif size_bytes >= 1024**2:
            return f"{size_bytes / (1024**2):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} bytes"
    
    def cleanup_old_backups(self, keep_daily=7, keep_weekly=4, keep_monthly=12):
        """پاک‌سازی بکاپ‌های قدیمی"""
        try:
            print("🧹 پاک‌سازی بکاپ‌های قدیمی...")
            
            # تنظیمات پاک‌سازی
            cleanup_rules = [
                (self.daily_dir, keep_daily, "روزانه"),
                (self.weekly_dir, keep_weekly, "هفتگی"), 
                (self.monthly_dir, keep_monthly, "ماهانه")
            ]
            
            total_deleted = 0
            total_size_freed = 0
            
            for backup_dir, keep_count, backup_type in cleanup_rules:
                if not backup_dir.exists():
                    continue
                
                # لیست فایل‌های بکاپ بر اساس تاریخ
                backup_files = sorted(
                    [f for f in backup_dir.glob("*.zip")],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                # حذف فایل‌های اضافی
                files_to_delete = backup_files[keep_count:]
                
                for file_path in files_to_delete:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    total_deleted += 1
                    total_size_freed += file_size
                    print(f"🗑️ حذف شد: {file_path.name}")
            
            if total_deleted > 0:
                print(f"✅ {total_deleted} فایل حذف شد، {self._format_size(total_size_freed)} فضا آزاد شد")
            else:
                print("✅ نیازی به پاک‌سازی نیست")
                
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            print(f"❌ خطا در پاک‌سازی: {e}")
    
    def list_backups(self):
        """لیست بکاپ‌ها"""
        try:
            print("📋 لیست بکاپ‌ها:")
            
            backup_dirs = [
                (self.daily_dir, "روزانه"),
                (self.weekly_dir, "هفتگی"),
                (self.monthly_dir, "ماهانه"),
                (self.backup_dir, "دستی")
            ]
            
            total_size = 0
            total_count = 0
            
            for backup_dir, backup_type in backup_dirs:
                if not backup_dir.exists():
                    continue
                
                backup_files = list(backup_dir.glob("*.zip"))
                if not backup_files:
                    continue
                
                print(f"\n📁 {backup_type}:")
                
                for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                    size = backup_file.stat().st_size
                    mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    print(f"  • {backup_file.name}")
                    print(f"    📅 {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    📦 {self._format_size(size)}")
                    
                    total_size += size
                    total_count += 1
            
            print(f"\n📊 خلاصه: {total_count} بکاپ، {self._format_size(total_size)} حجم کل")
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            print(f"❌ خطا در لیست بکاپ‌ها: {e}")
    
    def restore_backup(self, backup_path):
        """بازیابی از بکاپ"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                print(f"❌ فایل بکاپ یافت نشد: {backup_path}")
                return False
            
            print(f"🔄 شروع بازیابی از: {backup_path.name}")
            
            # ایجاد بکاپ فعلی قبل از بازیابی
            print("📦 ایجاد بکاپ ایمنی...")
            safety_backup = self.create_backup("safety_restore", include_logs=False)
            
            # استخراج بکاپ
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # بررسی manifest
                try:
                    manifest_content = zipf.read("MANIFEST.json")
                    manifest = json.loads(manifest_content)
                    print(f"📋 بکاپ نوع {manifest['backup_info']['type']} از تاریخ {manifest['backup_info']['timestamp']}")
                except:
                    print("⚠️ Manifest یافت نشد، ادامه بازیابی...")
                
                # بازیابی پایگاه داده
                try:
                    db_data = zipf.read("database/mrtrader.db")
                    with open(Config.DATABASE_PATH, 'wb') as f:
                        f.write(db_data)
                    print("✅ پایگاه داده بازیابی شد")
                except Exception as e:
                    print(f"⚠️ خطا در بازیابی پایگاه داده: {e}")
                
                # بازیابی فایل‌های CSV
                data_dir = self.project_root / "data"
                data_dir.mkdir(exist_ok=True)
                
                for file_info in zipf.filelist:
                    if file_info.filename.startswith("data/") and file_info.filename.endswith(".csv"):
                        zipf.extract(file_info, self.project_root)
                        print(f"✅ بازیابی شد: {file_info.filename}")
            
            print("✅ بازیابی با موفقیت تکمیل شد")
            print(f"🛡️ بکاپ ایمنی: {safety_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            print(f"❌ خطا در بازیابی: {e}")
            return False


def main():
    """تابع اصلی"""
    parser = argparse.ArgumentParser(description="مدیریت بکاپ MrTrader Bot")
    parser.add_argument("action", choices=["create", "list", "cleanup", "restore"],
                       help="عمل مورد نظر")
    parser.add_argument("--type", default="manual", choices=["daily", "weekly", "monthly", "manual"],
                       help="نوع بکاپ")
    parser.add_argument("--include-logs", action="store_true",
                       help="شامل کردن لاگ‌ها در بکاپ")
    parser.add_argument("--backup-path", 
                       help="مسیر فایل بکاپ برای بازیابی")
    
    args = parser.parse_args()
    
    try:
        backup_manager = BackupManager()
        
        if args.action == "create":
            backup_manager.create_backup(args.type, args.include_logs)
        
        elif args.action == "list":
            backup_manager.list_backups()
        
        elif args.action == "cleanup":
            backup_manager.cleanup_old_backups()
        
        elif args.action == "restore":
            if not args.backup_path:
                print("❌ مسیر فایل بکاپ مشخص نشده (--backup-path)")
                return False
            
            backup_manager.restore_backup(args.backup_path)
        
        return True
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)