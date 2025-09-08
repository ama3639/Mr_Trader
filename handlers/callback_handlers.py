"""
هندلرهای پردازش Callback Query برای MrTrader Bot - نسخه ساده و کامل
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
from datetime import datetime
import re
import html
from core.config import Config
from utils.logger import logger, log_user_action
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.security_manager import SecurityManager
from managers.referral_manager import ReferralManager
from managers.settings_manager import SettingsManager
from managers.message_manager import MessageManager
from managers.payment_manager import PaymentManager
from managers.symbol_manager import SymbolManager
from managers.strategy_manager import StrategyManager
from managers.report_manager import ReportManager
from api.api_client import api_client
from utils.time_manager import TimeManager
from utils.helpers import extract_signal_details, format_signal_message
from templates.keyboards import KeyboardTemplates
from templates.messages import MessageTemplates
from core.cache import cache

class CallbackHandler:
    """هندلر اصلی Callback Query ها"""
    
    def __init__(self):
        # مقداردهی manager ها
        self.user_manager = UserManager()
        self.admin_manager = AdminManager()
        self.security_manager = SecurityManager()
        self.referral_manager = ReferralManager()
        self.settings_manager = SettingsManager()
        self.message_manager = MessageManager()
        self.payment_manager = PaymentManager()
        self.symbol_manager = SymbolManager()
        self.strategy_manager = StrategyManager()
        self.report_manager = ReportManager()
        self.time_manager = TimeManager()

    # =========================
    # هندلر اصلی Callback Query
    # =========================

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هندلر اصلی پردازش callback query ها"""
        try:
            query = update.callback_query
            user = update.effective_user
            
            # تأیید callback query
            await query.answer()
            
            # استخراج داده‌های callback
            callback_data = query.data
            
            # لاگ فعالیت کاربر
            log_user_action(user.id, "callback_query", f"Callback: {callback_data}")
            
            # بررسی امنیت
            if hasattr(self.security_manager, 'is_user_allowed'):
                is_allowed = await self.security_manager.is_user_allowed(user.id)
                if not is_allowed:
                    await query.edit_message_text("⛔ دسترسی شما محدود شده است.")
                    return
            
            # پردازش callback
            await self._process_callback(query, context, callback_data)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}", exc_info=True)
            try:
                await query.edit_message_text("⛔ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except:
                pass


    async def handle_download_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, filename: str):
        """پردازش درخواست دانلود گزارش - اصلاح شده"""
        try:
            user_id = query.from_user.id
            
            # بررسی وجود فایل در context
            file_key = f"report_{filename}"
            if file_key not in context.user_data:
                await query.answer("⚠️ فایل گزارش منقضی شده است. لطفاً تحلیل جدیدی انجام دهید.", show_alert=True)
                return
            
            filepath = context.user_data[file_key]
            
            # بررسی وجود فایل فیزیکی
            if not os.path.exists(filepath):
                await query.answer("⚠️ فایل گزارش یافت نشد.", show_alert=True)
                return
            
            await query.answer("📤 در حال ارسال فایل گزارش...")
            
            # ارسال فایل به عنوان پاسخ به پیام فعلی
            with open(filepath, 'rb') as file:
                await query.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📊 <b>گزارش تحلیل تکمیلی</b>\n\n📄 فایل: {filename}\n\n⚠️ این تحلیل جنبه آموزشی دارد.",
                    parse_mode=ParseMode.HTML
                )
            
            # حذف فوری فایل بعد از ارسال
            try:
                os.remove(filepath)
                del context.user_data[file_key]
                logger.info(f"فایل بعد از ارسال حذف شد: {filepath}")
            except Exception as cleanup_error:
                logger.warning(f"خطا در حذف فایل بعد از ارسال: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"خطا در دانلود گزارش {filename}: {e}", exc_info=True)
            await query.answer("⚠️ خطا در ارسال فایل گزارش.", show_alert=True)                
        
    async def _process_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """پردازش callback بر اساس نوع"""
        try:
            # تجزیه callback data
            if ':' in callback_data:
                parts = callback_data.split(':', 1)
                action = parts[0]
                param = parts[1] if len(parts) > 1 else None
            else:
                action = callback_data
                param = None
            
            # پردازش بر اساس action
            if action == "main_menu":
                await self.show_main_menu(query, context)
            elif action == "user_profile":
                await self.show_user_profile(query, context)
            elif action == "wallet_menu":
                await self.show_wallet_menu(query, context)
            elif action == "admin_panel":
                await self.show_admin_panel(query, context)
            elif action == "admin_users":
                page = int(param) if param else 1
                await self.show_user_management(query, context, page)
            elif action == "admin_view_user":
                target_user_id = int(param)
                await self.show_user_details_for_admin(query, context, target_user_id)
            elif action == "admin_block":
                target_user_id = int(param)
                await self.handle_user_block(query, context, target_user_id)
            elif action == "admin_unblock":
                target_user_id = int(param)
                await self.handle_user_unblock(query, context, target_user_id)
            elif action == "admin_change_pkg":
                target_user_id = int(param)
                await self.show_change_package_menu(query, context, target_user_id)
            elif action.startswith("pkg_change_"):
                package_type = action.replace("pkg_change_", "")
                target_user_id = int(param)
                await self.handle_package_change(query, context, package_type, target_user_id)
            elif action == "admin_charge_wallet":
                target_user_id = int(param)
                await self.show_charge_wallet_form(query, context, target_user_id)
            elif action == "admin_send_msg":
                target_user_id = int(param)
                await self.show_send_message_form(query, context, target_user_id)
            elif action == "analysis_menu":
                await self.show_strategy_menu(query, context)
            elif action == "packages_menu":
                await self.show_packages_menu(query, context)
            elif action == "referral_menu":
                await self.show_referral_menu(query, context)
            elif action == "help_menu":
                await self.show_help_menu(query, context)
            elif action == "support_menu":
                await self.show_support_menu(query, context)

            elif action == "select_strategy":
                await self.handle_strategy_selection(query, context, param)
            elif action == "select_symbol":
                await self.handle_symbol_selection(query, context, param)
            elif action == "manual_symbol":
                await self.handle_manual_symbol_request(query, context, param)
            elif action == "select_currency":
                await self.handle_currency_selection(query, context, param)
            elif action == "select_timeframe":
                await self.handle_timeframe_selection(query, context, param)
            elif action == "download_report":  # ✅ اضافه شده
                await self.handle_download_report(query, context, param)

            else:
                # سایر callback های ساده
                await self.handle_simple_callbacks(query, context, action)
                    
        except Exception as e:
            logger.error(f"Error processing callback {callback_data}: {e}")
            await query.edit_message_text("❌ خطا در پردازش درخواست.")

    # =========================
    # توابع منوهای اصلی
    # =========================

    async def show_main_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی"""
        try:
            user = query.from_user
            user_data = self.user_manager.get_user_by_telegram_id(user.id) or {}
            user_package = user_data.get('package', 'demo')
            is_admin = self.admin_manager.is_admin(user.id)
            
            menu_message = f"""🏠 <b>منوی اصلی MrTrader</b>

👋 سلام {user.first_name}
📦 پکیج فعال: <b>{user_package.upper()}</b>

لطفاً از گزینه‌های زیر یکی را انتخاب کنید:

📊 <b>تحلیل ارز:</b> تحلیل تکنیکال کامل
💎 <b>لیست ارزها:</b> مشاهده قیمت ارزها
📈 <b>نمودار قیمت:</b> رسم نمودار تعاملی
🔔 <b>هشدار قیمت:</b> تنظیم آلارم قیمت
🎯 <b>سیگنال‌ها:</b> سیگنال‌های خرید/فروش
📰 <b>اخبار بازار:</b> آخرین اخبار کریپتو"""
            
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
            
            if is_admin:
                keyboard.append([
                    InlineKeyboardButton("🔧 پنل مدیریت", callback_data="admin_panel")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                menu_message.strip(),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await query.edit_message_text("⛔ خطا در نمایش منو.")

    async def show_user_profile(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پروفایل کاربر"""
        try:
            user = query.from_user
            user_data = self.user_manager.get_user_by_telegram_id(user.id)
            
            if not user_data:
                await query.edit_message_text("⛔ اطلاعات کاربری یافت نشد.")
                return
            
            user_package = user_data.get('package', 'demo')
            is_expired, days_left = self.user_manager.is_package_expired(user.id)
            is_admin = self.admin_manager.is_admin(user.id)
            
            profile_message = f"""👤 <b>پروفایل کاربری</b>

🆔 <b>شناسه:</b> <code>{user.id}</code>
👤 <b>نام:</b> {user.first_name} {user.last_name or ''}
{'📱 <b>نام کاربری:</b> @' + user.username if user.username else ''}

📦 <b>پکیج فعلی:</b> <b>{user_package.upper()}</b>
{'🔴 منقضی شده' if is_expired and user_package != 'demo' else '🟢 فعال'}
{'⏰ <b>روزهای باقیمانده:</b> ' + str(days_left) if not is_expired and user_package != 'demo' else ''}

📊 <b>آمار استفاده:</b>
📈 تحلیل‌های امروز: <code>{user_data.get('api_calls_count', 0)}</code>
📊 محدودیت روزانه: <code>{user_data.get('daily_limit', 5)}</code>

💰 <b>موجودی:</b> <b>{user_data.get('balance', 0):,}</b> تومان
🎁 <b>کد رفرال:</b> <code>{user_data.get('referral_code', 'ندارد')}</code>

📅 <b>تاریخ عضویت:</b> {user_data.get('entry_date', 'نامشخص')}"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🛒 ارتقای پکیج", callback_data="packages_menu"),
                    InlineKeyboardButton("💰 کیف پول", callback_data="wallet_menu")
                ],
                [
                    InlineKeyboardButton("🎁 دعوت دوستان", callback_data="referral_menu"),
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="user_stats")
                ],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            
            if is_admin:
                keyboard.insert(-1, [InlineKeyboardButton("🔧 پنل ادمین", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                profile_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing user profile: {e}")
            await query.edit_message_text("⛔ خطا در نمایش پروفایل.")

    # =======================================
    # <<< توابع جدید برای جریان تحلیل ارز >>>
    # =======================================

    async def handle_strategy_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, strategy_key: str):
        """مرحله 1: کاربر استراتژی را انتخاب کرده است. حالا نماد را می‌پرسیم."""
        try:
            # ذخیره استراتژی انتخاب شده در حافظه موقت کاربر
            context.user_data['selected_strategy'] = strategy_key
            
            strategy_name = self.strategy_manager.get_strategy_display_name(strategy_key)
            
            # ارسال پیام درخواست نماد
            message = MessageTemplates.get_ask_for_symbol_message(strategy_name)
            keyboard = KeyboardTemplates.symbol_selection(strategy_key)
            
            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error in handle_strategy_selection for {strategy_key}: {e}")
            await query.edit_message_text("⛔/start \n  خطا در پردازش استراتژی.")

    async def handle_symbol_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, param: str):
        """مرحله 2: کاربر نماد را انتخاب کرده است. حالا ارز مرجع را می‌پرسیم."""
        try:
            strategy_key, symbol = param.split('|')
            context.user_data['selected_symbol'] = symbol

            message = MessageTemplates.get_ask_for_currency_message(symbol)
            keyboard = KeyboardTemplates.currency_selection(strategy_key, symbol)
            
            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error in handle_symbol_selection for {param}: {e}")

    async def handle_manual_symbol_request(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, strategy_key: str):
        """کاربر درخواست ورود دستی نماد را داده است."""
        context.user_data['waiting_for_manual_symbol'] = strategy_key
        message = "🪙 لطفاً نماد ارز مورد نظر را تایپ کنید (مثلاً: `BTC`):"
        await query.edit_message_text(text=message, parse_mode=ParseMode.MARKDOWN)

    async def handle_currency_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, param: str):
        """مرحله 3: کاربر ارز مرجع را انتخاب کرده است. حالا تایم‌فریم را می‌پرسیم."""
        try:
            strategy_key, symbol, currency = param.split('|')
            context.user_data['selected_currency'] = currency

            message = MessageTemplates.get_ask_for_timeframe_message(symbol, currency)
            keyboard = KeyboardTemplates.timeframe_selection(strategy_key, symbol, currency)

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error in handle_currency_selection for {param}: {e}")


    async def handle_timeframe_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, param: str):
        """مرحله نهایی: کاربر تایم‌فریم را انتخاب کرده است. تحلیل را انجام می‌دهیم."""
        try:
            strategy_key, symbol, currency, timeframe = param.split('|')
            user_id = query.from_user.id
            
            # نمایش پیام "در حال پردازش"
            await query.edit_message_text(
                text=f"⏳ <b>در حال تحلیل...</b>\n\n📊 استراتژی: {strategy_key}\n💰 نماد: {symbol}/{currency}\n⏰ تایم‌فریم: {timeframe}",
                parse_mode=ParseMode.HTML
            )

            # فراخوانی API برای تحلیل با تولید فایل گزارش
            analysis_result = await self.strategy_manager.analyze_strategy(
                user_id, strategy_key, symbol, currency, timeframe, generate_file=True
            )
            
            if "error" in analysis_result:
                # در صورت خطا، پیام خطا را با یک کیبورد کامل نمایش بده
                await query.edit_message_text(
                    text=f"⚠️ <b>خطا در تحلیل</b>\n\n{analysis_result['error']}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 تحلیل جدید", callback_data="analysis_menu")],
                        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
                return

            # فرمت‌بندی نتیجه با استفاده از توابع جدید
            try:
                # استخراج سیگنال
                signal_details = extract_signal_details(strategy_key, analysis_result)
                
                # دریافت chart_url از پاسخ API و اضافه کردن آن به signal_details
                if 'chart_url' in analysis_result:
                    signal_details['chart_url'] = analysis_result['chart_url']
                
                # فرمت‌بندی پیام با استفاده از تابع جدید
                formatted_message = format_signal_message(
                    signal_details, symbol, currency, timeframe, strategy_key
                )
                
            except Exception as format_error:
                logger.error(f"خطا در فرمت‌بندی پیام: {format_error}")
                formatted_message = f"""✅ <b>تحلیل {symbol}/{currency} کامل شد!</b>
    📊 <b>استراتژی:</b> {strategy_key}
    ⏰ <b>تایم‌فریم:</b> {timeframe}
    🎯 <b>نتیجه:</b> {analysis_result.get('signal_direction', 'تحلیل انجام شد')}
    ⚠️ <b>یادآوری:</b> این تحلیل جنبه آموزشی دارد."""
            
            # کیبورد اقدامات بعدی
            keyboard_buttons = []
            
            # دکمه دانلود گزارش در صورت وجود فایل
            report_file = analysis_result.get("report_file")
            if report_file and not report_file.get("error"):
                keyboard_buttons.append([
                    InlineKeyboardButton("📄 دانلود گزارش", callback_data=f"download_report:{report_file.get('filename', '')}")
                ])
                
                # ذخیره اطلاعات فایل در context برای دانلود
                file_key = f"report_{report_file.get('filename', '')}"
                context.user_data[file_key] = report_file.get('filepath', '')
                
                # تنظیم تایمر حذف فایل بعد از 30 ثانیه
                asyncio.create_task(self._schedule_file_cleanup(context, file_key, 30))
            
            # دکمه‌های اقدامات
            keyboard_buttons.extend([
                [
                    InlineKeyboardButton("🔄 تحلیل جدید", callback_data="analysis_menu"),
                    InlineKeyboardButton("📈 استراتژی دیگر", callback_data=f"select_strategy:{strategy_key}")
                ],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await query.edit_message_text(
                text=formatted_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"خطا در handle_timeframe_selection: {e}", exc_info=True)
            await query.edit_message_text(
                text="⚠️ خطایی در اجرای تحلیل رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تحلیل جدید", callback_data="analysis_menu")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ]),
                parse_mode=ParseMode.HTML
            )
        finally:
            # پاکسازی حافظه موقت کاربر
            keys_to_clear = ['selected_strategy', 'selected_symbol', 'selected_currency']
            for key in keys_to_clear:
                if key in context.user_data:
                    del context.user_data[key]


    async def _schedule_file_cleanup(self, context: ContextTypes.DEFAULT_TYPE, file_key: str, delay_seconds: int):
        """برنامه‌ریزی حذف فایل بعد از مدت زمان مشخص"""
        try:
            await asyncio.sleep(delay_seconds)
            
            if file_key in context.user_data:
                filepath = context.user_data[file_key]
                
                # حذف فایل فیزیکی در صورت وجود
                try:
                    if filepath and os.path.exists(filepath):
                        os.remove(filepath)
                        logger.info(f"فایل حذف شد: {filepath}")
                except Exception as file_error:
                    logger.warning(f"خطا در حذف فایل {filepath}: {file_error}")
                
                # حذف از context
                del context.user_data[file_key]
                logger.info(f"اطلاعات فایل از context حذف شد: {file_key}")
                
        except Exception as e:
            logger.error(f"خطا در برنامه‌ریزی حذف فایل: {e}")
                
    def _convert_markdown_to_html(self, text: str) -> str:
        """تبدیل markdown syntax به HTML و escape کردن کاراکترهای خاص"""
        try:
            if not text:
                return ""
            
            # escape کردن کاراکترهای خاص HTML
            text = html.escape(text)
            
            # تبدیل markdown syntax به HTML
            # Bold: **text** -> <b>text</b>
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            
            # Headers: ## text -> <b>text</b>
            text = re.sub(r'^## (.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
            
            # Italic: *text* -> <i>text</i>
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            
            # Code: `text` -> <code>text</code>
            text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
            
            # پاک کردن خطوط جداکننده markdown
            text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^─+$', '', text, flags=re.MULTILINE)
            
            # پاک کردن خطوط خالی اضافی
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {e}")
            # در صورت خطا، فقط escape کردن کاراکترهای HTML
            return html.escape(str(text)) if text else ""
                                    
    # =========================
    # توابع پنل ادمین
    # =========================

    async def show_admin_panel(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی پنل مدیریت"""
        user_id = query.from_user.id
        
        if not self.admin_manager.is_admin(user_id):
            await query.answer("⛔ شما دسترسی ادمین ندارید.", show_alert=True)
            return

        message = "🔧 **پنل مدیریت MrTrader**\n\nلطفا یک گزینه را برای مدیریت انتخاب کنید:"
        keyboard = [
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def show_user_management(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
        """مدیریت کاربران با نمایش لیست صفحه‌بندی شده"""
        try:
            per_page = 5
            users_list = self.user_manager.get_all_users_paginated(page=page, per_page=per_page)
            total_users = self.user_manager.count_all_users()
            
            if total_users == 0:
                total_pages = 1
            else:
                total_pages = (total_users + per_page - 1) // per_page

            message_text = f"👥 **مدیریت کاربران ({total_users} کل)** - صفحه {page}/{total_pages}\n"
            message_text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            keyboard = []
            if not users_list:
                message_text += "هیچ کاربری برای نمایش وجود ندارد."
            else:
                for user in users_list:
                    user_id_db = user.get('telegram_id')
                    first_name = user.get('first_name', 'کاربر')
                    last_name = user.get('last_name', '')
                    username = f"(@{user.get('username')})" if user.get('username') else ""
                    
                    label = f"{first_name} {last_name} {username}".strip()
                    callback = f"admin_view_user:{user_id_db}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

            # ساخت دکمه‌های صفحه‌بندی
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_users:{page-1}"))
            
            if total_pages > 1:
                pagination_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))

            if page < total_pages:
                pagination_row.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"admin_users:{page+1}"))
            
            if pagination_row:
                keyboard.append(pagination_row)

            keyboard.append([InlineKeyboardButton("⬅️ بازگشت به پنل ادمین", callback_data="admin_panel")])
            
            await query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in show_user_management: {e}", exc_info=True)
            await query.edit_message_text("⛔ خطا در نمایش لیست کاربران.")

    async def show_user_details_for_admin(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """اطلاعات کامل یک کاربر را برای ادمین نمایش می‌دهد"""
        
        if not target_user_id:
            await query.edit_message_text("⛔ آیدی کاربر مشخص نشده است.")
            return

        user_data = self.user_manager.get_user_by_telegram_id(target_user_id)

        if not user_data:
            await query.edit_message_text(f"⛔ کاربری با آیدی <code>{target_user_id}</code> یافت نشد.", parse_mode="HTML")
            return

        # escape کردن داده‌ها
        first_name = html.escape(user_data.get('first_name') or '')
        last_name = html.escape(user_data.get('last_name') or '')
        phone_number = html.escape(user_data.get('phone_number') or 'ثبت نشده')
        package = html.escape(str(user_data.get('package', 'ندارد')).upper())
        entry_date = html.escape(user_data.get('entry_date') or 'نامشخص')
        last_activity = html.escape(user_data.get('last_activity') or 'نامشخص')
        balance = f"{user_data.get('balance', 0):,}"
        
        is_blocked_text = "✅ بله" if user_data.get('is_blocked') else "❌ خیر"
        is_expired, days_left = self.user_manager.is_package_expired(target_user_id)
        expiry_text = "منقضی شده" if is_expired else f"{days_left} روز باقیمانده"
        
        raw_username = user_data.get('username')
        username_display = f"<a href='https://t.me/{raw_username}'>@{raw_username}</a>" if raw_username else "ندارد"

        details_message = (
            f"👤 <b>پروفایل کاربر: {first_name} {last_name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>آیدی تلگرام:</b> <code>{target_user_id}</code>\n"
            f"👤 <b>نام کاربری:</b> {username_display}\n"
            f"📱 <b>شماره تلفن:</b> <code>{phone_number}</code>\n"
            f"--- \n"
            f"📦 <b>پکیج فعلی:</b> <b>{package}</b>\n"
            f"⏰ <b>اعتبار پکیج:</b> {expiry_text}\n"
            f"💰 <b>موجودی کیف پول:</b> <code>{balance} تومان</code>\n"
            f"--- \n"
            f"📅 <b>تاریخ عضویت:</b> {entry_date}\n"
            f"🕒 <b>آخرین فعالیت:</b> {last_activity}\n"
            f"🚫 <b>مسدود شده:</b> {is_blocked_text}\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🚫 مسدود کردن", callback_data=f"admin_block:{target_user_id}"),
                InlineKeyboardButton("✅ آزاد کردن", callback_data=f"admin_unblock:{target_user_id}")
            ],
            [
                InlineKeyboardButton("📦 تغییر پکیج", callback_data=f"admin_change_pkg:{target_user_id}"),
                InlineKeyboardButton("💰 شارژ کیف پول", callback_data=f"admin_charge_wallet:{target_user_id}")
            ],
            [InlineKeyboardButton("💬 ارسال پیام", callback_data=f"admin_send_msg:{target_user_id}")],
            [InlineKeyboardButton("⬅️ بازگشت به لیست", callback_data="admin_users:1")]
        ]

        await query.edit_message_text(
            details_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    async def handle_user_block(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """مسدود کردن کاربر"""
        success = self.user_manager.block_user(target_user_id)
        if success:
            await query.answer("✅ کاربر با موفقیت مسدود شد.", show_alert=True)
            await self.notify_user(context, target_user_id, "🚫 حساب کاربری شما توسط مدیریت مسدود شد.")
            await self.show_user_details_for_admin(query, context, target_user_id)
        else:
            await query.answer("⛔ خطا در مسدود کردن کاربر.", show_alert=True)

    async def handle_user_unblock(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """آزاد کردن کاربر"""
        success = self.user_manager.unblock_user(target_user_id)
        if success:
            await query.answer("✅ کاربر با موفقیت آزاد شد.", show_alert=True)
            await self.notify_user(context, target_user_id, "✅ حساب کاربری شما مجدداً فعال شد.")
            await self.show_user_details_for_admin(query, context, target_user_id)
        else:
            await query.answer("⛔ خطا در آزاد کردن کاربر.", show_alert=True)

    async def show_change_package_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """نمایش منوی تغییر پکیج کاربر"""
        user_data = self.user_manager.get_user_by_telegram_id(target_user_id)
        if not user_data:
            await query.edit_message_text("⛔ کاربر یافت نشد.")
            return
        
        current_package = user_data.get('package', 'demo')
        message = f"📦 **تغییر پکیج کاربر**\n\n👤 کاربر: `{target_user_id}`\n📦 پکیج فعلی: `{current_package.upper()}`\n\nلطفاً پکیج جدید را انتخاب کنید:"
        
        keyboard = [
            [
                InlineKeyboardButton("🆓 DEMO", callback_data=f"pkg_change_demo:{target_user_id}"),
                InlineKeyboardButton("🥉 BASIC", callback_data=f"pkg_change_basic:{target_user_id}")
            ],
            [
                InlineKeyboardButton("🥈 PREMIUM", callback_data=f"pkg_change_premium:{target_user_id}"),
                InlineKeyboardButton("🥇 VIP", callback_data=f"pkg_change_vip:{target_user_id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_view_user:{target_user_id}")]
        ]
        
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_package_change(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, package_type: str, target_user_id: int):
        """پردازش تغییر پکیج کاربر توسط ادمین"""
        try:
            # تغییر پکیج کاربر
            success = self.user_manager.update_user(target_user_id, package=package_type)
            
            if success:
                package_names = {
                    'demo': 'دمو',
                    'basic': 'پایه', 
                    'premium': 'ویژه',
                    'vip': 'VIP'
                }
                
                notification_message = f"📦 پکیج شما به <b>{package_names.get(package_type, package_type)}</b> تغییر یافت."
                
                await self.notify_user(context, target_user_id, notification_message)
                
                await query.edit_message_text(
                    f"✅ <b>پکیج با موفقیت تغییر یافت</b>\n\n👤 کاربر: <code>{target_user_id}</code>\n📦 پکیج جدید: <code>{package_type.upper()}</code>\n\n✉️ اطلاعیه به کاربر ارسال شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("👁️ مشاهده کاربر", callback_data=f"admin_view_user:{target_user_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_users")]
                    ]),
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text("⛔ خطا در تغییر پکیج کاربر")
                
        except Exception as e:
            logger.error(f"Error changing package: {e}")
            await query.edit_message_text("⛔ خطا در پردازش درخواست")

    async def show_charge_wallet_form(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """نمایش فرم شارژ کیف پول"""
        context.user_data['awaiting_charge_amount'] = target_user_id
        message = f"💰 **شارژ کیف پول کاربر**\n\n👤 کاربر: `{target_user_id}`\n\nلطفاً مبلغ مورد نظر برای شارژ را به تومان وارد کنید.\n\nبرای لغو /cancel را ارسال کنید."
        await query.edit_message_text(text=message, parse_mode="Markdown")

    async def show_send_message_form(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """نمایش فرم ارسال پیام"""
        context.user_data['awaiting_message_for'] = target_user_id
        message = f"💬 **ارسال پیام به کاربر**\n\n👤 کاربر: `{target_user_id}`\n\nلطفاً متن پیام خود را ارسال کنید.\n\nبرای لغو /cancel را ارسال کنید."
        await query.edit_message_text(message, parse_mode="Markdown")

    async def handle_admin_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام متنی ادمین برای شارژ کیف پول یا ارسال پیام"""
        user_id = update.effective_user.id
        text = update.message.text

        # بررسی دسترسی ادمین
        if not self.admin_manager.is_admin(user_id):
            return

        # لغو عملیات
        if text == "/cancel":
            context.user_data.clear()
            await update.message.reply_text("عملیات لغو شد.")
            return

        # شارژ کیف پول
        if 'awaiting_charge_amount' in context.user_data:
            target_user_id = context.user_data['awaiting_charge_amount']
            try:
                amount = float(text)
                if amount <= 0:
                    await update.message.reply_text("⛔ مبلغ باید مثبت باشد. لطفاً مبلغ معتبر وارد کنید.")
                    return

                success = self.user_manager.add_balance(target_user_id, amount)
                if success:
                    await update.message.reply_text(
                        f"✅ کیف پول کاربر `{target_user_id}` با موفقیت به مبلغ `{amount:,.0f}` تومان شارژ شد.", 
                        parse_mode="Markdown"
                    )
                    # اطلاع‌رسانی به کاربر
                    await self.notify_user(
                        context, 
                        target_user_id, 
                        f"✅ حساب شما به مبلغ <b>{amount:,.0f} تومان</b> توسط مدیریت شارژ شد."
                    )
                else:
                    await update.message.reply_text("⛔ خطا در شارژ کیف پول. لطفاً دوباره تلاش کنید.")
            except ValueError:
                await update.message.reply_text("⛔ مبلغ وارد شده نامعتبر است. لطفاً فقط عدد وارد کنید.")
                return

            context.user_data.clear()

        # ارسال پیام
        elif 'awaiting_message_for' in context.user_data:
            target_user_id = context.user_data['awaiting_message_for']
            success = await self.notify_user(context, target_user_id, f"📢 <b>پیام از مدیریت:</b>\n\n{text}")
            
            if success:
                await update.message.reply_text(
                    f"✅ پیام با موفقیت به کاربر `{target_user_id}` ارسال شد.\n\n📝 متن پیام:\n{text}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("⛔ خطا در ارسال پیام به کاربر.")

            context.user_data.clear()

    async def notify_user(self, context: ContextTypes.DEFAULT_TYPE, target_user_id: int, message: str):
        """ارسال پیام اطلاع‌رسانی به کاربر"""
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info(f"Notification sent to user {target_user_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to send notification to user {target_user_id}: {e}")
            return False

    # =========================
    # سایر توابع منو
    # =========================

    async def show_wallet_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی کیف پول"""
        try:
            user = query.from_user
            user_data = self.user_manager.get_user_by_telegram_id(user.id) or {}
            balance = user_data.get('balance', 0)
            
            wallet_message = f"""💰 <b>کیف پول شما</b>

💵 موجودی فعلی: <b>{balance:,}</b> تومان

از گزینه‌های زیر استفاده کنید:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ افزایش موجودی", callback_data="add_balance"),
                    InlineKeyboardButton("💳 برداشت", callback_data="withdraw")
                ],
                [InlineKeyboardButton("📊 تاریخچه تراکنش‌ها", callback_data="transaction_history")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                wallet_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing wallet menu: {e}")
            await query.edit_message_text("⛔ خطا در نمایش کیف پول.")

    async def show_strategy_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی استراتژی‌ها با timeout handling بهبود یافته"""
        try:
            user = query.from_user
            user_data = self.user_manager.get_user_by_telegram_id(user.id) or {}
            user_package = user_data.get('package', 'demo')
            
            message = f"""📊 <b>استراتژی‌های تحلیل MrTrader</b>

    🎯 <b>پکیج فعلی شما:</b> {user_package.upper()}

    📈 <b>انتخاب استراتژی مورد نظر:</b>"""
            
            try:
                # تلاش برای استفاده از KeyboardTemplates با timeout کوتاه‌تر
                import asyncio
                keyboard = await asyncio.wait_for(
                    self._build_strategy_keyboard_safe(user_package), 
                    timeout=2.0  # کاهش timeout به 2 ثانیه
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Strategy keyboard generation failed: {e}")
                # استفاده از کیبورد ساده fallback
                keyboard = self._build_simple_strategy_keyboard(user_package)

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing strategy menu: {e}")
            # در صورت هر خطایی، نمایش پیام ساده
            await query.edit_message_text(
                "❌ خطا در نمایش استراتژی‌ها. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="analysis_menu")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ]),
                parse_mode=ParseMode.HTML
            )

    async def _build_strategy_keyboard_safe(self, user_package: str) -> InlineKeyboardMarkup:
        """ساخت کیبورد استراتژی با error handling بهبود یافته"""
        try:
            # تلاش برای استفاده از KeyboardTemplates
            if hasattr(KeyboardTemplates, "strategy_menu"):
                return KeyboardTemplates.strategy_menu(user_package)
            else:
                return self._build_simple_strategy_keyboard(user_package)
        except Exception as e:
            logger.warning(f"KeyboardTemplates failed: {e}")
            return self._build_simple_strategy_keyboard(user_package)

    def _build_simple_strategy_keyboard(self, user_package: str = "demo") -> InlineKeyboardMarkup:
        """کیبورد ساده و سریع برای استراتژی‌ها - بهینه‌سازی شده"""
        try:
            # استراتژی‌های پایه برای هر پکیج - ساده‌تر و سریع‌تر
            if user_package in ["demo", "free"]:
                strategies = [
                    ("📊 تحلیل CCI", "select_strategy:cci_analysis"),
                    ("📈 تحلیل RSI", "select_strategy:rsi"),
                    ("🌊 تحلیل MACD", "select_strategy:macd"),
                    ("☁️ ابر ایچیموکو", "select_strategy:ichimoku")
                ]
            elif user_package == "basic":
                strategies = [
                    ("📊 تحلیل CCI", "select_strategy:cci_analysis"),
                    ("📈 تحلیل RSI", "select_strategy:rsi"),
                    ("🌊 تحلیل MACD", "select_strategy:macd"),
                    ("☁️ ابر ایچیموکو", "select_strategy:ichimoku"),
                    ("📈 تحلیل EMA", "select_strategy:ema_analysis"),
                    ("📉 Williams R", "select_strategy:williams_r_analysis")
                ]
            elif user_package == "premium":
                strategies = [
                    ("📊 تحلیل CCI", "select_strategy:cci_analysis"),
                    ("📈 تحلیل RSI", "select_strategy:rsi"),
                    ("🌊 تحلیل MACD", "select_strategy:macd"),
                    ("☁️ ابر ایچیموکو", "select_strategy:ichimoku"),
                    ("📈 تحلیل EMA", "select_strategy:ema_analysis"),
                    ("📉 Williams R", "select_strategy:williams_r_analysis"),
                    ("🕯️ تحلیل کندل استیک", "select_strategy:a_candlestick"),
                    ("⛰️ الگوی دو قله", "select_strategy:double_top_pattern"),
                    ("🌀 استراتژی فیبوناچی", "select_strategy:fibonacci_strategy"),
                    ("📊 باندهای بولینگر", "select_strategy:bollinger_bands")
                ]
            else:  # vip, ghost
                strategies = [
                    ("📊 تحلیل CCI", "select_strategy:cci_analysis"),
                    ("📈 تحلیل RSI", "select_strategy:rsi"),
                    ("🌊 تحلیل MACD", "select_strategy:macd"),
                    ("☁️ ابر ایچیموکو", "select_strategy:ichimoku"),
                    ("📈 تحلیل EMA", "select_strategy:ema_analysis"),
                    ("📉 Williams R", "select_strategy:williams_r_analysis"),
                    ("🕯️ تحلیل کندل استیک", "select_strategy:a_candlestick"),
                    ("⛰️ الگوی دو قله", "select_strategy:double_top_pattern"),
                    ("🌀 استراتژی فیبوناچی", "select_strategy:fibonacci_strategy"),
                    ("📊 باندهای بولینگر", "select_strategy:bollinger_bands"),
                    ("📊 تحلیل ATR", "select_strategy:atr"),
                    ("💎 الگوی الماس", "select_strategy:diamond_pattern"),
                    ("💎 تحلیل VWAP", "select_strategy:vwap"),
                    ("🎯 تحلیل CRT", "select_strategy:crt")
                ]
            
            # ساخت کیبورد به صورت 2 تا در هر ردیف
            keyboard = []
            for i in range(0, len(strategies), 2):
                row = []
                for j in range(2):
                    if i + j < len(strategies):
                        name, callback = strategies[i + j]
                        row.append(InlineKeyboardButton(name, callback_data=callback))
                if row:
                    keyboard.append(row)
            
            # دکمه‌های اضافی
            keyboard.append([
                InlineKeyboardButton("💎 ارتقا پکیج", callback_data="packages_menu"),
                InlineKeyboardButton("ℹ️ راهنما", callback_data="help_menu")
            ])
            keyboard.append([
                InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error building simple strategy keyboard: {e}")
            # حتی در fallback نیز خطا، کیبورد بسیار ساده
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 تحلیل CCI", callback_data="select_strategy:cci_analysis")],
                [InlineKeyboardButton("📈 تحلیل RSI", callback_data="select_strategy:rsi")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ])
        
        
    def _build_strategy_keyboard_fallback(self, user_package: str = "free") -> InlineKeyboardMarkup:
        """Fallback برای زمانی که KeyboardTemplates.strategy_menu قابل استفاده نباشد"""
        kb = []
        try:
            categories = getattr(Config, "STRATEGY_CATEGORIES", None)
            names_map = getattr(Config, "STRATEGY_NAMES", {})

            if categories and isinstance(categories, dict):
                for cat, strategies in categories.items():
                    kb.append([InlineKeyboardButton(f"— {cat} —", callback_data=f"info_{cat}")])
                    for i in range(0, min(len(strategies), 4), 2):
                        row = []
                        for j in range(2):
                            if i + j < len(strategies):
                                s = strategies[i + j]
                                label = names_map.get(s, s.replace('_', ' ').title())
                                row.append(InlineKeyboardButton(label, callback_data=f"strategy_{s}"))
                        if row:
                            kb.append(row)
            else:
                sample = ["demo_price_action", "demo_rsi", "strategy_rsi", "strategy_macd"]
                for i in range(0, len(sample), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(sample):
                            s = sample[i + j]
                            label = s.replace('_', ' ').title()
                            row.append(InlineKeyboardButton(label, callback_data=f"strategy_{s}"))
                    kb.append(row)

        except Exception as e:
            logger.warning(f"Strategy keyboard fallback generation failed: {e}")
            kb = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]

        kb.append([InlineKeyboardButton("💎 ارتقا پکیج", callback_data="packages_menu")])
        kb.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")])

        return InlineKeyboardMarkup(kb)

    async def show_packages_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        message = """💎 <b>پکیج‌های MrTrader Bot</b>

🎯 <b>انتخاب پکیج مناسب برای نیازهای تحلیلی شما:</b>

🆓 <b>DEMO</b> - رایگان، 5 تحلیل روزانه
🥉 <b>BASIC</b> - پایه و کاربردی
🥈 <b>PREMIUM</b> - پیشرفته و حرفه‌ای  
🏆 <b>VIP</b> - کامل و بی‌نظیر

برای مشاهده جزئیات هر پکیج، روی آن کلیک کنید."""
        
        try:
            keyboard = KeyboardTemplates.packages_menu()
        except:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    async def show_referral_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = query.from_user
            user_data = self.user_manager.get_user_by_telegram_id(user.id) or {}
            
            referral_code = user_data.get('referral_code', self.user_manager.generate_referral_code())
            
            if not user_data.get('referral_code'):
                self.user_manager.update_user(user.id, referral_code=referral_code)
            
            referral_stats = {
                'total_referrals': 0,
                'total_commission': 0,
                'available_commission': 0
            }
            
            message = f"""🎁 <b>سیستم دعوت از دوستان</b>

🔗 <b>لینک دعوت شما:</b>
<code>https://t.me/MrTraderBot?start=ref_{referral_code}</code>

📊 <b>آمار شما:</b>
👥 تعداد دعوت شدگان: <b>{referral_stats['total_referrals']}</b>
💰 کل کمیسیون: <b>{referral_stats['total_commission']:,} تومان</b>
💳 قابل برداشت: <b>{referral_stats['available_commission']:,} تومان</b>

🎯 <b>نرخ کمیسیون:</b>
• پکیج Basic: 10%
• پکیج Premium: 15%
• پکیج VIP: 20%

لینک خود را با دوستان به اشتراک بگذارید!"""
            
            keyboard = [
                [InlineKeyboardButton("📊 آمار تفصیلی", callback_data="referral_stats")],
                [InlineKeyboardButton("💰 برداشت کمیسیون", callback_data="claim_rewards")],
                [InlineKeyboardButton("📤 اشتراک‌گذاری", 
                                    url=f"https://t.me/share/url?url=https://t.me/MrTraderBot?start=ref_{referral_code}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"Error showing referral menu: {e}")
            await query.edit_message_text("⛔ خطا در نمایش منوی رفرال.")

    async def show_help_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        message = """📚 <b>راهنمای MrTrader Bot</b>

🎯 <b>راهنماهای موجود:</b>

🚀 شروع کار - نحوه استفاده از ربات
📊 استراتژی‌ها - توضیح انواع تحلیل‌ها  
💎 پکیج‌ها - مقایسه و انتخاب پکیج
❓ سوالات متداول - پاسخ سوالات رایج

💡 <b>نکته:</b> برای دریافت راهنمای هر بخش، روی آن کلیک کنید."""
        
        try:
            keyboard = KeyboardTemplates.help_menu()
        except:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    async def show_support_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        message = """📞 <b>پشتیبانی MrTrader</b>

چگونه می‌توانیم کمکتان کنیم؟

📧 ایمیل: support@mrtrader.com
💬 تلگرام: @mrtrader_support
⏰ پاسخگویی: 9 صبح تا 9 شب"""
        
        keyboard = [
            [InlineKeyboardButton("💬 چت با پشتیبان", url="https://t.me/mrtrader_support")],
            [InlineKeyboardButton("❓ سوالات متداول", callback_data="help_faq")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    async def handle_simple_callbacks(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str):
        """پردازش callback های ساده"""
        simple_message = "این بخش در حال توسعه است."
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        await query.edit_message_text(simple_message, reply_markup=InlineKeyboardMarkup(keyboard))

    # =========================
    # Get Handlers
    # =========================

    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CallbackQueryHandler(self.handle_callback_query),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_text_message)
        ]

# Export
__all__ = ['CallbackHandler']