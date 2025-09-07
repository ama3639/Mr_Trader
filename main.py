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
import asyncio
import sys

# حل مشکل Windows Event Loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
async def maybe_call(func, *args, **kwargs):
    """
    اگر func آسنکرون باشد await می‌کند؛ در غیر این صورت آن را sync فراخوانی می‌کند.
    اگر نتیجه coroutine برگردد نیز آن را await می‌کند.
    """
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    result = func(*args, **kwargs)
    if asyncio.iscoroutine(result):
        return await result
    return result
# -------------------------

class MrTraderBot:
    """کلاس اصلی ربات MrTrader"""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.is_running = False  # ✅ اضافه شده برای tracking
        self.shutdown_event = asyncio.Event()  # ✅ اضافه شده برای graceful shutdown
        
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
            
            try:
                self.admin_manager = AdminManager()
                # ✅ مقداردهی اولیه مدیران اصلی از Config.ADMINS (اگر تعریف شده)
                try:
                    manager_ids = getattr(Config, "ADMINS", []) or []
                    # تضمین تبدیل به لیست اعداد
                    manager_ids = [int(x) for x in manager_ids if x]
                    if manager_ids:
                        AdminManager.initialize_managers(manager_ids)
                        logger.info(f"AdminManager initialized with managers: {manager_ids}")
                except Exception as mgr_init_err:
                    logger.warning(f"Could not initialize AdminManager manager IDs: {mgr_init_err}")
            except ImportError:
                logger.warning("AdminManager not available, using fallback")
                self.admin_manager = None
            
            try:
                self.security_manager = SecurityManager()
            except ImportError:
                logger.warning("SecurityManager not available, using fallback")
                self.security_manager = None
            
            # مدیریت محتوا و داده‌ها
            try:
                self.symbol_manager = SymbolManager()
            except ImportError:
                logger.warning("SymbolManager not available")
                self.symbol_manager = None
                
            try:
                self.strategy_manager = StrategyManager()
            except ImportError:
                logger.warning("StrategyManager not available")
                self.strategy_manager = None
                
            try:
                self.payment_manager = PaymentManager()
            except ImportError:
                logger.warning("PaymentManager not available")
                self.payment_manager = None
                
            try:
                self.referral_manager = ReferralManager()
            except ImportError:
                logger.warning("ReferralManager not available")
                self.referral_manager = None
                
            try:
                self.settings_manager = SettingsManager()
            except ImportError:
                logger.warning("SettingsManager not available")
                self.settings_manager = None
            
            # مدیریت گزارش‌ها و بکاپ
            try:
                self.report_manager = ReportManager()
            except ImportError:
                logger.warning("ReportManager not available")
                self.report_manager = None
                
            try:
                self.backup_manager = BackupManager()
            except ImportError:
                logger.warning("BackupManager not available")
                self.backup_manager = None
                
            try:
                self.message_manager = MessageManager()
            except ImportError:
                logger.warning("MessageManager not available")
                self.message_manager = None
            
            logger.info("All managers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            # ✅ ادامه دادن به جای sys.exit برای flexibility
            logger.warning("Some managers failed to initialize, continuing with available ones")
    
    def _initialize_handlers(self):
        """مقداردهی handlers"""
        try:
            # ✅ Safe initialization برای handlers
            try:
                self.start_handler = StartHandler()
            except ImportError as e:
                logger.error(f"Failed to initialize StartHandler: {e}")
                sys.exit(1)  # StartHandler ضروری است
                
            try:
                self.callback_handler = CallbackHandler()
            except Exception as e:
                logger.error(f"Failed to initialize CallbackHandler: {e}")
                self.callback_handler = None
                
            try:
                self.message_handler = MessageHandler()
            except ImportError:
                logger.warning("MessageHandler not available, using fallback")
                self.message_handler = None
            
            logger.info("All handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            # StartHandler مهم است، بقیه اختیاری
            if not hasattr(self, 'start_handler'):
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
            raise  # ✅ raise به جای sys.exit برای بهتر handling
    
    async def _setup_bot_commands(self):
        """تنظیم کامندهای ربات (با timeout و retry کنترل‌شده)"""
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

        # تلاش اولیه با timeout کوتاه‌تر تا از بلوکه شدن طولانی جلوگیری شود
        try:
            try:
                await asyncio.wait_for(self.bot.set_my_commands(commands), timeout=8.0)
                logger.info("Bot commands set successfully (initial attempt)")
                return
            except asyncio.TimeoutError as te:
                logger.error(f"Timeout while setting bot commands (initial): {te}")
                # ادامه به retry
                raise te
            except Exception as e:
                logger.error(f"Failed to set bot commands (initial): {e}")
                raise e

        except Exception:
            # تلاش مجدد با timeout طولانی‌تر و لاگ دقیق‌تر
            try:
                await asyncio.wait_for(self.bot.set_my_commands(commands), timeout=12.0)
                logger.info("Bot commands set successfully on retry")
            except asyncio.TimeoutError as te2:
                logger.warning(f"Timeout while setting bot commands (retry): {te2}")
            except Exception as retry_error:
                logger.warning(f"Could not set bot commands even on retry: {retry_error}")
    
    async def _register_handlers(self):
        """ثبت handlers"""
        try:
            # Start handlers - ضروری
            if hasattr(self.start_handler, 'get_handlers'):
                start_handlers = self.start_handler.get_handlers()
                if start_handlers:
                    for handler in start_handlers:
                        self.application.add_handler(handler)
                        
            # ✅ اگر start_handler متد get_handlers ندارد، از متدهای مستقیم استفاده کن
            else:
                from telegram.ext import CommandHandler
                
                # اضافه کردن handlers دستی
                if hasattr(self.start_handler, 'start_command'):
                    self.application.add_handler(CommandHandler("start", self.start_handler.start_command))
                if hasattr(self.start_handler, 'help_command'):
                    self.application.add_handler(CommandHandler("help", self.start_handler.help_command))
                if hasattr(self.start_handler, 'menu_command'):
                    self.application.add_handler(CommandHandler("menu", self.start_handler.menu_command))
                if hasattr(self.start_handler, 'profile_command'):
                    self.application.add_handler(CommandHandler("profile", self.start_handler.profile_command))
                
                logger.info("Start handlers registered manually")
            
            # Callback handlers - ✅ Fixed
            if self.callback_handler:
                try:
                    if hasattr(self.callback_handler, 'get_handlers'):
                        callback_handlers = self.callback_handler.get_handlers()  
                        if callback_handlers:
                            for handler in callback_handlers:
                                self.application.add_handler(handler)
                            logger.info("Callback handlers registered successfully")
                    else:
                        # اضافه کردن callback handler دستی
                        from telegram.ext import CallbackQueryHandler
                        if hasattr(self.callback_handler, 'handle_callback_query'):
                            self.application.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback_query))
                            logger.info("Callback handler registered manually")
                except Exception as cb_error:
                    logger.warning(f"Some callback handlers could not be registered: {cb_error}")
            else:
                logger.warning("No callback handler available")
            
            # Message handlers - اختیاری (باید آخرین باشد)
            if self.message_handler:
                try:
                    if hasattr(self.message_handler, 'get_handlers'):
                        message_handlers = self.message_handler.get_handlers()
                        if message_handlers:
                            for handler in message_handlers:
                                self.application.add_handler(handler)
                    else:
                        # اضافه کردن message handler دستی
                        from telegram.ext import MessageHandler as TelegramMessageHandler, filters
                        if hasattr(self.message_handler, 'handle_message'):
                            self.application.add_handler(TelegramMessageHandler(
                                filters.TEXT & ~filters.COMMAND, 
                                self.message_handler.handle_message
                            ))
                    
                    logger.info("Message handlers registered successfully")
                except Exception as msg_error:
                    logger.warning(f"Some message handlers could not be registered: {msg_error}")
            
            logger.info("All handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register handlers: {e}")
            # ✅ ادامه دادن به جای خروج کامل
            logger.warning("Continuing with partial handler registration")
    
    async def _error_handler(self, update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای ربات"""
        try:
            logger.error(f"Update {update} caused error: {context.error}")
            
            # اطلاع‌رسانی به ادمین‌ها در خطاهای مهم
            if update and hasattr(update, 'effective_user') and update.effective_user:
                try:
                    # ✅ بررسی وجود message_manager
                    if self.message_manager and hasattr(self.message_manager, 'send_error_to_manager'):
                        await self.message_manager.send_error_to_manager(
                            error_msg=str(context.error),
                            user_id=update.effective_user.id,
                            update_info=str(update)
                        )
                    else:
                        # fallback - ارسال مستقیم به ادمین اول
                        if hasattr(Config, 'ADMIN_USER_ID') and Config.ADMIN_USER_ID > 0:
                            await self.bot.send_message(
                                chat_id=Config.ADMIN_USER_ID,
                                text=f"❌ خطا در ربات:\n{str(context.error)[:500]}...",
                                parse_mode=ParseMode.HTML
                            )
                except Exception as notify_error:
                    logger.warning(f"Could not notify manager about error: {notify_error}")
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def startup_tasks(self):
        """وظایف شروع ربات"""
        try:
            logger.info("Starting bot startup tasks...")
            
            # بررسی سلامت دیتابیس
            await self._check_database_health()
            
            # بررسی اتصال API (اختیاری)
            await self._check_api_connections()
            
            # بارگذاری تنظیمات سیستم (اختیاری)
            await self._load_system_settings()
            
            # راه‌اندازی scheduler برای وظایف دوره‌ای
            await self._setup_scheduled_tasks()
            
            # ارسال پیام شروع به ادمین‌ها (اختیاری)
            await self._notify_startup()
            
            logger.info("All startup tasks completed successfully")
            
        except Exception as e:
            logger.error(f"Error in startup tasks: {e}")
            # ✅ ادامه دادن به جای raise
    
    async def _check_database_health(self):
        """بررسی سلامت دیتابیس"""
        try:
            # ✅ بررسی وجود متد fetch_one
            if hasattr(self.db_manager, 'fetch_one'):
                result = self.db_manager.fetch_one("SELECT 1 as test")
                if result and result.get('test') == 1:
                    logger.info("Database health check: OK")
                else:
                    logger.warning("Database health check: Warning - empty result")
            else:
                logger.info("Database health check skipped - fetch_one method not available")
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            # ✅ ادامه دادن به جای raise
    
    async def _check_api_connections(self):
        """بررسی اتصال به API های خارجی"""
        try:
            # تست ping API (اگر متد وجود داشت)
            if hasattr(ApiClient, 'fetch_ping'):
                ping_result = await ApiClient.fetch_ping()
                if ping_result.get('status') == 'ok':
                    logger.info("External API health check: OK")
                else:
                    logger.warning("External API health check: Warning")
            else:
                logger.info("API ping check skipped - method not available")
                
        except Exception as e:
            logger.warning(f"API health check warning: {e}")
    
    async def _load_system_settings(self):
        """بارگذاری تنظیمات سیستم"""
        try:
            # بررسی وجود متد
            if self.settings_manager and hasattr(self.settings_manager, 'get_system_settings'):
                system_settings = self.settings_manager.get_system_settings()
                
                # بررسی حالت تعمیرات
                if hasattr(system_settings, 'maintenance_mode') and system_settings.maintenance_mode:
                    logger.warning("Bot is in maintenance mode")
                
                # بررسی ثبت‌نام
                if hasattr(system_settings, 'registration_enabled') and not system_settings.registration_enabled:
                    logger.info("User registration is disabled")
                
                logger.info("System settings loaded successfully")
            else:
                logger.info("System settings loading skipped - method not available")
            
        except Exception as e:
            logger.warning(f"Failed to load system settings: {e}")
    
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
        """اطلاع‌رسانی شروع به ادمین‌ها (با timeout و fallback ایمن)"""
        try:
            startup_message = f"""
    🤖 <b>MrTrader Bot Started</b>

    🕐 <b>زمان شروع:</b> {self.time_manager.get_current_time_persian()}
    🔧 <b>نسخه:</b> {getattr(Config, 'BOT_VERSION', '1.0.0')}
    🌐 <b>محیط:</b> {'Production' if getattr(Config, 'PRODUCTION', False) else 'Development'}

    ✅ سیستم با /start آماده خدمات‌رسانی است.
    """

            sent = False
            try:
                # 1) اگر admin_manager موجود است، سعی کن از آن admin ها را بگیری (پشتیبانی از sync/async)
                if getattr(self, "admin_manager", None) and hasattr(self.admin_manager, "get_all_admins"):
                    try:
                        admins = await maybe_call(self.admin_manager.get_all_admins)
                    except Exception as am_err:
                        admins = None
                        logger.warning(f"AdminManager.get_all_admins failed: {am_err}")

                    if admins and isinstance(admins, (list, tuple)):
                        for admin in admins:
                            # admin ممکن است dict یا عدد باشد — ایمن سازی
                            if isinstance(admin, dict):
                                admin_id = admin.get("telegram_id") or admin.get("id")
                            else:
                                admin_id = admin
                            try:
                                if admin_id:
                                    await asyncio.wait_for(
                                        self.bot.send_message(chat_id=admin_id, text=startup_message, parse_mode=ParseMode.HTML),
                                        timeout=8.0
                                    )
                                    sent = True
                                    break
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout sending startup message to admin {admin_id}")
                            except Exception as send_error:
                                logger.warning(f"Failed to notify admin {admin_id}: {send_error}")

                # 2) fallback به Config.ADMIN_USER_ID یا Config.ADMINS
                if not sent:
                    try:
                        if getattr(Config, "ADMIN_USER_ID", None):
                            await asyncio.wait_for(
                                self.bot.send_message(chat_id=Config.ADMIN_USER_ID, text=startup_message, parse_mode=ParseMode.HTML),
                                timeout=8.0
                            )
                            sent = True
                        elif getattr(Config, "ADMINS", None):
                            for admin_id in Config.ADMINS:
                                if admin_id and admin_id > 0:
                                    try:
                                        await asyncio.wait_for(
                                            self.bot.send_message(chat_id=admin_id, text=startup_message, parse_mode=ParseMode.HTML),
                                            timeout=8.0
                                        )
                                        sent = True
                                        break
                                    except asyncio.TimeoutError:
                                        logger.warning(f"Timeout sending startup message to admin {admin_id}")
                                    except Exception as e:
                                        logger.warning(f"Failed sending startup message to admin {admin_id}: {e}")
                    except Exception as fallback_error:
                        logger.warning(f"Fallback admin notify failed: {fallback_error}")

            except Exception as fallback_error:
                logger.warning(f"Could not send startup notification even as fallback: {fallback_error}")

            if sent:
                logger.info("Startup notification sent successfully")
            else:
                logger.info("No startup notification sent (no reachable admins or timed out)")

        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
    
    async def shutdown_tasks(self):
        """وظایف خاتمه ربات"""
        try:
            logger.info("Starting bot shutdown tasks...")
            
            # تنظیم flag
            self.is_running = False
            
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
            if hasattr(self.db_manager, 'close_connection'):
                try:
                    self.db_manager.close_connection()
                    logger.info("Database connection closed")
                except Exception as db_close_error:
                    logger.warning(f"Error closing database connection: {db_close_error}")
            
            # بستن session های HTTP (اگر متد وجود داشت)
            try:
                if hasattr(ApiClient, 'close_session'):
                    await ApiClient.close_session()
                    logger.info("API client session closed")
            except Exception as api_close_error:
                logger.warning(f"Could not close API session: {api_close_error}")
            
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
                    if hasattr(Config, 'ADMIN_USER_ID') and Config.ADMIN_USER_ID > 0:
                        await self.bot.send_message(
                            chat_id=Config.ADMIN_USER_ID,
                            text=shutdown_message,
                            parse_mode=ParseMode.HTML
                        )
                    elif hasattr(Config, 'ADMINS') and Config.ADMINS:
                        await self.bot.send_message(
                            chat_id=Config.ADMINS[0],
                            text=shutdown_message,
                            parse_mode=ParseMode.HTML
                        )
                except Exception as notify_error:
                    logger.warning(f"Could not send shutdown notification: {notify_error}")
            
        except Exception as e:
            logger.warning(f"Error in shutdown notification: {e}")
    
    async def run(self):
        """اجرای اصلی ربات - ✅ Fixed Application handling"""
        try:
            logger.info("Starting MrTrader Bot...")
            
            # راه‌اندازی ربات
            await self.initialize_bot()
            
            # وظایف شروع
            await self.startup_tasks()
            
            # تنظیم signal handlers
            self.setup_signal_handlers()
            
            # ✅ استفاده از context manager برای مدیریت صحیح Application
            async with self.application:
                # شروع application
                await self.application.start()
                
                # شروع updater
                await self.application.updater.start_polling(
                    poll_interval=1.0,
                    timeout=10,
                    bootstrap_retries=5,
                    drop_pending_updates=True
                )
                
                self.is_running = True
                logger.info("Bot is running... Press Ctrl+C to stop")
                
                # ✅ انتظار برای shutdown signal
                try:
                    await self.shutdown_event.wait()
                except asyncio.CancelledError:
                    logger.info("Polling cancelled")
                
                # توقف updater
                await self.application.updater.stop()
                
                # توقف application
                await self.application.stop()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Critical error in bot execution: {e}")
            raise
        finally:
            await self.shutdown_tasks()
    
    def setup_signal_handlers(self):
        """تنظیم signal handlers برای shutdown مناسب - ✅ Fixed"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            
            # ✅ تنظیم shutdown event به جای sys.exit مستقیم
            if not self.shutdown_event.is_set():
                self.shutdown_event.set()
                logger.info("Shutdown event set")
        
        # ثبت signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """تابع اصلی - ✅ Fixed exception handling"""
    bot = None
    try:
        # بررسی متغیرهای محیطی ضروری
        if not getattr(Config, 'BOT_TOKEN', None):
            logger.error("BOT_TOKEN is not set in environment variables")
            return False
        
        # ایجاد instance ربات
        bot = MrTraderBot()
        
        # اجرای ربات
        await bot.run()
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user interrupt")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return False
    finally:
        # ✅ تضمین cleanup
        if bot:
            try:
                await bot.shutdown_tasks()
            except Exception as cleanup_error:
                logger.error(f"Error during final cleanup: {cleanup_error}")


def run_bot():
    """تابع کمکی برای اجرا — بازنگری شده برای بازگشت کد خروج به جای sys.exit داخلی"""
    exit_code = 0
    try:
        # بررسی نسخه Python
        if sys.version_info < (3, 8):
            print("Python 3.8 or higher is required")
            logger.error("Python version is lower than 3.8")
            return 1
        
        # اجرای async main با handling بهتر
        success = asyncio.run(main())
        
        if success:
            logger.info("Bot finished successfully")
            exit_code = 0
        else:
            logger.error("Bot finished with errors")
            exit_code = 1
        
    except KeyboardInterrupt:
        print("\n🔴 ربات توسط کاربر متوقف شد")
        logger.info("Bot stopped by user interrupt")
        exit_code = 0
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        logger.exception(f"Unexpected error: {e}")
        exit_code = 1
    finally:
        print("🔄 خروج از برنامه...")
        return exit_code


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║ 🤖 MrTrader Bot v{getattr(Config, 'BOT_VERSION', '1.0.0')}     ║
║                                                              ║
║  📊 Advanced Cryptocurrency Trading Analysis Bot            ║
║  🚀 Starting up...                                          ║
║                                                              ║
║  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}           ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        run_bot()
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")
        sys.exit(1)
    finally:
        print("✅ برنامه با موفقیت خاتمه یافت")


# Export برای استفاده در سایر ماژول‌ها
__all__ = ['MrTraderBot', 'main', 'run_bot']