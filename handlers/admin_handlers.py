"""
هندلرهای مدیریتی - مدیریت دسترسی‌های ادمین
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Any, Optional

from core.config import Config
from managers.admin_manager import AdminManager
from managers.user_manager import UserManager
from managers.backup_manager import BackupManager
from managers.report_manager import ReportManager
from managers.security_manager import SecurityManager
from utils.logger import UserLogger, AdminLogger
from utils.time_manager import TimeManager
from utils.validators import Validators, ValidationError

# States for conversation handlers
ADMIN_WAITING_USER_ID = 1
ADMIN_WAITING_MESSAGE = 2
ADMIN_WAITING_PACKAGE = 3
ADMIN_WAITING_DURATION = 4

class AdminHandlers:
    """کلاس هندلرهای مدیریتی"""
    
    @staticmethod
    async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل مدیریت"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # بررسی دسترسی ادمین
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ شما دسترسی ادمین ندارید!", show_alert=True)
                return
            
            # آمار کلی
            stats = AdminManager.get_admin_stats()
            
            admin_text = (
                f"🔧 **پنل مدیریت MrTrader Bot**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 **آمار کلی:**\n"
                f"👥 کل کاربران: `{stats['total_users']:,}`\n"
                f"✅ کاربران فعال: `{stats['active_users']:,}`\n"
                f"💎 کاربران VIP: `{stats['vip_users']:,}`\n"
                f"📈 درخواست‌های امروز: `{stats['today_requests']:,}`\n"
                f"💰 درآمد این ماه: `${stats['monthly_revenue']:,.2f}`\n\n"
                f"🕒 آخرین به‌روزرسانی: `{TimeManager.to_shamsi(datetime.now())}`"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                    InlineKeyboardButton("📊 گزارش‌ها", callback_data="admin_reports")
                ],
                [
                    InlineKeyboardButton("💰 مدیریت پکیج‌ها", callback_data="admin_packages"),
                    InlineKeyboardButton("🔒 امنیت", callback_data="admin_security")
                ],
                [
                    InlineKeyboardButton("📤 ارسال پیام گروهی", callback_data="admin_broadcast"),
                    InlineKeyboardButton("🔧 تنظیمات", callback_data="admin_settings")
                ],
                [
                    InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup"),
                    InlineKeyboardButton("📋 لاگ‌ها", callback_data="admin_logs")
                ],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                admin_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # ثبت لاگ دسترسی ادمین
            AdminLogger.log_admin_action(user_id, "admin_panel_access", "دسترسی به پنل مدیریت")
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_panel: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش پنل مدیریت. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ])
            )
    
    @staticmethod
    async def admin_users_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت کاربران"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # آمار کاربران
            user_stats = UserManager.get_user_statistics()
            
            users_text = (
                f"👥 **مدیریت کاربران**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📈 **آمار کاربران:**\n"
                f"🆔 کل کاربران: `{user_stats['total']:,}`\n"
                f"🟢 فعال امروز: `{user_stats['active_today']:,}`\n"
                f"🟡 فعال این هفته: `{user_stats['active_week']:,}`\n"
                f"🆕 عضو جدید امروز: `{user_stats['new_today']:,}`\n"
                f"💎 VIP فعال: `{user_stats['vip_active']:,}`\n"
                f"⏸ معلق شده: `{user_stats['suspended']:,}`\n\n"
                f"⚡ **اقدامات سریع:**"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
                    InlineKeyboardButton("👤 اطلاعات کاربر", callback_data="admin_user_info")
                ],
                [
                    InlineKeyboardButton("🎁 اعطای پکیج", callback_data="admin_grant_package"),
                    InlineKeyboardButton("⛔ مسدود کردن", callback_data="admin_ban_user")
                ],
                [
                    InlineKeyboardButton("📋 لیست VIP ها", callback_data="admin_vip_list"),
                    InlineKeyboardButton("🔓 رفع مسدودیت", callback_data="admin_unban_user")
                ],
                [
                    InlineKeyboardButton("📊 گزارش کاربران", callback_data="admin_users_report"),
                    InlineKeyboardButton("💸 تخفیف ویژه", callback_data="admin_special_discount")
                ],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="admin_panel")]
            ]
            
            await query.edit_message_text(
                users_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_users_management: {e}")
            await query.edit_message_text("❌ خطا در نمایش مدیریت کاربران")
    
    @staticmethod
    async def admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش‌های مدیریتی"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return
            
            reports_text = (
                f"📊 **گزارش‌های مدیریتی**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📈 **گزارش‌های موجود:**\n"
                f"انتخاب نوع گزارش مورد نظر:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📈 گزارش فروش", callback_data="admin_sales_report"),
                    InlineKeyboardButton("👥 گزارش کاربران", callback_data="admin_users_report")
                ],
                [
                    InlineKeyboardButton("📊 آمار استراتژی‌ها", callback_data="admin_strategies_report"),
                    InlineKeyboardButton("💰 گزارش درآمد", callback_data="admin_revenue_report")
                ],
                [
                    InlineKeyboardButton("🔄 گزارش فعالیت", callback_data="admin_activity_report"),
                    InlineKeyboardButton("⚠️ گزارش خطاها", callback_data="admin_errors_report")
                ],
                [
                    InlineKeyboardButton("📅 گزارش روزانه", callback_data="admin_daily_report"),
                    InlineKeyboardButton("📊 گزارش ماهانه", callback_data="admin_monthly_report")
                ],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="admin_panel")]
            ]
            
            await query.edit_message_text(
                reports_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_reports: {e}")
    
    @staticmethod
    async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ارسال پیام گروهی"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return
            
            broadcast_text = (
                f"📤 **ارسال پیام گروهی**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 لطفاً متن پیام خود را ارسال کنید:\n\n"
                f"⚠️ **توجه:**\n"
                f"• پیام برای همه کاربران ارسال خواهد شد\n"
                f"• از markdown استفاده کنید\n"
                f"• دقت کنید پیام مناسب باشد\n\n"
                f"برای لغو، روی دکمه لغو کلیک کنید."
            )
            
            keyboard = [
                [InlineKeyboardButton("❌ لغو", callback_data="admin_panel")]
            ]
            
            await query.edit_message_text(
                broadcast_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # ذخیره وضعیت در context
            context.user_data['admin_action'] = 'broadcast'
            
            return ADMIN_WAITING_MESSAGE
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_broadcast_start: {e}")
    
    @staticmethod
    async def admin_grant_package_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع اعطای پکیج"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return
            
            grant_text = (
                f"🎁 **اعطای پکیج رایگان**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 لطفاً شناسه کاربر (User ID) را ارسال کنید:\n\n"
                f"مثال: `123456789`\n\n"
                f"⚠️ شناسه باید دقیق باشد."
            )
            
            keyboard = [
                [InlineKeyboardButton("❌ لغو", callback_data="admin_users")]
            ]
            
            await query.edit_message_text(
                grant_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            context.user_data['admin_action'] = 'grant_package'
            
            return ADMIN_WAITING_USER_ID
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_grant_package_start: {e}")
    
    @staticmethod
    async def handle_admin_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش شناسه کاربر"""
        message = update.message
        admin_id = message.from_user.id
        
        try:
            if not AdminManager.is_admin(admin_id):
                await message.reply_text("⛔ دسترسی غیرمجاز!")
                return ConversationHandler.END
            
            # اعتبارسنجی شناسه کاربر
            try:
                target_user_id = Validators.validate_user_id(message.text)
            except ValidationError as e:
                await message.reply_text(f"❌ {e.message}\nلطفاً شناسه معتبر ارسال کنید.")
                return ADMIN_WAITING_USER_ID
            
            # بررسی وجود کاربر
            if not UserManager.user_exists(target_user_id):
                await message.reply_text(
                    f"❌ کاربر با شناسه `{target_user_id}` یافت نشد.\n"
                    f"لطفاً شناسه صحیح ارسال کنید.",
                    parse_mode="Markdown"
                )
                return ADMIN_WAITING_USER_ID
            
            # دریافت اطلاعات کاربر
            user_info = UserManager.get_user(target_user_id)
            
            if context.user_data.get('admin_action') == 'grant_package':
                # ذخیره شناسه کاربر و نمایش انتخاب پکیج
                context.user_data['target_user_id'] = target_user_id
                
                package_text = (
                    f"🎁 **اعطای پکیج به کاربر**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 **کاربر انتخابی:**\n"
                    f"🆔 شناسه: `{target_user_id}`\n"
                    f"👤 نام: `{user_info.get('full_name', 'نامشخص')}`\n"
                    f"📦 پکیج فعلی: `{user_info.get('current_package', 'Free')}`\n\n"
                    f"📦 **انتخاب پکیج جدید:**"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🥉 Basic", callback_data="admin_pkg_basic"),
                        InlineKeyboardButton("🥈 Premium", callback_data="admin_pkg_premium")
                    ],
                    [
                        InlineKeyboardButton("🥇 VIP", callback_data="admin_pkg_vip"),
                        InlineKeyboardButton("👻 Ghost", callback_data="admin_pkg_ghost")
                    ],
                    [InlineKeyboardButton("❌ لغو", callback_data="admin_users")]
                ]
                
                await message.reply_text(
                    package_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                
                return ADMIN_WAITING_PACKAGE
            
        except Exception as e:
            UserLogger.log_error(admin_id, f"Error in handle_admin_user_id: {e}")
            await message.reply_text("❌ خطا در پردازش. لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END
    
    @staticmethod
    async def handle_admin_package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب پکیج"""
        query = update.callback_query
        admin_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(admin_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return ConversationHandler.END
            
            # استخراج نوع پکیج
            package_type = query.data.replace('admin_pkg_', '')
            target_user_id = context.user_data.get('target_user_id')
            
            if not target_user_id:
                await query.edit_message_text("❌ خطا: شناسه کاربر یافت نشد")
                return ConversationHandler.END
            
            # ذخیره نوع پکیج و نمایش انتخاب مدت
            context.user_data['selected_package'] = package_type
            
            duration_text = (
                f"⏱ **انتخاب مدت پکیج**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 پکیج: `{package_type.upper()}`\n"
                f"👤 کاربر: `{target_user_id}`\n\n"
                f"⏰ **مدت زمان پکیج:**"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 1 ماه", callback_data="admin_dur_monthly"),
                    InlineKeyboardButton("📅 3 ماه", callback_data="admin_dur_quarterly")
                ],
                [
                    InlineKeyboardButton("📅 1 سال", callback_data="admin_dur_yearly"),
                    InlineKeyboardButton("♾ مادام‌العمر", callback_data="admin_dur_lifetime")
                ],
                [InlineKeyboardButton("❌ لغو", callback_data="admin_users")]
            ]
            
            await query.edit_message_text(
                duration_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return ADMIN_WAITING_DURATION
            
        except Exception as e:
            UserLogger.log_error(admin_id, f"Error in handle_admin_package_selection: {e}")
            await query.edit_message_text("❌ خطا در انتخاب پکیج")
            return ConversationHandler.END
    
    @staticmethod
    async def handle_admin_duration_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب مدت پکیج"""
        query = update.callback_query
        admin_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(admin_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return ConversationHandler.END
            
            # استخراج اطلاعات
            duration = query.data.replace('admin_dur_', '')
            target_user_id = context.user_data.get('target_user_id')
            package_type = context.user_data.get('selected_package')
            
            if not all([target_user_id, package_type, duration]):
                await query.edit_message_text("❌ خطا: اطلاعات ناقص")
                return ConversationHandler.END
            
            # اعطای پکیج
            success = AdminManager.grant_package_to_user(
                admin_id=admin_id,
                target_user_id=target_user_id,
                package_type=package_type,
                duration=duration
            )
            
            if success:
                # ارسال اطلاعیه به کاربر
                try:
                    package_names = {
                        'basic': 'پایه',
                        'premium': 'ویژه', 
                        'vip': 'VIP',
                        'ghost': 'شبح'
                    }
                    
                    duration_names = {
                        'monthly': '1 ماهه',
                        'quarterly': '3 ماهه',
                        'yearly': '1 ساله',
                        'lifetime': 'مادام‌العمر'
                    }
                    
                    notification_text = (
                        f"🎉 **تبریک! پکیج رایگان دریافت کردید**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"📦 **پکیج اعطایی:** {package_names.get(package_type, package_type)}\n"
                        f"⏰ **مدت زمان:** {duration_names.get(duration, duration)}\n"
                        f"🕒 **زمان فعال‌سازی:** {TimeManager.to_shamsi(datetime.now())}\n\n"
                        f"✨ از امکانات جدید لذت ببرید!"
                    )
                    
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=notification_text,
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass  # اگر ارسال به کاربر ممکن نباشد
                
                # پیام موفقیت برای ادمین
                success_text = (
                    f"✅ **پکیج با موفقیت اعطا شد**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 کاربر: `{target_user_id}`\n"
                    f"📦 پکیج: `{package_type.upper()}`\n"
                    f"⏰ مدت: `{duration}`\n"
                    f"🕒 زمان: `{TimeManager.to_shamsi(datetime.now())}`\n\n"
                    f"📤 اطلاعیه به کاربر ارسال شد."
                )
                
                keyboard = [
                    [InlineKeyboardButton("🎁 اعطای پکیج دیگر", callback_data="admin_grant_package")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="admin_users")]
                ]
                
            else:
                success_text = (
                    f"❌ **خطا در اعطای پکیج**\n\n"
                    f"متأسفانه در فرآیند اعطای پکیج مشکلی پیش آمد.\n"
                    f"لطفاً دوباره تلاش کنید."
                )
                
                keyboard = [
                    [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="admin_grant_package")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="admin_users")]
                ]
            
            await query.edit_message_text(
                success_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # پاک کردن داده‌های موقت
            context.user_data.pop('admin_action', None)
            context.user_data.pop('target_user_id', None)
            context.user_data.pop('selected_package', None)
            
            return ConversationHandler.END
            
        except Exception as e:
            UserLogger.log_error(admin_id, f"Error in handle_admin_duration_selection: {e}")
            await query.edit_message_text("❌ خطا در تکمیل فرآیند")
            return ConversationHandler.END
    
    @staticmethod
    async def admin_backup_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت پشتیبان‌گیری"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            if not AdminManager.is_admin(user_id):
                await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # اطلاعات آخرین پشتیبان‌گیری
            last_backup = BackupManager.get_last_backup_info()
            
            backup_text = (
                f"💾 **مدیریت پشتیبان‌گیری**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📅 **آخرین پشتیبان‌گیری:**\n"
                f"🕒 زمان: `{last_backup.get('date', 'هرگز')}`\n"
                f"📦 اندازه: `{last_backup.get('size', 'نامشخص')}`\n"
                f"✅ وضعیت: `{last_backup.get('status', 'نامشخص')}`\n\n"
                f"🔧 **عملیات پشتیبان‌گیری:**"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("💾 پشتیبان‌گیری فوری", callback_data="admin_backup_now"),
                    InlineKeyboardButton("📋 لیست پشتیبان‌ها", callback_data="admin_backup_list")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_backup_settings"),
                    InlineKeyboardButton("🔄 بازیابی", callback_data="admin_restore")
                ],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="admin_panel")]
            ]
            
            await query.edit_message_text(
                backup_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in admin_backup_management: {e}")
    
    @staticmethod
    async def cancel_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات ادمین"""
        query = update.callback_query
        
        # پاک کردن داده‌های موقت
        context.user_data.pop('admin_action', None)
        context.user_data.pop('target_user_id', None)
        context.user_data.pop('selected_package', None)
        
        await query.answer("عملیات لغو شد")
        return ConversationHandler.END

# ایجاد conversation handler برای عملیات ادمین
def build_admin_conversation_handler():
    """ایجاد conversation handler برای عملیات مدیریتی"""
    from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(AdminHandlers.admin_broadcast_start, pattern="^admin_broadcast$"),
            CallbackQueryHandler(AdminHandlers.admin_grant_package_start, pattern="^admin_grant_package$"),
        ],
        states={
            ADMIN_WAITING_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.handle_admin_user_id)
            ],
            ADMIN_WAITING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.handle_broadcast_message)
            ],
            ADMIN_WAITING_PACKAGE: [
                CallbackQueryHandler(AdminHandlers.handle_admin_package_selection, pattern="^admin_pkg_")
            ],
            ADMIN_WAITING_DURATION: [
                CallbackQueryHandler(AdminHandlers.handle_admin_duration_selection, pattern="^admin_dur_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(AdminHandlers.cancel_admin_action, pattern="^admin_(panel|users)$"),
            CallbackQueryHandler(AdminHandlers.cancel_admin_action, pattern="^main_menu$")
        ],
        name="admin_operations",
        persistent=True
    )
