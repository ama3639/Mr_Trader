"""
هندلرهای پردازش Callback Query برای MrTrader Bot - Fixed Version
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
from datetime import datetime

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
from utils.helpers import extract_signal_details
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
        
        # <- بعد (نگاشت به نام متدها به صورت رشته؛ کمترین تغییر در ساختار)
        # نقشه callback ها به توابع - بروزرسانی شده (از bound methods به نام متدها)
        self.callback_map = {
            # منوی اصلی و پروفایل
            'main_menu': 'show_main_menu',
            'user_profile': 'show_user_profile',
            'wallet_menu': 'show_wallet_menu',
            'help_menu': 'show_help_menu',
            'support_menu': 'show_support_menu',

            # استراتژی‌ها و تحلیل
            'analysis_menu': 'show_strategy_menu',
            'menu_strategy': 'show_strategy_menu',
            'coins_list': 'show_coins_list',
            'price_chart': 'show_price_chart',
            'price_alert': 'show_price_alert',
            'signals_menu': 'show_signals_menu',
            'market_news': 'show_market_news',

            # پکیج‌ها و پرداخت
            'packages_menu': 'show_packages_menu',
            'menu_packages': 'show_packages_menu',
            'referral_menu': 'show_referral_menu',

            # سایر callback های موجود...
            'pkg_select': 'handle_package_selection',
            'payment_methods': 'show_payment_methods',
            'show_referral': 'show_referral_menu',
            'referral_stats': 'show_referral_stats',
            'claim_rewards': 'handle_claim_rewards',
            'show_reports': 'show_reports_menu',
            'daily_report': 'show_daily_report',
            'weekly_report': 'show_weekly_report',
            'user_report': 'show_user_report',
            'contact_support': 'contact_support',
            'support_contact': 'contact_support',
            'create_ticket': 'create_support_ticket',
            'admin_panel': 'show_admin_panel',
            'user_management': 'show_user_management',
            'system_stats': 'show_system_statistics',
            'broadcast_message': 'handle_broadcast_message',
            'show_help': 'show_help_menu',
            'help_getting_started': 'show_getting_started_help',
            'help_strategies': 'show_strategies_help',
            'help_packages': 'show_packages_help',
            'help_faq': 'show_faq',
            'back': 'handle_back_action',
            'cancel': 'handle_cancel_action',
            'refresh': 'handle_refresh_action'
        }
    def _build_strategy_keyboard_fallback(self, user_package: str = "free") -> InlineKeyboardMarkup:
        """
        Fallback برای زمانی که KeyboardTemplates.strategy_menu قابل استفاده نباشد.
        تولید یک کیبورد ساده و امن که از Config/KeyboardTemplates پویا استفاده کند.
        """
        kb = []
        try:
            # اگر Config دسته‌بندی‌ها/نام‌ها را دارد، از آن استفاده کن
            categories = getattr(Config, "STRATEGY_CATEGORIES", None)
            names_map = getattr(Config, "STRATEGY_NAMES", {})

            if categories and isinstance(categories, dict):
                for cat, strategies in categories.items():
                    # عنوان دسته (غیرقابل کلیک)
                    kb.append([InlineKeyboardButton(f"— {cat} —", callback_data=f"info_{cat}")])
                    # اضافه کردن حداکثر 4 استراتژی در هر دسته (برای جلوگیری از شلوغی)
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
                # اگر Config نبود، حداقل چند دکمه نمونه بساز
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
            # حداقل یک دکمه بازگشت در هر صورت
            kb = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]

        # دکمه‌های نهایی: ارتقا و بازگشت
        kb.append([InlineKeyboardButton("💎 ارتقا پکیج", callback_data="menu_packages")])
        kb.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")])

        return InlineKeyboardMarkup(kb)

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
            
            # بررسی امنیت - بدون await چون sync است
            if hasattr(self.security_manager, 'is_user_allowed'):
                is_allowed = self.security_manager.is_user_allowed(user.id)
                if not is_allowed:
                    await query.edit_message_text("❌ دسترسی شما محدود شده است.")
                    return
            
            # پردازش callback با در نظر گیری پارامترها
            await self._process_callback(query, context, callback_data)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                await query.edit_message_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except:
                pass
    
    async def _process_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """پردازش callback بر اساس نوع"""
        try:
            # تجزیه callback data (ممکن است شامل پارامتر باشد)
            if '|' in callback_data:
                # برای callback های پیچیده با پارامترهای متعدد
                parts = callback_data.split('|')
                action = parts[0]
                params = parts[1:] if len(parts) > 1 else []
            elif ':' in callback_data:
                # برای callback های ساده با یک پارامتر
                parts = callback_data.split(':', 1)
                action = parts[0]
                params = [parts[1]] if len(parts) > 1 else []
            else:
                action = callback_data
                params = []
            
            # ذخیره پارامترها در context
            if params:
                context.user_data['callback_params'] = params
            
            # بررسی callback های مرحله‌ای (4 مرحله انتخاب)
            if action.startswith('strategy_'):
                await self.handle_strategy_selection(query, context, action)
            elif action.startswith('symbol_'):
                await self.handle_symbol_selection(query, context, action, params)
            elif action.startswith('currency_'):
                await self.handle_currency_selection(query, context, action, params)
            elif action.startswith('timeframe_'):
                await self.handle_timeframe_selection(query, context, action, params)
            elif action.startswith('manual_'):
                await self.handle_manual_input(query, context, action, params)
            elif action.startswith('pkg_select_'):
                await self.handle_package_selection(query, context, action)
            elif action.startswith('buy_'):
                await self.handle_package_purchase(query, context, action, params)
            elif action.startswith('admin_'):
                await self.handle_admin_action(query, context, action, params)
            else:
                # <- بعد (resolve کردن entry به صورت رشته یا callback واقعی)
                # یافتن تابع مناسب در نقشه و resolve کردن آن در زمان اجرا
                handler_entry = self.callback_map.get(action)
                handler_function = None

                if handler_entry:
                    # اگر نگاشت به صورت نام متد (رشته) است، getattr کنیم
                    if isinstance(handler_entry, str):
                        handler_function = getattr(self, handler_entry, None)
                        if handler_function is None:
                            logger.warning(f"Callback mapped to method name '{handler_entry}' but method not found on CallbackHandler.")
                    else:
                        # فرض می‌کنیم مستقیم یک callable باشد
                        handler_function = handler_entry

                if handler_function:
                    try:
                        await handler_function(query, context)
                    except Exception as hf_err:
                        logger.error(f"Error while executing callback handler for action '{action}': {hf_err}")
                        await query.edit_message_text("❌ خطا در اجرای عملیات.")
                else:
                    await query.edit_message_text("❌ عمل نامشخص.")
                
        except Exception as e:
            logger.error(f"Error processing callback {callback_data}: {e}")
            await query.edit_message_text("❌ خطا در پردازش درخواست.")
    
    # =========================
    # هندلرهای منوی اصلی - جدید
    # =========================
    
    async def show_main_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی"""
        try:
            user = query.from_user
            user_data = UserManager.safe_get_user(user.id)
            
            user_package = user_data.get('package', 'demo')
            
            # بررسی ادمین بودن
            is_admin = False
            if hasattr(self.admin_manager, 'is_admin'):
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
            
            # اضافه کردن دکمه ادمین
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
            await query.edit_message_text("❌ خطا در نمایش منو.")
    
    async def show_wallet_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی کیف پول"""
        try:
            user = query.from_user
            user_data = UserManager.safe_get_user(user.id)
            
            balance = user_data.get('balance', 0)
            
            wallet_message = f"""💰 <b>کیف پول شما</b>

💵 موجودی فعلی: <b>{balance:,}</b> تومان

از گزینه‌های زیر استفاده کنید:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ افزایش موجودی", callback_data="add_balance"),
                    InlineKeyboardButton("💳 برداشت", callback_data="withdraw")
                ],
                [
                    InlineKeyboardButton("📊 تاریخچه تراکنش‌ها", callback_data="transaction_history")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                wallet_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing wallet menu: {e}")
            await query.edit_message_text("❌ خطا در نمایش کیف پول.")
    
    async def show_coins_list(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست ارزها"""
        try:
            message = """💎 <b>لیست ارزهای دیجیتال</b>

🔄 در حال دریافت قیمت‌ها...

لطفاً کمی صبر کنید."""
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="coins_list")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing coins list: {e}")
    
    async def show_price_chart(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش نمودار قیمت"""
        try:
            message = """📈 <b>نمودار قیمت</b>

برای مشاهده نمودار، ابتدا ارز مورد نظر را انتخاب کنید:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("₿ BTC", callback_data="chart_BTC"),
                    InlineKeyboardButton("♦️ ETH", callback_data="chart_ETH"),
                    InlineKeyboardButton("🔶 BNB", callback_data="chart_BNB")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing price chart menu: {e}")
    
    async def show_price_alert(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تنظیمات هشدار قیمت"""
        try:
            message = """🔔 <b>تنظیم هشدار قیمت</b>

⚠️ این قابلیت در حال توسعه است.

به زودی می‌توانید برای قیمت‌های مورد نظر خود هشدار تنظیم کنید."""
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing price alert menu: {e}")
    
    async def show_signals_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سیگنال‌ها"""
        try:
            message = """🎯 <b>سیگنال‌های معاملاتی</b>

📊 برای دریافت سیگنال، ابتدا تحلیل انجام دهید.

سیگنال‌های اخیر شما:
• هنوز سیگنالی ندارید"""
            
            keyboard = [
                [InlineKeyboardButton("📊 انجام تحلیل", callback_data="analysis_menu")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing signals menu: {e}")
    
    async def show_market_news(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش اخبار بازار"""
        try:
            message = """📰 <b>اخبار بازار ارزهای دیجیتال</b>

📡 در حال دریافت آخرین اخبار...

⚠️ این قابلیت به زودی راه‌اندازی می‌شود."""
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing market news: {e}")
    
    async def show_support_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی پشتیبانی"""
        try:
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
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing support menu: {e}")
    
    # =========================
    # اصلاح هندلرهای موجود
    # =========================
    
    async def show_user_profile(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پروفایل کاربر - FIXED: حذف await"""
        try:
            user = query.from_user
            # حذف await چون get_user_by_telegram_id یک تابع sync است
            user_data = self.user_manager.get_user_by_telegram_id(user.id)
            
            if not user_data:
                await query.edit_message_text("❌ اطلاعات کاربری یافت نشد.")
                return
            
            # استفاده از safe_get_user برای اطمینان
            user_data = UserManager.safe_get_user(user.id)
            
            user_package = user_data.get('package', 'demo')
            
            # بررسی انقضا - بدون await
            is_expired, days_left = UserManager.is_package_expired(user.id)
            
            # بررسی ادمین بودن
            is_admin = False
            if hasattr(self.admin_manager, 'is_admin'):
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
            
            # اضافه کردن دکمه ادمین
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
            await query.edit_message_text("❌ خطا در نمایش پروفایل.")
    
    async def show_strategy_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی استراتژی‌ها"""
        try:
            user = query.from_user
            user_data = UserManager.safe_get_user(user.id)
            user_package = user_data.get('package', 'demo')
            
            message = f"""📊 <b>استراتژی‌های تحلیل MrTrader</b>

    🎯 <b>پکیج فعلی شما:</b> {user_package.upper()}

    📈 <b>انتخاب استراتژی مورد نظر:</b>"""
            
            # تلاش برای استفاده از قالب اصلی؛ در صورت خطا از فالن‌بک استفاده کن
            try:
                if hasattr(KeyboardTemplates, "strategy_menu"):
                    try:
                        keyboard = KeyboardTemplates.strategy_menu(user_package)
                    except Exception as kt_e:
                        logger.warning(f"KeyboardTemplates.strategy_menu raised: {kt_e}; using fallback.")
                        keyboard = self._build_strategy_keyboard_fallback(user_package)
                else:
                    keyboard = self._build_strategy_keyboard_fallback(user_package)
            except Exception as final_kb_err:
                logger.error(f"Failed to build strategy keyboard: {final_kb_err}")
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]])

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing strategy menu: {e}")
            await query.edit_message_text("❌ خطا در نمایش استراتژی‌ها.")
    
    async def show_referral_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سیستم رفرال"""
        try:
            user = query.from_user
            user_data = UserManager.safe_get_user(user.id)
            
            referral_code = user_data.get('referral_code', UserManager.generate_referral_code())
            
            # اگر کد رفرال ندارد، یکی بسازیم
            if not user_data.get('referral_code'):
                UserManager.update_user(user.id, referral_code=referral_code)
            
            # محاسبه آمار رفرال
            referral_stats = {
                'total_referrals': 0,
                'total_commission': 0,
                'available_commission': 0
            }
            
            # اگر referral_manager موجود بود
            if hasattr(self.referral_manager, 'get_user_referral_data'):
                try:
                    stats = self.referral_manager.get_user_referral_data(user.id)
                    if stats:
                        referral_stats.update(stats)
                except:
                    pass
            
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
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing referral menu: {e}")
            await query.edit_message_text("❌ خطا در نمایش منوی رفرال.")

    async def handle_package_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """هندلر موقت برای انتخاب پکیج - این متد برای رفع خطا اضافه شده است"""
        try:
            await query.edit_message_text(
                "🛒 بخش انتخاب پکیج در حال توسعه است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
                ])
            )
        except Exception as e:
            logger.error(f"Error in placeholder handle_package_selection: {e}")

    # =========================
    # بقیه متدهای موجود بدون تغییر
    # =========================
    
    async def handle_strategy_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str):
        """مرحله 1: انتخاب استراتژی"""
        try:
            user = query.from_user
            strategy = action.replace('strategy_', '')
            
            # بررسی دسترسی به استراتژی
            can_use = True
            message = ""
            if hasattr(StrategyManager, 'can_use_strategy'):
                can_use, message = StrategyManager.can_use_strategy(user.id, strategy)
            
            if not can_use:
                await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # ذخیره استراتژی انتخاب شده
            context.user_data['selected_strategy'] = strategy
            
            # نمایش معرفی استراتژی و انتخاب نماد
            user_data = UserManager.safe_get_user(user.id)
            user_package = user_data.get('package', 'demo')
            
            strategy_intro = MessageTemplates.strategy_intro(strategy, user_package)
            
            intro_message = f"""{strategy_intro}

━━━━━━━━━━━━━━━━━━━━━━
🪙 **مرحله 1: انتخاب نماد ارز**

لطفاً ارز مورد نظر خود را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.symbol_selection(strategy)
            
            await query.edit_message_text(
                intro_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling strategy selection: {e}")
    
    async def show_packages_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی پکیج‌ها"""
        try:
            message = """💎 <b>پکیج‌های MrTrader Bot</b>

🎯 <b>انتخاب پکیج مناسب برای نیازهای تحلیلی شما:</b>

🆓 <b>DEMO</b> - رایگان، 5 تحلیل روزانه
🥉 <b>BASIC</b> - پایه و کاربردی
🥈 <b>PREMIUM</b> - پیشرفته و حرفه‌ای  
👑 <b>VIP</b> - کامل و بی‌نظیر

برای مشاهده جزئیات هر پکیج، روی آن کلیک کنید."""
            
            keyboard = KeyboardTemplates.packages_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing packages menu: {e}")
    
    async def show_help_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی راهنما"""
        try:
            message = """📚 <b>راهنمای MrTrader Bot</b>

🎯 <b>راهنماهای موجود:</b>

🚀 شروع کار - نحوه استفاده از ربات
📊 استراتژی‌ها - توضیح انواع تحلیل‌ها  
💎 پکیج‌ها - مقایسه و انتخاب پکیج
❓ سوالات متداول - پاسخ سوالات رایج

💡 <b>نکته:</b> برای دریافت راهنمای هر بخش، روی آن کلیک کنید."""
            
            keyboard = KeyboardTemplates.help_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing help menu: {e}")
    
    # متدهای موقت برای رفع خطا
    async def show_payment_methods(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_referral_stats(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def handle_claim_rewards(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_reports_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_daily_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_weekly_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_user_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def contact_support(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def create_support_ticket(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_admin_panel(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل مدیریت برای ادمین"""
        if AdminManager.is_admin(query.from_user.id):
            await query.edit_message_text("❌ شما دسترسی به پنل مدیریت ندارید.")
            return

        # ساختار دکمه‌های پنل ادمین
        message = "پنل مدیریت\n\nانتخاب کنید:"
        keyboard = [
            [InlineKeyboardButton("مدیریت کاربران", callback_data="admin:manage_users")],
            [InlineKeyboardButton("مدیریت پکیج‌ها", callback_data="admin:manage_packages")],
            [InlineKeyboardButton("مدیریت گزارش‌ها", callback_data="admin:manage_reports")],
            [InlineKeyboardButton("بازگشت", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


    async def show_user_management(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_system_statistics(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def handle_broadcast_message(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_getting_started_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_strategies_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_packages_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def show_faq(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def handle_back_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def handle_cancel_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    async def handle_refresh_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        await query.edit_message_text("این بخش در حال توسعه است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))

    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CallbackQueryHandler(self.handle_callback_query)
        ]


# Export
__all__ = ['CallbackHandler']