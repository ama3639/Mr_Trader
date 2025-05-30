#!/usr/bin/env python3
"""
اسکریپت پاک‌سازی لاگ‌های قدیمی MrTrader Bot
"""
import os
import sys
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# اضافه کردن پوشه پروژه به path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import logger


class LogCleaner:
    """کلاس پاک‌سازی لاگ‌ها"""
    
    def __init__(self):
        self.logs_dir = project_root / "logs"
        self.archive_dir = self.logs_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
    
    def cleanup_logs(self, days_to_keep=30, compress_old=True, delete_old=False):
        """پاک‌سازی لاگ‌های قدیمی"""
        try:
            if not self.logs_dir.exists():
                print("📁 پوشه logs وجود ندارد")
                return
            
            print(f"🧹 شروع پاک‌سازی لاگ‌ها (نگهداری {days_to_keep} روز)")
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # پیدا کردن فایل‌های لاگ
            log_files = list(self.logs_dir.glob("*.log*"))
            
            if not log_files:
                print("📄 فایل لاگی یافت نشد")
                return
            
            # آمار
            compressed_count = 0
            deleted_count = 0
            total_size_freed = 0
            
            for log_file in log_files:
                try:
                    # بررسی تاریخ فایل
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_date < cutoff_date:
                        file_size = log_file.stat().st_size
                        
                        if delete_old:
                            # حذف فایل قدیمی
                            log_file.unlink()
                            deleted_count += 1
                            total_size_freed += file_size
                            print(f"🗑️ حذف شد: {log_file.name}")
                            
                        elif compress_old and not log_file.name.endswith('.gz'):
                            # فشرده‌سازی فایل قدیمی
                            compressed_file = self.archive_dir / f"{log_file.name}.gz"
                            
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(compressed_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            
                            # حذف فایل اصلی
                            log_file.unlink()
                            
                            compressed_count += 1
                            compression_ratio = compressed_file.stat().st_size / file_size
                            print(f"📦 فشرده شد: {log_file.name} (نسبت: {compression_ratio:.2f})")
                    
                except Exception as e:
                    print(f"❌ خطا در پردازش {log_file.name}: {e}")
                    continue
            
            # خلاصه نتایج
            print(f"\n📊 خلاصه پاک‌سازی:")
            if compress_old:
                print(f"📦 فایل‌های فشرده شده: {compressed_count}")
            if delete_old:
                print(f"🗑️ فایل‌های حذف شده: {deleted_count}")
                print(f"💾 فضای آزاد شده: {self._format_size(total_size_freed)}")
            
            # پاک‌سازی آرشیو قدیمی
            self._cleanup_archive(days_to_keep * 2)  # آرشیو 2 برابر بیشتر نگه داشته شود
            
        except Exception as e:
            print(f"❌ خطا در پاک‌سازی لاگ‌ها: {e}")
            logger.error(f"Error cleaning logs: {e}")
    
    def _cleanup_archive(self, archive_days=60):
        """پاک‌سازی آرشیو قدیمی"""
        try:
            cutoff_date = datetime.now() - timedelta(days=archive_days)
            archive_files = list(self.archive_dir.glob("*.gz"))
            
            deleted_archive_count = 0
            
            for archive_file in archive_files:
                file_date = datetime.fromtimestamp(archive_file.stat().st_mtime)
                
                if file_date < cutoff_date:
                    archive_file.unlink()
                    deleted_archive_count += 1
                    print(f"🗑️ آرشیو حذف شد: {archive_file.name}")
            
            if deleted_archive_count > 0:
                print(f"📁 {deleted_archive_count} فایل آرشیو قدیمی حذف شد")
                
        except Exception as e:
            print(f"❌ خطا در پاک‌سازی آرشیو: {e}")
    
    def analyze_logs(self):
        """تحلیل لاگ‌ها"""
        try:
            if not self.logs_dir.exists():
                print("📁 پوشه logs وجود ندارد")
                return
            
            print("📊 تحلیل لاگ‌ها:")
            
            # آمار فایل‌های لاگ
            log_files = list(self.logs_dir.glob("*.log*"))
            archive_files = list(self.archive_dir.glob("*.gz")) if self.archive_dir.exists() else []
            
            total_size = sum(f.stat().st_size for f in log_files)
            archive_size = sum(f.stat().st_size for f in archive_files) if archive_files else 0
            
            print(f"📄 فایل‌های لاگ فعال: {len(log_files)}")
            print(f"📦 فایل‌های آرشیو: {len(archive_files)}")
            print(f"💾 حجم کل لاگ‌ها: {self._format_size(total_size)}")
            print(f"💾 حجم آرشیو: {self._format_size(archive_size)}")
            
            # تحلیل سن فایل‌ها
            if log_files:
                oldest_file = min(log_files, key=lambda f: f.stat().st_mtime)
                newest_file = max(log_files, key=lambda f: f.stat().st_mtime)
                
                oldest_date = datetime.fromtimestamp(oldest_file.stat().st_mtime)
                newest_date = datetime.fromtimestamp(newest_file.stat().st_mtime)
                
                print(f"📅 قدیمی‌ترین لاگ: {oldest_date.strftime('%Y-%m-%d %H:%M')} ({oldest_file.name})")
                print(f"📅 جدیدترین لاگ: {newest_date.strftime('%Y-%m-%d %H:%M')} ({newest_file.name})")
                
                age_days = (datetime.now() - oldest_date).days
                print(f"📊 دامنه سنی: {age_days} روز")
            
            # بررسی لاگ‌های بزرگ
            large_files = [f for f in log_files if f.stat().st_size > 10 * 1024 * 1024]  # بزرگتر از 10MB
            if large_files:
                print(f"\n📈 فایل‌های بزرگ (>10MB):")
                for file in large_files:
                    size = self._format_size(file.stat().st_size)
                    print(f"  • {file.name}: {size}")
            
            # پیشنهادات
            self._suggest_cleanup_strategy(log_files, total_size)
            
        except Exception as e:
            print(f"❌ خطا در تحلیل لاگ‌ها: {e}")
    
    def _suggest_cleanup_strategy(self, log_files, total_size):
        """پیشنهاد استراتژی پاک‌سازی"""
        print(f"\n💡 پیشنهادات:")
        
        if total_size > 100 * 1024 * 1024:  # بیش از 100MB
            print("  • حجم لاگ‌ها زیاد است، پاک‌سازی توصیه می‌شود")
        
        if len(log_files) > 50:
            print("  • تعداد فایل‌های لاگ زیاد است")
        
        # بررسی فایل‌های قدیمی
        old_files = []
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for file in log_files:
            file_date = datetime.fromtimestamp(file.stat().st_mtime)
            if file_date < cutoff_date:
                old_files.append(file)
        
        if old_files:
            old_size = sum(f.stat().st_size for f in old_files)
            print(f"  • {len(old_files)} فایل قدیمی‌تر از 30 روز ({self._format_size(old_size)})")
            print("  • دستور پیشنهادی: python scripts/cleanup_logs.py --days 30 --compress")
        else:
            print("  • لاگ‌ها در وضعیت خوبی هستند")
    
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
    
    def rotate_current_logs(self):
        """چرخش لاگ‌های فعلی"""
        try:
            current_logs = [
                "mrtrader.log",
                "errors.log",
                "api.log",
                "user_activity.log"
            ]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_count = 0
            
            for log_name in current_logs:
                log_file = self.logs_dir / log_name
                
                if log_file.exists() and log_file.stat().st_size > 0:
                    # تعیین نام فایل جدید
                    name_parts = log_name.split('.')
                    rotated_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                    rotated_file = self.logs_dir / rotated_name
                    
                    # جابجایی فایل
                    log_file.rename(rotated_file)
                    rotated_count += 1
                    
                    print(f"🔄 چرخش: {log_name} → {rotated_name}")
            
            print(f"✅ {rotated_count} فایل لاگ چرخش داده شد")
            
        except Exception as e:
            print(f"❌ خطا در چرخش لاگ‌ها: {e}")


def main():
    """تابع اصلی"""
    parser = argparse.ArgumentParser(description="پاک‌سازی لاگ‌های MrTrader Bot")
    parser.add_argument("--days", type=int, default=30,
                       help="تعداد روزهای نگهداری (پیش‌فرض: 30)")
    parser.add_argument("--compress", action="store_true",
                       help="فشرده‌سازی فایل‌های قدیمی")
    parser.add_argument("--delete", action="store_true",
                       help="حذف فایل‌های قدیمی (بجای فشرده‌سازی)")
    parser.add_argument("--analyze", action="store_true",
                       help="فقط تحلیل لاگ‌ها (بدون تغییر)")
    parser.add_argument("--rotate", action="store_true",
                       help="چرخش لاگ‌های فعلی")
    
    args = parser.parse_args()
    
    try:
        cleaner = LogCleaner()
        
        if args.analyze:
            cleaner.analyze_logs()
        elif args.rotate:
            cleaner.rotate_current_logs()
        else:
            cleaner.cleanup_logs(
                days_to_keep=args.days,
                compress_old=args.compress,
                delete_old=args.delete
            )
        
        return True
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)