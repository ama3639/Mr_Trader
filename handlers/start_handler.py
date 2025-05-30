"""
هندلرهای شروع، راهنما و کامندهای اولیه MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from typing import List, Dict, Any
import asyncio

from core.config import Config
from utils.logger import logger, log_user_action
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.security_manager import SecurityManager
from managers.referral_manager import ReferralManager
from managers.settings_manager import SettingsManager
from managers.message_manager import MessageManager
from utils.time_manager import TimeManager


class StartHandler:
    """هندلر کامندهای شروع و راهنما"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.admin_manager = AdminManager()
        self.security_manager = SecurityManager()
        self.referral_manager = ReferralManager()
        self.settings_manager = SettingsManager()
        self.message_manager = MessageManager()
        self.time_manager = TimeManager()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر کامند /start"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # بررسی امنیت
            if not await self.security_manager.is_user_allowed(user.id):
                await self.message_manager.send_security_warning(chat.id, "کاربر مسدود شده")
                return
            
            # لاگ فعالیت کاربر
            log_user_action(user.id, "start_command", f"User started bot: {user.username}")
            
            # استخراج پارامتر start (برای رفرال)
            referral_code = None
            if context.args and len(context.args) > 0:
                referral_code = context.args[0].upper()
                logger.info(f"User {user.id} started with referral code: {referral_code}")
            
            # بررسی وجود کاربر
            existing_user = await self.user_manager.get_user_by_telegram_id(user.id)
            
            if existing_user:
                # کاربر موجود - نمایش منوی اصلی
                await self._show_returning_user_menu(update, context, existing_user)
            else:
                # کاربر جدید - فرآیند ثبت‌نام
                await self._handle_new_user_registration(update, context, referral_code)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "❌ خطایی در اجرای دستور رخ داد. لطفاً دوباره تلاش کنید.",
                parse_mode=ParseMode.HTML
            )
    
    async def _handle_new_user_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE, referral_code: str = None):
        """مدیریت ثبت‌نام کاربر جدید"""
        try:
            user = update.effective_user
            
            # بررسی فعال بودن ثبت‌نام
            if not self.settings_manager.is_registration_enabled():
                await update.message.reply_text(
                    "⛔️ ثبت‌نام کاربران جدید در حال حاضر غیرفعال است.\n"
                    "لطفاً بعداً دوباره تلاش کنید.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # پیام خوش‌آمدگویی
            welcome_message = self._generate_welcome_message(user.first_name)
            
            # کیبورد ثبت‌نام
            keyboard = [
                [InlineKeyboardButton("✅ ثبت‌نام در ربات", callback_data="register_user")],
                [InlineKeyboardButton("📋 مطالعه قوانین", callback_data="show_terms")],
                [InlineKeyboardButton("❓ راهنما", callback_data="show_help")]
            ]
            
            if referral_code:
                # اعتبارسنجی کد رفرال
                validation = self.referral_manager.validate_referral_code(referral_code)
                if validation['valid']:
                    welcome_message += f"\n\n🎉 شما با کد رفرال <code>{referral_code}</code> دعوت شده‌اید!"
                    welcome_message += f"\n💰 پس از ثبت‌نام پاداش دریافت خواهید کرد."
                    
                    # ذخیره کد رفرال در context
                    context.user_data['referral_code'] = referral_code
                else:
                    welcome_message += f"\n\n⚠️ کد رفرال نامعتبر است: {validation['message']}"
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling new user registration: {e}")
    
    def _generate_welcome_message(self, first_name: str) -> str:
        """تولید پیام خوش‌آمدگویی"""
        return f"""
🤖 <b>سلام {first_name}، به ربات MrTrader خوش آمدید!</b>

🚀 <b>امکانات ربات:</b>
📊 تحلیل تکنیکال ارزهای دیجیتال
📈 سیگنال‌های معاملاتی هوشمند
💰 مدیریت ریسک پیشرفته
📱 اعلان‌های قیمتی
📊 گزارش‌های تفصیلی عملکرد
🎯 استراتژی‌های متنوع تحلیل

💎 <b>ویژگی‌های ویژه:</b>
✅ تحلیل real-time بازار
✅ هوش مصنوعی پیشرفته
✅ پشتیبانی 24/7
✅ رابط کاربری ساده

برای شروع، روی دکمه ثبت‌نام کلیک کنید 👇
"""
    
    async def _show_returning_user_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: Dict):
        """نمایش منوی کاربر بازگشتی"""
        try:
            user = update.effective_user
            
            # بروزرسانی آخرین فعالیت
            await self.user_manager.update_last_activity(user.id)
            
            # تنظیمات کاربر
            user_settings = self.settings_manager.get_user_settings(user.id)
            
            # پیام خوش‌آمدگویی مجدد
            welcome_back_message = f"""
👋 سلام مجدد <b>{user.first_name}</b>!

📊 <b>وضعیت حساب شما:</b>
🎟️ پکیج فعال: {user_data.get('package_type', 'رایگان')}
📅 تاریخ انقضا: {self.time_manager.format_date_persian(user_data.get('expiry_date', 'نامحدود'))}
⭐ امتیاز: {user_data.get('user_points', 0):,} امتیاز

🕐 آخرین ورود: {self.time_manager.format_datetime_persian(user_data.get('last_login'))}

از منوی زیر گزینه مورد نظر را انتخاب کنید:
"""
            
            # منوی اصلی
            keyboard = [
                [
                    InlineKeyboardButton("📊 تحلیل سریع", callback_data="quick_analysis"),
                    InlineKeyboardButton("📈 سیگنال‌ها", callback_data="show_signals")
                ],
                [
                    InlineKeyboardButton("💼 پورتفولیو", callback_data="show_portfolio"),
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="show_settings")
                ],
                [
                    InlineKeyboardButton("📊 گزارش‌ها", callback_data="show_reports"),
                    InlineKeyboardButton("🎁 رفرال", callback_data="show_referral")
                ],
                [
                    InlineKeyboardButton("💎 ارتقاء پکیج", callback_data="show_packages"),
                    InlineKeyboardButton("🆘 پشتیبانی", callback_data="contact_support")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_back_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing returning user menu: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر کامند /help"""
        try:
            user = update.effective_user
            log_user_action(user.id, "help_command", "User requested help")
            
            help_message = self._generate_help_message()
            
            # کیبورد راهنما
            keyboard = [
                [
                    InlineKeyboardButton("🚀 شروع سریع", callback_data="quick_start_guide"),
                    InlineKeyboardButton("📊 راهنمای تحلیل", callback_data="analysis_guide")
                ],
                [
                    InlineKeyboardButton("💰 راهنمای سیگنال‌ها", callback_data="signals_guide"),
                    InlineKeyboardButton("⚙️ راهنمای تنظیمات", callback_data="settings_guide")
                ],
                [
                    InlineKeyboardButton("🎁 راهنمای رفرال", callback_data="referral_guide"),
                    InlineKeyboardButton("💎 راهنمای پکیج‌ها", callback_data="packages_guide")
                ],
                [
                    InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                help_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
    
    def _generate_help_message(self) -> str:
        """تولید پیام راهنما"""
        return """
📚 <b>راهنمای کامل ربات MrTrader</b>

🔧 <b>دستورات اصلی:</b>
/start - شروع یا منوی اصلی
/help - نمایش این راهنما
/menu - منوی سریع
/analysis - تحلیل سریع
/signals - سیگنال‌های فعال
/portfolio - پورتفولیو شما
/settings - تنظیمات

📊 <b>نحوه استفاده:</b>
1️⃣ ابتدا ارز مورد نظر را انتخاب کنید
2️⃣ نوع تحلیل را مشخص کنید
3️⃣ تایم فریم دلخواه را انتخاب کنید
4️⃣ نتایج را دریافت و بررسی کنید

💡 <b>نکات مهم:</b>
• همیشه مدیریت ریسک را رعایت کنید
• از چند تحلیل برای تصمیم‌گیری استفاده کنید
• بازارهای مالی ریسک دارند

❓ برای کسب اطلاعات بیشتر از منوی زیر استفاده کنید.
"""
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر کامند /menu"""
        try:
            user = update.effective_user
            log_user_action(user.id, "menu_command", "User opened menu")
            
            # بررسی وجود کاربر
            user_data = await self.user_manager.get_user_by_telegram_id(user.id)
            if not user_data:
                await update.message.reply_text(
                    "❌ ابتدا باید در ربات ثبت‌نام کنید.\nاز دستور /start استفاده کنید.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # نمایش منوی سریع
            await self._show_quick_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error in menu command: {e}")
    
    async def _show_quick_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سریع"""
        try:
            menu_message = """
🔥 <b>منوی سریع MrTrader</b>

یکی از گزینه‌های زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("⚡ تحلیل فوری", callback_data="instant_analysis"),
                    InlineKeyboardButton("📊 نمادهای محبوب", callback_data="popular_symbols")
                ],
                [
                    InlineKeyboardButton("🔥 سیگنال‌های داغ", callback_data="hot_signals"),
                    InlineKeyboardButton("📈 بازار کل", callback_data="market_overview")
                ],
                [
                    InlineKeyboardButton("💰 قیمت‌ها", callback_data="price_check"),
                    InlineKeyboardButton("🔔 هشدارها", callback_data="price_alerts")
                ],
                [
                    InlineKeyboardButton("👤 پروفایل من", callback_data="my_profile")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                menu_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing quick menu: {e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر کامند /status - نمایش وضعیت سیستم"""
        try:
            user = update.effective_user
            
            # بررسی ادمین بودن
            if not await self.admin_manager.is_admin(user.id):
                await update.message.reply_text("❌ شما مجوز دسترسی به این بخش را ندارید.")
                return
            
            # دریافت وضعیت سیستم
            system_status = await self._get_system_status()
            
            status_message = f"""
🖥️ <b>وضعیت سیستم MrTrader</b>

🟢 <b>سلامت کلی:</b> {system_status['health']}
📊 <b>کاربران فعال:</b> {system_status['active_users']}
💾 <b>استفاده دیتابیس:</b> {system_status['db_usage']}
🌐 <b>وضعیت API:</b> {system_status['api_status']}
📡 <b>آخرین بکاپ:</b> {system_status['last_backup']}

⏱️ <b>زمان تولید گزارش:</b> {self.time_manager.get_current_time_persian()}
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 تازه‌سازی", callback_data="refresh_status"),
                    InlineKeyboardButton("📊 گزارش کامل", callback_data="full_system_report")
                ],
                [
                    InlineKeyboardButton("🔧 مدیریت سیستم", callback_data="system_management")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
    
    async def _get_system_status(self) -> Dict[str, str]:
        """دریافت وضعیت سیستم"""
        try:
            # این‌ها داده‌های نمونه هستند - در پیاده‌سازی واقعی از منابع مناسب دریافت شوند
            return {
                'health': '✅ سالم',
                'active_users': '1,247 نفر',
                'db_usage': '2.3 GB',
                'api_status': '🟢 فعال',
                'last_backup': self.time_manager.format_datetime_persian(datetime.now())
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'health': '❌ خطا',
                'active_users': 'نامشخص',
                'db_usage': 'نامشخص',
                'api_status': '❌ خطا',
                'last_backup': 'نامشخص'
            }
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر کامند /version"""
        try:
            version_message = f"""
🤖 <b>اطلاعات نسخه MrTrader Bot</b>

🔢 <b>نسخه:</b> {Config.BOT_VERSION}
📅 <b>تاریخ انتشار:</b> {Config.RELEASE_DATE}
👨‍💻 <b>سازنده:</b> {Config.DEVELOPER_NAME}

🆕 <b>آخرین بروزرسانی‌ها:</b>
• بهبود دقت سیگنال‌ها
• افزودن استراتژی‌های جدید
• بهینه‌سازی سرعت

📞 <b>پشتیبانی:</b> @{Config.SUPPORT_USERNAME}
🌐 <b>وب‌سایت:</b> {Config.WEBSITE_URL}
"""
            
            await update.message.reply_text(
                version_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in version command: {e}")
    
    async def setup_bot_commands(self, application):
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
                BotCommand("version", "نسخه ربات")
            ]
            
            await application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
            
        except Exception as e:
            logger.error(f"Error setting bot commands: {e}")
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("menu", self.menu_command),
            CommandHandler("status", self.status_command),
            CommandHandler("version", self.version_command),
        ]


# Export
__all__ = ['StartHandler']