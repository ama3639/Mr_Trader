#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی محیط MrTrader Bot
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
import json

# اضافه کردن پوشه پروژه به path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class EnvironmentSetup:
    """کلاس راه‌اندازی محیط"""
    
    def __init__(self):
        self.project_root = project_root
        self.required_dirs = [
            "data",
            "logs", 
            "backups",
            "backups/daily",
            "backups/weekly", 
            "backups/monthly",
            "reports",
            "reports/analysis",
            "reports/user_reports",
            "reports/admin_reports"
        ]
        
        self.required_files = {
            ".env": ".env.example",
            "data/.gitkeep": None,
            "logs/.gitkeep": None,
            "backups/.gitkeep": None,
            "reports/.gitkeep": None
        }
    
    def setup_full_environment(self):
        """راه‌اندازی کامل محیط"""
        print("🚀 شروع راه‌اندازی محیط MrTrader Bot")
        print("="*50)
        
        steps = [
            ("بررسی Python", self.check_python_version),
            ("ایجاد پوشه‌ها", self.create_directories),
            ("ایجاد فایل‌ها", self.create_files),
            ("نصب وابستگی‌ها", self.install_dependencies),
            ("تنظیم پایگاه داده", self.setup_database),
            ("بررسی تنظیمات", self.verify_configuration),
            ("تست اتصالات", self.test_connections)
        ]
        
        for step_name, step_function in steps:
            print(f"\n📋 {step_name}...")
            try:
                result = step_function()
                if result:
                    print(f"✅ {step_name}: موفق")
                else:
                    print(f"⚠️ {step_name}: با هشدار")
            except Exception as e:
                print(f"❌ {step_name}: خطا - {e}")
                return False
        
        print("\n" + "="*50)
        print("🎉 راه‌اندازی محیط با موفقیت تکمیل شد!")
        self._print_next_steps()
        
        return True
    
    def check_python_version(self):
        """بررسی نسخه Python"""
        try:
            version = sys.version_info
            
            if version < (3, 8):
                raise Exception(f"Python 3.8+ مورد نیاز است. نسخه فعلی: {version.major}.{version.minor}")
            
            print(f"  Python نسخه {version.major}.{version.minor}.{version.micro}")
            
            # بررسی pip
            try:
                import pip
                print(f"  pip موجود است")
            except ImportError:
                raise Exception("pip نصب نیست")
            
            return True
            
        except Exception as e:
            print(f"  ❌ {e}")
            return False
    
    def create_directories(self):
        """ایجاد پوشه‌های مورد نیاز"""
        try:
            created_count = 0
            
            for dir_path in self.required_dirs:
                full_path = self.project_root / dir_path
                
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"  📁 ایجاد شد: {dir_path}")
                    created_count += 1
                else:
                    print(f"  📁 موجود: {dir_path}")
            
            if created_count > 0:
                print(f"  ✅ {created_count} پوشه جدید ایجاد شد")
            else:
                print(f"  ✅ تمام پوشه‌ها موجود بودند")
            
            return True
            
        except Exception as e:
            print(f"  ❌ خطا در ایجاد پوشه‌ها: {e}")
            return False
    
    def create_files(self):
        """ایجاد فایل‌های مورد نیاز"""
        try:
            created_count = 0
            
            for target_file, source_file in self.required_files.items():
                target_path = self.project_root / target_file
                
                if not target_path.exists():
                    if source_file:
                        # کپی از فایل نمونه
                        source_path = self.project_root / source_file
                        if source_path.exists():
                            shutil.copy2(source_path, target_path)
                            print(f"  📄 کپی شد: {source_file} → {target_file}")
                        else:
                            print(f"  ⚠️ فایل نمونه یافت نشد: {source_file}")
                    else:
                        # ایجاد فایل خالی
                        target_path.touch()
                        print(f"  📄 ایجاد شد: {target_file}")
                    
                    created_count += 1
                else:
                    print(f"  📄 موجود: {target_file}")
            
            # ایجاد .gitkeep برای پوشه‌های خالی
            gitkeep_dirs = ["logs", "backups", "reports"]
            for dir_name in gitkeep_dirs:
                gitkeep_file = self.project_root / dir_name / ".gitkeep"
                if not gitkeep_file.exists():
                    gitkeep_file.write_text("# Keep this directory in git\n")
                    print(f"  📄 ایجاد شد: {dir_name}/.gitkeep")
            
            if created_count > 0:
                print(f"  ✅ {created_count} فایل جدید ایجاد شد")
            
            return True
            
        except Exception as e:
            print(f"  ❌ خطا در ایجاد فایل‌ها: {e}")
            return False
    
    def install_dependencies(self):
        """نصب وابستگی‌ها"""
        try:
            requirements_file = self.project_root / "requirements.txt"
            
            if not requirements_file.exists():
                print("  ⚠️ فایل requirements.txt یافت نشد")
                return False
            
            print("  📦 نصب وابستگی‌ها...")
            
            # اجرای pip install
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✅ وابستگی‌ها با موفقیت نصب شدند")
                return True
            else:
                print(f"  ❌ خطا در نصب وابستگی‌ها:")
                print(f"  {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ خطا در نصب وابستگی‌ها: {e}")
            return False
    
    def setup_database(self):
        """تنظیم پایگاه داده"""
        try:
            # اجرای migration script
            migration_script = self.project_root / "scripts" / "migrate_database.py"
            
            if migration_script.exists():
                print("  🗄️ راه‌اندازی پایگاه داده...")
                
                result = subprocess.run([
                    sys.executable, str(migration_script)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("  ✅ پایگاه داده راه‌اندازی شد")
                    return True
                else:
                    print(f"  ❌ خطا در راه‌اندازی پایگاه داده:")
                    print(f"  {result.stderr}")
                    return False
            else:
                print("  ⚠️ اسکریپت migration یافت نشد")
                
                # ایجاد پایگاه داده خالی
                db_path = self.project_root / "data" / "mrtrader.db"
                if not db_path.exists():
                    db_path.touch()
                    print("  📄 فایل پایگاه داده خالی ایجاد شد")
                
                return True
                
        except Exception as e:
            print(f"  ❌ خطا در تنظیم پایگاه داده: {e}")
            return False
    
    def verify_configuration(self):
        """بررسی تنظیمات"""
        try:
            config_issues = []
            
            # بررسی فایل .env
            env_file = self.project_root / ".env"
            if env_file.exists():
                env_content = env_file.read_text()
                
                required_vars = [
                    "BOT_TOKEN",
                    "ADMIN_USER_ID",
                    "DATABASE_PATH"
                ]
                
                for var in required_vars:
                    if f"{var}=your_" in env_content or f"{var}=" not in env_content:
                        config_issues.append(f"متغیر {var} تنظیم نشده")
            else:
                config_issues.append("فایل .env وجود ندارد")
            
            # بررسی فایل‌های config
            config_dir = self.project_root / "config"
            if config_dir.exists():
                required_configs = ["api_servers_config.json"]
                for config_file in required_configs:
                    if not (config_dir / config_file).exists():
                        config_issues.append(f"فایل {config_file} موجود نیست")
            
            if config_issues:
                print("  ⚠️ مسائل تنظیمات:")
                for issue in config_issues:
                    print(f"    • {issue}")
                return False
            else:
                print("  ✅ تنظیمات صحیح هستند")
                return True
                
        except Exception as e:
            print(f"  ❌ خطا در بررسی تنظیمات: {e}")
            return False
    
    def test_connections(self):
        """تست اتصالات"""
        try:
            print("  🔗 تست اتصالات...")
            
            # تست پایگاه داده
            try:
                import sqlite3
                db_path = self.project_root / "data" / "mrtrader.db"
                
                if db_path.exists():
                    conn = sqlite3.connect(db_path)
                    conn.execute("SELECT 1")
                    conn.close()
                    print("    ✅ اتصال پایگاه داده")
                else:
                    print("    ⚠️ فایل پایگاه داده وجود ندارد")
            except Exception as e:
                print(f"    ❌ خطا در اتصال پایگاه داده: {e}")
            
            # تست import های اصلی
            try:
                import telegram
                print("    ✅ telegram library")
            except ImportError:
                print("    ❌ telegram library نصب نیست")
            
            try:
                import requests
                print("    ✅ requests library")
            except ImportError:
                print("    ❌ requests library نصب نیست")
            
            return True
            
        except Exception as e:
            print(f"  ❌ خطا در تست اتصالات: {e}")
            return False
    
    def _print_next_steps(self):
        """چاپ مراحل بعدی"""
        print("\n📋 مراحل بعدی:")
        print("1. فایل .env را ویرایش کنید و اطلاعات صحیح را وارد کنید")
        print("2. BOT_TOKEN را از @BotFather دریافت کنید")
        print("3. ADMIN_USER_ID را تنظیم کنید")
        print("4. API کلیدها را در .env اضافه کنید")
        print("5. ربات را با python main.py اجرا کنید")
        print("\n🔧 دستورات مفید:")
        print("  • تست سلامت: python scripts/health_check.py")
        print("  • بکاپ: python scripts/backup_data.py create")
        print("  • پاک‌سازی: python scripts/cleanup_logs.py --analyze")
    
    def create_sample_config(self):
        """ایجاد تنظیمات نمونه"""
        try:
            config_dir = self.project_root / "config"
            
            # ایجاد api_servers_config.json نمونه
            api_config = {
                "binance": {
                    "base_url": "https://api.binance.com",
                    "endpoints": {
                        "ticker": "/api/v3/ticker/24hr",
                        "klines": "/api/v3/klines",
                        "ping": "/api/v3/ping"
                    },
                    "rate_limit": 1200,
                    "timeout": 10
                },
                "coingecko": {
                    "base_url": "https://api.coingecko.com/api/v3",
                    "endpoints": {
                        "ping": "/ping",
                        "coins_list": "/coins/list",
                        "simple_price": "/simple/price"
                    },
                    "rate_limit": 100,
                    "timeout": 10
                }
            }
            
            api_config_file = config_dir / "api_servers_config.json"
            if not api_config_file.exists():
                with open(api_config_file, 'w', encoding='utf-8') as f:
                    json.dump(api_config, f, indent=2, ensure_ascii=False)
                print(f"  📄 ایجاد شد: config/api_servers_config.json")
            
            return True
            
        except Exception as e:
            print(f"  ❌ خطا در ایجاد تنظیمات نمونه: {e}")
            return False


def main():
    """تابع اصلی"""
    parser = argparse.ArgumentParser(description="راه‌اندازی محیط MrTrader Bot")
    parser.add_argument("--quick", action="store_true",
                       help="راه‌اندازی سریع (بدون نصب وابستگی‌ها)")
    parser.add_argument("--config-only", action="store_true",
                       help="فقط ایجاد تنظیمات")
    
    args = parser.parse_args()
    
    try:
        setup = EnvironmentSetup()
        
        if args.config_only:
            print("🔧 ایجاد تنظیمات نمونه...")
            return setup.create_sample_config()
        elif args.quick:
            print("⚡ راه‌اندازی سریع...")
            success = True
            success &= setup.create_directories()
            success &= setup.create_files()
            success &= setup.create_sample_config()
            return success
        else:
            return setup.setup_full_environment()
        
    except KeyboardInterrupt:
        print("\n⏹️ راه‌اندازی متوقف شد")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)