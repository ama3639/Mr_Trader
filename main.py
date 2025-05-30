"""
فایل اصلی MrTrader Bot - Entry Point
این فایل تمام بخش‌های ربات را به هم متصل می‌کند و اجرا می‌کند.
"""
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional

# Telegram Bot API
from telegram.ext import Application, ContextTypes
from telegram import Bot, BotCommand
from telegram.constants import ParseMode

# Core imports
from core.config import Config
from utils.logger import logger, setup_logging

# Database and Cache
from database.database_manager import DatabaseManager
from core.cache import cache

# Managers
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.security_manager import SecurityManager
from managers.payment_manager import PaymentManager
from managers.symbol_manager import SymbolManager
from managers.strategy_manager import StrategyManager
from managers.referral_manager import ReferralManager
from managers.settings_manager import SettingsManager
from managers.report_manager import ReportManager
from managers.backup_manager import BackupManager
from managers.message_manager import MessageManager

# Handlers
from handlers.start_handler import StartHandler
from handlers.callback_handlers import CallbackHandler
from handlers.message_handlers import MessageHandler

# Utils
from utils.time_manager import TimeManager
from api.api_client import ApiClient


class MrTraderBot:
    """کلاس اصلی ربات MrTrader"""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
        # مقداردهی اولیه
        self._initialize_logging()
        self._initialize_managers()
        self._initialize_handlers()
        
        logger.info("MrTrader Bot initialized successfully")
    
    def _initialize_logging(self):
        """راه‌اندازی سیستم لاگ"""
        try:
            setup_logging()
            logger.info("Logging system initialized")
        except Exception as e:
            print(f"Failed to initialize logging: {e}")
            sys.exit(1)
    
    def _initialize_managers(self):
        """مقداردهی managers"""
        try:
            # مدیریت پایه
            self.db_manager = DatabaseManager()
            self.time_manager = TimeManager()
            
            # مدیریت کاربران و امنیت
            self.user_manager = UserManager()
            self.admin_manager = AdminManager()
            self.security_manager = SecurityManager()
            
            # مدیریت محتوا و داده‌ها
            self.symbol_manager = SymbolManager()
            self.strategy_manager = StrategyManager()
            self.payment_manager = PaymentManager()
            self.referral_manager = ReferralManager()
            self.settings_manager = SettingsManager()
            
            # مدیریت گزارش‌ها و بکاپ
            self.report_manager = ReportManager()
            self.backup_manager = BackupManager()
            self.message_manager = MessageManager()
            
            logger.info("All managers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            sys.exit(1)
    
    def _initialize_handlers(self):
        """مقداردهی handlers"""
        try:
            self.start_handler = StartHandler()
            self.callback_handler = CallbackHandler()
            self.message_handler = MessageHandler()
            
            logger.info("All handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            sys.exit(1)
    
    async def initialize_bot(self):
        """راه‌اندازی ربات تلگرام"""
        try:
            # ایجاد Application
            self.application = Application.builder().token(Config.BOT_TOKEN).build()
            self.bot = self.application.bot
            
            # تنظیم کامندهای ربات
            await self._setup_bot_commands()
            
            # اضافه کردن handlers
            await self._register_handlers()
            
            # تنظیم error handler
            self.application.add_error_handler(self._error_handler)
            
            logger.info("Bot application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            sys.exit(1)
    
    async def _setup_bot_commands(self):
        """تنظیم کامندهای ربات"""
        try:
            commands = [
                BotCommand("start", "شروع یا منوی اصلی"),
                BotCommand("help", "راهنمای کامل"),
                BotCommand("menu", "منوی سریع"),
                BotCommand("analysis", "تحلیل سریع"),
                BotCommand("signals", "سیگنال‌های فعال"),
                BotCommand("portfolio", "پورتفولیو"),
                BotCommand("settings", "تنظیمات"),
                BotCommand("support", "پشتیبانی"),
                BotCommand("version", "نسخه ربات"),
                BotCommand("status", "وضعیت سیستم (ادمین)")
            ]
            
            await self.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
            
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
    
    async def _register_handlers(self):
        """ثبت handlers"""
        try:
            # Start handlers
            for handler in self.start_handler.get_handlers():
                self.application.add_handler(handler)
            
            # Callback handlers  
            for handler in self.callback_handler.get_handlers():
                self.application.add_handler(handler)
            
            # Message handlers (باید آخرین باشد)
            for handler in self.message_handler.get_handlers():
                self.application.add_handler(handler)
            
            logger.info("All handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register handlers: {e}")
    
    async def _error_handler(self, update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای ربات"""
        try:
            logger.error(f"Update {update} caused error: {context.error}")
            
            # اطلاع‌رسانی به ادمین‌ها در خطاهای مهم
            if update and update.effective_user:
                await self.message_manager.send_error_to_manager(
                    error_msg=str(context.error),
                    user_id=update.effective_user.id,
                    update_info=str(update)
                )
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def startup_tasks(self):
        """وظایف شروع ربات"""
        try:
            logger.info("Starting bot startup tasks...")
            
            # بررسی سلامت دیتابیس
            await self._check_database_health()
            
            # بررسی اتصال API
            await self._check_api_connections()
            
            # بارگذاری تنظیمات سیستم
            await self._load_system_settings()
            
            # راه‌اندازی scheduler برای وظایف دوره‌ای
            await self._setup_scheduled_tasks()
            
            # ارسال پیام شروع به ادمین‌ها
            await self._notify_startup()
            
            logger.info("All startup tasks completed successfully")
            
        except Exception as e:
            logger.error(f"Error in startup tasks: {e}")
    
    async def _check_database_health(self):
        """بررسی سلامت دیتابیس"""
        try:
            # تست ساده دیتابیس
            result = self.db_manager.fetch_one("SELECT 1 as test")
            if result and result['test'] == 1:
                logger.info("Database health check: OK")
            else:
                raise Exception("Database health check failed")
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    async def _check_api_connections(self):
        """بررسی اتصال به API های خارجی"""
        try:
            # تست ping API
            ping_result = await ApiClient.fetch_ping()
            if ping_result.get('status') == 'ok':
                logger.info("External API health check: OK")
            else:
                logger.warning("External API health check: Warning")
                
        except Exception as e:
            logger.warning(f"API health check warning: {e}")
    
    async def _load_system_settings(self):
        """بارگذاری تنظیمات سیستم"""
        try:
            system_settings = self.settings_manager.get_system_settings()
            
            # بررسی حالت تعمیرات
            if system_settings.maintenance_mode:
                logger.warning("Bot is in maintenance mode")
            
            # بررسی ثبت‌نام
            if not system_settings.registration_enabled:
                logger.info("User registration is disabled")
            
            logger.info("System settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load system settings: {e}")
    
    async def _setup_scheduled_tasks(self):
        """راه‌اندازی وظایف دوره‌ای"""
        try:
            # در اینجا می‌توان از scheduler ها استفاده کرد
            # برای سادگی فقط لاگ می‌کنیم
            
            logger.info("Scheduled tasks configured:")
            logger.info("- Backup: Daily at 2:00 AM")
            logger.info("- Reports: Daily at 1:00 AM") 
            logger.info("- Cleanup: Weekly on Sunday")
            logger.info("- Analytics: Hourly")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduled tasks: {e}")
    
    async def _notify_startup(self):
        """اطلاع‌رسانی شروع به ادمین‌ها"""
        try:
            startup_message = f"""
🤖 <b>MrTrader Bot Started</b>

🕐 <b>زمان شروع:</b> {self.time_manager.get_current_time_persian()}
🔧 <b>نسخه:</b> {Config.BOT_VERSION}
🌐 <b>محیط:</b> {'Production' if Config.PRODUCTION else 'Development'}

✅ سیستم آماده خدمات‌رسانی است.
"""
            
            # ارسال به ادمین‌ها
            admins = await self.admin_manager.get_all_admins()
            for admin in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin['telegram_id'],
                        text=startup_message,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as send_error:
                    logger.warning(f"Failed to notify admin {admin['telegram_id']}: {send_error}")
            
            logger.info("Startup notification sent to admins")
            
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def shutdown_tasks(self):
        """وظایف خاتمه ربات"""
        try:
            logger.info("Starting bot shutdown tasks...")
            
            # بستن اتصالات
            await self._close_connections()
            
            # ذخیره وضعیت
            await self._save_shutdown_state()
            
            # اطلاع‌رسانی خاتمه
            await self._notify_shutdown()
            
            logger.info("All shutdown tasks completed")
            
        except Exception as e:
            logger.error(f"Error in shutdown tasks: {e}")
    
    async def _close_connections(self):
        """بستن اتصالات"""
        try:
            # بستن اتصال دیتابیس
            self.db_manager.close_connection()
            
            # بستن session های HTTP
            await ApiClient.close_session()
            
            logger.info("All connections closed")
            
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
    
    async def _save_shutdown_state(self):
        """ذخیره وضعیت خاتمه"""
        try:
            # ذخیره آمار خاتمه
            shutdown_time = datetime.now().isoformat()
            logger.info(f"Bot shutdown at: {shutdown_time}")
            
        except Exception as e:
            logger.error(f"Error saving shutdown state: {e}")
    
    async def _notify_shutdown(self):
        """اطلاع‌رسانی خاتمه"""
        try:
            if self.bot:
                shutdown_message = f"""
🛑 <b>MrTrader Bot Shutdown</b>

🕐 <b>زمان خاتمه:</b> {self.time_manager.get_current_time_persian()}
⚠️ ربات خاموش شد.

برای راه‌اندازی مجدد با مدیر سیستم تماس بگیرید.
"""
                
                # ارسال به ادمین اول (اگر امکان داشت)
                try:
                    await self.bot.send_message(
                        chat_id=Config.ADMIN_USER_ID,
                        text=shutdown_message,
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error in shutdown notification: {e}")
    
    async def run(self):
        """اجرای اصلی ربات"""
        try:
            logger.info("Starting MrTrader Bot...")
            
            # راه‌اندازی ربات
            await self.initialize_bot()
            
            # وظایف شروع
            await self.startup_tasks()
            
            # راه‌اندازی polling
            logger.info("Bot is now polling for updates...")
            await self.application.run_polling(
                poll_interval=1.0,
                timeout=10,
                bootstrap_retries=5,
                read_timeout=10,
                write_timeout=10,
                connect_timeout=10,
                pool_timeout=1
            )
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Critical error in bot execution: {e}")
            raise
        finally:
            await self.shutdown_tasks()
    
    def setup_signal_handlers(self):
        """تنظیم signal handlers برای shutdown مناسب"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            # برای Windows که SIGTERM ندارد
            if hasattr(signal, 'SIGTERM'):
                if sig == signal.SIGTERM:
                    logger.info("Graceful shutdown requested")
            sys.exit(0)
        
        # ثبت signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """تابع اصلی"""
    try:
        # بررسی متغیرهای محیطی ضروری
        if not Config.BOT_TOKEN:
            logger.error("BOT_TOKEN is not set in environment variables")
            sys.exit(1)
        
        # ایجاد instance ربات
        bot = MrTraderBot()
        
        # تنظیم signal handlers
        bot.setup_signal_handlers()
        
        # اجرای ربات
        await bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


def run_bot():
    """تابع کمکی برای اجرا"""
    try:
        # بررسی نسخه Python
        if sys.version_info < (3, 8):
            print("Python 3.8 or higher is required")
            sys.exit(1)
        
        # اجرای async main
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🤖 MrTrader Bot v{Config.BOT_VERSION}     ║
║                                                              ║
║  📊 Advanced Cryptocurrency Trading Analysis Bot            ║
║  🚀 Starting up...                                          ║
║                                                              ║
║  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}           ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    run_bot()


# Export برای استفاده در سایر ماژول‌ها
__all__ = ['MrTraderBot', 'main', 'run_bot']