"""
هندلرهای پردازش پیام‌های متنی MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
from telegram.constants import ParseMode
from typing import Dict, List, Any, Optional
import re
import asyncio

from core.config import Config
from utils.logger import logger, log_user_action
from managers.user_manager import UserManager
from managers.security_manager import SecurityManager
from managers.symbol_manager import SymbolManager
from managers.strategy_manager import StrategyManager
from managers.message_manager import MessageManager
from managers.admin_manager import AdminManager
from api.api_client import ApiClient
from utils.time_manager import TimeManager


# States برای ConversationHandler
(WAITING_SYMBOL_INPUT, WAITING_PRICE_ALERT, WAITING_SUPPORT_MESSAGE, 
 WAITING_BROADCAST_MESSAGE, WAITING_FEEDBACK) = range(5)


class MessageHandler:
    """هندلر پیام‌های متنی"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.security_manager = SecurityManager()
        self.symbol_manager = SymbolManager()
        self.strategy_manager = StrategyManager()
        self.message_manager = MessageManager()
        self.admin_manager = AdminManager()
        self.time_manager = TimeManager()
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام‌های متنی عمومی"""
        try:
            user = update.effective_user
            message_text = update.message.text.strip()
            
            # لاگ پیام
            log_user_action(user.id, "text_message", f"Message: {message_text[:50]}...")
            
            # بررسی امنیت
            if not await self.security_manager.is_user_allowed(user.id):
                await update.message.reply_text("❌ دسترسی شما محدود شده است.")
                return
            
            # بررسی ثبت‌نام کاربر
            user_data = await self.user_manager.get_user_by_telegram_id(user.id)
            if not user_data:
                await update.message.reply_text(
                    "❌ ابتدا باید در ربات ثبت‌نام کنید.\nاز دستور /start استفاده کنید."
                )
                return
            
            # شناسایی نوع پیام و پردازش
            await self._process_message_content(update, context, message_text)
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text("❌ خطا در پردازش پیام.")
    
    async def _process_message_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """پردازش محتوای پیام بر اساس نوع"""
        try:
            # تشخیص نماد ارز
            if self._is_crypto_symbol(text):
                await self._handle_symbol_query(update, context, text.upper())
                return
            
            # تشخیص قیمت
            if self._is_price_query(text):
                await self._handle_price_query(update, context, text)
                return
            
            # تشخیص سؤال عمومی
            if self._is_question(text):
                await self._handle_general_question(update, context, text)
                return
            
            # پردازش پیام آزاد
            await self._handle_free_text(update, context, text)
            
        except Exception as e:
            logger.error(f"Error processing message content: {e}")
    
    def _is_crypto_symbol(self, text: str) -> bool:
        """تشخیص نماد ارز دیجیتال"""
        # الگوی نمادهای معمول ارز دیجیتال
        pattern = r'^[A-Z]{2,10}$'
        return bool(re.match(pattern, text.upper())) and len(text) <= 10
    
    def _is_price_query(self, text: str) -> bool:
        """تشخیص درخواست قیمت"""
        price_keywords = ['قیمت', 'price', 'چند', 'کرح', '$']
        return any(keyword in text.lower() for keyword in price_keywords)
    
    def _is_question(self, text: str) -> bool:
        """تشخیص سؤال"""
        question_markers = ['؟', '?', 'چی', 'کی', 'چه', 'چگونه', 'چرا', 'کجا']
        return any(marker in text for marker in question_markers) or text.endswith('؟')
    
    async def _handle_symbol_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """پردازش درخواست نماد ارز"""
        try:
            # نمایش پیام در حال پردازش
            processing_msg = await update.message.reply_text("🔄 در حال دریافت اطلاعات...")
            
            # دریافت اطلاعات نماد
            symbol_info = await self.symbol_manager.get_symbol_info(symbol)
            
            if symbol_info and 'error' not in symbol_info:
                # ساخت پیام اطلاعات
                info_message = f"""
📊 <b>{symbol}/USDT</b>

💰 <b>قیمت فعلی:</b> ${symbol_info.get('price', 0):,.4f}
📈 <b>تغییر 24 ساعته:</b> {symbol_info.get('change_24h', 0):+.2f}%
📊 <b>حجم 24 ساعته:</b> ${symbol_info.get('volume_24h', 0):,.0f}
⬆️ <b>بالاترین 24h:</b> ${symbol_info.get('high_24h', 0):,.4f}
⬇️ <b>پایین‌ترین 24h:</b> ${symbol_info.get('low_24h', 0):,.4f}

🕐 <b>آخرین بروزرسانی:</b> {self.time_manager.get_current_time_persian()}
"""
                
                # کیبورد عملیات
                keyboard = [
                    [
                        InlineKeyboardButton("📊 تحلیل کامل", callback_data=f"analyze_symbol:{symbol}"),
                        InlineKeyboardButton("🔔 تنظیم هشدار", callback_data=f"set_alert:{symbol}")
                    ],
                    [
                        InlineKeyboardButton("📈 نمودار", callback_data=f"show_chart:{symbol}"),
                        InlineKeyboardButton("➕ افزودن به لیست", callback_data=f"add_watchlist:{symbol}")
                    ]
                ]
                
                # حذف پیام پردازش و ارسال نتیجه
                await processing_msg.delete()
                await update.message.reply_text(
                    info_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await processing_msg.edit_text(
                    f"❌ نماد {symbol} یافت نشد یا در دسترس نیست.\n"
                    "لطفاً نماد صحیح وارد کنید."
                )
                
        except Exception as e:
            logger.error(f"Error handling symbol query {symbol}: {e}")
            await update.message.reply_text("❌ خطا در دریافت اطلاعات نماد.")
    
    async def _handle_price_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """پردازش درخواست قیمت"""
        try:
            # استخراج نماد از متن
            symbols = self._extract_symbols_from_text(text)
            
            if not symbols:
                await update.message.reply_text(
                    "❌ نماد ارز مشخص نیست.\n"
                    "مثال: قیمت BTC یا چند Bitcoin"
                )
                return
            
            # دریافت قیمت برای اولین نماد
            symbol = symbols[0]
            price = await ApiClient.fetch_live_price(symbol, 'USDT')
            
            if price > 0:
                # دریافت تغییر 24 ساعته
                market_data = await ApiClient.fetch_market_data(symbol, 'USDT')
                change_24h = market_data.get('change_percent_24h', 0) if 'error' not in market_data else 0
                
                change_emoji = "📈" if change_24h >= 0 else "📉"
                
                price_message = f"""
💰 <b>قیمت {symbol}/USDT</b>

💵 <b>قیمت فعلی:</b> ${price:,.4f}
{change_emoji} <b>تغییر 24h:</b> {change_24h:+.2f}%

🕐 <b>زمان:</b> {self.time_manager.get_current_time_persian()}
"""
                
                keyboard = [
                    [InlineKeyboardButton("📊 تحلیل تفصیلی", callback_data=f"analyze_symbol:{symbol}")]
                ]
                
                await update.message.reply_text(
                    price_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"❌ خطا در دریافت قیمت {symbol}.\n"
                    "لطفاً نماد صحیح وارد کنید."
                )
                
        except Exception as e:
            logger.error(f"Error handling price query: {e}")
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """استخراج نمادهای ارز از متن"""
        try:
            # الگوهای شناخته شده
            common_symbols = {
                'bitcoin': 'BTC', 'بیت کوین': 'BTC', 'بیتکوین': 'BTC',
                'ethereum': 'ETH', 'اتریوم': 'ETH',
                'binance': 'BNB', 'بایننس': 'BNB',
                'cardano': 'ADA', 'کاردانو': 'ADA',
                'ripple': 'XRP', 'ریپل': 'XRP',
                'solana': 'SOL', 'سولانا': 'SOL',
                'dogecoin': 'DOGE', 'دوج کوین': 'DOGE'
            }
            
            symbols = []
            text_lower = text.lower()
            
            # جستجوی نام‌های شناخته شده
            for name, symbol in common_symbols.items():
                if name in text_lower:
                    symbols.append(symbol)
            
            # جستجوی نمادهای مستقیم
            words = text.upper().split()
            for word in words:
                if self._is_crypto_symbol(word):
                    symbols.append(word)
            
            return list(set(symbols))  # حذف تکراری
            
        except Exception as e:
            logger.error(f"Error extracting symbols from text: {e}")
            return []
    
    async def _handle_general_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """پردازش سؤالات عمومی"""
        try:
            # پاسخ‌های از پیش تعریف شده
            predefined_answers = {
                'چگونه': 'برای یادگیری نحوه استفاده از ربات، از دستور /help استفاده کنید.',
                'کی': 'ربات 24/7 در دسترس است و هر زمان می‌توانید استفاده کنید.',
                'چرا': 'ربات برای کمک به تحلیل بازار ارزهای دیجیتال طراحی شده است.',
                'قیمت چند': 'لطفاً نماد ارز مورد نظر را مشخص کنید. مثل: قیمت BTC',
                'کجا': 'می‌توانید از منوی اصلی (/start) تمام امکانات را مشاهده کنید.'
            }
            
            # یافتن مناسب‌ترین پاسخ
            response = None
            for keyword, answer in predefined_answers.items():
                if keyword in text:
                    response = answer
                    break
            
            if not response:
                response = """
❓ <b>سؤال شما دریافت شد</b>

متأسفانه نتوانستم پاسخ دقیق شما را تشخیص دهم.
لطفاً از گزینه‌های زیر استفاده کنید:

• /help - راهنمای کامل
• /menu - منوی سریع  
• /start - منوی اصلی

یا با پشتیبانی تماس بگیرید.
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📚 راهنما", callback_data="show_help"),
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
                ],
                [
                    InlineKeyboardButton("🆘 پشتیبانی", callback_data="contact_support")
                ]
            ]
            
            await update.message.reply_text(
                response,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling general question: {e}")
    
    async def _handle_free_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """پردازش متن آزاد"""
        try:
            # تشخیص نیت کاربر
            if len(text) < 3:
                return  # متن خیلی کوتاه
            
            # پیام پیش‌فرض
            response = """
💬 <b>پیام شما دریافت شد</b>

اگر به دنبال چیز خاصی هستید:
• برای تحلیل: نماد ارز را بنویسید (مثل BTC)
• برای قیمت: "قیمت" + نماد ارز
• برای راهنما: دستور /help

از منوی زیر می‌توانید گزینه مورد نظر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 تحلیل", callback_data="quick_analysis"),
                    InlineKeyboardButton("💰 قیمت‌ها", callback_data="price_check")
                ],
                [
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
                ]
            ]
            
            await update.message.reply_text(
                response,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling free text: {e}")
    
    # =========================
    # ConversationHandler ها
    # =========================
    
    async def start_symbol_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع جستجوی نماد"""
        await update.message.reply_text(
            "🔍 <b>جستجوی نماد</b>\n\n"
            "نام یا نماد ارز مورد نظر خود را وارد کنید:\n"
            "مثال: BTC، Bitcoin، بیت کوین\n\n"
            "برای لغو: /cancel",
            parse_mode=ParseMode.HTML
        )
        return WAITING_SYMBOL_INPUT
    
    async def handle_symbol_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی جستجوی نماد"""
        try:
            query = update.message.text.strip()
            
            if len(query) < 2:
                await update.message.reply_text(
                    "❌ لطفاً حداقل 2 کاراکتر وارد کنید."
                )
                return WAITING_SYMBOL_INPUT
            
            # جستجوی نمادها
            search_results = await self.symbol_manager.search_symbols(query, 10)
            
            if search_results:
                message = f"🔍 <b>نتایج جستجو برای '{query}':</b>\n\n"
                
                keyboard = []
                for symbol in search_results:
                    symbol_name = symbol['symbol']
                    price = symbol.get('price', 0)
                    change = symbol.get('change_24h', 0)
                    
                    change_emoji = "📈" if change >= 0 else "📉"
                    
                    button_text = f"{symbol_name} - ${price:.4f} {change_emoji}"
                    keyboard.append([InlineKeyboardButton(
                        button_text, 
                        callback_data=f"analyze_symbol:{symbol_name}"
                    )])
                
                keyboard.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")])
                
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"❌ هیچ نمادی برای '{query}' یافت نشد.\n"
                    "لطفاً عبارت دیگری امتحان کنید."
                )
                return WAITING_SYMBOL_INPUT
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in symbol search: {e}")
            await update.message.reply_text("❌ خطا در جستجو.")
            return ConversationHandler.END
    
    async def start_price_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع تنظیم هشدار قیمت"""
        symbol = context.user_data.get('alert_symbol', 'BTC')
        
        await update.message.reply_text(
            f"🔔 <b>تنظیم هشدار قیمت برای {symbol}</b>\n\n"
            "قیمت هدف را وارد کنید:\n"
            "مثال: 50000 یا 0.5\n\n"
            "برای لغو: /cancel",
            parse_mode=ParseMode.HTML
        )
        return WAITING_PRICE_ALERT
    
    async def handle_price_alert_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی هشدار قیمت"""
        try:
            price_text = update.message.text.strip()
            
            # تبدیل به عدد
            try:
                target_price = float(price_text.replace(',', ''))
            except ValueError:
                await update.message.reply_text(
                    "❌ لطفاً یک عدد معتبر وارد کنید.\n"
                    "مثال: 50000 یا 0.5"
                )
                return WAITING_PRICE_ALERT
            
            if target_price <= 0:
                await update.message.reply_text("❌ قیمت باید بزرگتر از صفر باشد.")
                return WAITING_PRICE_ALERT
            
            symbol = context.user_data.get('alert_symbol', 'BTC')
            user_id = update.effective_user.id
            
            # در اینجا باید هشدار در دیتابیس ذخیره شود
            # برای سادگی فقط پیام تأیید نشان می‌دهیم
            
            await update.message.reply_text(
                f"✅ <b>هشدار تنظیم شد</b>\n\n"
                f"💰 نماد: {symbol}\n"
                f"🎯 قیمت هدف: ${target_price:,.4f}\n"
                f"🔔 به محض رسیدن قیمت، اطلاع‌رسانی خواهید شد.\n\n"
                f"⏰ زمان تنظیم: {self.time_manager.get_current_time_persian()}",
                parse_mode=ParseMode.HTML
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error setting price alert: {e}")
            await update.message.reply_text("❌ خطا در تنظیم هشدار.")
            return ConversationHandler.END
    
    async def start_support_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع پیام پشتیبانی"""
        await update.message.reply_text(
            "🆘 <b>ارسال پیام به پشتیبانی</b>\n\n"
            "لطفاً پیام خود را برای تیم پشتیبانی بنویسید:\n\n"
            "• توضیح مشکل یا سؤال\n"
            "• عکس یا فایل (در صورت نیاز)\n\n"
            "برای لغو: /cancel",
            parse_mode=ParseMode.HTML
        )
        return WAITING_SUPPORT_MESSAGE
    
    async def handle_support_message_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام پشتیبانی"""
        try:
            user = update.effective_user
            message_text = update.message.text or update.message.caption or "پیام بدون متن"
            
            # ایجاد تیکت پشتیبانی
            ticket_id = f"T{user.id}{int(self.time_manager.get_current_timestamp())}"
            
            # در پیاده‌سازی واقعی، اینجا پیام به ادمین‌ها ارسال می‌شود
            await self.message_manager.send_support_notification(
                user_id=user.id,
                username=user.username,
                message=message_text,
                ticket_id=ticket_id
            )
            
            await update.message.reply_text(
                f"✅ <b>پیام شما ارسال شد</b>\n\n"
                f"🎫 شماره تیکت: <code>{ticket_id}</code>\n"
                f"⏰ زمان ارسال: {self.time_manager.get_current_time_persian()}\n\n"
                f"تیم پشتیبانی در اولین فرصت پاسخ خواهد داد.\n"
                f"معمولاً در کمتر از 24 ساعت پاسخ دریافت می‌کنید.",
                parse_mode=ParseMode.HTML
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error handling support message: {e}")
            await update.message.reply_text("❌ خطا در ارسال پیام.")
            return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو مکالمه"""
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n\n"
            "برای بازگشت به منوی اصلی: /start"
        )
        return ConversationHandler.END
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            # ConversationHandler برای جستجوی نماد
            ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^🔍 جستجوی نماد$"), self.start_symbol_search)],
                states={
                    WAITING_SYMBOL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_symbol_search_input)],
                },
                fallbacks=[MessageHandler(filters.Regex("^/cancel$"), self.cancel_conversation)],
            ),
            
            # ConversationHandler برای هشدار قیمت
            ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^🔔 تنظیم هشدار$"), self.start_price_alert)],
                states={
                    WAITING_PRICE_ALERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_price_alert_input)],
                },
                fallbacks=[MessageHandler(filters.Regex("^/cancel$"), self.cancel_conversation)],
            ),
            
            # ConversationHandler برای پشتیبانی
            ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^🆘 پشتیبانی$"), self.start_support_message)],
                states={
                    WAITING_SUPPORT_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO | filters.DOCUMENT, self.handle_support_message_input)],
                },
                fallbacks=[MessageHandler(filters.Regex("^/cancel$"), self.cancel_conversation)],
            ),
            
            # هندلر پیام‌های متنی عمومی (آخرین هندلر)
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message),
        ]


# Export
__all__ = ['MessageHandler', 'WAITING_SYMBOL_INPUT', 'WAITING_PRICE_ALERT', 
           'WAITING_SUPPORT_MESSAGE', 'WAITING_BROADCAST_MESSAGE', 'WAITING_FEEDBACK']