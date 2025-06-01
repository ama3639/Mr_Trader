# 📁 ساختار کامل پروژه MrTrader Bot - نسخه نهایی
## 1404/03/10
```
MrTrader_Bot/
│
├── 📁 config/                          # تنظیمات و پیکربندی
│   ├── __init__.py                     # ✅ موجود و کامل
│   ├── api_servers_config.json         # ✅ اصلی و کامل - آدرس سرورهای API
│   ├── development.json                # ✅ تنظیمات محیط توسعه
│   └── production.json                 # ✅ تنظیمات محیط تولید
│
├── 📁 core/                            # هسته اصلی سیستم
│   ├── __init__.py                     # ✅ موجود و کامل
│   ├── config.py                       # ✅ بروزرسانی شده - مدیریت تنظیمات
│   └── cache.py                        # ✅ کامل - سیستم کش 60 ثانیه‌ای
│
├── 📁 database/                        # مدیریت پایگاه داده
│   ├── __init__.py                     # ✅ خودکار ایجاد می‌شود
│   └── database_manager.py             # ✅ موجود از چت قبلی
│
├── 📁 managers/                        # مدیریت‌کننده‌های سیستم
│   ├── __init__.py                     # ✅ بروزرسانی شده - import های کامل
│   ├── settings_manager.py             # ✅ جدید ساخته شده - مدیریت API config
│   ├── strategy_manager.py             # ✅ بروزرسانی شده - یکپارچه با settings
│   ├── user_manager.py                 # ✅ کامل - مدیریت کاربران
│   ├── admin_manager.py                # ✅ کامل - عملیات مدیریتی
│   ├── payment_manager.py              # ✅ کامل - مدیریت پرداخت‌ها
│   ├── security_manager.py             # ✅ کامل - امنیت سیستم
│   ├── message_manager.py              # ✅ کامل - مدیریت پیام‌ها
│   ├── referral_manager.py             # ✅ کامل - سیستم رفرال
│   ├── report_manager.py               # ✅ کامل - گزارش‌گیری
│   ├── backup_manager.py               # ✅ کامل - پشتیبان‌گیری
│   ├── symbol_manager.py               # ✅ کامل - مدیریت نمادها
│   └── csv_manager.py                  # ✅ کامل - مدیریت CSV
│
├── 📁 api/                             # ارتباط با API های خارجی
│   ├── __init__.py                     # ✅ موجود و کامل
│   └── api_client.py                   # ✅ بروزرسانی شده - یکپارچه و پیشرفته
│
├── 📁 models/                          # مدل‌های داده
│   ├── __init__.py                     # ✅ موجود و کامل
│   ├── signal.py                       # ✅ کامل - مدل سیگنال پیشرفته
│   ├── user.py                         # ✅ جدید ساخته شده - مدل کامل کاربر
│   ├── package.py                      # ✅ جدید ساخته شده - مدل پکیج‌ها
│   └── transaction.py                  # ✅ جدید ساخته شده - مدل تراکنش‌ها
│
├── 📁 utils/                           # ابزارهای کمکی
│   ├── __init__.py                     # ✅ موجود و کامل
│   ├── logger.py                       # ✅ کامل - سیستم لاگ پیشرفته
│   ├── time_manager.py                 # ✅ کامل - مدیریت زمان
│   ├── scheduler.py                    # ✅ کامل - زمانبندی وظایف
│   ├── validators.py                   # ✅ جدید ساخته شده - اعتبارسنجی کامل
│   ├── helpers.py                      # ✅ جدید ساخته شده - توابع کمکی
│   └── formatters.py                   # ✅ جدید ساخته شده - فرمت‌کننده‌ها
│
├── 📁 handlers/                        # هندلرهای تلگرام
│   ├── __init__.py                     # ✅ کامل - import های صحیح
│   ├── start_handler.py                # ✅ کامل - مدیریت شروع
│   ├── callback_handlers.py            # ✅ کامل - callback های پیچیده
│   ├── message_handlers.py             # ✅ کامل - پردازش پیام‌ها
│   ├── admin_handlers.py               # ✅ جدید ساخته شده - هندلرهای مدیریتی
│   └── payment_handlers.py             # ✅ جدید ساخته شده - هندلرهای پرداخت
│
├── 📁 templates/                       # قالب‌های پیام و رابط کاربری
│   ├── __init__.py                     # ✅ خودکار ایجاد می‌شود
│   ├── keyboards.py                    # ✅ جدید ساخته شده - کیبوردهای inline
│   ├── messages.py                     # ✅ جدید ساخته شده - قالب‌های پیام
│   └── reports.py                      # ✅ جدید ساخته شده - قالب‌های گزارش
│
├── 📁 tests/                           # تست‌های واحد (اختیاری)
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_strategy_manager.py
│   ├── test_user_manager.py
│   ├── test_cache.py
│   └── test_database.py
│
├── 📁 docs/                            # مستندات
│   ├── README.md                       # ✅ جدید ساخته شده - راهنمای کامل
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── TROUBLESHOOTING.md
│   └── CHANGELOG.md
│
├── 📁 data/                            # داده‌ها و فایل‌های تولیدی
│   ├── mrtrader.db                     # پایگاه داده SQLite
│   ├── users.csv                       # فایل CSV کاربران (بکاپ)
│   └── .gitkeep                        # نگه‌داری پوشه در git
│
├── 📁 logs/                            # فایل‌های لاگ
│   ├── mrtrader.log                    # لاگ اصلی
│   ├── error.log                       # لاگ خطاها
│   ├── api.log                         # لاگ API ها
│   ├── user_activity.log               # لاگ فعالیت کاربران
│   └── .gitkeep
│
├── 📁 backups/                         # فایل‌های پشتیبان
│   ├── daily/                          # بکاپ‌های روزانه
│   ├── weekly/                         # بکاپ‌های هفتگی
│   ├── monthly/                        # بکاپ‌های ماهانه
│   └── .gitkeep
│
├── 📁 reports/                         # گزارش‌های تولید شده
│   ├── analysis/                       # گزارش‌های تحلیل
│   ├── user_reports/                   # گزارش‌های کاربران
│   ├── admin_reports/                  # گزارش‌های مدیریتی
│   └── .gitkeep
│
├── 📁 scripts/                         # اسکریپت‌های کمکی
│   ├── __init__.py                     # ✅ خودکار ایجاد می‌شود
│   ├── setup_environment.py           # ✅ جدید ساخته شده - راه‌اندازی اولیه
│   ├── migrate_database.py            # مهاجرت پایگاه داده
│   ├── backup_data.py                 # پشتیبان‌گیری داده‌ها
│   ├── health_check.py                # بررسی سلامت سیستم
│   └── cleanup_logs.py                # پاک‌سازی لاگ‌ها
│
├── 📁 assets/                          # منابع استاتیک
│   ├── images/                         # تصاویر
│   ├── icons/                          # آیکون‌ها
│   └── fonts/                          # فونت‌ها (در صورت نیاز)
│
├── 📄 main.py                          # ✅ فایل اصلی (main_file.py تغییر نام یافته)
├── 📄 requirements.txt                 # وابستگی‌های Python
├── 📄 requirements-dev.txt             # وابستگی‌های محیط توسعه
├── 📄 .env                             # متغیرهای محیطی (محرمانه)
├── 📄 .env.example                     # نمونه متغیرهای محیطی
├── 📄 .gitignore                       # فایل‌های نادیده گرفته شده در git
├── 📄 docker-compose.yml               # تنظیمات Docker (اختیاری)
├── 📄 Dockerfile                       # فایل Docker (اختیاری)
├── 📄 setup.py                         # تنظیمات نصب پکیج
├── 📄 pytest.ini                       # تنظیمات تست
├── 📄 .pre-commit-config.yaml          # تنظیمات pre-commit hooks
├── 📄 mrtrader.service                 # فایل سرویس systemd
└── 📄 LICENSE                          # مجوز پروژه
```
