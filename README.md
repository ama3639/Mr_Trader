# 📁 ساختار کامل پروژه MrTrader Bot - بروزرسانی شده

```
MrTrader_Bot/
│
├── 📁 config/                          # تنظیمات و پیکربندی
│   ├── __init__.py                     # ✅ موجود
│   ├── api_servers_config.json         # ✅ اصلی و کامل
│   ├── development.json                # ✅ موجود
│   ├── production.json                 # ✅ موجود
│   └── ❌ api_endpoints_config.json    # حذف شود (اضافی)
│
├── 📁 core/                            # هسته اصلی سیستم
│   ├── __init__.py                     # ✅ موجود
│   ├── config.py                       # 🔄 بروزرسانی شده
│   └── cache.py                        # ✅ کامل و مناسب
│
├── 📁 database/                        # مدیریت پایگاه داده
│   ├── __init__.py
│   └── database_manager.py             # ✅ موجود (از چت قبلی)
│
├── 📁 managers/                        # مدیریت‌کننده‌های سیستم
│   ├── __init__.py
│   ├── settings_manager.py             # 🆕 ایجاد شده
│   ├── strategy_manager.py             # 🔄 نیاز به بروزرسانی
│   ├── user_manager.py                 # ✅ موجود (از چت قبلی)
│   ├── admin_manager.py                # ✅ موجود (از چت قبلی)
│   ├── payment_manager.py              # 🔄 نیاز به بروزرسانی
│   ├── security_manager.py             # ✅ موجود (از چت قبلی)
│   ├── message_manager.py              # ✅ موجود (از چت قبلی)
│   ├── referral_manager.py             # 🔄 نیاز به بروزرسانی
│   ├── report_manager.py               # ✅ موجود (از چت قبلی)
│   ├── backup_manager.py               # ✅ موجود (از چت قبلی)
│   ├── symbol_manager.py               # 🔄 نیاز به بروزرسانی
│   └── csv_manager.py                  # ✅ موجود (از چت قبلی)
│
├── 📁 api/                             # ارتباط با API های خارجی
│   ├── __init__.py
│   └── api_client.py                   # 🔄 نیاز به بروزرسانی
│
├── 📁 models/                          # مدل‌های داده
│   ├── __init__.py
│   ├── signal.py                       # 🔄 نیاز به بروزرسانی
│   ├── user.py                         # ⏳ در انتظار بررسی
│   ├── package.py                      # ⏳ در انتظار بررسی
│   └── transaction.py                  # ⏳ در انتظار بررسی
│
├── 📁 utils/                           # ابزارهای کمکی
│   ├── __init__.py
│   ├── logger.py                       # ✅ موجود (از چت قبلی)
│   ├── time_manager.py                 # ✅ موجود (از چت قبلی)
│   ├── validators.py                   # ⏳ در انتظار بررسی
│   ├── formatters.py                   # ⏳ در انتظار بررسی
│   └── helpers.py                      # ⏳ در انتظار بررسی
│
├── 📁 handlers/                        # هندلرهای تلگرام
│   ├── __init__.py
│   ├── start_handler.py                # 🔄 نیاز به بروزرسانی
│   ├── callback_handlers.py            # 🔄 نیاز به بروزرسانی
│   ├── message_handlers.py             # 🔄 نیاز به بروزرسانی
│   ├── admin_handlers.py               # ⏳ در انتظار بررسی
│   ├── payment_handlers.py             # ⏳ در انتظار بررسی
│   └── error_handlers.py               # ⏳ در انتظار بررسی
│
├── 📁 middleware/                      # میدل‌ویرها (اختیاری)
│   ├── __init__.py
│   ├── auth_middleware.py              # ⏳ در انتظار بررسی
│   ├── rate_limit_middleware.py        # ⏳ در انتظار بررسی
│   └── logging_middleware.py           # ⏳ در انتظار بررسی
│
├── 📁 templates/                       # قالب‌های پیام
│   ├── __init__.py
│   ├── keyboards.py                    # ⏳ در انتظار بررسی
│   ├── messages.py                     # ⏳ در انتظار بررسی
│   └── reports.py                      # ⏳ در انتظار بررسی
│
├── 📁 tests/                           # تست‌های واحد
│   ├── __init__.py
│   ├── test_api_client.py              # ⏳ در انتظار بررسی
│   ├── test_strategy_manager.py        # ⏳ در انتظار بررسی
│   ├── test_user_manager.py            # ⏳ در انتظار بررسی
│   ├── test_cache.py                   # ⏳ در انتظار بررسی
│   └── test_database.py               # ⏳ در انتظار بررسی
│
├── 📁 docs/                            # مستندات
│   ├── README.md                       # ⏳ در انتظار بررسی
│   ├── API.md                          # ⏳ در انتظار بررسی
│   ├── DEPLOYMENT.md                   # ⏳ در انتظار بررسی
│   ├── TROUBLESHOOTING.md              # ⏳ در انتظار بررسی
│   └── CHANGELOG.md                    # ⏳ در انتظار بررسی
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
│   ├── __init__.py
│   ├── migrate_database.py             # مهاجرت پایگاه داده
│   ├── backup_data.py                  # پشتیبان‌گیری داده‌ها
│   ├── health_check.py                 # بررسی سلامت سیستم
│   ├── cleanup_logs.py                 # پاک‌سازی لاگ‌ها
│   └── setup_environment.py           # راه‌اندازی محیط
│
├── 📁 assets/                          # منابع استاتیک
│   ├── images/                         # تصاویر
│   ├── icons/                          # آیکون‌ها
│   └── fonts/                          # فونت‌ها (در صورت نیاز)
│
├── 📄 main.py                          # 🔄 نیاز به بروزرسانی
├── 📄 requirements.txt                 # ⏳ در انتظار بررسی
├── 📄 requirements-dev.txt             # وابستگی‌های محیط توسعه
├── 📄 .env                             # متغیرهای محیطی (محرمانه)
├── 📄 .env.example                     # ⏳ در انتظار بررسی
├── 📄 .gitignore                       # فایل‌های نادیده گرفته شده در git
├── 📄 docker-compose.yml               # تنظیمات Docker (اختیاری)
├── 📄 Dockerfile                       # فایل Docker (اختیاری)
├── 📄 setup.py                         # تنظیمات نصب پکیج
├── 📄 pytest.ini                       # تنظیمات تست
├── 📄 .pre-commit-config.yaml          # تنظیمات pre-commit hooks
└── 📄 LICENSE                          # مجوز پروژه
```

## 📋 توضیح پوشه‌ها و فایل‌های کلیدی:

### 🔧 **پوشه‌های اصلی:**

| پوشه | نقش | اهمیت |
|------|-----|-------|
| `config/` | تنظیمات API و پیکربندی سیستم | ⭐⭐⭐ |
| `core/` | هسته اصلی سیستم (Config, Cache) | ⭐⭐⭐ |
| `managers/` | منطق کسب و کار و مدیریت | ⭐⭐⭐ |
| `handlers/` | واسط کاربری تلگرام | ⭐⭐⭐ |
| `api/` | ارتباط با سرویس‌های خارجی | ⭐⭐⭐ |
| `database/` | مدیریت پایگاه داده | ⭐⭐⭐ |
| `models/` | ساختار داده‌ها | ⭐⭐ |
| `utils/` | ابزارهای کمکی | ⭐⭐ |
| `tests/` | تست‌های واحد | ⭐⭐ |
| `docs/` | مستندات | ⭐ |

### 📄 **فایل‌های مهم:**

| فایل | نقش | اولویت |
|------|-----|--------|
| `main.py` | نقطه شروع برنامه | ⭐⭐⭐ |
| `config/api_servers_config.json` | تنظیمات API سرورها | ⭐⭐⭐ |
| `requirements.txt` | وابستگی‌های Python | ⭐⭐⭐ |
| `.env` | متغیرهای محیطی | ⭐⭐⭐ |
| `README.md` | مستندات اصلی | ⭐⭐ |

### 🔄 **جریان کاری پروژه:**

```
main.py
    ↓
core/config.py (بارگذاری تنظیمات)
    ↓
managers/settings_manager.py (بارگذاری API config)
    ↓
handlers/ (تنظیم هندلرهای تلگرام)
    ↓
managers/ (پردازش منطق کسب و کار)
    ↓
api/api_client.py (ارتباط با سرویس‌ها)
    ↓
database/ (ذخیره/خواندن داده‌ها)
```

### 🛠️ **نکات مهم پیاده‌سازی:**

1. **موازی‌سازی:** هر manager مستقل از دیگری عمل کند
2. **وابستگی‌ها:** ترتیب import ها رعایت شود
3. **تست‌پذیری:** هر کلاس قابل تست واحد باشد
4. **مقیاس‌پذیری:** امکان اضافه کردن قابلیت‌های جدید
5. **نگهداری:** کد تمیز و مستندسازی شده

### 🔐 **فایل‌های امنیتی:**

- `.env` - نباید در git قرار گیرد
- `data/` - حاوی پایگاه داده (محرمانه)
- `logs/` - ممکن است حاوی اطلاعات حساس باشد
- `backups/` - حاوی بکاپ پایگاه داده

### 📦 **فایل‌های تولید:**

- `reports/` - گزارش‌های تولید شده برای کاربران
- `data/` - پایگاه داده و فایل‌های CSV
- `logs/` - فایل‌های لاگ سیستم


## 📊 وضعیت فایل‌های بررسی شده:

### ✅ **فایل‌های کامل و مناسب (19 فایل):**
**Core & Config:**
- `core/cache.py` - سیستم کش عالی ✅
- `core/__init__.py` - مناسب ✅
- `config/__init__.py` - مناسب ✅  
- `config/development.json` - تنظیمات محیط توسعه ✅
- `config/production.json` - تنظیمات محیط تولید ✅
- `config/api_servers_config.json` - فایل اصلی API ها ✅

**Managers:**
- `managers/admin_manager.py` - عالی و کامل ✅
- `managers/backup_manager.py` - کامل و حرفه‌ای ✅  
- `managers/csv_manager.py` - مناسب و کارآمد ✅
- `managers/message_manager.py` - کامل و جامع ✅
- `managers/payment_manager.py` - کامل و جامع ✅
- `managers/referral_manager.py` - بسیار کامل ✅
- `managers/report_manager.py` - جامع و حرفه‌ای ✅
- `managers/security_manager.py` - عالی و امن ✅
- `managers/symbol_manager.py` - کامل و پیشرفته ✅
- `managers/user_manager.py` - جامع و کاربردی ✅

**Models & API:**
- `models/signal.py` - بسیار کامل و حرفه‌ای ✅
- `models/__init__.py` - مناسب ✅
- `api/__init__.py` - مناسب ✅

### 🔄 **فایل‌های بروزرسانی شده (6 فایل):**
- `core/config.py` - اضافه شدن تنظیمات استراتژی‌ها و پکیج‌ها ✅
- `managers/settings_manager.py` - فایل جدید برای مدیریت تنظیمات ✅
- `managers/strategy_manager.py` - بروزرسانی شده با settings_manager ✅
- `managers/__init__.py` - بروزرسانی import ها ✅
- `api/api_client.py` - بروزرسانی شده با قابلیت‌های جدید ✅
- `complete_project_structure.md` - بروزرسانی ساختار ✅

### ✅ **فایل‌های کامل managers/ (9 فایل):**
- `admin_manager.py` - عالی و کامل ✅
- `backup_manager.py` - کامل و حرفه‌ای ✅  
- `csv_manager.py` - مناسب و کارآمد ✅
- `payment_manager.py` - کامل و جامع ✅
- `referral_manager.py` - بسیار کامل ✅
- `report_manager.py` - جامع و حرفه‌ای ✅
- `security_manager.py` - عالی و امن ✅
- `symbol_manager.py` - کامل و پیشرفته ✅
- `user_manager.py` - جامع و کاربردی ✅

3. **ویژگی‌های جدید API Client:**
   - متدهای validate_symbol_pair, get_top_symbols, fetch_symbol_info
   - batch_price_fetch برای دریافت همزمان قیمت‌ها
   - health_check پیشرفته
   - توابع helper برای extract_signal_details و format_analysis_result



### حین پیاده‌سازی:
- [ ] هر فایل import های صحیح داشته باشد
- [ ] وابستگی‌ها به ترتیب رعایت شود
- [ ] متغیرهای global مدیریت شود
- [ ] logger در همه جا فعال باشد

### بعد از پیاده‌سازی:
- [ ] فایل main.py به درستی اجرا شود
- [ ] تمام ویژگی‌ها کار کند
- [ ] هیچ import error وجود نداشته باشد
- [ ] تست‌های اولیه انجام شود


## 📈 **پیشرفت پروژه:**
- ✅ **26 فایل** بررسی و آماده شده
- 🔄 **6 فایل** بروزرسانی شده 
- 🆕 **1 فایل** جدید ایجاد شده
- ❌ **1 فایل** اضافی برای حذف
- ⏳ **حدود 8-10 فایل** در انتظار ارسال
