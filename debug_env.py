import os
from dotenv import load_dotenv
from pathlib import Path

print("--- شروع تست فایل .env ---")

# مسیر فایل .env را مشخص می‌کنیم
env_path = Path('.') / '.env'
print(f"مسیر فایل .env که بررسی می‌شود: {env_path.resolve()}")

# بررسی وجود فایل
if not env_path.exists():
    print(f"❌ خطا: فایل .env در مسیر مشخص شده وجود ندارد!")
else:
    print("✅ فایل .env پیدا شد.")
    # سعی در بارگذاری فایل
    try:
        load_dotenv(dotenv_path=env_path, verbose=True)
        print("✅ دستور load_dotenv() بدون خطا اجرا شد.")

        # حالا متغیرها را می‌خوانیم
        db_url = os.getenv("DATABASE_URL")
        bot_token = os.getenv("BOT_TOKEN")

        if db_url:
            print(f"✅  DATABASE_URL با موفقیت خوانده شد: {db_url}")
        else:
            print("❌  DATABASE_URL خوانده نشد یا خالی است.")

        if bot_token:
            # برای امنیت، فقط چند کاراکتر آخر توکن را نمایش می‌دهیم
            print(f"✅  BOT_TOKEN با موفقیت خوانده شد: ...{bot_token[-6:]}")
        else:
            print("❌  BOT_TOKEN خوانده نشد یا خالی است.")

    except Exception as e:
        print(f"❌ یک خطای غیرمنتظره هنگام پردازش فایل .env رخ داد: {e}")


print("--- پایان تست ---")