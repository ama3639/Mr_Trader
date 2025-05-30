"""
هندلرهای ادمین برای MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.constants import ParseMode
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime, timedelta

from core.config import Config
from utils.logger import logger, log_admin_action
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.security_manager import SecurityManager
from managers.payment_manager import PaymentManager
from managers.referral_manager import ReferralManager
from managers.report_manager import ReportManager
from managers.backup_manager import BackupManager
from managers.message_manager import MessageManager
from utils.time_manager import TimeManager
from utils.formatters import NumberFormatter, DateTimeFormatter, ReportFormatter
from utils.validators import TelegramValidator, ComprehensiveValidator


# States برای ConversationHandler
(WAITING_USER_ID, WAITING_BROADCAST_MESSAGE, WAITING_ADMIN_COMMAND, 
 WAITING_BACKUP_CONFIRM, WAITING_USER_ACTION) = range(5)


class AdminHandler:
    """هندلر عملیات ادمین"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.admin_manager = AdminManager()
        self.security_manager = SecurityManager()
        self.payment_manager = PaymentManager()
        self.referral_manager = ReferralManager()
        self.report_manager = ReportManager()
        self.backup_manager = BackupManager()
        self.message_manager = MessageManager()
        self.time_manager = TimeManager()
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """کامند /admin - ورود به پنل ادمین"""
        try:
            user = update.effective_user
            
            # بررسی ادمین بودن
            if not await self.admin_manager.is_admin(user.id):
                await update.message.reply_text("❌ شما مجوز دسترسی به این بخش را ندارید.")
                return
            
            # لاگ ورود ادمین
            log_admin_action(user.id, "admin_panel_access", "Admin accessed panel")
            
            # نمایش پنل ادمین
            await self._show_admin_panel(update, context)
            
        except Exception as e:
            logger.error(f"Error in admin command: {e}")
            await update.message.reply_text("❌ خطا در دسترسی به پنل ادمین.")
    
    async def _show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل ادمین اصلی"""
        try:
            # دریافت آمار کلی
            stats = await self._get_admin_stats()
            
            panel_message = f"""
🛠️ <b>پنل مدیریت MrTrader Bot</b>

📊 <b>آمار کلی:</b>
👥 کاربران کل: {NumberFormatter.format_number_persian(stats['total_users'])}
🟢 کاربران فعال: {NumberFormatter.format_number_persian(stats['active_users'])}
🆕 کاربران جدید امروز: {NumberFormatter.format_number_persian(stats['new_users_today'])}
💰 درآمد ماهانه: ${NumberFormatter.format_number_persian(stats['monthly_revenue'])}

🕐 آخرین بروزرسانی: {self.time_manager.get_current_time_persian()}
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                    InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")
                ],
                [
                    InlineKeyboardButton("💰 مدیریت پرداخت", callback_data="admin_payments"),
                    InlineKeyboardButton("🎁 مدیریت رفرال", callback_data="admin_referrals")
                ],
                [
                    InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
                    InlineKeyboardButton("📋 گزارش‌ها", callback_data="admin_reports")
                ],
                [
                    InlineKeyboardButton("🔒 امنیت", callback_data="admin_security"),
                    InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات سیستم", callback_data="admin_settings"),
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_refresh")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    panel_message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    panel_message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                
        except Exception as e:
            logger.error(f"Error showing admin panel: {e}")
    
    async def _get_admin_stats(self) -> Dict[str, int]:
        """دریافت آمار برای پنل ادمین"""
        try:
            stats = {
                'total_users': await self.user_manager.get_total_users_count(),
                'active_users': await self.user_manager.get_active_users_count(),
                'new_users_today': await self.user_manager.get_new_users_today_count(),
                'monthly_revenue': await self.payment_manager.get_monthly_revenue()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {'total_users': 0, 'active_users': 0, 'new_users_today': 0, 'monthly_revenue': 0}
    
    # =========================
    # مدیریت کاربران
    # =========================
    
    async def handle_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت کاربران"""
        try:
            query = update.callback_query
            await query.answer()
            
            message = """
👥 <b>مدیریت کاربران</b>

یکی از گزینه‌های زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="admin_list_users")
                ],
                [
                    InlineKeyboardButton("🚫 کاربران مسدود", callback_data="admin_blocked_users"),
                    InlineKeyboardButton("⭐ کاربران VIP", callback_data="admin_vip_users")
                ],
                [
                    InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_user_stats"),
                    InlineKeyboardButton("🆕 کاربران جدید", callback_data="admin_new_users")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in user management: {e}")
    
    async def handle_search_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع جستجوی کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "🔍 <b>جستجوی کاربر</b>\n\n"
                "شناسه تلگرام کاربر را وارد کنید:\n"
                "مثال: 123456789\n\n"
                "برای لغو: /cancel",
                parse_mode=ParseMode.HTML
            )
            
            return WAITING_USER_ID
            
        except Exception as e:
            logger.error(f"Error in search user: {e}")
            return ConversationHandler.END
    
    async def process_user_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش جستجوی کاربر"""
        try:
            user_input = update.message.text.strip()
            
            # اعتبارسنجی شناسه
            if not TelegramValidator.validate_telegram_id(user_input):
                await update.message.reply_text(
                    "❌ شناسه تلگرام نامعتبر است.\n"
                    "لطفاً یک عدد صحیح وارد کنید."
                )
                return WAITING_USER_ID
            
            user_id = int(user_input)
            
            # جستجوی کاربر
            user_data = await self.user_manager.get_user_by_telegram_id(user_id)
            
            if not user_data:
                await update.message.reply_text(
                    f"❌ کاربری با شناسه {user_id} یافت نشد."
                )
                return ConversationHandler.END
            
            # نمایش اطلاعات کاربر
            await self._show_user_details(update, context, user_data)
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error processing user search: {e}")
            await update.message.reply_text("❌ خطا در جستجوی کاربر.")
            return ConversationHandler.END
    
    async def _show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: Dict[str, Any]):
        """نمایش جزئیات کاربر"""
        try:
            user_info = f"""
👤 <b>اطلاعات کاربر</b>

🆔 <b>شناسه:</b> <code>{user_data.get('telegram_id')}</code>
👤 <b>نام:</b> {user_data.get('first_name', 'نامشخص')}
📝 <b>نام کاربری:</b> @{user_data.get('username', 'ندارد')}
📦 <b>پکیج:</b> {user_data.get('package_type', 'رایگان')}
📅 <b>تاریخ عضویت:</b> {DateTimeFormatter.format_date_persian(user_data.get('registration_date'))}
🕐 <b>آخرین فعالیت:</b> {DateTimeFormatter.format_datetime_persian(user_data.get('last_activity'))}
⭐ <b>امتیاز:</b> {NumberFormatter.format_number_persian(user_data.get('user_points', 0))}
🚫 <b>وضعیت:</b> {'مسدود' if user_data.get('is_blocked') else 'فعال'}

📊 <b>آمار:</b>
• سیگنال‌های دریافتی: {user_data.get('total_signals_received', 0)}
• معاملات موفق: {user_data.get('successful_trades', 0)}
• معاملات ناموفق: {user_data.get('failed_trades', 0)}
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🚫 مسدود کردن" if not user_data.get('is_blocked') else "✅ رفع مسدودی", 
                                       callback_data=f"admin_toggle_block:{user_data['telegram_id']}"),
                    InlineKeyboardButton("⭐ تغییر پکیج", callback_data=f"admin_change_package:{user_data['telegram_id']}")
                ],
                [
                    InlineKeyboardButton("💰 اضافه کردن امتیاز", callback_data=f"admin_add_points:{user_data['telegram_id']}"),
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data=f"admin_user_details:{user_data['telegram_id']}")
                ],
                [
                    InlineKeyboardButton("💬 ارسال پیام", callback_data=f"admin_message_user:{user_data['telegram_id']}"),
                    InlineKeyboardButton("🗑️ حذف کاربر", callback_data=f"admin_delete_user:{user_data['telegram_id']}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users")
                ]
            ]
            
            await update.message.reply_text(
                user_info,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing user details: {e}")
    
    # =========================
    # پیام همگانی
    # =========================
    
    async def handle_broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ارسال پیام همگانی"""
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "📢 <b>ارسال پیام همگانی</b>\n\n"
                "پیام خود را بنویسید:\n"
                "• می‌توانید از HTML formatting استفاده کنید\n"
                "• تصویر، ویدیو یا فایل هم ضمیمه کنید\n\n"
                "برای لغو: /cancel",
                parse_mode=ParseMode.HTML
            )
            
            return WAITING_BROADCAST_MESSAGE
            
        except Exception as e:
            logger.error(f"Error starting broadcast: {e}")
            return ConversationHandler.END
    
    async def process_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام همگانی"""
        try:
            admin = update.effective_user
            message_text = update.message.text or update.message.caption or ""
            
            if len(message_text.strip()) == 0:
                await update.message.reply_text(
                    "❌ پیام نمی‌تواند خالی باشد.\n"
                    "لطفاً پیام خود را بنویسید."
                )
                return WAITING_BROADCAST_MESSAGE
            
            # تأیید ارسال
            confirm_message = f"""
📢 <b>تأیید ارسال پیام همگانی</b>

<b>پیام شما:</b>
{message_text[:200]}{'...' if len(message_text) > 200 else ''}

آیا مطمئن هستید که این پیام به همه کاربران ارسال شود؟
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ تأیید ارسال", callback_data="admin_confirm_broadcast"),
                    InlineKeyboardButton("❌ لغو", callback_data="admin_cancel_broadcast")
                ]
            ]
            
            # ذخیره پیام در context
            context.user_data['broadcast_message'] = message_text
            context.user_data['broadcast_media'] = None
            
            # اگر پیام شامل رسانه باشد
            if update.message.photo:
                context.user_data['broadcast_media'] = {
                    'type': 'photo',
                    'file_id': update.message.photo[-1].file_id
                }
            elif update.message.video:
                context.user_data['broadcast_media'] = {
                    'type': 'video',
                    'file_id': update.message.video.file_id
                }
            elif update.message.document:
                context.user_data['broadcast_media'] = {
                    'type': 'document',
                    'file_id': update.message.document.file_id
                }
            
            await update.message.reply_text(
                confirm_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error processing broadcast message: {e}")
            await update.message.reply_text("❌ خطا در پردازش پیام.")
            return ConversationHandler.END
    
    async def handle_broadcast_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید و ارسال پیام همگانی"""
        try:
            query = update.callback_query
            await query.answer()
            
            admin = query.from_user
            message_text = context.user_data.get('broadcast_message', '')
            media_data = context.user_data.get('broadcast_media')
            
            if not message_text:
                await query.edit_message_text("❌ پیام یافت نشد.")
                return
            
            # شروع ارسال
            await query.edit_message_text(
                "📤 <b>در حال ارسال پیام همگانی...</b>\n\n"
                "لطفاً صبر کنید...",
                parse_mode=ParseMode.HTML
            )
            
            # ارسال پیام همگانی
            result = await self.message_manager.send_broadcast_message(
                message_text=message_text,
                media_data=media_data,
                admin_id=admin.id
            )
            
            # لاگ عملیات
            log_admin_action(admin.id, "broadcast_message", f"Sent to {result['sent']} users")
            
            # نمایش نتیجه
            result_message = f"""
✅ <b>ارسال پیام همگانی تکمیل شد</b>

📊 <b>آمار ارسال:</b>
✅ موفق: {result['sent']}
❌ ناموفق: {result['failed']}
👥 کل کاربران: {result['total']}

⏱️ <b>زمان ارسال:</b> {DateTimeFormatter.format_datetime_persian(datetime.now())}
"""
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="admin_panel")]]
            
            await query.edit_message_text(
                result_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error confirming broadcast: {e}")
            await query.edit_message_text("❌ خطا در ارسال پیام همگانی.")
    
    # =========================
    # گزارش‌ها و آمار
    # =========================
    
    async def handle_admin_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت گزارش‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            message = """
📋 <b>گزارش‌ها و آمار</b>

یکی از گزینه‌های زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 گزارش روزانه", callback_data="admin_daily_report"),
                    InlineKeyboardButton("📈 گزارش هفتگی", callback_data="admin_weekly_report")
                ],
                [
                    InlineKeyboardButton("💰 گزارش مالی", callback_data="admin_financial_report"),
                    InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_detailed_user_stats")
                ],
                [
                    InlineKeyboardButton("📊 آمار سیگنال‌ها", callback_data="admin_signal_stats"),
                    InlineKeyboardButton("🎁 آمار رفرال", callback_data="admin_referral_stats")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in admin reports: {e}")
    
    async def handle_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش روزانه"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت داده‌های گزارش
            report_data = await self.report_manager.generate_daily_report()
            
            # فرمت‌بندی گزارش
            report_text = ReportFormatter.format_daily_report(report_data)
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports")]]
            
            await query.edit_message_text(
                report_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            await query.edit_message_text("❌ خطا در تولید گزارش روزانه.")
    
    # =========================
    # بکاپ و تنظیمات
    # =========================
    
    async def handle_backup_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت بکاپ"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آخرین بکاپ
            last_backup = await self.backup_manager.get_last_backup_info()
            last_backup_str = DateTimeFormatter.format_datetime_persian(last_backup) if last_backup else "هرگز"
            
            message = f"""
💾 <b>مدیریت پشتیبان‌گیری</b>

📅 <b>آخرین بکاپ:</b> {last_backup_str}
💿 <b>فضای استفاده شده:</b> {self.backup_manager.get_backup_size_info()}

یکی از گزینه‌های زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 بکاپ فوری", callback_data="admin_create_backup"),
                    InlineKeyboardButton("📋 لیست بکاپ‌ها", callback_data="admin_list_backups")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات بکاپ", callback_data="admin_backup_settings"),
                    InlineKeyboardButton("🗑️ پاک‌سازی", callback_data="admin_cleanup_backups")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in backup management: {e}")
    
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n\n"
            "برای بازگشت به پنل ادمین: /admin"
        )
        return ConversationHandler.END
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            # کامند ادمین
            CommandHandler("admin", self.admin_command),
            
            # ConversationHandler برای جستجوی کاربر
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.handle_search_user, pattern="^admin_search_user$")],
                states={
                    WAITING_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_user_search)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel_operation)],
            ),
            
            # ConversationHandler برای پیام همگانی
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.handle_broadcast_start, pattern="^admin_broadcast$")],
                states={
                    WAITING_BROADCAST_MESSAGE: [MessageHandler(
                        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.DOCUMENT, 
                        self.process_broadcast_message
                    )],
                },
                fallbacks=[CommandHandler("cancel", self.cancel_operation)],
            ),
            
            # Callback handlers
            CallbackQueryHandler(self._show_admin_panel, pattern="^admin_panel$"),
            CallbackQueryHandler(self.handle_user_management, pattern="^admin_users$"),
            CallbackQueryHandler(self.handle_admin_reports, pattern="^admin_reports$"),
            CallbackQueryHandler(self.handle_daily_report, pattern="^admin_daily_report$"),
            CallbackQueryHandler(self.handle_backup_management, pattern="^admin_backup$"),
            CallbackQueryHandler(self.handle_broadcast_confirm, pattern="^admin_confirm_broadcast$"),
        ]


# Export
__all__ = ['AdminHandler']