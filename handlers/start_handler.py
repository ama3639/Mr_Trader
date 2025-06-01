"""
هندلر کامند شروع (/start) - Fixed Imports Only
"""
import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import Config
from utils.logger import logger, log_user_action
from utils.time_manager import TimeManager
from managers.user_manager import UserManager
from managers.security_manager import SecurityManager



class StartHandler:
    """کلاس مدیریت کامند شروع"""
    
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """هندلر کامند شروع (/start)
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            # ✅ دریافت اطلاعات کاربر
            user_info = update.effective_user
            telegram_id = user_info.id
            username = user_info.username
            first_name = user_info.first_name or ""
            last_name = user_info.last_name or ""
            
            logger.info(f"Start command received from user {telegram_id}")
            
            # ✅ بررسی مسدودیت کاربر
            if UserManager.is_user_blocked(telegram_id):
                await update.message.reply_text(
                    "⛔ حساب کاربری شما مسدود شده است.\n"
                    "لطفاً با پشتیبانی تماس بگیرید: @mrtrader_support",
                    parse_mode='HTML'
                )
                return
            
            # ✅ دریافت یا ایجاد کاربر - بدون await
            user_data = UserManager.get_or_create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            # ✅ لاگ اکشن کاربر
            log_user_action(telegram_id, "start_command", f"User started bot: {username}")
            
            # ✅ بررسی آیا کاربر از لینک رفرال آمده
            args = context.args
            if args and args[0].startswith('ref_'):
                await StartHandler._handle_referral(update, context, args[0], telegram_id)
            
            # ✅ ارسال پیام خوشامدگویی
            await StartHandler._send_welcome_message(update, user_data)
            
            # ✅ نمایش منوی اصلی
            await StartHandler._show_main_menu(update, user_data)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            try:
                await update.message.reply_text(
                    "❌ خطایی در شروع ربات رخ داد. لطفاً مجدداً تلاش کنید.\n"
                    "اگر مشکل ادامه داشت با پشتیبانی تماس بگیرید: @mrtrader_support"
                )
            except Exception as reply_error:
                logger.error(f"Error sending error message: {reply_error}")
    
    @staticmethod
    async def _handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              ref_code: str, telegram_id: int) -> None:
        """پردازش کد رفرال
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            ref_code: کد رفرال
            telegram_id: شناسه تلگرام کاربر
        """
        try:
            # استخراج کد رفرال
            referral_code = ref_code.replace('ref_', '')
            
            # یافتن کاربر معرف
            try:
                # استفاده از CSVManager برای یافتن معرف
                from managers.csv_manager import CSVManager
                referrer_id = CSVManager.find_user_by_referral_code(referral_code)
                
                if referrer_id and int(referrer_id) != telegram_id:
                    # پردازش رفرال
                    success = UserManager.process_referral(int(referrer_id), telegram_id)
                    
                    if success:
                        # به‌روزرسانی کاربر جدید
                        UserManager.update_user(telegram_id, referred_by=int(referrer_id))
                        
                        await update.message.reply_text(
                            "🎉 شما از طریق لینک رفرال وارد شدید!\n"
                            "پاداش رفرال به حساب معرف شما اضافه شد.",
                            parse_mode='HTML'
                        )
                        
                        # اطلاع به معرف
                        try:
                            await context.bot.send_message(
                                chat_id=int(referrer_id),
                                text=f"🎉 یک کاربر جدید از طریق لینک رفرال شما عضو شد!\n"
                                     f"پاداش 50,000 تومان به حساب شما اضافه شد.",
                                parse_mode='HTML'
                            )
                        except Exception as notify_error:
                            logger.warning(f"Could not notify referrer {referrer_id}: {notify_error}")
                    else:
                        logger.warning(f"Failed to process referral for {telegram_id}")
                else:
                    logger.warning(f"Invalid referral code or self-referral: {referral_code}")
                    
            except Exception as ref_error:
                logger.warning(f"Error processing referral code {referral_code}: {ref_error}")
                
        except Exception as e:
            logger.error(f"Error handling referral: {e}")
    
    @staticmethod
    async def _send_welcome_message(update: Update, user_data: Dict[str, Any]) -> None:
        """ارسال پیام خوشامدگویی
        
        Args:
            update: آپدیت تلگرام
            user_data: اطلاعات کاربر
        """
        try:
            # ✅ دریافت نام کاربر
            first_name = user_data.get('first_name', '')
            username = user_data.get('username', '')
            display_name = first_name or username or "کاربر"
            
            # ✅ تعیین نوع پکیج
            package = user_data.get('package', 'demo')
            package_info = Config.get_package_info(package)
            package_name = package_info.get('name', 'دمو')
            
            # ✅ بررسی وضعیت پکیج - بدون await
            is_expired, days_left = UserManager.is_package_expired(user_data.get('telegram_id'))
            
            # ✅ پیام خوشامدگویی
            welcome_message = f"""
🎉 <b>به ربات تحلیل ارزهای دیجیتال MrTrader خوش آمدید!</b>

👋 سلام <b>{display_name}</b>

📊 <b>وضعیت حساب شما:</b>
🎫 پکیج فعلی: <b>{package_name}</b>
{'⏰ روزهای باقیمانده: <b>' + str(days_left) + '</b>' if not is_expired and package != 'demo' else ''}
{'✅ بدون محدودیت زمانی' if package == 'demo' else ''}
💰 موجودی: <b>{user_data.get('balance', 0):,}</b> تومان

🔰 <b>امکانات ربات:</b>
📈 تحلیل تکنیکال کامل
🎯 سیگنال‌های خرید و فروش
📊 نمودارهای قیمت
🔔 هشدارهای قیمتی
💎 تحلیل ارزهای مختلف

🚀 برای شروع از منوی زیر استفاده کنید:
            """
            
            await update.message.reply_text(
                welcome_message.strip(),
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            # ✅ پیام ساده در صورت خطا
            try:
                await update.message.reply_text(
                    "🎉 به ربات MrTrader خوش آمدید!\n"
                    "از منوی زیر برای شروع استفاده کنید."
                )
            except Exception as simple_error:
                logger.error(f"Error sending simple welcome: {simple_error}")
    
    @staticmethod
    async def _show_main_menu(update: Update, user_data: Dict[str, Any]) -> None:
        """نمایش منوی اصلی
        
        Args:
            update: آپدیت تلگرام
            user_data: اطلاعات کاربر
        """
        try:
            # ✅ ایجاد کیبورد منوی اصلی
            keyboard = [
                [
                    InlineKeyboardButton("📊 تحلیل ارز", callback_data="analysis_menu"),
                    InlineKeyboardButton("💎 لیست ارزها", callback_data="coins_list")
                ],
                [
                    InlineKeyboardButton("📈 نمودار قیمت", callback_data="price_chart"),
                    InlineKeyboardButton("🔔 هشدار قیمت", callback_data="price_alert")
                ],
                [
                    InlineKeyboardButton("🎯 سیگنال‌ها", callback_data="signals_menu"),
                    InlineKeyboardButton("📰 اخبار بازار", callback_data="market_news")
                ],
                [
                    InlineKeyboardButton("👤 حساب کاربری", callback_data="user_profile"),
                    InlineKeyboardButton("💰 کیف پول", callback_data="wallet_menu")
                ],
                [
                    InlineKeyboardButton("🛒 خرید پکیج", callback_data="packages_menu"),
                    InlineKeyboardButton("🎁 دعوت دوستان", callback_data="referral_menu")
                ],
                [
                    InlineKeyboardButton("ℹ️ راهنما", callback_data="help_menu"),
                    InlineKeyboardButton("📞 پشتیبانی", callback_data="support_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            menu_text = """
🏠 <b>منوی اصلی MrTrader</b>

لطفاً از گزینه‌های زیر یکی را انتخاب کنید:

📊 <b>تحلیل ارز:</b> تحلیل تکنیکال کامل
💎 <b>لیست ارزها:</b> مشاهده قیمت ارزها
📈 <b>نمودار قیمت:</b> رسم نمودار تعاملی
🔔 <b>هشدار قیمت:</b> تنظیم آلارم قیمت
🎯 <b>سیگنال‌ها:</b> سیگنال‌های خرید/فروش
📰 <b>اخبار بازار:</b> آخرین اخبار کریپتو
            """
            
            await update.message.reply_text(
                menu_text.strip(),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            # ✅ منوی ساده در صورت خطا
            try:
                simple_keyboard = [
                    [InlineKeyboardButton("📊 تحلیل ارز", callback_data="analysis_menu")],
                    [InlineKeyboardButton("💎 لیست ارزها", callback_data="coins_list")],
                    [InlineKeyboardButton("ℹ️ راهنما", callback_data="help_menu")]
                ]
                
                reply_markup = InlineKeyboardMarkup(simple_keyboard)
                
                await update.message.reply_text(
                    "🏠 منوی اصلی\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
                    reply_markup=reply_markup
                )
            except Exception as simple_error:
                logger.error(f"Error sending simple menu: {simple_error}")
    
    @staticmethod
    async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """هندلر کامند منو (/menu)
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            telegram_id = update.effective_user.id
            
            # ✅ دریافت اطلاعات کاربر - بدون await
            user_data = UserManager.safe_get_user(telegram_id)
            
            # ✅ نمایش منوی اصلی
            await StartHandler._show_main_menu(update, user_data)
            
            log_user_action(telegram_id, "menu_command", "User accessed menu")
            
        except Exception as e:
            logger.error(f"Error in menu command: {e}")
            try:
                await update.message.reply_text(
                    "❌ خطایی در نمایش منو رخ داد. لطفاً از /start استفاده کنید."
                )
            except Exception as reply_error:
                logger.error(f"Error sending menu error message: {reply_error}")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """هندلر کامند راهنما (/help)
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            help_text = """
🤖 <b>راهنمای ربات MrTrader</b>

<b>📋 دستورات اصلی:</b>
/start - شروع ربات و منوی اصلی
/menu - نمایش منوی اصلی
/help - نمایش این راهنما
/profile - مشاهده پروفایل کاربری
/balance - مشاهده موجودی کیف پول

<b>🔍 نحوه تحلیل ارز:</b>
1️⃣ روی "📊 تحلیل ارز" کلیک کنید
2️⃣ نماد ارز مورد نظر را وارد کنید (مثل: BTC)
3️⃣ نوع تحلیل را انتخاب کنید
4️⃣ نتایج تحلیل را دریافت کنید

<b>📊 امکانات موجود:</b>
• تحلیل تکنیکال 35 اندیکاتور
• سیگنال‌های خرید و فروش
• نمودارهای قیمت تعاملی  
• هشدارهای قیمتی
• اخبار بازار لحظه‌ای
• پورتفوی شخصی

<b>💎 پکیج‌های اشتراک:</b>
🆓 دمو: 5 تحلیل روزانه
💰 پایه: 20 تحلیل روزانه - 99 هزار تومان
🌟 ویژه: 50 تحلیل روزانه - 199 هزار تومان  
👑 VIP: نامحدود - 399 هزار تومان

<b>📞 پشتیبانی:</b>
@mrtrader_support - پشتیبانی فنی
@mrtrader_channel - کانال اصلی
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu"),
                    InlineKeyboardButton("📞 پشتیبانی", callback_data="support_menu")
                ],
                [
                    InlineKeyboardButton("🛒 خرید پکیج", callback_data="packages_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                help_text.strip(),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            telegram_id = update.effective_user.id
            log_user_action(telegram_id, "help_command", "User viewed help")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            try:
                await update.message.reply_text(
                    "❌ خطایی در نمایش راهنما رخ داد.\n"
                    "لطفاً با پشتیبانی تماس بگیرید: @mrtrader_support"
                )
            except Exception as reply_error:
                logger.error(f"Error sending help error message: {reply_error}")
    
    @staticmethod
    async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """هندلر کامند پروفایل (/profile)
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            telegram_id = update.effective_user.id
            
            # ✅ دریافت اطلاعات کاربر - بدون await
            user_data = UserManager.safe_get_user(telegram_id)
            
            # ✅ محاسبه اطلاعات پروفایل
            package = user_data.get('package', 'demo')
            package_info = Config.get_package_info(package)
            
            # ✅ بررسی انقضا - بدون await
            is_expired, days_left = UserManager.is_package_expired(telegram_id)
            
            profile_text = f"""
👤 <b>پروفایل کاربری</b>

🆔 شناسه: <code>{telegram_id}</code>
👤 نام: <b>{user_data.get('first_name', 'نامشخص')}</b>
📱 نام کاربری: @{user_data.get('username', 'ندارد')}

🎫 <b>اطلاعات اشتراک:</b>
📦 پکیج فعلی: <b>{package_info.get('name', 'دمو')}</b>
{'⏰ روزهای باقیمانده: <b>' + str(days_left) + '</b>' if not is_expired and package != 'demo' else ''}
{'✅ بدون محدودیت زمانی' if package == 'demo' else ''}
📊 حد روزانه: <b>{user_data.get('daily_limit', 5)}</b> تحلیل
📈 استفاده امروز: <b>{user_data.get('api_calls_count', 0)}</b> تحلیل

💰 <b>اطلاعات مالی:</b>
💵 موجودی: <b>{user_data.get('balance', 0):,}</b> تومان
🎁 کد رفرال: <code>{user_data.get('referral_code', 'ندارد')}</code>

📅 <b>اطلاعات تکمیلی:</b>
📝 تاریخ عضویت: <b>{user_data.get('entry_date', 'نامشخص')}</b>
🕒 آخرین فعالیت: <b>{user_data.get('last_activity', 'نامشخص')}</b>
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🛒 ارتقای پکیج", callback_data="packages_menu"),
                    InlineKeyboardButton("💰 کیف پول", callback_data="wallet_menu")
                ],
                [
                    InlineKeyboardButton("🎁 دعوت دوستان", callback_data="referral_menu"),
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                profile_text.strip(),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            log_user_action(telegram_id, "profile_command", "User viewed profile")
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            try:
                await update.message.reply_text(
                    "❌ خطایی در نمایش پروفایل رخ داد.\n"
                    "لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
            except Exception as reply_error:
                logger.error(f"Error sending profile error message: {reply_error}")


# Export برای استفاده آسان‌تر
__all__ = ['StartHandler']