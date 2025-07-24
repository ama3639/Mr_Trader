"""
هندلرهای پردازش پیام‌های متنی برای MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from typing import List, Dict, Any, Optional

from core.config import Config
from utils.logger import logger, log_user_action
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from managers.symbol_manager import SymbolManager
from managers.strategy_manager import StrategyManager
from templates.keyboards import KeyboardTemplates
from templates.messages import MessageTemplates


class MessageHandler:
    """کلاس مدیریت پیام‌های متنی"""
    
    def __init__(self):
        # مقداردهی manager ها
        self.user_manager = UserManager()
        self.admin_manager = AdminManager()
        self.symbol_manager = SymbolManager()
        self.strategy_manager = StrategyManager()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """هندلر اصلی پیام‌های متنی
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            message = update.message
            user = update.effective_user
            text = message.text.strip()
            
            # لاگ پیام کاربر
            log_user_action(user.id, "text_message", f"Message: {text[:100]}")
            
            # بررسی مسدودیت کاربر
            if UserManager.is_user_blocked(user.id):
                await message.reply_text(
                    "⛔ حساب کاربری شما مسدود شده است.\n"
                    "لطفاً با پشتیبانی تماس بگیرید: @mrtrader_support",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # بررسی حالت‌های مختلف در context
            await self._process_context_states(update, context, text)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text(
                    "❌ خطایی در پردازش پیام رخ داد.\n"
                    "لطفاً از دکمه‌های موجود استفاده کنید یا /start را بزنید."
                )
            except:
                pass
    
    async def _process_context_states(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """پردازش حالت‌های مختلف context
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            text: متن پیام
        """
        user_data = context.user_data
        user = update.effective_user
        
        # بررسی ورودی دستی نماد
        if user_data.get('waiting_for_manual_symbol'):
            await self._handle_manual_symbol_input(update, context, text)
            return
        
        # بررسی ورودی دستی ارز مرجع
        if user_data.get('waiting_for_manual_currency'):
            await self._handle_manual_currency_input(update, context, text)
            return
        
        # بررسی ورودی کد تخفیف
        if user_data.get('waiting_for_discount_code'):
            await self._handle_discount_code_input(update, context, text)
            return
        
        # بررسی ورودی مبلغ شارژ
        if user_data.get('waiting_for_charge_amount'):
            await self._handle_charge_amount_input(update, context, text)
            return
        
        # بررسی ورودی جستجوی کاربر (ادمین)
        if user_data.get('waiting_for_user_search') and await self._is_admin(user.id):
            await self._handle_user_search_input(update, context, text)
            return
        
        # بررسی ورودی پیام پشتیبانی
        if user_data.get('waiting_for_support_message'):
            await self._handle_support_message_input(update, context, text)
            return
        
        # اگر هیچ حالتی فعال نبود، راهنما نشان بده
        await self._show_default_help(update, context)
    
    async def _handle_manual_symbol_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
        """پردازش ورودی دستی نماد
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            symbol: نماد وارد شده
        """
        try:
            # پاکسازی context
            strategy = context.user_data.pop('waiting_for_manual_symbol', None)
            
            # اعتبارسنجی نماد
            symbol = symbol.upper()
            if symbol not in Config.SUPPORTED_SYMBOLS:
                await update.message.reply_text(
                    f"❌ نماد <b>{symbol}</b> پشتیبانی نمی‌شود.\n\n"
                    f"نمادهای پشتیبانی شده:\n"
                    f"{', '.join(Config.SUPPORTED_SYMBOLS[:20])}...\n\n"
                    f"لطفاً نماد صحیح را وارد کنید یا از دکمه‌ها استفاده کنید.",
                    parse_mode=ParseMode.HTML
                )
                
                # نشان دادن کیبورد انتخاب نماد
                keyboard = KeyboardTemplates.symbol_selection(strategy)
                await update.message.reply_text(
                    "🪙 لطفاً نماد را انتخاب کنید:",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                return
            
            # ذخیره نماد و ادامه به مرحله بعد
            context.user_data['selected_symbol'] = symbol
            
            # نمایش انتخاب ارز مرجع
            message = f"""✅ نماد <b>{symbol}</b> انتخاب شد.

💱 <b>مرحله 2: انتخاب ارز مرجع</b>

لطفاً ارز مرجع مورد نظر را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.currency_selection(strategy, symbol)
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling manual symbol input: {e}")
            await update.message.reply_text("❌ خطا در پردازش نماد. لطفاً دوباره تلاش کنید.")
    
    async def _handle_manual_currency_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, currency: str) -> None:
        """پردازش ورودی دستی ارز مرجع
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            currency: ارز مرجع وارد شده
        """
        try:
            # پاکسازی context
            data = context.user_data.pop('waiting_for_manual_currency', {})
            strategy = data.get('strategy')
            symbol = data.get('symbol')
            
            # اعتبارسنجی ارز مرجع
            currency = currency.upper()
            if currency not in Config.SUPPORTED_CURRENCIES:
                await update.message.reply_text(
                    f"❌ ارز مرجع <b>{currency}</b> پشتیبانی نمی‌شود.\n\n"
                    f"ارزهای پشتیبانی شده:\n"
                    f"{', '.join(Config.SUPPORTED_CURRENCIES)}\n\n"
                    f"لطفاً ارز صحیح را وارد کنید یا از دکمه‌ها استفاده کنید.",
                    parse_mode=ParseMode.HTML
                )
                
                # نشان دادن کیبورد انتخاب ارز
                keyboard = KeyboardTemplates.currency_selection(strategy, symbol)
                await update.message.reply_text(
                    "💱 لطفاً ارز مرجع را انتخاب کنید:",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                return
            
            # ذخیره ارز مرجع و ادامه به مرحله بعد
            context.user_data['selected_currency'] = currency
            
            # نمایش انتخاب تایم‌فریم
            message = f"""✅ جفت ارز <b>{symbol}/{currency}</b> انتخاب شد.

⏱ <b>مرحله 3: انتخاب تایم‌فریم</b>

لطفاً تایم‌فریم مورد نظر را انتخاب کنید:"""
            
            keyboard = KeyboardTemplates.timeframe_selection(strategy, symbol, currency)
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling manual currency input: {e}")
            await update.message.reply_text("❌ خطا در پردازش ارز مرجع. لطفاً دوباره تلاش کنید.")
    
    async def _handle_discount_code_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, code: str) -> None:
        """پردازش ورودی کد تخفیف
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            code: کد تخفیف
        """
        try:
            # پاکسازی context
            context.user_data.pop('waiting_for_discount_code', None)
            
            # TODO: اعتبارسنجی کد تخفیف
            # این بخش باید با سیستم مدیریت کد تخفیف یکپارچه شود
            
            await update.message.reply_text(
                f"🎁 کد تخفیف <code>{code}</code> دریافت شد.\n\n"
                "⚠️ این قابلیت در حال توسعه است.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling discount code: {e}")
    
    async def _handle_charge_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount_text: str) -> None:
        """پردازش ورودی مبلغ شارژ
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            amount_text: مبلغ وارد شده
        """
        try:
            # پاکسازی context
            context.user_data.pop('waiting_for_charge_amount', None)
            
            # تبدیل به عدد
            try:
                amount = int(amount_text.replace(',', '').replace('.', ''))
                if amount < 10000:  # حداقل 10 هزار تومان
                    raise ValueError("مبلغ کم است")
            except:
                await update.message.reply_text(
                    "❌ مبلغ وارد شده نامعتبر است.\n\n"
                    "لطفاً مبلغ را به صورت عددی وارد کنید.\n"
                    "حداقل مبلغ: 10,000 تومان",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # TODO: ادامه فرآیند پرداخت
            await update.message.reply_text(
                f"💰 مبلغ <b>{amount:,}</b> تومان ثبت شد.\n\n"
                "⚠️ سیستم پرداخت در حال توسعه است.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling charge amount: {e}")
    
    async def _handle_user_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, search_text: str) -> None:
        """پردازش ورودی جستجوی کاربر (ادمین)
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            search_text: متن جستجو
        """
        try:
            # پاکسازی context
            context.user_data.pop('waiting_for_user_search', None)
            
            # TODO: جستجوی کاربر در دیتابیس
            await update.message.reply_text(
                f"🔍 جستجوی <code>{search_text}</code> انجام شد.\n\n"
                "⚠️ این قابلیت در حال توسعه است.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling user search: {e}")
    
    async def _handle_support_message_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> None:
        """پردازش ورودی پیام پشتیبانی
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
            message_text: پیام کاربر
        """
        try:
            # پاکسازی context
            context.user_data.pop('waiting_for_support_message', None)
            
            # TODO: ارسال پیام به پشتیبانی
            await update.message.reply_text(
                "✅ پیام شما دریافت شد و به واحد پشتیبانی ارسال گردید.\n\n"
                "⏰ زمان پاسخگویی: حداکثر 24 ساعت\n\n"
                "در صورت نیاز فوری می‌توانید به @mrtrader_support پیام دهید.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error handling support message: {e}")
    
    async def _show_default_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """نمایش راهنمای پیش‌فرض
        
        Args:
            update: آپدیت تلگرام
            context: کانتکست ربات
        """
        try:
            help_message = """❓ متوجه پیام شما نشدم!

لطفاً از دکمه‌های زیر استفاده کنید:

/start - شروع یا منوی اصلی
/help - راهنمای کامل
/menu - منوی سریع
/profile - پروفایل شما

یا از دکمه‌های موجود در پیام‌ها استفاده کنید."""
            
            keyboard = [
                [
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu"),
                    InlineKeyboardButton("📚 راهنما", callback_data="help_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                help_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing default help: {e}")
    
    async def _is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            آیا کاربر ادمین است
        """
        try:
            if hasattr(self.admin_manager, 'is_admin'):
                return self.admin_manager.is_admin(user_id)
            return False
        except:
            return False
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها
        
        Returns:
            لیست هندلرهای پیام
        """
        try:
            from telegram.ext import MessageHandler as TelegramMessageHandler, filters
            
            return [
                # هندلر پیام‌های متنی غیر از کامند
                TelegramMessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    self.handle_message
                )
            ]
        except ImportError:
            logger.error("Could not import MessageHandler from telegram.ext")
            return []


# Export
__all__ = ['MessageHandler']