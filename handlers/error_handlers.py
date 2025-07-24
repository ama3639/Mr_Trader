"""
مدیریت خطاها و exception handling برای MrTrader Bot
"""
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import NetworkError, TimedOut, BadRequest, Forbidden, ChatMigrated

from core.config import Config
from utils.logger import logger, log_error, log_security_event
from managers.admin_manager import AdminManager
from managers.message_manager import MessageManager
from managers.security_manager import SecurityManager
from utils.formatters import DateTimeFormatter


class ErrorHandler:
    """کلاس مدیریت خطاها"""
    
    def __init__(self):
        self.admin_manager = AdminManager()
        self.message_manager = MessageManager()
        self.security_manager = SecurityManager()
        self.error_count = {}  # شمارش خطاها برای هر کاربر
    
    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
        """هندلر اصلی مدیریت خطاها"""
        try:
            error = context.error
            
            # دریافت اطلاعات کاربر
            user_id = None
            username = None
            if update and update.effective_user:
                user_id = update.effective_user.id
                username = update.effective_user.username
            
            # لاگ خطا
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'user_id': user_id,
                'username': username,
                'update_info': str(update) if update else None,
                'timestamp': datetime.now().isoformat()
            }
            
            log_error(error, context="error_handler", user_id=user_id or 0)
            
            # شمارش خطاها برای کاربر
            if user_id:
                self.error_count[user_id] = self.error_count.get(user_id, 0) + 1
                
                # اگر کاربر خطاهای زیادی داشته باشد
                if self.error_count[user_id] > 10:
                    await self.security_manager.flag_suspicious_activity(
                        user_id, 
                        "excessive_errors", 
                        f"User generated {self.error_count[user_id]} errors"
                    )
            
            # مدیریت انواع مختلف خطا
            await self._handle_specific_error(error, update, context, error_info)
            
            # اطلاع‌رسانی به ادمین‌ها در خطاهای مهم
            if self._is_critical_error(error):
                await self._notify_admins_about_error(error_info, traceback.format_exc())
            
        except Exception as handler_error:
            # خطا در خود error handler
            logger.critical(f"Error in error handler: {handler_error}")
            print(f"CRITICAL: Error handler failed: {handler_error}")
    
    async def _handle_specific_error(self, error: Exception, update: Optional[Update], 
                                   context: ContextTypes.DEFAULT_TYPE, error_info: Dict[str, Any]):
        """مدیریت انواع خاص خطا"""
        try:
            error_type = type(error).__name__
            
            if isinstance(error, NetworkError):
                await self._handle_network_error(error, update, context)
            elif isinstance(error, TimedOut):
                await self._handle_timeout_error(error, update, context)
            elif isinstance(error, BadRequest):
                await self._handle_bad_request_error(error, update, context)
            elif isinstance(error, Forbidden):
                await self._handle_forbidden_error(error, update, context)
            elif isinstance(error, ChatMigrated):
                await self._handle_chat_migrated_error(error, update, context)
            elif "rate limit" in str(error).lower():
                await self._handle_rate_limit_error(error, update, context)
            else:
                await self._handle_generic_error(error, update, context)
                
        except Exception as e:
            logger.error(f"Error in specific error handling: {e}")
    
    async def _handle_network_error(self, error: NetworkError, update: Optional[Update], 
                                  context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای شبکه"""
        logger.warning(f"Network error: {error}")
        
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="🌐 مشکل در اتصال به شبکه.\nلطفاً چند لحظه صبر کنید و دوباره تلاش کنید."
                )
            except:
                pass  # اگر ارسال پیام هم ناموفق باشد
    
    async def _handle_timeout_error(self, error: TimedOut, update: Optional[Update], 
                                  context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای timeout"""
        logger.warning(f"Timeout error: {error}")
        
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="⏱️ درخواست شما زمان‌بر بود.\nلطفاً دوباره تلاش کنید."
                )
            except:
                pass
    
    async def _handle_bad_request_error(self, error: BadRequest, update: Optional[Update], 
                                      context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای Bad Request"""
        error_message = str(error).lower()
        
        if "message is not modified" in error_message:
            # پیام تغییری نکرده - نیازی به اقدام نیست
            return
        elif "message to delete not found" in error_message:
            # پیام برای حذف یافت نشد
            return
        elif "query is too old" in error_message:
            # callback query خیلی قدیمی است
            if update and update.callback_query:
                try:
                    await update.callback_query.answer("❌ درخواست منقضی شده است.")
                except:
                    pass
        else:
            logger.warning(f"Bad request error: {error}")
            
            if update and update.effective_user:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text="❌ درخواست نامعتبر.\nلطفاً دوباره تلاش کنید."
                    )
                except:
                    pass
    
    async def _handle_forbidden_error(self, error: Forbidden, update: Optional[Update], 
                                    context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای Forbidden"""
        if update and update.effective_user:
            user_id = update.effective_user.id
            
            # کاربر ربات را مسدود کرده
            logger.info(f"User {user_id} blocked the bot")
            
            # علامت‌گذاری کاربر به عنوان غیرفعال
            try:
                from managers.user_manager import UserManager
                user_manager = UserManager()
                await user_manager.mark_user_inactive(user_id, "bot_blocked")
            except Exception as e:
                logger.error(f"Error marking user inactive: {e}")
    
    async def _handle_chat_migrated_error(self, error: ChatMigrated, update: Optional[Update], 
                                        context: ContextTypes.DEFAULT_TYPE):
        """مدیریت مهاجرت چت"""
        new_chat_id = error.new_chat_id
        logger.info(f"Chat migrated to new ID: {new_chat_id}")
        
        # بروزرسانی chat_id در دیتابیس اگر نیاز باشد
        # این معمولاً برای گروه‌ها اتفاق می‌افتد
    
    async def _handle_rate_limit_error(self, error: Exception, update: Optional[Update], 
                                     context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای rate limit"""
        logger.warning(f"Rate limit error: {error}")
        
        if update and update.effective_user:
            user_id = update.effective_user.id
            
            # ثبت رویداد امنیتی
            log_security_event(
                "rate_limit_exceeded",
                user_id,
                details=f"User hit rate limit: {error}"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚫 شما درخواست‌های زیادی ارسال کرده‌اید.\n"
                         "لطفاً چند دقیقه صبر کنید."
                )
            except:
                pass
    
    async def _handle_generic_error(self, error: Exception, update: Optional[Update], 
                                  context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای عمومی"""
        logger.error(f"Generic error: {error}")
        
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ خطایی رخ داد.\nتیم فنی در حال بررسی موضوع است."
                )
            except:
                pass
    
    def _is_critical_error(self, error: Exception) -> bool:
        """بررسی اینکه آیا خطا مهم است و نیاز به اطلاع‌رسانی دارد"""
        critical_errors = [
            'DatabaseError',
            'ConnectionError',
            'ConfigurationError',
            'SecurityError',
            'PaymentError'
        ]
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # خطاهای مهم بر اساس نوع
        if error_type in critical_errors:
            return True
        
        # خطاهای مهم بر اساس پیام
        critical_keywords = [
            'database',
            'payment',
            'security',
            'authentication',
            'configuration',
            'memory',
            'disk space'
        ]
        
        return any(keyword in error_message for keyword in critical_keywords)
    
    async def _notify_admins_about_error(self, error_info: Dict[str, Any], traceback_str: str):
        """اطلاع‌رسانی خطاهای مهم به ادمین‌ها"""
        try:
            error_message = f"""
🚨 <b>خطای مهم در سیستم</b>

🕐 <b>زمان:</b> {DateTimeFormatter.format_datetime_persian(datetime.now())}
🔍 <b>نوع خطا:</b> {error_info['error_type']}
💬 <b>پیام خطا:</b> <code>{error_info['error_message']}</code>

👤 <b>کاربر:</b> {error_info['user_id']} (@{error_info['username']})

<b>جزئیات تکنیکی:</b>
<code>{traceback_str[:500]}...</code>

لطفاً هر چه سریع‌تر بررسی کنید.
"""
            
            # ارسال به ادمین‌ها
            admins = await self.admin_manager.get_all_admins()
            for admin in admins:
                try:
                    await self.message_manager.send_message_to_user(
                        admin['telegram_id'],
                        error_message,
                        parse_mode='HTML'
                    )
                except Exception as send_error:
                    logger.error(f"Failed to notify admin {admin['telegram_id']}: {send_error}")
            
        except Exception as e:
            logger.error(f"Error notifying admins: {e}")
    
    async def handle_callback_query_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای callback query"""
        try:
            if update.callback_query:
                await update.callback_query.answer(
                    "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                    show_alert=True
                )
        except Exception as e:
            logger.error(f"Error in callback query error handler: {e}")
    
    async def handle_message_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاهای پیام"""
        try:
            if update.message:
                await update.message.reply_text(
                    "❌ خطایی در پردازش پیام شما رخ داد.\n"
                    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
        except Exception as e:
            logger.error(f"Error in message error handler: {e}")
    
    def reset_error_count(self, user_id: int):
        """ریست کردن شمارش خطاهای کاربر"""
        if user_id in self.error_count:
            del self.error_count[user_id]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """دریافت آمار خطاها"""
        total_errors = sum(self.error_count.values())
        users_with_errors = len(self.error_count)
        
        return {
            'total_errors': total_errors,
            'users_with_errors': users_with_errors,
            'average_errors_per_user': total_errors / users_with_errors if users_with_errors > 0 else 0,
            'max_errors_by_user': max(self.error_count.values()) if self.error_count else 0
        }


class DatabaseErrorHandler:
    """مدیریت خطاهای دیتابیس"""
    
    @staticmethod
    async def handle_database_error(error: Exception, operation: str, context: str = ""):
        """مدیریت خطاهای دیتابیس"""
        logger.error(f"Database error in {operation}: {error}")
        
        # اگر خطای اتصال باشد
        if "connection" in str(error).lower():
            logger.critical("Database connection error - attempting reconnection")
            # در اینجا می‌توان تلاش برای اتصال مجدد کرد
        
        # اگر خطای کورپشن باشد
        elif "corrupt" in str(error).lower():
            logger.critical("Database corruption detected")
            # اطلاع‌رسانی فوری به ادمین‌ها


class APIErrorHandler:
    """مدیریت خطاهای API"""
    
    @staticmethod
    async def handle_api_error(error: Exception, endpoint: str, params: Dict = None):
        """مدیریت خطاهای API"""
        logger.error(f"API error at {endpoint}: {error}")
        
        # اگر API در دسترس نباشد
        if "timeout" in str(error).lower() or "connection" in str(error).lower():
            logger.warning(f"API {endpoint} is not accessible")
            # تعویض به API بکاپ یا کش
        
        # اگر rate limit باشد
        elif "rate limit" in str(error).lower():
            logger.warning(f"Rate limit hit for API {endpoint}")
            # اعمال تأخیر یا استفاده از API جایگزین


class SecurityErrorHandler:
    """مدیریت خطاهای امنیتی"""
    
    @staticmethod
    async def handle_security_error(error: Exception, user_id: int, action: str):
        """مدیریت خطاهای امنیتی"""
        logger.warning(f"Security error for user {user_id} in action {action}: {error}")
        
        # ثبت رویداد امنیتی
        log_security_event(
            "security_error",
            user_id,
            details=f"Action: {action}, Error: {str(error)}"
        )
        
        # اقدامات امنیتی اضافی در صورت نیاز
        # مثل مسدود کردن موقت کاربر


# سینگلتون Error Handler
error_handler_instance = ErrorHandler()

# توابع کمکی برای استفاده آسان
async def handle_error(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
    """تابع کمکی برای مدیریت خطا"""
    await error_handler_instance.handle_error(update, context)

async def handle_callback_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تابع کمکی برای خطاهای callback"""
    await error_handler_instance.handle_callback_query_error(update, context)

async def handle_message_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تابع کمکی برای خطاهای پیام"""
    await error_handler_instance.handle_message_error(update, context)


# Export
__all__ = [
    'ErrorHandler',
    'DatabaseErrorHandler', 
    'APIErrorHandler',
    'SecurityErrorHandler',
    'error_handler_instance',
    'handle_error',
    'handle_callback_error',
    'handle_message_error'
]