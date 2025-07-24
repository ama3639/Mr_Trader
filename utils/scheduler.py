# mr_trader/utils/scheduler.py

import asyncio
import logging
import datetime as dt
from telegram.ext import JobQueue


async def check_expired_packages(application):
    """بررسی و اطلاع‌رسانی انقضای پکیج‌ها"""
    from ..managers.user_manager import UserManager
    from ..core.globals import TELEGRAM_TOKEN

    users = UserManager.get_all_users()
    for user in users:
        expiry_date = user.get('expiry_date')
        if expiry_date and datetime.strptime(expiry_date, "%Y-%m-%d") < datetime.now():
            await application.bot.send_message(
                chat_id=user['telegram_id'],
                text="پکیج شما منقضی شده است. لطفاً تمدید کنید."
            )

async def update_statistics(application):
    """به‌روزرسانی آمار کاربران و سیستم"""
    total_users = len(UserManager.get_all_users())
    active_users = len([user for user in UserManager.get_all_users() if user.get('is_blocked') == 0])
    await application.bot.send_message(
        chat_id=Config.MANAGER_IDS[0],
        text=f"📊 آمار سیستم:\nکاربران کل: {total_users}\nکاربران فعال: {active_users}"
    )

def setup_scheduler(application):
    """تنظیم وظایف زمان‌بندی شده با استفاده از job_queue تلگرام"""
    job_queue = application.job_queue
    
    # بررسی منظم انقضای پکیج‌ها (هر روز ساعت 10 صبح)
    job_queue.run_daily(
        lambda context: asyncio.create_task(check_expired_packages(context.application)),
        dt.time(hour=10, minute=0),
        name="daily_check_expired_packages"
    )
    
    # پشتیبان‌گیری خودکار (هر هفته یکشنبه ساعت 2 بامداد)
    job_queue.run_daily(
        lambda context: asyncio.create_task(BackupManager.create_backup_job(context.application)),
        dt.time(hour=2, minute=0),
        days=[6],  # 6 = یکشنبه (0 = دوشنبه)
        name="weekly_backup"
    )
    
    # به‌روزرسانی آمار (هر 6 ساعت)
    job_queue.run_repeating(
        lambda context: asyncio.create_task(update_statistics(context.application)),
        interval=21600,  # 6 ساعت به ثانیه
        first=10,  # شروع بعد از 10 ثانیه
        name="update_statistics"
    )
    
    # پاکسازی بکاپ‌های قدیمی (هر ماه)
    job_queue.run_monthly(
        lambda context: asyncio.create_task(BackupManager.cleanup_old_backups(context.application)),
        when=dt.time(hour=3, minute=0),  # ساعت 3 بامداد
        day=1,  # روز اول هر ماه
        name="monthly_cleanup_old_backups"
    )
    
    logger.info("Scheduler (job_queue) configured successfully")
    return job_queue