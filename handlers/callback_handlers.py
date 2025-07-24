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
        
        # نقشه callback ها به توابع - بروزرسانی شده
        self.callback_map = {
            # منوی اصلی و پروفایل
            'main_menu': self.show_main_menu,
            'user_profile': self.show_user_profile,
            'wallet_menu': self.show_wallet_menu,
            'help_menu': self.show_help_menu,
            'support_menu': self.show_support_menu,
            
            # استراتژی‌ها و تحلیل
            'analysis_menu': self.show_strategy_menu,
            'menu_strategy': self.show_strategy_menu,
            'coins_list': self.show_coins_list,
            'price_chart': self.show_price_chart,
            'price_alert': self.show_price_alert,
            'signals_menu': self.show_signals_menu,
            'market_news': self.show_market_news,
            
            # پکیج‌ها و پرداخت
            'packages_menu': self.show_packages_menu,
            'menu_packages': self.show_packages_menu,
            'referral_menu': self.show_referral_menu,
            
            # سایر callback های موجود...
            'pkg_select': self.handle_package_selection,
            'payment_methods': self.show_payment_methods,
            'show_referral': self.show_referral_menu,
            'referral_stats': self.show_referral_stats,
            'claim_rewards': self.handle_claim_rewards,
            'show_reports': self.show_reports_menu,
            'daily_report': self.show_daily_report,
            'weekly_report': self.show_weekly_report,
            'user_report': self.show_user_report,
            'contact_support': self.contact_support,
            'support_contact': self.contact_support,
            'create_ticket': self.create_support_ticket,
            'admin_panel': self.show_admin_panel,
            'user_management': self.show_user_management,
            'system_stats': self.show_system_statistics,
            'broadcast_message': self.handle_broadcast_message,
            'show_help': self.show_help_menu,
            'help_getting_started': self.show_getting_started_help,
            'help_strategies': self.show_strategies_help,
            'help_packages': self.show_packages_help,
            'help_faq': self.show_faq,
            'back': self.handle_back_action,
            'cancel': self.handle_cancel_action,
            'refresh': self.handle_refresh_action
        }
    
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
                # یافتن تابع مناسب در نقشه
                handler_function = self.callback_map.get(action)
                if handler_function:
                    await handler_function(query, context)
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
            
            keyboard = KeyboardTemplates.strategy_menu(user_package)
            
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
    
    # بقیه متدها همانطور که بودند، فقط اطمینان از عدم استفاده از await برای متدهای sync
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CallbackQueryHandler(self.handle_callback_query)
        ]


# Export
__all__ = ['CallbackHandler']