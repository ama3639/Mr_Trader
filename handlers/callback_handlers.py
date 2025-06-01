"""
هندلرهای پردازش Callback Query برای MrTrader Bot
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
        
        # نقشه callback ها به توابع
        self.callback_map = {
            # ثبت‌نام و شروع
            'register_user': self.handle_user_registration,
            'show_terms': self.show_terms_and_conditions,
            'accept_terms': self.handle_terms_acceptance,
            'main_menu': self.show_main_menu,
            
            # منوهای اصلی
            'menu_strategy': self.show_strategy_menu,
            'menu_packages': self.show_packages_menu,
            'menu_live_prices': self.show_live_prices_menu,
            'menu_help': self.show_help_menu,
            'user_profile': self.show_user_profile,
            
            # مرحله 1: انتخاب استراتژی (strategy_*)
            # مرحله 2: انتخاب نماد (symbol_*)
            # مرحله 3: انتخاب ارز مرجع (currency_*)  
            # مرحله 4: انتخاب تایم‌فریم (timeframe_*)
            
            # پکیج‌ها و پرداخت
            'pkg_select': self.handle_package_selection,
            'payment_methods': self.show_payment_methods,
            
            # رفرال
            'show_referral': self.show_referral_menu,
            'referral_stats': self.show_referral_stats,
            'claim_rewards': self.handle_claim_rewards,
            
            # گزارش‌ها
            'show_reports': self.show_reports_menu,
            'daily_report': self.show_daily_report,
            'weekly_report': self.show_weekly_report,
            'user_report': self.show_user_report,
            
            # پشتیبانی
            'contact_support': self.contact_support,
            'create_ticket': self.create_support_ticket,
            'support_contact': self.contact_support,
            
            # ادمین
            'admin_panel': self.show_admin_panel,
            'user_management': self.show_user_management,
            'system_stats': self.show_system_statistics,
            'broadcast_message': self.handle_broadcast_message,
            
            # راهنما
            'show_help': self.show_help_menu,
            'help_getting_started': self.show_getting_started_help,
            'help_strategies': self.show_strategies_help,
            'help_packages': self.show_packages_help,
            'help_faq': self.show_faq,
            
            # عمومی
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
            
            # بررسی امنیت
            if not await self.security_manager.is_user_allowed(user.id):
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
    # هندلرهای ثبت‌نام و شروع
    # =========================
    
    async def handle_user_registration(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ثبت‌نام کاربر جدید"""
        try:
            user = query.from_user
            
            # بررسی اینکه کاربر قبلاً ثبت‌نام کرده یا نه
            existing_user = await self.user_manager.get_user_by_telegram_id(user.id)
            
            if existing_user:
                await self.show_main_menu(query, context)
                return
            
            # ثبت‌نام کاربر جدید
            registration_data = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'package_type': 'free',
                'registration_date': datetime.now().isoformat()
            }
            
            success = await self.user_manager.create_user(registration_data)
            
            if success:
                welcome_message = f"""🎉 **خوش آمدید به MrTrader Bot!**
━━━━━━━━━━━━━━━━━━━━━━

👋 سلام {user.first_name}!

✅ ثبت‌نام شما با موفقیت انجام شد.
🎁 پکیج رایگان شما فعال شده است.

🎯 **امکانات پکیج رایگان:**
• 2 استراتژی دمو
• 5 تحلیل در روز
• دسترسی به راهنماها

برای شروع، دکمه **ادامه** را بزنید."""
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ ادامه", callback_data="main_menu")
                ]])
                
                await query.edit_message_text(
                    welcome_message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text("❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")
                
        except Exception as e:
            logger.error(f"Error in user registration: {e}")
            await query.edit_message_text("❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")
    
    async def show_terms_and_conditions(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش قوانین و مقررات"""
        try:
            terms_message = """📋 **قوانین و مقررات MrTrader Bot**
━━━━━━━━━━━━━━━━━━━━━━

🔸 **مسئولیت:**
• تمام تحلیل‌ها صرفاً جنبه آموزشی دارند
• تصمیم‌گیری سرمایه‌گذاری بر عهده شماست
• ربات هیچ مسئولیتی در قبال سود یا زیان ندارد

🔸 **استفاده مجاز:**
• استفاده شخصی و غیرتجاری
• ممنوعیت انتشار بدون اجازه
• رعایت قوانین کشور محل اقامت

🔸 **حریم خصوصی:**
• اطلاعات شما محفوظ نگهداری می‌شود
• عدم فروش اطلاعات به اشخاص ثالث
• استفاده از اطلاعات صرفاً جهت بهبود سرویس

🔸 **پرداخت:**
• قیمت‌ها قابل تغییر هستند
• امکان لغو اشتراک در هر زمان
• عدم بازگشت وجه پس از استفاده

با کلیک روی "موافقم" قوانین را می‌پذیرید."""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ موافقم", callback_data="accept_terms")],
                [InlineKeyboardButton("❌ مخالفم", callback_data="cancel")]
            ])
            
            await query.edit_message_text(
                terms_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing terms: {e}")
    
    async def handle_terms_acceptance(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پذیرش قوانین"""
        try:
            user = query.from_user
            
            # ثبت پذیرش قوانین
            await self.user_manager.update_user_field(user.id, 'terms_accepted', True)
            await self.user_manager.update_user_field(user.id, 'terms_accepted_date', datetime.now().isoformat())
            
            await query.edit_message_text(
                "✅ **قوانین پذیرفته شد!**\n\nاکنون می‌توانید از تمام امکانات ربات استفاده کنید.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # هدایت به منوی اصلی پس از 2 ثانیه
            await asyncio.sleep(2)
            await self.show_main_menu(query, context)
            
        except Exception as e:
            logger.error(f"Error handling terms acceptance: {e}")
    
    # =========================
    # هندلرهای منوی اصلی
    # =========================
    
    async def show_main_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی"""
        try:
            user = query.from_user
            user_data = await self.user_manager.get_user_by_telegram_id(user.id)
            
            if not user_data:
                await query.edit_message_text("❌ ابتدا باید ثبت‌نام کنید.")
                return
            
            user_package = user_data.get('package_type', 'free')
            is_admin = await self.admin_manager.is_admin(user.id)
            
            menu_message = f"""🏠 **منوی اصلی MrTrader**
━━━━━━━━━━━━━━━━━━━━━━

👋 سلام {user.first_name}
📦 پکیج فعال: **{user_package.upper()}**
⭐ امتیاز: **{user_data.get('user_points', 0):,}**

یکی از گزینه‌های زیر را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.main_menu(user_package, is_admin)
            
            await query.edit_message_text(
                menu_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
    
    async def show_strategy_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی استراتژی‌ها"""
        try:
            user = query.from_user
            user_package = StrategyManager.get_user_package_level(user.id)
            
            if not user_package:
                user_package_name = "free"
            else:
                user_package_name = user_package.value
            
            message = f"""📊 **استراتژی‌های تحلیل MrTrader**
━━━━━━━━━━━━━━━━━━━━━━

🎯 **پکیج فعلی شما:** {user_package_name.upper()}

📈 **انتخاب استراتژی مورد نظر:**"""
            
            keyboard = KeyboardTemplates.strategy_menu(user_package_name)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing strategy menu: {e}")
    
    async def show_live_prices_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی قیمت‌های زنده"""
        try:
            message = """💹 **قیمت‌های زنده ارزهای دیجیتال**
━━━━━━━━━━━━━━━━━━━━━━

🔄 در حال دریافت آخرین قیمت‌ها...

⚠️ **توجه:** قیمت‌ها از صرافی Binance دریافت می‌شوند و هر 30 ثانیه بروزرسانی می‌شوند."""
            
            keyboard = KeyboardTemplates.back_to_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # درخواست قیمت‌های زنده (اختیاری - نیاز به پیاده‌سازی API)
            # prices = await api_client.fetch_live_prices()
            
        except Exception as e:
            logger.error(f"Error showing live prices: {e}")
    
    # =========================
    # هندلرهای 4 مرحله‌ای انتخاب
    # =========================
    
    async def handle_strategy_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str):
        """مرحله 1: انتخاب استراتژی"""
        try:
            user = query.from_user
            strategy = action.replace('strategy_', '')
            
            # بررسی دسترسی به استراتژی
            can_use, message = StrategyManager.can_use_strategy(user.id, strategy)
            if not can_use:
                await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # ذخیره استراتژی انتخاب شده
            context.user_data['selected_strategy'] = strategy
            
            # نمایش معرفی استراتژی و انتخاب نماد
            user_package = StrategyManager.get_user_package_level(user.id)
            user_package_name = user_package.value if user_package else "free"
            
            strategy_intro = MessageTemplates.strategy_intro(strategy, user_package_name)
            
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
    
    async def handle_symbol_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """مرحله 2: انتخاب نماد ارز"""
        try:
            if not params:
                await query.edit_message_text("❌ پارامتر نماد یافت نشد.")
                return
            
            strategy = context.user_data.get('selected_strategy')
            if not strategy:
                await query.edit_message_text("❌ استراتژی انتخاب نشده. لطفاً دوباره شروع کنید.")
                return
            
            symbol = params[0]
            
            # اعتبارسنجی نماد
            if symbol.upper() not in Config.SUPPORTED_SYMBOLS:
                await query.edit_message_text(f"❌ نماد {symbol} پشتیبانی نمی‌شود.")
                return
            
            # ذخیره نماد انتخاب شده
            context.user_data['selected_symbol'] = symbol.upper()
            
            strategy_display_name = StrategyManager.get_strategy_display_name(strategy)
            
            message = f"""📊 **استراتژی:** {strategy_display_name}
🪙 **نماد انتخاب شده:** {symbol.upper()}

━━━━━━━━━━━━━━━━━━━━━━
💱 **مرحله 2: انتخاب ارز مرجع**

لطفاً ارز مرجع مورد نظر را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.currency_selection(strategy, symbol)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling symbol selection: {e}")
    
    async def handle_currency_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """مرحله 3: انتخاب ارز مرجع"""
        try:
            if len(params) < 2:
                await query.edit_message_text("❌ پارامترهای کافی یافت نشد.")
                return
            
            strategy = context.user_data.get('selected_strategy')
            symbol = context.user_data.get('selected_symbol', params[0])
            currency = params[1]
            
            if not strategy:
                await query.edit_message_text("❌ استراتژی انتخاب نشده. لطفاً دوباره شروع کنید.")
                return
            
            # اعتبارسنجی ارز مرجع
            if currency.upper() not in Config.SUPPORTED_CURRENCIES:
                await query.edit_message_text(f"❌ ارز مرجع {currency} پشتیبانی نمی‌شود.")
                return
            
            # ذخیره ارز مرجع انتخاب شده
            context.user_data['selected_currency'] = currency.upper()
            
            strategy_display_name = StrategyManager.get_strategy_display_name(strategy)
            
            message = f"""📊 **استراتژی:** {strategy_display_name}
🪙 **جفت ارز:** {symbol.upper()}/{currency.upper()}

━━━━━━━━━━━━━━━━━━━━━━
⏱ **مرحله 3: انتخاب تایم‌فریم**

لطفاً تایم‌فریم مورد نظر را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.timeframe_selection(strategy, symbol, currency)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling currency selection: {e}")
    
    async def handle_timeframe_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """مرحله 4: انتخاب تایم‌فریم و انجام تحلیل"""
        try:
            if len(params) < 3:
                await query.edit_message_text("❌ پارامترهای کافی یافت نشد.")
                return
            
            strategy = context.user_data.get('selected_strategy')
            symbol = context.user_data.get('selected_symbol', params[0])
            currency = context.user_data.get('selected_currency', params[1])
            timeframe = params[2]
            
            if not strategy:
                await query.edit_message_text("❌ استراتژی انتخاب نشده. لطفاً دوباره شروع کنید.")
                return
            
            user = query.from_user
            
            # بررسی دسترسی تایم‌فریم
            can_use_timeframe, timeframe_message = StrategyManager.check_timeframe_access(user.id, timeframe)
            if not can_use_timeframe:
                await query.edit_message_text(timeframe_message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # اعتبارسنجی پارامترها
            is_valid, validation_message = StrategyManager.validate_strategy_parameters(
                strategy, symbol, currency, timeframe
            )
            if not is_valid:
                await query.edit_message_text(validation_message)
                return
            
            # شروع تحلیل
            await self.perform_analysis(query, context, strategy, symbol, currency, timeframe)
            
        except Exception as e:
            logger.error(f"Error handling timeframe selection: {e}")
    
    async def perform_analysis(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, 
                             strategy: str, symbol: str, currency: str, timeframe: str):
        """انجام تحلیل و نمایش نتایج"""
        try:
            user = query.from_user
            
            # نمایش پیام در حال پردازش
            processing_message = MessageTemplates.processing_message("analyzing", f"{symbol}/{currency}", strategy)
            await query.edit_message_text(processing_message, parse_mode=ParseMode.MARKDOWN)
            
            # بررسی کش
            cache_key = f"analysis_{strategy}_{symbol}_{currency}_{timeframe}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for {cache_key}")
                analysis_data = cached_result
                is_cached = True
            else:
                # فراخوانی API
                try:
                    # نمایش پیام دریافت داده‌ها
                    processing_message = MessageTemplates.processing_message("fetching_data")
                    await query.edit_message_text(processing_message, parse_mode=ParseMode.MARKDOWN)
                    
                    analysis_data = await api_client.fetch_strategy_analysis(
                        strategy, symbol, currency, timeframe
                    )
                    
                    if analysis_data:
                        # ذخیره در کش
                        cache.set(cache_key, analysis_data, ttl=Config.SIGNAL_CACHE_DURATION)
                        is_cached = False
                    else:
                        raise Exception("No data received from API")
                        
                except Exception as api_error:
                    logger.error(f"API error for {strategy}: {api_error}")
                    error_message = MessageTemplates.error_message("api_error", str(api_error))
                    await query.edit_message_text(error_message, parse_mode=ParseMode.MARKDOWN)
                    return
            
            # پردازش داده‌های تحلیل
            try:
                # نمایش پیام پردازش
                processing_message = MessageTemplates.processing_message("processing", strategy=strategy)
                await query.edit_message_text(processing_message, parse_mode=ParseMode.MARKDOWN)
                
                # استخراج جزئیات سیگنال
                signal_details = extract_signal_details(analysis_data)
                
                # دریافت قیمت فعلی
                current_price = signal_details.get('entry_price', 0)
                if current_price == 0:
                    try:
                        current_price = await api_client.fetch_current_price(symbol, currency)
                    except:
                        current_price = 0
                
                # تشخیص نوع استراتژی برای انتخاب قالب مناسب
                strategy_type = StrategyManager.get_strategy_type_from_name(strategy)
                
                # تولید پیام نتیجه
                result_message = MessageTemplates.analysis_result(
                    symbol, currency, timeframe, signal_details, current_price, strategy_type
                )
                
                # اضافه کردن اطلاعات کش
                if is_cached:
                    cache_info = f"\n\n💾 {Config.MESSAGES['cached_result'].format(time='1 دقیقه پیش')}"
                else:
                    cache_info = f"\n\n🔄 {Config.MESSAGES['fresh_result']}"
                
                result_message += cache_info
                
                # کیبورد اقدامات
                keyboard = KeyboardTemplates.analysis_result_actions(strategy, symbol, currency, timeframe)
                
                await query.edit_message_text(
                    result_message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # ثبت آمار استفاده
                try:
                    if strategy.startswith('demo_'):
                        StrategyManager.increment_demo_usage(user.id)
                    
                    # ثبت در دیتابیس
                    await self.user_manager.log_analysis_request(
                        user.id, strategy, symbol, currency, timeframe, 
                        signal_details.get('signal_direction', 'neutral'),
                        signal_details.get('confidence', 0)
                    )
                except Exception as log_error:
                    logger.error(f"Error logging analysis: {log_error}")
                
            except Exception as process_error:
                logger.error(f"Error processing analysis data: {process_error}")
                error_message = MessageTemplates.error_message("invalid_input", str(process_error))
                await query.edit_message_text(error_message, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            error_message = MessageTemplates.error_message("error_occurred", str(e))
            await query.edit_message_text(error_message, parse_mode=ParseMode.MARKDOWN)
    
    # =========================
    # هندلرهای پکیج‌ها
    # =========================
    
    async def show_packages_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی پکیج‌ها"""
        try:
            message = """💎 **پکیج‌های MrTrader Bot**
━━━━━━━━━━━━━━━━━━━━━━

🎯 **انتخاب پکیج مناسب برای نیازهای تحلیلی شما:**

🥉 **BASIC** - پایه و کاربردی
🥈 **PREMIUM** - پیشرفته و حرفه‌ای  
👑 **VIP** - کامل و بی‌نظیر

برای مشاهده جزئیات هر پکیج، روی آن کلیک کنید."""
            
            keyboard = KeyboardTemplates.packages_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing packages menu: {e}")
    
    async def handle_package_selection(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str = None):
        """نمایش جزئیات پکیج انتخاب شده"""
        try:
            if action:
                package_name = action.replace('pkg_select_', '')
            else:
                # برای compatibility با callback map
                package_name = "basic"
            
            # اطلاعات پکیج‌ها
            packages_info = {
                "basic": {
                    "title": "🥉 پکیج بیسیک",
                    "price": "50,000 تومان/ماه",
                    "features": [
                        "✅ 9 استراتژی اصلی",
                        "✅ 50 درخواست در روز", 
                        "✅ همه تایم‌فریم‌ها (به جز 1m، 3m)",
                        "✅ ذخیره گزارش‌ها",
                        "✅ پشتیبانی ایمیل"
                    ]
                },
                "premium": {
                    "title": "🥈 پکیج پریمیوم",
                    "price": "150,000 تومان/ماه", 
                    "features": [
                        "✅ 26 استراتژی پیشرفته",
                        "✅ 200 درخواست در روز",
                        "✅ همه تایم‌فریم‌ها", 
                        "✅ ذخیره گزارش‌ها",
                        "✅ پشتیبانی زنده",
                        "✅ الگوهای پیشرفته",
                        "✅ تحلیل‌های ترکیبی"
                    ]
                },
                "vip": {
                    "title": "👑 پکیج وی‌آی‌پی",
                    "price": "350,000 تومان/ماه",
                    "features": [
                        "✅ 35 استراتژی کامل",
                        "✅ 500 درخواست در روز",
                        "✅ همه تایم‌فریم‌ها",
                        "✅ ذخیره گزارش‌ها", 
                        "✅ پشتیبانی اولویت‌دار",
                        "✅ تحلیل حجم پیشرفته",
                        "✅ الگوهای نادر",
                        "✅ گزارش‌های تخصصی",
                        "✅ رفرال 20%"
                    ]
                }
            }
            
            if package_name not in packages_info:
                package_name = "basic"
            
            package = packages_info[package_name]
            
            message = f"""{package['title']}
━━━━━━━━━━━━━━━━━━━━━━

💰 **قیمت:** {package['price']}

🎯 **ویژگی‌ها:**"""
            
            for feature in package['features']:
                message += f"\n{feature}"
            
            message += f"\n\n🎁 **پیشنهاد ویژه:** خرید 3 ماهه 10% تخفیف!"
            
            keyboard = KeyboardTemplates.package_details(package_name)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling package selection: {e}")
    
    async def show_payment_methods(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش روش‌های پرداخت"""
        try:
            message = """💳 **روش‌های پرداخت**
━━━━━━━━━━━━━━━━━━━━━━

🏦 **درگاه‌های بانکی:**
• درگاه زرین‌پال
• درگاه بانک ملت
• درگاه پارسیان

💰 **ارزهای دیجیتال:**
• بیت کوین (BTC)
• اتریوم (ETH)
• تتر (USDT)

🎁 **کد تخفیف:**
اگر کد تخفیف دارید، پس از انتخاب روش پرداخت وارد کنید.

لطفاً روش پرداخت مورد نظر را انتخاب کنید:"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 درگاه بانکی", callback_data="payment_bank")],
                [InlineKeyboardButton("💰 ارز دیجیتال", callback_data="payment_crypto")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_packages")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing payment methods: {e}")
    
    # =========================
    # هندلرهای رفرال
    # =========================
    
    async def show_referral_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سیستم رفرال"""
        try:
            user = query.from_user
            referral_data = await self.referral_manager.get_user_referral_data(user.id)
            
            message = f"""🎁 **سیستم دعوت از دوستان**
━━━━━━━━━━━━━━━━━━━━━━

🔗 **لینک دعوت شما:**
`https://t.me/MrTraderBot?start={referral_data.get('referral_code', 'unknown')}`

📊 **آمار شما:**
👥 تعداد دعوت شدگان: **{referral_data.get('total_referrals', 0)}**
💰 کل کمیسیون: **{referral_data.get('total_commission', 0):,} تومان**
💳 کمیسیون قابل برداشت: **{referral_data.get('available_commission', 0):,} تومان**

🎯 **نرخ کمیسیون:**
• پکیج Basic: 10%
• پکیج Premium: 15%
• پکیج VIP: 20%

لینک خود را با دوستان به اشتراک بگذارید!"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 آمار تفصیلی", callback_data="referral_stats")],
                [InlineKeyboardButton("💰 برداشت کمیسیون", callback_data="claim_rewards")],
                [InlineKeyboardButton("📤 اشتراک‌گذاری", 
                                    url=f"https://t.me/share/url?url=https://t.me/MrTraderBot?start={referral_data.get('referral_code', '')}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing referral menu: {e}")
    
    async def show_referral_stats(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار تفصیلی رفرال"""
        try:
            user = query.from_user
            detailed_stats = await self.referral_manager.get_detailed_referral_stats(user.id)
            
            message = """📈 **آمار تفصیلی دعوت‌ها**
━━━━━━━━━━━━━━━━━━━━━━

📅 **آمار ماهانه:**"""
            
            for month_data in detailed_stats.get('monthly_stats', []):
                message += f"\n• {month_data['month']}: {month_data['referrals']} نفر"
            
            message += f"""

💰 **تاریخچه کمیسیون:**"""
            
            for commission in detailed_stats.get('commission_history', []):
                message += f"\n• {commission['date']}: {commission['amount']:,} تومان"
            
            keyboard = KeyboardTemplates.back_to_menu("show_referral", "🔙 بازگشت به رفرال")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing referral stats: {e}")
    
    async def handle_claim_rewards(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش درخواست برداشت کمیسیون"""
        try:
            user = query.from_user
            available_commission = await self.referral_manager.get_available_commission(user.id)
            
            if available_commission < 10000:  # حداقل 10 هزار تومان
                await query.edit_message_text(
                    f"❌ **حداقل مبلغ برداشت 10,000 تومان است**\n\nموجودی فعلی شما: {available_commission:,} تومان",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = f"""💰 **درخواست برداشت کمیسیون**
━━━━━━━━━━━━━━━━━━━━━━

💳 **مبلغ قابل برداشت:** {available_commission:,} تومان

🏦 **روش‌های برداشت:**
• کارت بانکی
• کیف پول ارز دیجیتال

⚠️ **نکته:** پردازش درخواست 24-48 ساعت زمان می‌برد.

آیا مایل به ادامه هستید؟"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تایید درخواست", callback_data="confirm_withdrawal")],
                [InlineKeyboardButton("❌ انصراف", callback_data="show_referral")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling claim rewards: {e}")
    
    # =========================
    # هندلرهای گزارش‌ها
    # =========================
    
    async def show_reports_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی گزارش‌ها"""
        try:
            message = """📊 **گزارش‌های MrTrader**
━━━━━━━━━━━━━━━━━━━━━━

📈 **انواع گزارش‌ها:**

📅 **گزارش روزانه** - عملکرد امروز
📆 **گزارش هفتگی** - خلاصه هفته
👤 **گزارش شخصی** - آمار کامل شما

🎯 **محتوای گزارش‌ها:**
• آمار تحلیل‌ها
• نرخ موفقیت سیگنال‌ها
• استراتژی‌های محبوب
• عملکرد پکیج‌ها

لطفاً نوع گزارش مورد نظر را انتخاب کنید:"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 گزارش روزانه", callback_data="daily_report")],
                [InlineKeyboardButton("📆 گزارش هفتگی", callback_data="weekly_report")],
                [InlineKeyboardButton("👤 گزارش شخصی", callback_data="user_report")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing reports menu: {e}")
    
    async def show_daily_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزارش روزانه"""
        try:
            daily_stats = await self.report_manager.get_daily_report()
            
            message = f"""📅 **گزارش روزانه - {datetime.now().strftime('%Y/%m/%d')}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **آمار کلی:**
• کل تحلیل‌ها: **{daily_stats.get('total_analyses', 0):,}**
• کاربران فعال: **{daily_stats.get('active_users', 0):,}**
• کاربران جدید: **{daily_stats.get('new_users', 0):,}**

📈 **استراتژی‌های محبوب:**"""
            
            for strategy in daily_stats.get('popular_strategies', []):
                message += f"\n• {strategy['name']}: {strategy['count']} تحلیل"
            
            message += f"""

💎 **آمار پکیج‌ها:**
• رایگان: {daily_stats.get('free_users', 0)} نفر
• Basic: {daily_stats.get('basic_users', 0)} نفر  
• Premium: {daily_stats.get('premium_users', 0)} نفر
• VIP: {daily_stats.get('vip_users', 0)} نفر"""
            
            keyboard = KeyboardTemplates.back_to_menu("show_reports", "🔙 بازگشت به گزارش‌ها")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing daily report: {e}")
    
    async def show_weekly_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزارش هفتگی"""
        try:
            weekly_stats = await self.report_manager.get_weekly_report()
            
            message = f"""📆 **گزارش هفتگی**
━━━━━━━━━━━━━━━━━━━━━━

📊 **خلاصه هفته:**
• کل تحلیل‌ها: **{weekly_stats.get('total_analyses', 0):,}**
• میانگین روزانه: **{weekly_stats.get('daily_average', 0):,}**
• رشد نسبت به هفته قبل: **{weekly_stats.get('growth_rate', 0):+.1f}%**

📈 **روند روزانه:**"""
            
            for day in weekly_stats.get('daily_trend', []):
                message += f"\n• {day['date']}: {day['analyses']} تحلیل"
            
            keyboard = KeyboardTemplates.back_to_menu("show_reports", "🔙 بازگشت به گزارش‌ها")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing weekly report: {e}")
    
    async def show_user_report(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزارش شخصی کاربر"""
        try:
            user = query.from_user
            user_stats = await self.report_manager.get_user_report(user.id)
            
            message = f"""👤 **گزارش شخصی شما**
━━━━━━━━━━━━━━━━━━━━━━

📊 **آمار کلی:**
• کل تحلیل‌ها: **{user_stats.get('total_analyses', 0):,}**
• تحلیل‌های امروز: **{user_stats.get('today_analyses', 0):,}**
• آخرین تحلیل: **{user_stats.get('last_analysis', 'هنوز ندارید')}**

🎯 **استراتژی محبوب:**
{user_stats.get('favorite_strategy', 'هنوز مشخص نشده')}

📈 **عملکرد:**
• نرخ موفقیت: **{user_stats.get('success_rate', 0):.1f}%**
• میانگین اعتماد: **{user_stats.get('avg_confidence', 0):.1f}%**

🏆 **رتبه‌بندی:**
شما در رتبه **{user_stats.get('user_rank', 'نامشخص')}** از کل کاربران قرار دارید."""
            
            keyboard = KeyboardTemplates.back_to_menu("show_reports", "🔙 بازگشت به گزارش‌ها")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing user report: {e}")
    
    # =========================
    # هندلرهای پشتیبانی
    # =========================
    
    async def create_support_ticket(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد تیکت پشتیبانی"""
        try:
            message = """🎫 **ایجاد تیکت پشتیبانی**
━━━━━━━━━━━━━━━━━━━━━━

لطفاً موضوع مشکل خود را انتخاب کنید:

🔧 **مشکلات فنی**
💰 **مسائل پرداخت**
📊 **مشکلات تحلیل**
💎 **درباره پکیج‌ها**
❓ **سایر موارد**

پس از انتخاب موضوع، توضیحات تکمیلی خود را ارسال کنید."""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔧 مشکل فنی", callback_data="ticket_technical")],
                [InlineKeyboardButton("💰 مسئله پرداخت", callback_data="ticket_payment")],
                [InlineKeyboardButton("📊 مشکل تحلیل", callback_data="ticket_analysis")],
                [InlineKeyboardButton("💎 درباره پکیج", callback_data="ticket_package")],
                [InlineKeyboardButton("❓ سایر موارد", callback_data="ticket_other")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="contact_support")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
    
    # =========================
    # هندلرهای ادمین
    # =========================
    
    async def show_user_management(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل مدیریت کاربران"""
        try:
            user = query.from_user
            if not await self.admin_manager.is_admin(user.id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید.")
                return
            
            user_stats = await self.admin_manager.get_user_management_stats()
            
            message = f"""👥 **مدیریت کاربران**
━━━━━━━━━━━━━━━━━━━━━━

📊 **آمار کلی:**
• کل کاربران: **{user_stats.get('total_users', 0):,}**
• کاربران فعال امروز: **{user_stats.get('active_today', 0):,}**
• کاربران جدید امروز: **{user_stats.get('new_today', 0):,}**

💎 **توزیع پکیج‌ها:**
• رایگان: {user_stats.get('free_users', 0)} نفر
• Basic: {user_stats.get('basic_users', 0)} نفر
• Premium: {user_stats.get('premium_users', 0)} نفر  
• VIP: {user_stats.get('vip_users', 0)} نفر"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 جستجوی کاربر", callback_data="admin_search_user")],
                [InlineKeyboardButton("🎁 اعطای پکیج", callback_data="admin_grant_package")],
                [InlineKeyboardButton("🚫 مسدود کردن", callback_data="admin_ban_user")],
                [InlineKeyboardButton("📊 آمار تفصیلی", callback_data="admin_detailed_stats")],
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_panel")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing user management: {e}")
    
    async def show_system_statistics(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار سیستم"""
        try:
            user = query.from_user
            if not await self.admin_manager.is_admin(user.id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید.")
                return
            
            system_stats = await self.admin_manager.get_system_statistics()
            
            message = f"""📊 **آمار سیستم**
━━━━━━━━━━━━━━━━━━━━━━

⚡ **عملکرد:**
• آپتایم: **{system_stats.get('uptime', '0')}**
• تحلیل‌های امروز: **{system_stats.get('today_analyses', 0):,}**
• میانگین پاسخ API: **{system_stats.get('avg_response_time', 0):.2f}s**

💾 **کش سیستم:**
• Hit Rate: **{system_stats.get('cache_hit_rate', 0):.1f}%**
• فضای استفاده شده: **{system_stats.get('cache_usage', 0):.1f}MB**

🔧 **وضعیت API ها:**
• فعال: **{system_stats.get('active_apis', 0)}/35**
• خطا: **{system_stats.get('failed_apis', 0)}**

💰 **مالی:**
• درآمد امروز: **{system_stats.get('today_revenue', 0):,} تومان**
• درآمد ماه: **{system_stats.get('month_revenue', 0):,} تومان**"""
            
            keyboard = KeyboardTemplates.back_to_menu("admin_panel", "🔙 پنل ادمین")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing system statistics: {e}")
    
    async def handle_broadcast_message(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ارسال پیام گروهی"""
        try:
            user = query.from_user
            if not await self.admin_manager.is_admin(user.id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید.")
                return
            
            message = """📤 **ارسال پیام گروهی**
━━━━━━━━━━━━━━━━━━━━━━

🎯 **مخاطبان:**

👥 **همه کاربران** - ارسال به تمام کاربران
💎 **کاربران پولی** - فقط دارندگان پکیج
🆓 **کاربران رایگان** - فقط پکیج رایگان
📅 **کاربران فعال** - فعال در 7 روز اخیر

⚠️ **نکته:** پیام شما برای گروه انتخابی ارسال خواهد شد.

لطفاً گروه مخاطب را انتخاب کنید:"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 همه کاربران", callback_data="broadcast_all")],
                [InlineKeyboardButton("💎 کاربران پولی", callback_data="broadcast_paid")],
                [InlineKeyboardButton("🆓 کاربران رایگان", callback_data="broadcast_free")],
                [InlineKeyboardButton("📅 کاربران فعال", callback_data="broadcast_active")],
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_panel")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling broadcast message: {e}")
    
    # =========================
    # هندلرهای کمکی
    # =========================
    
    async def handle_manual_input(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """مدیریت ورودی دستی"""
        try:
            if action == "manual_symbol":
                strategy = context.user_data.get('selected_strategy')
                message = f"""🔤 **ورود دستی نماد**

لطفاً نماد ارز مورد نظر خود را تایپ کنید:
مثال: BTC, ETH, ADA

نمادهای پشتیبانی شده:
{', '.join(Config.SUPPORTED_SYMBOLS[:10])}...

برای لغو /cancel را بفرستید."""
                
                context.user_data['waiting_for_manual_symbol'] = strategy
                
            elif action == "manual_currency":
                symbol = params[0] if params else context.user_data.get('selected_symbol')
                strategy = context.user_data.get('selected_strategy')
                
                message = f"""💱 **ورود دستی ارز مرجع**

نماد انتخاب شده: {symbol}

لطفاً ارز مرجع مورد نظر را تایپ کنید:
مثال: USDT, BUSD, BTC, ETH

ارزهای پشتیبانی شده:
{', '.join(Config.SUPPORTED_CURRENCIES)}

برای لغو /cancel را بفرستید."""
                
                context.user_data['waiting_for_manual_currency'] = {'strategy': strategy, 'symbol': symbol}
            
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error handling manual input: {e}")
    
    async def show_user_profile(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پروفایل کاربر"""
        try:
            user = query.from_user
            user_data = await self.user_manager.get_user_by_telegram_id(user.id)
            
            if not user_data:
                await query.edit_message_text("❌ اطلاعات کاربری یافت نشد.")
                return
            
            user_package = StrategyManager.get_user_package_level(user.id)
            package_name = user_package.value if user_package else "free"
            
            is_expired = StrategyManager.is_package_expired(user.id)
            usage_stats = StrategyManager.get_user_usage_stats(user.id)
            
            profile_message = f"""👤 **پروفایل کاربری**
━━━━━━━━━━━━━━━━━━━━━━

🆔 **شناسه:** `{user.id}`
👤 **نام:** {user.first_name} {user.last_name or ''}
📅 **تاریخ عضویت:** {user_data.get('created_at', 'نامشخص')}

📦 **پکیج فعلی:** **{package_name.upper()}**
{'🔴 منقضی شده' if is_expired else '🟢 فعال'}

📊 **آمار استفاده:**
📈 کل تحلیل‌ها: `{usage_stats.get('total_analyses', 0):,}`
📅 تحلیل‌های امروز: `{usage_stats.get('today_analyses', 0):,}`
⭐ امتیاز: `{user_data.get('user_points', 0):,}`

🏆 **استراتژی محبوب:** {usage_stats.get('favorite_strategy', 'هنوز نداریم')}"""
            
            is_admin = await self.admin_manager.is_admin(user.id)
            keyboard = KeyboardTemplates.user_profile_menu(is_admin)
            
            await query.edit_message_text(
                profile_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing user profile: {e}")
    
    async def show_help_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی راهنما"""
        try:
            message = """📚 **راهنمای MrTrader Bot**
━━━━━━━━━━━━━━━━━━━━━━

🎯 **راهنماهای موجود:**

🚀 شروع کار - نحوه استفاده از ربات
📊 استراتژی‌ها - توضیح انواع تحلیل‌ها  
💎 پکیج‌ها - مقایسه و انتخاب پکیج
❓ سوالات متداول - پاسخ سوالات رایج

💡 **نکته:** برای دریافت راهنمای هر بخش، روی آن کلیک کنید."""
            
            keyboard = KeyboardTemplates.help_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing help menu: {e}")
    
    async def contact_support(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """تماس با پشتیبانی"""
        try:
            message = """🎧 **پشتیبانی MrTrader Bot**
━━━━━━━━━━━━━━━━━━━━━━

📞 **راه‌های ارتباط:**

💬 **تلگرام:** @MrTraderSupport
📧 **ایمیل:** support@mrtrader.bot
🌐 **سایت:** mrtrader.bot

⏰ **ساعات پاسخگویی:**
شنبه تا پنج‌شنبه: 9:00 - 18:00
جمعه: تعطیل

🚀 **پاسخگویی سریع:** کاربران VIP در اولویت قرار دارند

❓ **پیش از تماس:**
لطفاً راهنماها و سوالات متداول را مطالعه کنید."""
            
            keyboard = KeyboardTemplates.back_to_menu()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing contact support: {e}")
    
    # =========================
    # هندلرهای راهنما
    # =========================
    
    async def show_getting_started_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای شروع کار"""
        try:
            message = MessageTemplates.help_message("getting_started")
            keyboard = KeyboardTemplates.back_to_menu("menu_help", "🔙 بازگشت به راهنما")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing getting started help: {e}")
    
    async def show_strategies_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای استراتژی‌ها"""
        try:
            message = MessageTemplates.help_message("strategies")
            keyboard = KeyboardTemplates.back_to_menu("menu_help", "🔙 بازگشت به راهنما")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing strategies help: {e}")
    
    async def show_packages_help(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای پکیج‌ها"""
        try:
            message = MessageTemplates.help_message("packages")
            keyboard = KeyboardTemplates.back_to_menu("menu_help", "🔙 بازگشت به راهنما")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing packages help: {e}")
    
    async def show_faq(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش سوالات متداول"""
        try:
            message = """❓ **سوالات متداول**
━━━━━━━━━━━━━━━━━━━━━━

**Q: آیا تحلیل‌ها توصیه سرمایه‌گذاری هستند؟**
A: خیر، تمام تحلیل‌ها صرفاً جنبه آموزشی دارند.

**Q: چگونه پکیج خود را ارتقا دهم؟** 
A: از منوی "💎 پکیج‌ها" استفاده کنید.

**Q: آیا اطلاعات من محفوظ است؟**
A: بله، تمام اطلاعات با رمزنگاری محافظت می‌شوند.

**Q: چند بار در روز می‌توانم تحلیل بگیرم؟**
A: بستگی به پکیج شما دارد:
• رایگان: 5 تحلیل دمو
• Basic: 50 در روز
• Premium: 200 در روز  
• VIP: 500 در روز

**Q: آیا می‌توانم پکیج را لغو کنم؟**
A: بله، در هر زمان قابل لغو است."""
            
            keyboard = KeyboardTemplates.back_to_menu("menu_help", "🔙 بازگشت به راهنما")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing FAQ: {e}")
    
    # =========================
    # هندلرهای عمومی
    # =========================
    
    async def handle_back_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش دکمه بازگشت"""
        try:
            await self.show_main_menu(query, context)
        except Exception as e:
            logger.error(f"Error handling back action: {e}")
    
    async def handle_cancel_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش دکمه لغو"""
        try:
            # پاک کردن داده‌های موقت
            context.user_data.clear()
            
            await query.edit_message_text(
                "❌ **عملیات لغو شد**\n\nبرای شروع مجدد از منوی اصلی استفاده کنید.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error handling cancel action: {e}")
    
    async def handle_refresh_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش دکمه بروزرسانی"""
        try:
            await self.show_main_menu(query, context)
        except Exception as e:
            logger.error(f"Error handling refresh action: {e}")
    
    # =========================
    # سایر هندلرها (اضافه شده برای compatibility)
    # =========================
    
    async def show_admin_panel(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل ادمین"""
        try:
            user = query.from_user
            if not await self.admin_manager.is_admin(user.id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید.")
                return
            
            message = """🔧 **پنل مدیریت MrTrader**
━━━━━━━━━━━━━━━━━━━━━━

👋 خوش آمدید به پنل مدیریت

📊 **عملکرد کلی سیستم:**
• وضعیت: 🟢 آنلاین
• آپتایم: 99.9%
• کاربران فعال: در حال محاسبه...

🛠 **دسترسی‌های مدیریت:**"""
            
            keyboard = KeyboardTemplates.admin_panel()
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing admin panel: {e}")
    
    async def handle_package_purchase(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """پردازش خرید پکیج"""
        try:
            package_name = action.replace('buy_', '')
            duration = params[0] if params else 'monthly'
            
            await query.edit_message_text(
                f"🛒 **خرید پکیج {package_name.upper()}**\n\nدر حال هدایت به درگاه پرداخت...",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error handling package purchase: {e}")
    
    async def handle_admin_action(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, params: List[str]):
        """پردازش اقدامات ادمین"""
        try:
            user = query.from_user
            if not await self.admin_manager.is_admin(user.id):
                await query.edit_message_text("❌ شما دسترسی ادمین ندارید.")
                return
            
            # پردازش اقدامات مختلف ادمین
            if action == "admin_search_user":
                await query.edit_message_text("🔍 **جستجوی کاربر**\n\nلطفاً ID یا username کاربر را ارسال کنید.")
            elif action == "admin_grant_package":
                await query.edit_message_text("🎁 **اعطای پکیج**\n\nابتدا کاربر مورد نظر را جستجو کنید.")
            # سایر اقدامات...
            
        except Exception as e:
            logger.error(f"Error handling admin action: {e}")
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CallbackQueryHandler(self.handle_callback_query)
        ]


# Export
__all__ = ['CallbackHandler']