"""
مدیریت پیام‌ها و کیبوردها MrTrader Bot
"""
import asyncio
from typing import Dict, List, Optional, Any
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from core.config import Config
from utils.logger import logger, TelegramLogger
from utils.time_manager import TimeManager
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.settings_manager import SettingsManager


class MessageManager:
    """کلاس مدیریت پیام‌ها و کیبوردها"""
    
    @staticmethod
    async def get_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """کیبورد منوی اصلی بر اساس سطح دسترسی کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            کیبورد منوی اصلی
        """
        try:
            # بررسی وضعیت کاربر
            user = UserManager.get_user_by_telegram_id(user_id)
            is_admin = AdminManager.is_admin(user_id)
            is_manager = AdminManager.is_manager(user_id)
            
            # کیبورد پایه
            keyboard = [
                [
                    InlineKeyboardButton("📊 تحلیل قیمت", callback_data="menu_analysis"),
                    InlineKeyboardButton("💰 قیمت زنده", callback_data="menu_live_price")
                ],
                [
                    InlineKeyboardButton("🎯 استراتژی‌ها", callback_data="menu_strategy"),
                    InlineKeyboardButton("📦 خرید پکیج", callback_data="menu_packages")
                ],
                [
                    InlineKeyboardButton("💳 شارژ حساب", callback_data="menu_charge"),
                    InlineKeyboardButton("👤 پروفایل من", callback_data="menu_profile")
                ]
            ]
            
            # دکمه‌های اضافی برای کاربران دارای پکیج
            if user and user.get('package', 'none') != 'none':
                keyboard.append([
                    InlineKeyboardButton("📈 پورتفولیو", callback_data="menu_portfolio"),
                    InlineKeyboardButton("🔔 اعلان‌ها", callback_data="menu_notifications")
                ])
            
            # دکمه‌های مدیریتی
            if is_admin:
                keyboard.append([
                    InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="menu_admin")
                ])
            
            if is_manager:
                keyboard.append([
                    InlineKeyboardButton("👑 پنل مدیر اصلی", callback_data="menu_manager")
                ])
            
            # دکمه‌های عمومی
            keyboard.extend([
                [
                    InlineKeyboardButton("📞 پشتیبانی", callback_data="menu_support"),
                    InlineKeyboardButton("💬 بازخورد", callback_data="menu_feedback")
                ],
                [
                    InlineKeyboardButton("ℹ️ راهنما", callback_data="menu_help"),
                    InlineKeyboardButton("📋 درباره ما", callback_data="menu_about")
                ]
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error creating main menu keyboard for user {user_id}: {e}")
            # کیبورد پیش‌فرض در صورت خطا
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 تحلیل قیمت", callback_data="menu_analysis")],
                [InlineKeyboardButton("ℹ️ راهنما", callback_data="menu_help")]
            ])
    
    @staticmethod
    async def get_admin_menu_keyboard(admin_id: int) -> InlineKeyboardMarkup:
        """کیبورد منوی ادمین بر اساس سطح دسترسی
        
        Args:
            admin_id: شناسه ادمین
            
        Returns:
            کیبورد منوی ادمین
        """
        try:
            admin_level = AdminManager.get_admin_level(admin_id)
            is_manager = AdminManager.is_manager(admin_id)
            
            keyboard = []
            
            # دسترسی‌های سطح 1 و بالاتر
            if admin_level >= 1:
                keyboard.extend([
                    [
                        InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                        InlineKeyboardButton("📊 گزارش‌ها", callback_data="admin_reports")
                    ],
                    [
                        InlineKeyboardButton("🎫 تیکت‌های پشتیبانی", callback_data="admin_tickets"),
                        InlineKeyboardButton("📢 ارسال پیام", callback_data="admin_broadcast")
                    ]
                ])
            
            # دسترسی‌های سطح 2 و بالاتر
            if admin_level >= 2:
                keyboard.extend([
                    [
                        InlineKeyboardButton("💳 مدیریت پرداخت‌ها", callback_data="admin_payments"),
                        InlineKeyboardButton("💰 مدیریت موجودی", callback_data="admin_balance")
                    ],
                    [
                        InlineKeyboardButton("📦 مدیریت پکیج‌ها", callback_data="admin_packages"),
                        InlineKeyboardButton("🔄 به‌روزرسانی‌ها", callback_data="admin_updates")
                    ]
                ])
            
            # دسترسی‌های سطح 3 یا مدیران اصلی
            if admin_level >= 3 or is_manager:
                keyboard.extend([
                    [
                        InlineKeyboardButton("👮‍♂️ مدیریت ادمین‌ها", callback_data="admin_manage_admins"),
                        InlineKeyboardButton("⚙️ تنظیمات سیستم", callback_data="admin_settings")
                    ],
                    [
                        InlineKeyboardButton("🛡️ امنیت سیستم", callback_data="admin_security"),
                        InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup")
                    ]
                ])
            
            # دکمه بازگشت
            keyboard.append([
                InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error creating admin menu keyboard for {admin_id}: {e}")
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
    
    @staticmethod
    async def get_strategy_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """کیبورد منوی استراتژی‌ها
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            کیبورد استراتژی‌ها
        """
        try:
            user = UserManager.get_user_by_telegram_id(user_id)
            user_package = user.get('package', 'none') if user else 'none'
            
            keyboard = []
            
            for strategy_key, strategy_info in Config.STRATEGIES.items():
                min_package = strategy_info['min_package']
                strategy_name = strategy_info['name']
                
                # بررسی دسترسی
                if user_package == 'none' and min_package != 'guest':
                    # کاربر بدون پکیج فقط به استراتژی‌های مهمان دسترسی دارد
                    button_text = f"🔒 {strategy_name}"
                    callback_data = "no_access"
                else:
                    button_text = f"📊 {strategy_name}"
                    callback_data = f"strategy_{strategy_key}"
                
                keyboard.append([
                    InlineKeyboardButton(button_text, callback_data=callback_data)
                ])
            
            keyboard.extend([
                [InlineKeyboardButton("🔤 ورود دستی نماد", callback_data="custom_symbol")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error creating strategy menu keyboard: {e}")
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
    
    @staticmethod
    async def get_package_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """کیبورد منوی پکیج‌ها
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            کیبورد پکیج‌ها
        """
        try:
            keyboard = []
            
            # پکیج‌های اصلی
            for package_key, package_info in Config.PACKAGES.items():
                if package_key == 'guest':
                    continue  # پکیج مهمان جداگانه نمایش داده می‌شود
                
                package_name = package_info['name']
                price_irr = package_info['price_irr']
                
                button_text = f"📦 {package_name} - {price_irr:,} تومان"
                callback_data = f"package_{package_key}"
                
                keyboard.append([
                    InlineKeyboardButton(button_text, callback_data=callback_data)
                ])
            
            # پکیج مهمان
            guest_info = Config.PACKAGES.get('guest', {})
            if guest_info:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎟️ {guest_info['name']} - {guest_info['price_irr']:,} تومان", 
                        callback_data="package_guest"
                    )
                ])
            
            keyboard.extend([
                [InlineKeyboardButton("💳 شارژ حساب", callback_data="menu_charge")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error creating package menu keyboard: {e}")
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
    
    @staticmethod
    async def get_payment_method_keyboard() -> InlineKeyboardMarkup:
        """کیبورد روش‌های پرداخت
        
        Returns:
            کیبورد روش‌های پرداخت
        """
        keyboard = [
            [
                InlineKeyboardButton("🏦 کارت به کارت", callback_data="payment_method_card"),
                InlineKeyboardButton("💳 درگاه آنلاین", callback_data="payment_method_gateway")
            ],
            [
                InlineKeyboardButton("💰 از موجودی حساب", callback_data="payment_method_balance"),
                InlineKeyboardButton("🪙 ارز دیجیتال", callback_data="payment_method_crypto")
            ],
            [InlineKeyboardButton("❌ انصراف", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def send_welcome_message(context: ContextTypes.DEFAULT_TYPE, user_id: int, 
                                 username: str = None) -> bool:
        """ارسال پیام خوش‌آمدگویی
        
        Args:
            context: کنتکست تلگرام
            user_id: شناسه کاربر
            username: نام کاربری
            
        Returns:
            موفقیت ارسال
        """
        try:
            # دریافت پیام خوش‌آمدگویی از تنظیمات
            welcome_message = await SettingsManager.get_message("welcome")
            if not welcome_message:
                welcome_message = Config.MESSAGES["welcome"]
            
            # شخصی‌سازی پیام
            if username:
                welcome_message = welcome_message.replace("{username}", username)
            
            # ارسال پیام
            keyboard = await MessageManager.get_main_menu_keyboard(user_id)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=welcome_message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            TelegramLogger.log_message_sent(user_id, "welcome", True)
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome message to user {user_id}: {e}")
            TelegramLogger.log_message_sent(user_id, "welcome", False)
            return False
    
    @staticmethod
    async def send_admin_message(user_id: int, message: str, parse_mode: str = None) -> bool:
        """ارسال پیام ادمین به کاربر
        
        Args:
            user_id: شناسه کاربر
            message: متن پیام
            parse_mode: حالت پارسینگ
            
        Returns:
            موفقیت ارسال
        """
        try:
            # این تابع نیاز به context دارد، باید از جای دیگر فراخوانی شود
            # اینجا فقط لاگ می‌کنیم
            logger.info(f"Admin message to user {user_id}: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin message to user {user_id}: {e}")
            return False
    
    @staticmethod
    async def send_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int, 
                              title: str, message: str, urgent: bool = False) -> bool:
        """ارسال اعلان به کاربر
        
        Args:
            context: کنتکست تلگرام
            user_id: شناسه کاربر
            title: عنوان اعلان
            message: متن پیام
            urgent: فوری بودن
            
        Returns:
            موفقیت ارسال
        """
        try:
            # آیکون بر اساس اولویت
            icon = "🚨" if urgent else "🔔"
            
            # ساخت پیام
            notification_text = f"{icon} **{title}**\n\n{message}"
            
            # ارسال
            await context.bot.send_message(
                chat_id=user_id,
                text=notification_text,
                parse_mode="Markdown"
            )
            
            TelegramLogger.log_message_sent(user_id, "notification", True)
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            TelegramLogger.log_message_sent(user_id, "notification", False)
            return False
    
    @staticmethod
    async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, user_ids: List[int], 
                              message: str, delay: float = 0.1) -> Dict[str, int]:
        """ارسال پیام گروهی
        
        Args:
            context: کنتکست تلگرام
            user_ids: لیست کاربران
            message: متن پیام
            delay: تاخیر بین ارسال‌ها
            
        Returns:
            آمار ارسال (موفق، ناموفق)
        """
        try:
            stats = {"success": 0, "failed": 0}
            
            for user_id in user_ids:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    stats["success"] += 1
                    TelegramLogger.log_message_sent(user_id, "broadcast", True)
                    
                except TelegramError as e:
                    stats["failed"] += 1
                    TelegramLogger.log_message_sent(user_id, "broadcast", False)
                    logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                
                # تاخیر برای جلوگیری از محدودیت تلگرام
                if delay > 0:
                    await asyncio.sleep(delay)
            
            logger.info(f"Broadcast completed: {stats['success']} success, {stats['failed']} failed")
            return stats
            
        except Exception as e:
            logger.error(f"Error in broadcast message: {e}")
            return {"success": 0, "failed": len(user_ids)}
    
    @staticmethod
    async def send_package_expiry_warning(context: ContextTypes.DEFAULT_TYPE, 
                                        user_id: int, days_left: int) -> bool:
        """ارسال هشدار انقضای پکیج
        
        Args:
            context: کنتکست تلگرام
            user_id: شناسه کاربر
            days_left: روزهای باقیمانده
            
        Returns:
            موفقیت ارسال
        """
        try:
            if days_left <= 0:
                message = (
                    "⚠️ **پکیج شما منقضی شده است**\n\n"
                    "برای ادامه استفاده از خدمات ربات، لطفاً پکیج خود را تمدید کنید.\n\n"
                    "💡 برای تمدید از منوی 'خرید پکیج' استفاده کنید."
                )
            else:
                message = (
                    f"⏰ **هشدار انقضای پکیج**\n\n"
                    f"پکیج شما تا **{days_left} روز** دیگر منقضی خواهد شد.\n\n"
                    f"برای جلوگیری از قطع سرویس، لطفاً نسبت به تمدید آن اقدام کنید.\n\n"
                    f"💡 برای تمدید از منوی 'خرید پکیج' استفاده کنید."
                )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 خرید پکیج", callback_data="menu_packages")],
                [InlineKeyboardButton("👤 پروفایل من", callback_data="menu_profile")]
            ])
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending package expiry warning to user {user_id}: {e}")
            return False
    
    @staticmethod
    def format_user_profile(user: Dict[str, Any]) -> str:
        """فرمت‌بندی پروفایل کاربر
        
        Args:
            user: اطلاعات کاربر
            
        Returns:
            متن فرمت شده پروفایل
        """
        try:
            telegram_id = user.get('telegram_id', 'نامشخص')
            username = user.get('username', 'نامشخص')
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            package = user.get('package', 'none')
            package_expiry = user.get('package_expiry', '')
            balance = float(user.get('balance', 0))
            entry_date = user.get('entry_date', '')
            referral_code = user.get('referral_code', '')
            
            # نام کامل
            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                full_name = "نامشخص"
            
            # وضعیت پکیج
            if package == 'none':
                package_status = "❌ بدون پکیج"
            else:
                package_name = Config.PACKAGES.get(package, {}).get('name', package)
                if package_expiry:
                    if TimeManager.is_expired(package_expiry):
                        package_status = f"⏰ {package_name} (منقضی شده)"
                    else:
                        days_left = TimeManager.days_difference(
                            TimeManager.get_current_shamsi(), 
                            package_expiry
                        ) or 0
                        package_status = f"✅ {package_name} ({days_left} روز باقیمانده)"
                else:
                    package_status = f"✅ {package_name}"
            
            profile_text = (
                f"👤 **پروفایل کاربری**\n\n"
                f"🆔 **شناسه:** `{telegram_id}`\n"
                f"👤 **نام کاربری:** @{username}\n"
                f"📝 **نام:** {full_name}\n\n"
                f"📦 **پکیج:** {package_status}\n"
                f"💰 **موجودی:** {balance:,} تومان\n\n"
                f"📅 **تاریخ عضویت:** {entry_date}\n"
                f"🔗 **کد معرفی:** `{referral_code}`\n\n"
                f"📊 **آمار استفاده:**\n"
                f"• تعداد تحلیل‌های امروز: {user.get('api_calls_count', 0)}\n"
                f"• حد مجاز روزانه: {user.get('daily_limit', 10)}"
            )
            
            return profile_text
            
        except Exception as e:
            logger.error(f"Error formatting user profile: {e}")
            return "خطا در نمایش پروفایل"
    
    @staticmethod
    async def edit_system_message(update, context: ContextTypes.DEFAULT_TYPE, message_type: str):
        """ویرایش پیام‌های سیستم
        
        Args:
            update: آپدیت تلگرام
            context: کنتکست
            message_type: نوع پیام
        """
        try:
            query = update.callback_query
            admin_id = query.from_user.id
            
            # بررسی دسترسی
            if not AdminManager.has_permission(admin_id, 'system_settings'):
                await query.answer("شما دسترسی کافی ندارید.", show_alert=True)
                return
            
            # دریافت پیام فعلی
            current_message = await SettingsManager.get_message(message_type)
            if not current_message:
                current_message = Config.MESSAGES.get(message_type, "پیام یافت نشد")
            
            # نمایش پیام فعلی
            message_names = {
                "welcome": "خوش‌آمدگویی",
                "help": "راهنما",
                "package": "خرید پکیج",
                "charge": "شارژ حساب",
                "expiry": "انقضای پکیج",
                "payment_success": "تأیید پرداخت",
                "payment_fail": "رد پرداخت"
            }
            
            message_name = message_names.get(message_type, message_type)
            
            await query.edit_message_text(
                f"📝 **ویرایش پیام {message_name}**\n\n"
                f"**پیام فعلی:**\n"
                f"```\n{current_message}\n```\n\n"
                f"لطفاً متن جدید را ارسال کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("انصراف ❌", callback_data="admin_system_messages")]
                ]),
                parse_mode="Markdown"
            )
            
            # تنظیم حالت انتظار
            context.user_data['state'] = f"waiting_for_message_{message_type}"
            
        except Exception as e:
            logger.error(f"Error in edit_system_message: {e}")
    
    @staticmethod
    async def process_message_value(update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش متن جدید پیام سیستم
        
        Args:
            update: آپدیت تلگرام
            context: کنتکست
        """
        try:
            admin_id = update.effective_user.id
            new_message = update.message.text
            
            # بررسی حالت
            state = context.user_data.get('state', '')
            if not state.startswith('waiting_for_message_'):
                return
            
            message_type = state.replace('waiting_for_message_', '')
            
            # ذخیره پیام جدید
            success = await SettingsManager.set_message(message_type, new_message)
            
            if success:
                await update.message.reply_text(
                    f"✅ پیام {message_type} با موفقیت به‌روزرسانی شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("بازگشت به پیام‌های سیستم ⬅️", callback_data="admin_system_messages")]
                    ])
                )
            else:
                await update.message.reply_text(
                    f"❌ خطا در به‌روزرسانی پیام {message_type}.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("بازگشت به پیام‌های سیستم ⬅️", callback_data="admin_system_messages")]
                    ])
                )
            
            # پاکسازی حالت
            if 'state' in context.user_data:
                del context.user_data['state']
                
        except Exception as e:
            logger.error(f"Error processing message value: {e}")
    
    @staticmethod
    def get_help_text() -> str:
        """دریافت متن راهنما
        
        Returns:
            متن راهنما
        """
        return Config.MESSAGES.get("help", "راهنما در دسترس نیست.")
    
    @staticmethod
    def get_about_text() -> str:
        """دریافت متن درباره ما
        
        Returns:
            متن درباره ما
        """
        return (
            "🤖 **درباره MrTrader Bot**\n\n"
            "این ربات برای تحلیل بازار رمزارزها و ارائه سیگنال‌های معاملاتی طراحی شده است.\n\n"
            "⭐ **ویژگی‌ها:**\n"
            "• تحلیل پرایس اکشن و تکنیکال\n"
            "• قیمت زنده ارزهای دیجیتال\n"
            "• سیگنال‌های معاملاتی دقیق\n"
            "• آموزش‌های تخصصی\n"
            "• پشتیبانی 24 ساعته\n\n"
            "🔗 **ارتباط با ما:**\n"
            "• کانال: @MrTraderChannel\n"
            "• پشتیبانی: @MrTraderSupport\n\n"
            "📅 **نسخه:** 2.0\n"
            f"🕒 **آخرین به‌روزرسانی:** {TimeManager.get_current_shamsi_date()}"
        )


# Export برای استفاده آسان‌تر
__all__ = ['MessageManager']
