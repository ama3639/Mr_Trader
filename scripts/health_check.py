#!/usr/bin/env python3
"""
اسکریپت بررسی سلامت سیستم MrTrader Bot
"""
import os
import sys
import sqlite3
import requests
import psutil
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# اضافه کردن پوشه پروژه به path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from utils.logger import logger


class HealthChecker:
    """کلاس بررسی سلامت سیستم"""
    
    def __init__(self):
        self.results = {}
        self.warnings = []
        self.errors = []
        
    def run_all_checks(self):
        """اجرای تمام بررسی‌ها"""
        print("🔍 شروع بررسی سلامت سیستم...")
        
        checks = [
            ("سیستم عامل", self.check_system_resources),
            ("پایگاه داده", self.check_database),
            ("فایل‌های پروژه", self.check_project_files),
            ("اتصال اینترنت", self.check_internet_connection),
            ("API های خارجی", self.check_external_apis),
            ("پوشه‌ها و مجوزها", self.check_directories),
            ("لاگ‌ها", self.check_logs),
            ("بکاپ‌ها", self.check_backups),
            ("کیفیت کد", self.check_code_quality)
        ]
        
        for check_name, check_function in checks:
            print(f"\n📋 بررسی {check_name}...")
            try:
                result = check_function()
                self.results[check_name] = result
                
                if result['status'] == 'OK':
                    print(f"✅ {check_name}: سالم")
                elif result['status'] == 'WARNING':
                    print(f"⚠️ {check_name}: هشدار - {result['message']}")
                    self.warnings.append(f"{check_name}: {result['message']}")
                else:
                    print(f"❌ {check_name}: خطا - {result['message']}")
                    self.errors.append(f"{check_name}: {result['message']}")
                    
            except Exception as e:
                error_msg = f"خطا در بررسی {check_name}: {e}"
                print(f"❌ {error_msg}")
                self.errors.append(error_msg)
                self.results[check_name] = {'status': 'ERROR', 'message': str(e)}
        
        # خلاصه نتایج
        self._print_summary()
        
        return len(self.errors) == 0
    
    def check_system_resources(self):
        """بررسی منابع سیستم"""
        try:
            # استفاده از CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # استفاده از RAM
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # استفاده از دیسک
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # بررسی آستانه‌ها
            if cpu_percent > 90:
                return {'status': 'ERROR', 'message': f'CPU usage خیلی بالا: {cpu_percent}%'}
            elif cpu_percent > 70:
                return {'status': 'WARNING', 'message': f'CPU usage بالا: {cpu_percent}%'}
            
            if memory_percent > 90:
                return {'status': 'ERROR', 'message': f'Memory usage خیلی بالا: {memory_percent}%'}
            elif memory_percent > 80:
                return {'status': 'WARNING', 'message': f'Memory usage بالا: {memory_percent}%'}
            
            if disk_percent > 95:
                return {'status': 'ERROR', 'message': f'Disk usage خیلی بالا: {disk_percent}%'}
            elif disk_percent > 85:
                return {'status': 'WARNING', 'message': f'Disk usage بالا: {disk_percent}%'}
            
            return {
                'status': 'OK',
                'details': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent
                }
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی منابع سیستم: {e}'}
    
    def check_database(self):
        """بررسی پایگاه داده"""
        try:
            db_path = Config.DATABASE_PATH
            
            # بررسی وجود فایل
            if not db_path.exists():
                return {'status': 'ERROR', 'message': 'فایل پایگاه داده وجود ندارد'}
            
            # بررسی اندازه فایل
            db_size = db_path.stat().st_size
            if db_size == 0:
                return {'status': 'ERROR', 'message': 'فایل پایگاه داده خالی است'}
            
            # بررسی اتصال
            with sqlite3.connect(db_path) as conn:
                # تست کوئری ساده
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()
                
                # بررسی یکپارچگی
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result != "ok":
                    return {'status': 'ERROR', 'message': f'مشکل یکپارچگی: {integrity_result}'}
                
                # بررسی جداول اصلی
                required_tables = ['users', 'admins', 'transactions', 'settings']
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                if missing_tables:
                    return {'status': 'WARNING', 'message': f'جداول ناقص: {missing_tables}'}
                
                # آمار پایگاه داده
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                users_count = cursor.fetchone()[0]
                
                return {
                    'status': 'OK',
                    'details': {
                        'db_size_mb': db_size / (1024 * 1024),
                        'users_count': users_count,
                        'tables_count': len(existing_tables)
                    }
                }
                
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی پایگاه داده: {e}'}
    
    def check_project_files(self):
        """بررسی فایل‌های پروژه"""
        try:
            required_files = [
                'main.py',
                'requirements.txt',
                'core/config.py',
                'managers/user_manager.py',
                'handlers/start_handler.py'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not (project_root / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                return {'status': 'ERROR', 'message': f'فایل‌های ناقص: {missing_files}'}
            
            # بررسی فایل .env (اگر نیاز باشد)
            env_file = project_root / '.env'
            if not env_file.exists():
                return {'status': 'WARNING', 'message': 'فایل .env وجود ندارد'}
            
            return {'status': 'OK', 'message': 'تمام فایل‌های ضروری موجودند'}
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی فایل‌ها: {e}'}
    
    def check_internet_connection(self):
        """بررسی اتصال اینترنت"""
        try:
            # تست اتصال به چند سرویس
            test_urls = [
                'https://www.google.com',
                'https://api.telegram.org',
                'https://httpbin.org/get'
            ]
            
            successful_connections = 0
            response_times = []
            
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        successful_connections += 1
                        response_times.append(response_time)
                        
                except requests.RequestException:
                    continue
            
            if successful_connections == 0:
                return {'status': 'ERROR', 'message': 'هیچ اتصال اینترنتی برقرار نیست'}
            elif successful_connections < len(test_urls):
                return {'status': 'WARNING', 'message': f'فقط {successful_connections}/{len(test_urls)} اتصال موفق'}
            
            avg_response_time = sum(response_times) / len(response_times)
            
            if avg_response_time > 5:
                return {'status': 'WARNING', 'message': f'اتصال کند: {avg_response_time:.2f}s'}
            
            return {
                'status': 'OK',
                'details': {
                    'successful_connections': successful_connections,
                    'avg_response_time': avg_response_time
                }
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی اتصال: {e}'}
    
    def check_external_apis(self):
        """بررسی API های خارجی"""
        try:
            apis_to_check = [
                {
                    'name': 'Binance API',
                    'url': 'https://api.binance.com/api/v3/ping',
                    'expected_key': None  # فقط status code 200
                },
                {
                    'name': 'CoinGecko API',
                    'url': 'https://api.coingecko.com/api/v3/ping',
                    'expected_key': 'gecko_says'
                }
            ]
            
            api_results = {}
            failed_apis = []
            
            for api in apis_to_check:
                try:
                    response = requests.get(api['url'], timeout=10)
                    
                    if response.status_code == 200:
                        if api['expected_key']:
                            data = response.json()
                            if api['expected_key'] in data:
                                api_results[api['name']] = 'OK'
                            else:
                                api_results[api['name']] = 'WARNING'
                        else:
                            api_results[api['name']] = 'OK'
                    else:
                        api_results[api['name']] = 'ERROR'
                        failed_apis.append(api['name'])
                        
                except Exception:
                    api_results[api['name']] = 'ERROR'
                    failed_apis.append(api['name'])
            
            if failed_apis:
                return {'status': 'WARNING', 'message': f'API های ناموفق: {failed_apis}'}
            
            return {'status': 'OK', 'details': api_results}
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی API ها: {e}'}
    
    def check_directories(self):
        """بررسی پوشه‌ها و مجوزها"""
        try:
            required_dirs = [
                'logs',
                'data', 
                'backups',
                'reports'
            ]
            
            issues = []
            
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                
                # بررسی وجود
                if not dir_path.exists():
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        print(f"📁 ایجاد شد: {dir_name}")
                    except Exception as e:
                        issues.append(f"نمی‌توان {dir_name} را ایجاد کرد: {e}")
                        continue
                
                # بررسی مجوز نوشتن
                if not os.access(dir_path, os.W_OK):
                    issues.append(f"مجوز نوشتن در {dir_name} وجود ندارد")
            
            if issues:
                return {'status': 'ERROR', 'message': '; '.join(issues)}
            
            return {'status': 'OK', 'message': 'تمام پوشه‌ها و مجوزها سالم'}
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی پوشه‌ها: {e}'}
    
    def check_logs(self):
        """بررسی لاگ‌ها"""
        try:
            logs_dir = project_root / 'logs'
            
            if not logs_dir.exists():
                return {'status': 'WARNING', 'message': 'پوشه logs وجود ندارد'}
            
            log_files = list(logs_dir.glob('*.log'))
            
            if not log_files:
                return {'status': 'WARNING', 'message': 'فایل لاگی وجود ندارد'}
            
            # بررسی آخرین لاگ
            newest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            log_age = datetime.now() - datetime.fromtimestamp(newest_log.stat().st_mtime)
            
            if log_age > timedelta(hours=24):
                return {'status': 'WARNING', 'message': f'آخرین لاگ {log_age.days} روز قدیمی است'}
            
            # بررسی اندازه لاگ‌ها
            total_log_size = sum(f.stat().st_size for f in log_files)
            total_log_size_mb = total_log_size / (1024 * 1024)
            
            if total_log_size_mb > 500:  # بیش از 500 مگابایت
                return {'status': 'WARNING', 'message': f'حجم لاگ‌ها زیاد: {total_log_size_mb:.1f}MB'}
            
            return {
                'status': 'OK',
                'details': {
                    'log_files_count': len(log_files),
                    'total_size_mb': total_log_size_mb,
                    'newest_log_age_hours': log_age.total_seconds() / 3600
                }
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی لاگ‌ها: {e}'}
    
    def check_backups(self):
        """بررسی بکاپ‌ها"""
        try:
            backups_dir = project_root / 'backups'
            
            if not backups_dir.exists():
                return {'status': 'WARNING', 'message': 'پوشه backups وجود ندارد'}
            
            backup_files = list(backups_dir.rglob('*.zip'))
            
            if not backup_files:
                return {'status': 'WARNING', 'message': 'هیچ بکاپی وجود ندارد'}
            
            # آخرین بکاپ
            newest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            backup_age = datetime.now() - datetime.fromtimestamp(newest_backup.stat().st_mtime)
            
            if backup_age > timedelta(days=7):
                return {'status': 'WARNING', 'message': f'آخرین بکاپ {backup_age.days} روز قدیمی است'}
            
            return {
                'status': 'OK',
                'details': {
                    'backup_files_count': len(backup_files),
                    'newest_backup_age_days': backup_age.days
                }
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی بکاپ‌ها: {e}'}
    
    def check_code_quality(self):
        """بررسی کیفیت کد"""
        try:
            issues = []
            
            # بررسی فایل requirements.txt
            requirements_file = project_root / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    requirements = f.read()
                    if 'python-telegram-bot' not in requirements:
                        issues.append('python-telegram-bot در requirements یافت نشد')
            else:
                issues.append('فایل requirements.txt وجود ندارد')
            
            # بررسی import های اصلی
            main_file = project_root / 'main.py'
            if main_file.exists():
                with open(main_file, 'r', encoding='utf-8') as f:
                    main_content = f.read()
                    if 'telegram' not in main_content:
                        issues.append('import telegram در main.py یافت نشد')
            
            # بررسی ساختار پوشه‌ها
            expected_dirs = ['core', 'managers', 'handlers', 'utils']
            for dir_name in expected_dirs:
                if not (project_root / dir_name).is_dir():
                    issues.append(f'پوشه {dir_name} وجود ندارد')
            
            if issues:
                return {'status': 'WARNING', 'message': '; '.join(issues)}
            
            return {'status': 'OK', 'message': 'ساختار پروژه مناسب است'}
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'خطا در بررسی کیفیت کد: {e}'}
    
    def _print_summary(self):
        """چاپ خلاصه نتایج"""
        print("\n" + "="*50)
        print("📊 خلاصه نتایج بررسی سلامت")
        print("="*50)
        
        # شمارش وضعیت‌ها
        status_counts = {'OK': 0, 'WARNING': 0, 'ERROR': 0}
        for result in self.results.values():
            status_counts[result['status']] += 1
        
        print(f"✅ سالم: {status_counts['OK']}")
        print(f"⚠️ هشدار: {status_counts['WARNING']}")
        print(f"❌ خطا: {status_counts['ERROR']}")
        
        # نمایش هشدارها
        if self.warnings:
            print(f"\n⚠️ هشدارها ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # نمایش خطاها
        if self.errors:
            print(f"\n❌ خطاها ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        # وضعیت کلی
        if self.errors:
            print(f"\n🔴 وضعیت کلی: نیاز به رفع خطاها")
        elif self.warnings:
            print(f"\n🟡 وضعیت کلی: قابل قبول با هشدارها")
        else:
            print(f"\n🟢 وضعیت کلی: عالی")
        
        print("="*50)
    
    def save_report(self, output_file=None):
        """ذخیره گزارش"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = project_root / f"health_report_{timestamp}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_checks': len(self.results),
                    'errors_count': len(self.errors),
                    'warnings_count': len(self.warnings)
                },
                'results': self.results,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📄 گزارش ذخیره شد: {output_file}")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره گزارش: {e}")


def main():
    """تابع اصلی"""
    parser = argparse.ArgumentParser(description="بررسی سلامت سیستم MrTrader Bot")
    parser.add_argument("--output", help="فایل خروجی گزارش")
    parser.add_argument("--quiet", action="store_true", help="خروجی ساده")
    
    args = parser.parse_args()
    
    try:
        checker = HealthChecker()
        
        if not args.quiet:
            print("🏥 ابزار بررسی سلامت MrTrader Bot")
            print("="*50)
        
        success = checker.run_all_checks()
        
        if args.output:
            checker.save_report(args.output)
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ بررسی متوقف شد")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)