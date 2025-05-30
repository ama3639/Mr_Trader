# 🤖 MrTrader Bot

## 📋 درباره پروژه

**MrTrader Bot** یک ربات تلگرام پیشرفته برای تحلیل و معاملات ارزهای دیجیتال است که قابلیت‌های زیر را ارائه می‌دهد:

- 📊 تحلیل تکنیکال پیشرفته
- 📈 سیگنال‌های معاملاتی هوشمند 
- 💰 مدیریت ریسک و پورتفولیو
- 🔔 هشدارهای قیمتی
- 📱 گزارش‌گیری جامع
- 🎁 سیستم رفرال و پاداش

## 🏗️ ساختار پروژه

```
MrTrader_Bot/
├── 📁 core/                 # هسته اصلی سیستم
│   ├── config.py           # تنظیمات و کانفیگ
│   ├── cache.py            # سیستم کش
│   └── __init__.py
├── 📁 database/            # مدیریت دیتابیس
│   ├── database_manager.py # مدیریت SQLite
│   └── __init__.py
├── 📁 utils/               # ابزارهای کمکی
│   ├── logger.py           # سیستم لاگ
│   ├── time_manager.py     # مدیریت زمان
│   └── __init__.py
├── 📁 managers/            # مدیریت‌کننده‌ها
│   ├── user_manager.py     # مدیریت کاربران
│   ├── admin_manager.py    # مدیریت ادمین‌ها
│   ├── security_manager.py # مدیریت امنیت
│   ├── payment_manager.py  # مدیریت پرداخت‌ها
│   ├── symbol_manager.py   # مدیریت نمادها
│   ├── strategy_manager.py # مدیریت استراتژی‌ها
│   ├── referral_manager.py # مدیریت رفرال
│   ├── settings_manager.py # مدیریت تنظیمات
│   ├── report_manager.py   # مدیریت گزارش‌ها
│   ├── backup_manager.py   # مدیریت بکاپ
│   ├── message_manager.py  # مدیریت پیام‌ها
│   ├── csv_manager.py      # مدیریت CSV
│   └── __init__.py
├── 📁 api/                 # ارتباط با API های خارجی
│   ├── api_client.py       # کلاینت API
│   └── __init__.py
├── 📁 models/              # مدل‌های داده
│   ├── signal.py           # مدل سیگنال‌ها
│   └── __init__.py
├── 📁 handlers/            # هندلرهای تلگرام
│   ├── start_handler.py    # هندلر شروع
│   ├── callback_handlers.py # هندلر callback
│   ├── message_handlers.py # هندلر پیام‌ها
│   └── __init__.py
├── 📁 data/                # فایل‌های داده
├── 📁 logs/                # فایل‌های لاگ
├── 📁 backups/             # فایل‌های بکاپ
├── main.py                 # فایل اصلی
├── requirements.txt        # وابستگی‌ها
├── .env.example           # نمونه متغیرهای محیطی
└── README.md              # این فایل
```

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.8 یا بالاتر
- pip (مدیریت پکیج Python)
- Git
- حساب Telegram Bot (از BotFather)

### مراحل نصب

1. **کلون کردن پروژه:**
```bash
git clone https://github.com/your-username/MrTrader-Bot.git
cd MrTrader-Bot
```

2. **ایجاد محیط مجازی:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **نصب وابستگی‌ها:**
```bash
pip install -r requirements.txt
```

4. **تنظیم متغیرهای محیطی:**
```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_id
DATABASE_FILE=data/mrtrader.db
SECRET_KEY=your_secret_key_here
```

5. **ایجاد پوشه‌های مورد نیاز:**
```bash
mkdir -p data logs backups
```

6. **اجرای ربات:**
```bash
python main.py
```

## ⚙️ تنظیمات

### متغیرهای محیطی

| متغیر | توضیح | مثال |
|-------|--------|-------|
| `BOT_TOKEN` | توکن ربات تلگرام | `123456:ABC-DEF...` |
| `ADMIN_USER_ID` | شناسه عددی ادمین اصلی | `123456789` |
| `DATABASE_FILE` | مسیر فایل دیتابیس | `data/mrtrader.db` |
| `SECRET_KEY` | کلید رمزنگاری | `your-secret-key` |
| `PRODUCTION` | حالت تولید | `True/False` |
| `LOG_LEVEL` | سطح لاگ | `INFO/DEBUG/ERROR` |

### تنظیمات ربات

فایل `core/config.py` شامل تمام تنظیمات ربات است که شامل:

- 🔧 تنظیمات API
- 💾 تنظیمات دیتابیس  
- 📨 تنظیمات پیام‌ها
- 💰 تنظیمات پکیج‌ها
- 🎁 تنظیمات رفرال

## 📊 ویژگی‌ها

### 🔍 تحلیل تکنیکال

- **شاخص‌های فنی:** RSI, MACD, MA, Bollinger Bands
- **تشخیص الگو:** شمعدان‌ها و الگوهای قیمتی
- **سطوح حمایت و مقاومت**
- **تحلیل حجم معاملات**

### 📈 سیگنال‌های معاملاتی

- سیگنال‌های خرید/فروش
- سطوح مختلف اطمینان
- مدیریت ریسک خودکار
- هشدارهای زمان‌بندی شده

### 💼 مدیریت کاربران

- ثبت‌نام و احراز هویت
- سیستم پکیج‌ها و اشتراک
- مدیریت دسترسی‌ها
- آمار و گزارش‌گیری

### 🎁 سیستم رفرال

- کدهای رفرال یکتا
- پاداش‌های خودکار
- رتبه‌بندی کاربران
- آمار عملکرد

## 🛠️ توسعه و Debugging

### اجرای در حالت توسعه

```bash
# با debug mode
python main.py --debug

# با log level مشخص
LOG_LEVEL=DEBUG python main.py
```

### تست کردن

```bash
# اجرای تست‌ها
python -m pytest tests/

# اجرای تست با coverage
python -m pytest tests/ --cov=.
```

### لاگ‌ها

لاگ‌ها در پوشه `logs/` ذخیره می‌شوند:

- `mrtrader.log` - لاگ اصلی
- `error.log` - لاگ خطاها
- `api.log` - لاگ API ها
- `user_activity.log` - فعالیت کاربران

## 📦 Migration از نسخه قدیمی

اگر نسخه تک‌فایلی قبلی دارید:

1. **بکاپ بگیرید:**
```bash
cp Mr-Trader.py Mr-Trader-backup.py
cp mrtrader.db mrtrader-backup.db
```

2. **اجرای migration:**
```bash
python tools/migrate_from_old.py
```

3. **بررسی:**
```bash
python main.py --check-migration
```

## 🔒 امنیت

### تنظیمات امنیتی

- رمزنگاری داده‌های حساس
- محدودیت نرخ درخواست
- احراز هویت چندمرحله‌ای
- لاگ‌گیری تمام فعالیت‌ها

### توصیه‌های امنیتی

- هرگز توکن ربات را در کد قرار ندهید
- از HTTPS برای webhook استفاده کنید
- فایل `.env` را در `.gitignore` قرار دهید
- بکاپ‌های منظم بگیرید

## 📈 مانیتورینگ و نظارت

### داشبورد ادمین

دسترسی ادمین‌ها به:
- آمار لحظه‌ای سیستم
- فعالیت کاربران
- گزارش خطاها
- مدیریت کاربران

### آلارم‌ها

سیستم آلارم برای:
- خطاهای مهم
- پر شدن فضای دیسک
- افت کیفیت API
- فعالیت‌های مشکوک

## 🚨 عیب‌یابی

### مشکلات رایج

**ربات پاسخ نمی‌دهد:**
```bash
# بررسی لاگ‌ها
tail -f logs/mrtrader.log

# بررسی توکن
python -c "from core.config import Config; print(bool(Config.BOT_TOKEN))"
```

**خطای دیتابیس:**
```bash
# بررسی سلامت دیتابیس
python -c "from database.database_manager import DatabaseManager; dm = DatabaseManager(); print(dm.fetch_one('SELECT 1'))"
```

**مشکل API:**
```bash
# تست اتصال
python -c "from api.api_client import ApiClient; import asyncio; print(asyncio.run(ApiClient.fetch_ping()))"
```

## 📚 مستندات API

### Endpoints اصلی

- `/start` - شروع ربات
- `/help` - راهنما
- `/analysis` - تحلیل سریع
- `/signals` - سیگنال‌ها
- `/portfolio` - پورتفولیو

### Callback Data Format

```
action:parameter:extra_data
```

مثال:
```
analyze_symbol:BTC
package_buy:premium:monthly
```

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. branch جدید بسازید: `git checkout -b feature/amazing-feature`
3. تغییرات را commit کنید: `git commit -m 'Add amazing feature'`
4. Push کنید: `git push origin feature/amazing-feature`
5. Pull Request بسازید

### استانداردهای کد

- از PEP 8 پیروی کنید
- docstring برای توابع بنویسید
- تست برای کد جدید اضافه کنید
- کامنت‌های مفید بنویسید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. جزئیات در فایل `LICENSE` موجود است.

## 👥 تیم توسعه

- **توسعه‌دهنده اصلی:** [نام شما]
- **طراحی UI/UX:** [نام طراح]
- **تست و QA:** [نام تستر]

## 📞 پشتیبانی

- **تلگرام:** @YourSupportBot
- **ایمیل:** support@mrtrader.com
- **وب‌سایت:** https://mrtrader.com

## 📊 آمار پروژه

![GitHub stars](https://img.shields.io/github/stars/your-username/MrTrader-Bot)
![GitHub forks](https://img.shields.io/github/forks/your-username/MrTrader-Bot)
![GitHub issues](https://img.shields.io/github/issues/your-username/MrTrader-Bot)
![Python version](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🗺️ نقشه راه

- [ ] ✅ ماژولار کردن کامل
- [ ] 🔄 پیاده‌سازی webhook
- [ ] 📱 اپلیکیشن موبایل
- [ ] 🤖 هوش مصنوعی پیشرفته‌تر
- [ ] 🌐 پشتیبانی چندزبانه
- [ ] ☁️ نسخه ابری

## ❤️ تشکر ویژه

از تمام کسانی که در توسعه این پروژه مشارکت داشته‌اند، تشکر می‌کنیم.

---

**⚠️ هشدار:** این ربات فقط جهت اطلاع‌رسانی است و مشاوره مالی نیست. همیشه تحقیق شخصی انجام دهید.

**🚀 برای شروع سریع، از دستور زیر استفاده کنید:**
```bash
git clone https://github.com/your-username/MrTrader-Bot.git && cd MrTrader-Bot && pip install -r requirements.txt && python main.py
```