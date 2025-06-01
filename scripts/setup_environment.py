"""
اسکریپت راه‌اندازی محیط - نصب و پیکربندی اولیه پروژه
"""

import os
import sys
import subprocess
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

class Colors:
    """رنگ‌های ترمینال"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class EnvironmentSetup:
    """کلاس راه‌اندازی محیط"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.required_python_version = (3, 8)
        self.required_dirs = [
            'data', 'logs', 'backups', 'reports', 'assets',
            'backups/daily', 'backups/weekly', 'backups/monthly',
            'reports/analysis', 'reports/user_reports', 'reports/admin_reports',
            'assets/images', 'assets/icons', 'assets/fonts'
        ]
        
    def print_colored(self, message: str, color: str = Colors.OKGREEN):
        """چاپ پیام رنگی"""
        print(f"{color}{message}{Colors.ENDC}")
    
    def print_step(self, step_number: int, description: str):
        """چاپ مرحله"""
        self.print_colored(f"\n{Colors.BOLD}📋 مرحله {step_number}: {description}{Colors.ENDC}")
    
    def check_python_version(self) -> bool:
        """بررسی نسخه Python"""
        current_version = sys.version_info[:2]
        if current_version >= self.required_python_version:
            self.print_colored(f"✅ Python {sys.version} - سازگار است")
            return True
        else:
            self.print_colored(
                f"❌ Python {current_version[0]}.{current_version[1]} نصب است. "
                f"حداقل Python {self.required_python_version[0]}.{self.required_python_version[1]} مورد نیاز است.",
                Colors.FAIL
            )
            return False
    
    def create_directories(self):
        """ایجاد پوشه‌های مورد نیاز"""
        self.print_step(1, "ایجاد ساختار پوشه‌ها")
        
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                
                # ایجاد فایل .gitkeep برای پوشه‌های خالی
                gitkeep_file = full_path / '.gitkeep'
                if not gitkeep_file.exists():
                    gitkeep_file.touch()
                
                self.print_colored(f"📁 {dir_path} ✅")
            except Exception as e:
                self.print_colored(f"❌ خطا در ایجاد {dir_path}: {e}", Colors.FAIL)
    
    def install_requirements(self):
        """نصب وابستگی‌ها"""
        self.print_step(2, "نصب وابستگی‌ها")
        
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            self.print_colored("❌ فایل requirements.txt یافت نشد!", Colors.FAIL)
            return False
        
        try:
            # به‌روزرسانی pip
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            self.print_colored("✅ pip به‌روزرسانی شد")
            
            # نصب وابستگی‌ها
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                         check=True, capture_output=True)
            self.print_colored("✅ تمام وابستگی‌ها نصب شدند")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_colored(f"❌ خطا در نصب وابستگی‌ها: {e}", Colors.FAIL)
            return False
    
    def setup_database(self):
        """راه‌اندازی پایگاه داده"""
        self.print_step(3, "راه‌اندازی پایگاه داده")
        
        db_path = self.project_root / 'data' / 'mrtrader.db'
        
        try:
            # ایجاد پایگاه داده
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # ایجاد جداول اصلی
            tables_sql = [
                # جدول کاربران
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    phone TEXT,
                    registration_date TEXT NOT NULL,
                    last_login TEXT,
                    status TEXT DEFAULT 'active',
                    is_admin BOOLEAN DEFAULT 0,
                    is_vip BOOLEAN DEFAULT 0,
                    referred_by INTEGER,
                    referral_code TEXT,
                    current_package TEXT,
                    stats TEXT,
                    settings TEXT,
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # جدول تراکنش‌ها
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    package_id TEXT,
                    package_name TEXT,
                    subscription_duration TEXT,
                    payment_details TEXT,
                    description TEXT,
                    notes TEXT DEFAULT '',
                    created_date TEXT NOT NULL,
                    updated_date TEXT NOT NULL,
                    completed_date TEXT,
                    refunded_date TEXT,
                    from_package_id TEXT,
                    to_package_id TEXT,
                    upgrade_days_remaining INTEGER,
                    referrer_user_id INTEGER,
                    referral_reward_amount REAL DEFAULT 0.0
                );
                """,
                
                # جدول لاگ‌ها
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    user_id INTEGER,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # جدول کش
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expiry_time TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # جدول تنظیمات
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
            
            for sql in tables_sql:
                cursor.execute(sql)
            
            # ایجاد ایندکس‌ها
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);",
                "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);",
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_cache_expiry ON cache(expiry_time);"
            ]
            
            for sql in indexes_sql:
                cursor.execute(sql)
            
            # درج تنظیمات پیش‌فرض
            default_settings = [
                ('bot_token', 'YOUR_BOT_TOKEN_HERE', 'telegram', 'توکن ربات تلگرام'),
                ('admin_chat_id', '0', 'telegram', 'شناسه چت ادمین'),
                ('api_base_url', 'https://api.mrtrader.bot', 'api', 'آدرس پایه API'),
                ('cache_ttl', '3600', 'performance', 'مدت زمان نگهداری کش (ثانیه)'),
                ('max_daily_requests_free', '5', 'limits', 'حداکثر درخواست روزانه برای کاربران رایگان'),
                ('maintenance_mode', 'false', 'system', 'حالت تعمیرات'),
                ('version', '1.0.0', 'system', 'نسخه سیستم')
            ]
            
            cursor.executemany(
                "INSERT OR IGNORE INTO settings (key, value, category, description) VALUES (?, ?, ?, ?)",
                default_settings
            )
            
            conn.commit()
            conn.close()
            
            self.print_colored(f"✅ پایگاه داده ایجاد شد: {db_path}")
            return True
            
        except Exception as e:
            self.print_colored(f"❌ خطا در راه‌اندازی پایگاه داده: {e}", Colors.FAIL)
            return False
    
    def create_env_file(self):
        """ایجاد فایل .env"""
        self.print_step(4, "ایجاد فایل تنظیمات محیطی")
        
        env_file = self.project_root / '.env'
        env_example_file = self.project_root / '.env.example'
        
        if env_file.exists():
            self.print_colored("⚠️ فایل .env موجود است، رد می‌شود", Colors.WARNING)
            return True
        
        if env_example_file.exists():
            try:
                shutil.copy2(env_example_file, env_file)
                self.print_colored("✅ فایل .env از .env.example کپی شد")
                self.print_colored("🔧 لطفاً متغیرهای محیطی را در فایل .env تنظیم کنید", Colors.WARNING)
                return True
            except Exception as e:
                self.print_colored(f"❌ خطا در کپی فایل .env: {e}", Colors.FAIL)
                return False
        else:
            # ایجاد فایل .env پیش‌فرض
            env_content = """# تنظیمات MrTrader Bot
# لطفاً مقادیر زیر را با اطلاعات واقعی جایگزین کنید

# Telegram Bot
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_CHAT_ID=YOUR_ADMIN_CHAT_ID

# Database
DATABASE_URL=sqlite:///data/mrtrader.db

# API Configuration
API_BASE_URL=https://api.mrtrader.bot
API_KEY=YOUR_API_KEY
API_SECRET=YOUR_API_SECRET

# Redis (اختیاری - برای کش)
REDIS_URL=redis://localhost:6379

# Payment Gateways
ZARINPAL_MERCHANT_ID=YOUR_ZARINPAL_MERCHANT_ID
MELLAT_TERMINAL_ID=YOUR_MELLAT_TERMINAL_ID
MELLAT_USERNAME=YOUR_MELLAT_USERNAME
MELLAT_PASSWORD=YOUR_MELLAT_PASSWORD

# External APIs
BINANCE_API_KEY=YOUR_BINANCE_API_KEY
BINANCE_API_SECRET=YOUR_BINANCE_API_SECRET

# System
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production

# Security
SECRET_KEY=YOUR_SECRET_KEY_HERE
ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY

# Performance
CACHE_TTL=3600
MAX_WORKERS=4
"""
            
            try:
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                self.print_colored("✅ فایل .env ایجاد شد")
                self.print_colored("🔧 لطفاً متغیرهای محیطی را تنظیم کنید", Colors.WARNING)
                return True
            except Exception as e:
                self.print_colored(f"❌ خطا در ایجاد فایل .env: {e}", Colors.FAIL)
                return False
    
    def set_permissions(self):
        """تنظیم دسترسی‌ها"""
        self.print_step(5, "تنظیم دسترسی‌ها")
        
        if os.name == 'posix':  # Unix/Linux/Mac
            try:
                # تنظیم دسترسی برای پوشه‌های حساس
                sensitive_dirs = ['data', 'logs', 'backups']
                for dir_name in sensitive_dirs:
                    dir_path = self.project_root / dir_name
                    if dir_path.exists():
                        os.chmod(dir_path, 0o750)
                
                # تنظیم دسترسی برای فایل .env
                env_file = self.project_root / '.env'
                if env_file.exists():
                    os.chmod(env_file, 0o600)
                
                # قابل اجرا کردن اسکریپت‌ها
                scripts_dir = self.project_root / 'scripts'
                if scripts_dir.exists():
                    for script_file in scripts_dir.glob('*.py'):
                        os.chmod(script_file, 0o755)
                
                self.print_colored("✅ دسترسی‌ها تنظیم شدند")
                return True
                
            except Exception as e:
                self.print_colored(f"⚠️ خطا در تنظیم دسترسی‌ها: {e}", Colors.WARNING)
                return False
        else:
            self.print_colored("ℹ️ تنظیم دسترسی‌ها در Windows پشتیبانی نمی‌شود", Colors.OKBLUE)
            return True
    
    def create_systemd_service(self):
        """ایجاد سرویس systemd (فقط Linux)"""
        if os.name != 'posix':
            return True
        
        try:
            import pwd
            current_user = pwd.getpwuid(os.getuid()).pw_name
        except:
            current_user = 'mrtrader'
        
        service_content = f"""[Unit]
Description=MrTrader Bot
After=network.target

[Service]
Type=simple
User={current_user}
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        try:
            service_file = self.project_root / 'mrtrader.service'
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            self.print_colored("✅ فایل سرویس systemd ایجاد شد")
            self.print_colored(f"💡 برای نصب: sudo cp {service_file} /etc/systemd/system/", Colors.OKBLUE)
            return True
            
        except Exception as e:
            self.print_colored(f"⚠️ خطا در ایجاد سرویس systemd: {e}", Colors.WARNING)
            return False
    
    def run_tests(self):
        """اجرای تست‌های اولیه"""
        self.print_step(6, "اجرای تست‌های اولیه")
        
        try:
            # تست import های اصلی
            test_imports = [
                'sqlite3', 'asyncio', 'json', 'datetime',
                'telegram', 'aiohttp', 'requests'
            ]
            
            for module_name in test_imports:
                try:
                    __import__(module_name)
                    self.print_colored(f"✅ {module_name}")
                except ImportError:
                    self.print_colored(f"❌ {module_name} - نصب نشده", Colors.FAIL)
                    return False
            
            # تست دسترسی به فایل‌ها
            db_path = self.project_root / 'data' / 'mrtrader.db'
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users")
                    conn.close()
                    self.print_colored("✅ اتصال پایگاه داده")
                except Exception as e:
                    self.print_colored(f"❌ خطا در اتصال پایگاه داده: {e}", Colors.FAIL)
                    return False
            
            self.print_colored("✅ همه تست‌ها موفقیت‌آمیز بودند")
            return True
            
        except Exception as e:
            self.print_colored(f"❌ خطا در اجرای تست‌ها: {e}", Colors.FAIL)
            return False
    
    def show_next_steps(self):
        """نمایش مراحل بعدی"""
        self.print_colored(f"\n{Colors.BOLD}🎉 راه‌اندازی تکمیل شد!{Colors.ENDC}")
        
        next_steps = [
            "1. فایل .env را ویرایش کنید و توکن ربات تلگرام را وارد کنید",
            "2. شناسه چت ادمین را در .env تنظیم کنید", 
            "3. کلیدهای API های مورد نیاز را پیکربندی کنید",
            "4. ربات را با دستور python main.py اجرا کنید",
            "5. /start را در تلگرام برای ربات ارسال کنید"
        ]
        
        self.print_colored(f"\n{Colors.BOLD}📋 مراحل بعدی:{Colors.ENDC}")
        for step in next_steps:
            self.print_colored(step, Colors.OKBLUE)
        
        self.print_colored(f"\n{Colors.BOLD}📚 مستندات:{Colors.ENDC}")
        self.print_colored("• README.md - راهنمای کامل", Colors.OKBLUE)
        self.print_colored("• docs/ - مستندات تخصصی", Colors.OKBLUE)
        
        self.print_colored(f"\n{Colors.BOLD}🆘 پشتیبانی:{Colors.ENDC}")
        self.print_colored("• GitHub Issues: https://github.com/mrtrader/bot/issues", Colors.OKBLUE)
        self.print_colored("• ایمیل: support@mrtrader.bot", Colors.OKBLUE)
    
    def run_setup(self):
        """اجرای کامل راه‌اندازی"""
        self.print_colored(f"{Colors.BOLD}🚀 شروع راه‌اندازی MrTrader Bot{Colors.ENDC}")
        self.print_colored(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # بررسی پیش‌نیازها
        if not self.check_python_version():
            return False
        
        # اجرای مراحل راه‌اندازی
        steps = [
            self.create_directories,
            self.install_requirements,
            self.setup_database,
            self.create_env_file,
            self.set_permissions,
            self.create_systemd_service,
            self.run_tests
        ]
        
        for step_func in steps:
            try:
                if not step_func():
                    self.print_colored("❌ راه‌اندازی متوقف شد", Colors.FAIL)
                    return False
            except KeyboardInterrupt:
                self.print_colored("\n⚠️ راه‌اندازی توسط کاربر لغو شد", Colors.WARNING)
                return False
            except Exception as e:
                self.print_colored(f"❌ خطای غیرمنتظره: {e}", Colors.FAIL)
                return False
        
        self.show_next_steps()
        return True

def main():
    """تابع اصلی"""
    setup = EnvironmentSetup()
    
    try:
        success = setup.run_setup()
        if success:
            setup.print_colored("\n✅ راه‌اندازی با موفقیت تکمیل شد!", Colors.OKGREEN)
            sys.exit(0)
        else:
            setup.print_colored("\n❌ راه‌اندازی با خطا مواجه شد!", Colors.FAIL)
            sys.exit(1)
    except KeyboardInterrupt:
        setup.print_colored("\n⚠️ راه‌اندازی لغو شد", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        setup.print_colored(f"\n❌ خطای غیرمنتظره: {e}", Colors.FAIL)
        sys.exit(1)

if __name__ == "__main__":
    main()
