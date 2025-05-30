"""
هندلرهای پردازش Callback Query برای MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from typing import Dict, List, Any, Optional
import asyncio
import json

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
from api.api_client import ApiClient
from utils.time_manager import TimeManager


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
            
            # تحلیل و سیگنال‌ها
            'quick_analysis': self.handle_quick_analysis,
            'show_signals': self.show_signals_menu,
            'instant_analysis': self.handle_instant_analysis,
            'popular_symbols': self.show_popular_symbols,
            'hot_signals': self.show_hot_signals,
            'market_overview': self.show_market_overview,
            
            # پورتفولیو و قیمت‌ها
            'show_portfolio': self.show_portfolio,
            'price_check': self.handle_price_check,
            'price_alerts': self.manage_price_alerts,
            
            # تنظیمات
            'show_settings': self.show_settings_menu,
            'notification_settings': self.handle_notification_settings,
            'trading_settings': self.handle_trading_settings,
            'account_settings': self.handle_account_settings,
            
            # پکیج‌ها و پرداخت
            'show_packages': self.show_packages_menu,
            'select_package': self.handle_package_selection,
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
            
            # ادمین
            'admin_panel': self.show_admin_panel,
            'user_management': self.show_user_management,
            'system_stats': self.show_system_statistics,
            'broadcast_message': self.handle_broadcast_message,
            
            # راهنما
            'show_help': self.show_help_menu,
            'quick_start_guide': self.show_quick_start_guide,
            'analysis_guide': self.show_analysis_guide,
            'signals_guide': self.show_signals_guide,
            
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
            parts = callback_data.split(':', 1)
            action = parts[0]
            param = parts[1] if len(parts) > 1 else None
            
            # ذخیره پارامتر در context
            if param:
                context.user_data['callback_param'] = param
            
            # یافتن تابع مناسب
            handler_function = self.callback_map.get(action)
            
            if handler_function:
                await handler_function(query, context)
            else:
                # callback های خاص که نیاز به پردازش پیشرفته‌تر دارند
                await self._handle_complex_callback(query, context, action, param)
                
        except Exception as e:
            logger.error(f"Error processing callback {callback_data}: {e}")
            await query.edit_message_text("❌ خطا در پردازش درخواست.")
    
    async def _handle_complex_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, action: str, param: str):
        """پردازش callback های پیچیده"""
        try:
            if action.startswith('analyze_symbol'):
                await self.handle_symbol_analysis(query, context, param)
            elif action.startswith('select_timeframe'):
                await self.handle_timeframe_selection(query, context, param)
            elif action.startswith('package_buy'):
                await self.handle_package_purchase(query, context, param)
            elif action.startswith('payment_confirm'):
                await self.handle_payment_confirmation(query, context, param)
            elif action.startswith('admin_user'):
                await self.handle_admin_user_action(query, context, param)
            elif action.startswith('symbol_page'):
                await self.handle_symbol_pagination(query, context, param)
            else:
                await query.edit_message_text("❌ عمل نامشخص.")
                
        except Exception as e:
            logger.error(f"Error handling complex callback {action}: {e}")
    
    # =========================
    # هندلرهای ثبت‌نام و شروع
    # =========================
    
    async def handle_user_registration(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ثبت‌نام کاربر"""
        try:
            user = query.from_user
            
            # بررسی عدم ثبت‌نام قبلی
            existing_user = await self.user_manager.get_user_by_telegram_id(user.id)
            if existing_user:
                await query.edit_message_text("✅ شما قبلاً ثبت‌نام کرده‌اید.")
                return
            
            # ثبت‌نام کاربر
            registration_result = await self.user_manager.register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            if registration_result['success']:
                # پردازش رفرال اگر وجود داشته باشد
                referral_code = context.user_data.get('referral_code')
                if referral_code:
                    await self.referral_manager.process_referral(user.id, referral_code)
                
                success_message = f"""
✅ <b>ثبت‌نام با موفقیت انجام شد!</b>

🎉 خوش آمدید به خانواده MrTrader
🆔 شناسه کاربری: <code>{user.id}</code>
📅 تاریخ ثبت‌نام: {self.time_manager.get_current_time_persian()}

💰 <b>پاداش خوش‌آمدگویی:</b>
🎁 {Config.WELCOME_BONUS} امتیاز هدیه
📊 {Config.FREE_TRIAL_DAYS} روز دسترسی رایگان

حالا می‌توانید از تمام امکانات ربات استفاده کنید!
"""
                
                keyboard = [
                    [InlineKeyboardButton("🚀 شروع کار", callback_data="main_menu")],
                    [InlineKeyboardButton("📚 آموزش سریع", callback_data="quick_start_guide")]
                ]
                
                await query.edit_message_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(f"❌ خطا در ثبت‌نام: {registration_result['message']}")
                
        except Exception as e:
            logger.error(f"Error in user registration: {e}")
            await query.edit_message_text("❌ خطا در فرآیند ثبت‌نام.")
    
    async def show_terms_and_conditions(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش قوانین و مقررات"""
        try:
            terms_text = f"""
📋 <b>قوانین و مقررات MrTrader Bot</b>

<b>1. شرایط استفاده:</b>
• ربات فقط جهت اطلاع‌رسانی و کمک به تحلیل است
• هیچ‌گونه مشاوره مالی ارائه نمی‌شود
• تصمیمات سرمایه‌گذاری بر عهده شماست

<b>2. مسئولیت:</b>
• ربات مسئولیت سود و زیان شما را ندارد
• همیشه تحقیق شخصی انجام دهید
• از مدیریت ریسک استفاده کنید

<b>3. حریم خصوصی:</b>
• اطلاعات شما محفوظ نگه داشته می‌شود
• هیچ‌گونه اطلاعات شخصی به اشتراک گذاشته نمی‌شود

<b>4. قوانین:</b>
• از ربات سوءاستفاده نکنید
• محترمانه رفتار کنید
• قوانین کشورتان را رعایت کنید

آیا قوانین را مطالعه کرده و می‌پذیرید؟
"""
            
            keyboard = [
                [InlineKeyboardButton("✅ قبول می‌کنم", callback_data="accept_terms")],
                [InlineKeyboardButton("❌ رد می‌کنم", callback_data="reject_terms")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ]
            
            await query.edit_message_text(
                terms_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing terms: {e}")
    
    async def handle_terms_acceptance(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پذیرش قوانین"""
        try:
            # ثبت پذیرش قوانین
            context.user_data['terms_accepted'] = True
            
            success_message = """
✅ <b>قوانین پذیرفته شد</b>

حالا می‌توانید در ربات ثبت‌نام کنید.
"""
            
            keyboard = [
                [InlineKeyboardButton("📝 ثبت‌نام", callback_data="register_user")]
            ]
            
            await query.edit_message_text(
                success_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
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
            
            menu_message = f"""
🏠 <b>منوی اصلی MrTrader</b>

👋 سلام {user.first_name}
📊 پکیج فعال: {user_data.get('package_type', 'رایگان')}
⭐ امتیاز: {user_data.get('user_points', 0):,}

یکی از گزینه‌های زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 تحلیل سریع", callback_data="quick_analysis"),
                    InlineKeyboardButton("📈 سیگنال‌ها", callback_data="show_signals")
                ],
                [
                    InlineKeyboardButton("💼 پورتفولیو", callback_data="show_portfolio"),
                    InlineKeyboardButton("💰 قیمت‌ها", callback_data="price_check")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="show_settings"),
                    InlineKeyboardButton("📊 گزارش‌ها", callback_data="show_reports")
                ],
                [
                    InlineKeyboardButton("🎁 رفرال", callback_data="show_referral"),
                    InlineKeyboardButton("💎 ارتقاء پکیج", callback_data="show_packages")
                ],
                [
                    InlineKeyboardButton("🆘 پشتیبانی", callback_data="contact_support"),
                    InlineKeyboardButton("❓ راهنما", callback_data="show_help")
                ]
            ]
            
            # افزودن پنل ادمین اگر کاربر ادمین است
            if await self.admin_manager.is_admin(user.id):
                keyboard.append([InlineKeyboardButton("🛠️ پنل ادمین", callback_data="admin_panel")])
            
            await query.edit_message_text(
                menu_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
    
    # =========================
    # هندلرهای تحلیل و سیگنال
    # =========================
    
    async def handle_quick_analysis(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """تحلیل سریع"""
        try:
            message = """
⚡ <b>تحلیل سریع</b>

لطفاً نماد ارز مورد نظر خود را انتخاب کنید:
"""
            
            # دریافت نمادهای محبوب
            popular_symbols = await self.symbol_manager.get_popular_symbols(8)
            
            keyboard = []
            for i in range(0, len(popular_symbols), 2):
                row = []
                for j in range(2):
                    if i + j < len(popular_symbols):
                        symbol = popular_symbols[i + j]
                        row.append(InlineKeyboardButton(
                            f"{symbol['symbol']}", 
                            callback_data=f"analyze_symbol:{symbol['symbol']}"
                        ))
                keyboard.append(row)
            
            keyboard.extend([
                [InlineKeyboardButton("🔍 جستجوی نماد", callback_data="search_symbol")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in quick analysis: {e}")
    
    async def handle_symbol_analysis(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """تحلیل نماد خاص"""
        try:
            # نمایش پیام در حال پردازش
            await query.edit_message_text("🔄 در حال تحلیل... لطفاً صبر کنید.")
            
            # انجام تحلیل
            analysis_results = await self.strategy_manager.analyze_symbol(symbol, 'USDT')
            
            if analysis_results:
                # ساخت پیام نتایج
                result_message = f"""
📊 <b>تحلیل {symbol}/USDT</b>

{self._format_analysis_results(analysis_results)}

🕐 آخرین بروزرسانی: {self.time_manager.get_current_time_persian()}
"""
                
                keyboard = [
                    [
                        InlineKeyboardButton("📈 تحلیل تفصیلی", callback_data=f"detailed_analysis:{symbol}"),
                        InlineKeyboardButton("🔔 تنظیم هشدار", callback_data=f"set_alert:{symbol}")
                    ],
                    [
                        InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_symbol:{symbol}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="quick_analysis")
                    ]
                ]
                
                await query.edit_message_text(
                    result_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    "❌ خطا در دریافت تحلیل. لطفاً دوباره تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="quick_analysis")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol}: {e}")
    
    def _format_analysis_results(self, results: List) -> str:
        """فرمت‌بندی نتایج تحلیل"""
        try:
            if not results:
                return "❌ تحلیلی یافت نشد"
            
            # انتخاب بهترین سیگنال
            best_signal = max(results, key=lambda x: x.confidence)
            
            signal_emoji = {
                'STRONG_BUY': '🟢⬆️',
                'BUY': '🟢',
                'HOLD': '🟡',
                'SELL': '🔴',
                'STRONG_SELL': '🔴⬇️'
            }
            
            emoji = signal_emoji.get(best_signal.signal_type.name, '⚪')
            
            formatted = f"""
{emoji} <b>سیگنال: {best_signal.signal_type.value.upper()}</b>
💰 قیمت فعلی: ${best_signal.current_price:,.4f}
💪 قدرت: {best_signal.strength.value}/5
🎯 اعتماد: {best_signal.confidence:.1%}
📈 ترند: {best_signal.trend_direction.value}
⚠️ ریسک: {best_signal.risk_level.value}

📊 <b>شاخص‌های تکنیکال:</b>
"""
            
            # افزودن شاخص‌ها
            for indicator in best_signal.indicators[:3]:  # نمایش 3 شاخص اول
                formatted += f"• {indicator.name}: {indicator.signal.value} ({indicator.confidence:.1%})\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting analysis results: {e}")
            return "❌ خطا در نمایش نتایج"
    
    # =========================
    # سایر هندلرها (ادامه در پیام بعدی...)
    # =========================
    
    async def show_signals_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سیگنال‌ها"""
        try:
            # این تابع و سایر توابع باقی‌مانده در ادامه...
            pass
        except Exception as e:
            logger.error(f"Error showing signals menu: {e}")
    
    # سایر توابع هندلر...
    # (به دلیل محدودیت طول، ادامه در فایل بعدی)
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            CallbackQueryHandler(self.handle_callback_query)
        ]


# Export
__all__ = ['CallbackHandler']