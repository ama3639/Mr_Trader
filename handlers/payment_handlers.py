"""
هندلرهای پرداخت و خرید پکیج MrTrader Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.constants import ParseMode
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

from core.config import Config
from utils.logger import logger, log_payment_action
from managers.user_manager import UserManager
from managers.payment_manager import PaymentManager
from managers.message_manager import MessageManager
from models.package import PackageModel, DefaultPackages
from models.transaction import TransactionModel, TransactionFactory, PaymentMethod, Currency
from utils.time_manager import TimeManager
from utils.formatters import NumberFormatter, DateTimeFormatter
from utils.validators import PaymentValidator, PackageValidator


# States برای ConversationHandler
(WAITING_PAYMENT_PROOF, WAITING_CUSTOM_AMOUNT, WAITING_DISCOUNT_CODE) = range(3)


class PaymentHandler:
    """هندلر پرداخت و خرید پکیج"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.payment_manager = PaymentManager()
        self.message_manager = MessageManager()
        self.time_manager = TimeManager()
        
        # پکیج‌های موجود
        self.packages = DefaultPackages.get_all_packages()
    
    async def handle_show_packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پکیج‌های موجود"""
        try:
            query = update.callback_query
            await query.answer()
            
            user = query.from_user
            user_data = await self.user_manager.get_user_by_telegram_id(user.id)
            
            if not user_data:
                await query.edit_message_text("❌ ابتدا باید در ربات ثبت‌نام کنید.")
                return
            
            current_package = user_data.get('package_type', 'free')
            
            message = f"""
💎 <b>پکیج‌های MrTrader Bot</b>

🎟️ پکیج فعلی شما: <b>{current_package.title()}</b>

یکی از پکیج‌های زیر را انتخاب کنید:
"""
            
            keyboard = []
            for package in self.packages:
                if package.package_id == 'free':
                    continue  # پکیج رایگان را نشان نمی‌دهیم
                
                # ایموجی ویژه برای پکیج محبوب
                emoji = "🌟 " if package.is_popular else ""
                
                # نمایش قیمت
                price_text = f"${package.price_monthly}/ماه" if package.price_monthly > 0 else "رایگان"
                
                button_text = f"{emoji}{package.name_persian} - {price_text}"
                keyboard.append([InlineKeyboardButton(
                    button_text, 
                    callback_data=f"select_package:{package.package_id}"
                )])
            
            keyboard.extend([
                [InlineKeyboardButton("🎁 کد تخفیف", callback_data="enter_discount_code")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing packages: {e}")
            await query.edit_message_text("❌ خطا در نمایش پکیج‌ها.")
    
    async def handle_package_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب پکیج"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج package_id از callback_data
            package_id = query.data.split(':')[1]
            
            # یافتن پکیج
            selected_package = None
            for package in self.packages:
                if package.package_id == package_id:
                    selected_package = package
                    break
            
            if not selected_package:
                await query.edit_message_text("❌ پکیج یافت نشد.")
                return
            
            # ذخیره انتخاب در context
            context.user_data['selected_package'] = selected_package
            
            # نمایش جزئیات پکیج
            await self._show_package_details(query, context, selected_package)
            
        except Exception as e:
            logger.error(f"Error in package selection: {e}")
            await query.edit_message_text("❌ خطا در انتخاب پکیج.")
    
    async def _show_package_details(self, query, context: ContextTypes.DEFAULT_TYPE, package: PackageModel):
        """نمایش جزئیات پکیج"""
        try:
            # ساخت متن ویژگی‌ها
            features_text = ""
            for feature in package.features:
                if feature.included:
                    limit_text = f" (حداکثر {feature.limit})" if feature.limit else ""
                    features_text += f"✅ {feature.description}{limit_text}\n"
            
            # محاسبه تخفیف
            discount_text = ""
            if package.yearly_discount > 0:
                discount_text = f"\n🎉 <b>تخفیف سالانه:</b> {NumberFormatter.format_percentage(package.yearly_discount)}"
            
            package_info = f"""
💎 <b>{package.name_persian}</b>

📝 <b>توضیحات:</b>
{package.description_persian}

💰 <b>قیمت‌گذاری:</b>
• ماهانه: ${package.price_monthly}
• سه‌ماهه: ${package.price_quarterly} (${package.price_quarterly/3:.2f}/ماه)
• سالانه: ${package.price_yearly} (${package.price_yearly/12:.2f}/ماه){discount_text}

✨ <b>ویژگی‌ها:</b>
{features_text}
📊 <b>سیگنال روزانه:</b> {package.daily_signals_limit}
🎯 <b>پشتیبانی:</b> {package.support_priority}

انتخاب مدت اشتراک:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton(f"1 ماه - ${package.price_monthly}", 
                                       callback_data=f"buy_package:{package.package_id}:1"),
                ],
            ]
            
            if package.price_quarterly > 0:
                monthly_equivalent = package.price_quarterly / 3
                savings = package.price_monthly - monthly_equivalent
                keyboard.append([
                    InlineKeyboardButton(f"3 ماه - ${package.price_quarterly} (صرفه‌جویی ${savings:.2f})", 
                                       callback_data=f"buy_package:{package.package_id}:3")
                ])
            
            if package.price_yearly > 0:
                monthly_equivalent = package.price_yearly / 12
                savings = package.price_monthly - monthly_equivalent
                keyboard.append([
                    InlineKeyboardButton(f"12 ماه - ${package.price_yearly} (صرفه‌جویی ${savings:.2f})", 
                                       callback_data=f"buy_package:{package.package_id}:12")
                ])
            
            keyboard.extend([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="show_packages")]
            ])
            
            await query.edit_message_text(
                package_info,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing package details: {e}")
    
    async def handle_package_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع خرید پکیج"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data
            parts = query.data.split(':')
            package_id = parts[1]
            duration_months = int(parts[2])
            
            user = query.from_user
            
            # یافتن پکیج
            selected_package = None
            for package in self.packages:
                if package.package_id == package_id:
                    selected_package = package
                    break
            
            if not selected_package:
                await query.edit_message_text("❌ پکیج یافت نشد.")
                return
            
            # محاسبه قیمت
            total_price = selected_package.calculate_price(duration_months)
            
            # اعمال تخفیف (اگر وجود داشته باشد)
            discount_code = context.user_data.get('discount_code')
            discount_amount = 0
            if discount_code:
                discount_result = await self.payment_manager.validate_discount_code(discount_code, total_price)
                if discount_result['valid']:
                    discount_amount = discount_result['discount_amount']
            
            final_price = total_price - discount_amount
            
            # ذخیره اطلاعات خرید
            purchase_info = {
                'package_id': package_id,
                'duration_months': duration_months,
                'original_price': total_price,
                'discount_amount': discount_amount,
                'final_price': final_price,
                'discount_code': discount_code
            }
            context.user_data['purchase_info'] = purchase_info
            
            # نمایش انتخاب روش پرداخت
            await self._show_payment_methods(query, context, purchase_info, selected_package)
            
        except Exception as e:
            logger.error(f"Error in package purchase: {e}")
            await query.edit_message_text("❌ خطا در شروع خرید.")
    
    async def _show_payment_methods(self, query, context: ContextTypes.DEFAULT_TYPE, 
                                  purchase_info: Dict, package: PackageModel):
        """نمایش روش‌های پرداخت"""
        try:
            discount_text = ""
            if purchase_info['discount_amount'] > 0:
                discount_text = f"""
🎟️ <b>کد تخفیف:</b> {purchase_info['discount_code']}
💰 <b>قیمت اصلی:</b> ${purchase_info['original_price']}
🎉 <b>تخفیف:</b> -${purchase_info['discount_amount']}
"""
            
            payment_info = f"""
💳 <b>انتخاب روش پرداخت</b>

📦 <b>پکیج:</b> {package.name_persian}
⏱️ <b>مدت:</b> {purchase_info['duration_months']} ماه{discount_text}
💵 <b>مبلغ نهایی:</b> ${purchase_info['final_price']}

یکی از روش‌های پرداخت زیر را انتخاب کنید:
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("💳 کارت اعتباری", 
                                       callback_data=f"payment_method:credit_card"),
                    InlineKeyboardButton("🏦 انتقال بانکی", 
                                       callback_data=f"payment_method:bank_transfer")
                ],
                [
                    InlineKeyboardButton("₿ بیت‌کوین", 
                                       callback_data=f"payment_method:bitcoin"),
                    InlineKeyboardButton("💰 تتر (USDT)", 
                                       callback_data=f"payment_method:tether")
                ],
                [
                    InlineKeyboardButton("💎 اتریوم", 
                                       callback_data=f"payment_method:ethereum"),
                    InlineKeyboardButton("🔄 Perfect Money", 
                                       callback_data=f"payment_method:perfect_money")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_package:{package.package_id}")
                ]
            ]
            
            await query.edit_message_text(
                payment_info,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing payment methods: {e}")
    
    async def handle_payment_method_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب روش پرداخت"""
        try:
            query = update.callback_query
            await query.answer()
            
            payment_method = query.data.split(':')[1]
            purchase_info = context.user_data.get('purchase_info')
            
            if not purchase_info:
                await query.edit_message_text("❌ اطلاعات خرید یافت نشد.")
                return
            
            user = query.from_user
            
            # ایجاد تراکنش
            transaction = TransactionFactory.create_package_purchase(
                user_id=user.id,
                package_id=purchase_info['package_id'],
                amount=purchase_info['final_price'],
                currency=Currency.USD,
                payment_method=PaymentMethod(payment_method),
                duration_months=purchase_info['duration_months']
            )
            
            # اعمال تخفیف
            if purchase_info['discount_amount'] > 0:
                transaction.apply_discount(
                    purchase_info['discount_amount'],
                    purchase_info['discount_code']
                )
            
            # ذخیره تراکنش
            await self.payment_manager.create_transaction(transaction)
            
            # لاگ عملیات
            log_payment_action(
                user.id, 
                "payment_initiated", 
                purchase_info['final_price'],
                transaction.transaction_id,
                f"Package: {purchase_info['package_id']}, Method: {payment_method}"
            )
            
            # نمایش جزئیات پرداخت
            await self._show_payment_details(query, context, transaction, payment_method)
            
        except Exception as e:
            logger.error(f"Error in payment method selection: {e}")
            await query.edit_message_text("❌ خطا در انتخاب روش پرداخت.")
    
    async def _show_payment_details(self, query, context: ContextTypes.DEFAULT_TYPE, 
                                  transaction: TransactionModel, payment_method: str):
        """نمایش جزئیات پرداخت"""
        try:
            payment_info = await self._get_payment_info(payment_method, transaction)
            
            details_message = f"""
💳 <b>جزئیات پرداخت</b>

🆔 <b>شناسه تراکنش:</b> <code>{transaction.transaction_id}</code>
💰 <b>مبلغ:</b> ${transaction.final_amount}
⏰ <b>زمان انقضا:</b> {DateTimeFormatter.format_datetime_persian(transaction.expires_at)}

{payment_info['details']}

<b>⚠️ نکات مهم:</b>
• فقط مبلغ دقیق را پرداخت کنید
• شناسه تراکنش را در توضیحات ذکر کنید
• پس از پرداخت، رسید را ارسال کنید
• حداکثر 30 دقیقه برای پرداخت فرصت دارید

آیا پرداخت را انجام داده‌اید؟
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ پرداخت کردم", 
                                       callback_data=f"payment_done:{transaction.transaction_id}"),
                    InlineKeyboardButton("❌ لغو پرداخت", 
                                       callback_data=f"payment_cancel:{transaction.transaction_id}")
                ],
                [
                    InlineKeyboardButton("🔄 روش پرداخت دیگر", callback_data="show_payment_methods")
                ]
            ]
            
            await query.edit_message_text(
                details_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
            # ذخیره شناسه تراکنش
            context.user_data['current_transaction_id'] = transaction.transaction_id
            
        except Exception as e:
            logger.error(f"Error showing payment details: {e}")
    
    async def _get_payment_info(self, payment_method: str, transaction: TransactionModel) -> Dict[str, str]:
        """دریافت اطلاعات پرداخت بر اساس روش"""
        payment_configs = {
            'credit_card': {
                'details': """
💳 <b>پرداخت با کارت اعتباری:</b>
• از درگاه امن پرداخت استفاده می‌شود
• تمام کارت‌های ویزا و مسترکارت پذیرفته می‌شود
• پرداخت فوری تأیید می‌شود
"""
            },
            'bank_transfer': {
                'details': f"""
🏦 <b>انتقال بانکی:</b>
• شماره حساب: {Config.BANK_ACCOUNT_NUMBER}
• شماره کارت: {Config.BANK_CARD_NUMBER}
• نام صاحب حساب: {Config.BANK_ACCOUNT_HOLDER}
• شناسه تراکنش را حتماً در توضیحات بنویسید
"""
            },
            'bitcoin': {
                'details': f"""
₿ <b>پرداخت با بیت‌کوین:</b>
• آدرس ولت: <code>{Config.BITCOIN_WALLET_ADDRESS}</code>
• مبلغ: {transaction.final_amount / Config.BTC_USD_RATE:.8f} BTC
• شبکه: Bitcoin (BTC)
• تأیید معمولاً 10-60 دقیقه طول می‌کشد
"""
            },
            'tether': {
                'details': f"""
💰 <b>پرداخت با تتر (USDT):</b>
• آدرس ولت: <code>{Config.USDT_WALLET_ADDRESS}</code>
• مبلغ: {transaction.final_amount} USDT
• شبکه: TRC20 (Tron)
• تأیید معمولاً 1-5 دقیقه طول می‌کشد
"""
            },
            'ethereum': {
                'details': f"""
💎 <b>پرداخت با اتریوم:</b>
• آدرس ولت: <code>{Config.ETHEREUM_WALLET_ADDRESS}</code>
• مبلغ: {transaction.final_amount / Config.ETH_USD_RATE:.6f} ETH
• شبکه: Ethereum (ERC20)
• تأیید معمولاً 2-15 دقیقه طول می‌کشد
"""
            },
            'perfect_money': {
                'details': f"""
🔄 <b>پرداخت با Perfect Money:</b>
• حساب: {Config.PERFECT_MONEY_ACCOUNT}
• مبلغ: ${transaction.final_amount} USD
• از حساب USD خود پرداخت کنید
• تأیید فوری
"""
            }
        }
        
        return payment_configs.get(payment_method, {'details': 'اطلاعات پرداخت در دسترس نیست'})
    
    async def handle_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید پرداخت توسط کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            transaction_id = query.data.split(':')[1]
            
            # یافتن تراکنش
            transaction = await self.payment_manager.get_transaction(transaction_id)
            if not transaction:
                await query.edit_message_text("❌ تراکنش یافت نشد.")
                return
            
            # بررسی انقضا
            if transaction.is_expired:
                await query.edit_message_text(
                    "⏰ <b>تراکنش منقضی شده</b>\n\n"
                    "زمان پرداخت به پایان رسیده است.\n"
                    "لطفاً دوباره تلاش کنید.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # درخواست ارسال رسید
            await query.edit_message_text(
                f"""
📄 <b>ارسال رسید پرداخت</b>

🆔 <b>شناسه تراکنش:</b> <code>{transaction_id}</code>

لطفاً رسید پرداخت خود را ارسال کنید:
• عکس رسید یا اسکرین‌شات
• شماره پیگیری (در صورت وجود)
• توضیحات اضافی (اختیاری)

برای لغو: /cancel
""",
                parse_mode=ParseMode.HTML
            )
            
            # ذخیره در context برای ConversationHandler
            context.user_data['awaiting_proof_for'] = transaction_id
            
            return WAITING_PAYMENT_PROOF
            
        except Exception as e:
            logger.error(f"Error in payment confirmation: {e}")
            await query.edit_message_text("❌ خطا در تأیید پرداخت.")
    
    async def handle_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت رسید پرداخت"""
        try:
            user = update.effective_user
            transaction_id = context.user_data.get('awaiting_proof_for')
            
            if not transaction_id:
                await update.message.reply_text("❌ شناسه تراکنش یافت نشد.")
                return ConversationHandler.END
            
            # دریافت رسید
            proof_data = {
                'transaction_id': transaction_id,
                'user_id': user.id,
                'timestamp': datetime.now(),
                'message_text': update.message.text or update.message.caption or "",
            }
            
            # ذخیره فایل‌های ضمیمه
            if update.message.photo:
                proof_data['photo_file_id'] = update.message.photo[-1].file_id
            elif update.message.document:
                proof_data['document_file_id'] = update.message.document.file_id
            
            # ارسال به ادمین‌ها برای بررسی
            await self.payment_manager.submit_payment_proof(proof_data)
            
            # پیام تأیید به کاربر
            confirmation_message = f"""
✅ <b>رسید پرداخت دریافت شد</b>

🆔 <b>شناسه تراکنش:</b> <code>{transaction_id}</code>
📅 <b>زمان ارسال:</b> {DateTimeFormatter.format_datetime_persian(datetime.now())}

رسید شما به تیم مالی ارسال شد و در اولین فرصت بررسی خواهد شد.

⏱️ <b>زمان بررسی:</b> معمولاً کمتر از 24 ساعت
📱 پس از تأیید، پکیج شما فعال خواهد شد.

برای استعلام وضعیت: /status
"""
            
            keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
            
            await update.message.reply_text(
                confirmation_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
            # لاگ عملیات
            log_payment_action(
                user.id,
                "payment_proof_submitted",
                0,
                transaction_id,
                "Payment proof submitted for review"
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error handling payment proof: {e}")
            await update.message.reply_text("❌ خطا در دریافت رسید.")
            return ConversationHandler.END
    
    async def handle_payment_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو پرداخت"""
        try:
            query = update.callback_query
            await query.answer()
            
            transaction_id = query.data.split(':')[1]
            
            # لغو تراکنش
            await self.payment_manager.cancel_transaction(transaction_id, "Cancelled by user")
            
            await query.edit_message_text(
                "❌ <b>پرداخت لغو شد</b>\n\n"
                "تراکنش شما لغو شد.\n"
                "می‌توانید در هر زمان دوباره تلاش کنید.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error cancelling payment: {e}")
    
    async def handle_discount_code_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ورود کد تخفیف"""
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "🎁 <b>ورود کد تخفیف</b>\n\n"
                "کد تخفیف خود را وارد کنید:\n\n"
                "برای لغو: /cancel",
                parse_mode=ParseMode.HTML
            )
            
            return WAITING_DISCOUNT_CODE
            
        except Exception as e:
            logger.error(f"Error in discount code entry: {e}")
            return ConversationHandler.END
    
    async def handle_discount_code_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش کد تخفیف"""
        try:
            discount_code = update.message.text.strip().upper()
            
            # اعتبارسنجی کد
            validation_result = await self.payment_manager.validate_discount_code(discount_code)
            
            if validation_result['valid']:
                context.user_data['discount_code'] = discount_code
                
                success_message = f"""
✅ <b>کد تخفیف تأیید شد!</b>

🎟️ <b>کد:</b> {discount_code}
🎉 <b>تخفیف:</b> {validation_result['discount_percentage']}%
💰 <b>حداکثر تخفیف:</b> ${validation_result['max_discount']}

حالا می‌توانید پکیج خود را انتخاب کنید.
"""
                
                keyboard = [[InlineKeyboardButton("💎 انتخاب پکیج", callback_data="show_packages")]]
                
                await update.message.reply_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"❌ کد تخفیف نامعتبر است.\n\n"
                    f"دلیل: {validation_result['message']}"
                )
                return WAITING_DISCOUNT_CODE
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error processing discount code: {e}")
            await update.message.reply_text("❌ خطا در پردازش کد تخفیف.")
            return ConversationHandler.END
    
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n\n"
            "برای بازگشت به منوی اصلی: /start"
        )
        return ConversationHandler.END
    
    def get_handlers(self) -> List:
        """دریافت لیست هندلرها"""
        return [
            # ConversationHandler برای رسید پرداخت
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.handle_payment_confirmation, pattern=r"^payment_done:")],
                states={
                    WAITING_PAYMENT_PROOF: [MessageHandler(
                        filters.PHOTO | filters.DOCUMENT | filters.TEXT, 
                        self.handle_payment_proof
                    )],
                },
                fallbacks=[MessageHandler(filters.Regex("^/cancel$"), self.cancel_operation)],
            ),
            
            # ConversationHandler برای کد تخفیف
            ConversationHandler(
                entry_points=[CallbackQueryHandler(self.handle_discount_code_entry, pattern="^enter_discount_code$")],
                states={
                    WAITING_DISCOUNT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_discount_code_input)],
                },
                fallbacks=[MessageHandler(filters.Regex("^/cancel$"), self.cancel_operation)],
            ),
            
            # Callback handlers
            CallbackQueryHandler(self.handle_show_packages, pattern="^show_packages$"),
            CallbackQueryHandler(self.handle_package_selection, pattern=r"^select_package:"),
            CallbackQueryHandler(self.handle_package_purchase, pattern=r"^buy_package:"),
            CallbackQueryHandler(self.handle_payment_method_selection, pattern=r"^payment_method:"),
            CallbackQueryHandler(self.handle_payment_cancel, pattern=r"^payment_cancel:"),
        ]


# Export
__all__ = ['PaymentHandler']