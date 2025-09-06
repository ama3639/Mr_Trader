"""
هندلرهای پرداخت - مدیریت خرید پکیج‌ها و پرداخت‌ها
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

from core.config import Config
from managers.payment_manager import PaymentManager
from managers.user_manager import UserManager
from managers.admin_manager import AdminManager
from models.package import PackageManager, PackageType, SubscriptionType
from models.transaction import TransactionManager, TransactionType, PaymentMethod
from utils.logger import UserLogger, PaymentLogger
from utils.time_manager import TimeManager
from utils.validators import Validators, ValidationError
from datetime import datetime, timedelta
from managers.user_manager import UserManager

# States for conversation handlers
PAYMENT_WAITING_PACKAGE = 1
PAYMENT_WAITING_DURATION = 2
PAYMENT_WAITING_METHOD = 3
PAYMENT_WAITING_CONFIRMATION = 4

class PaymentHandlers:
    """کلاس هندلرهای پرداخت"""
    
    @staticmethod
    async def show_packages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی پکیج‌ها"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # دریافت اطلاعات کاربر
            user_info = UserManager.get_user(user_id)
            current_package = user_info.get('current_package', {})
            current_package_type = current_package.get('package_type', 'free')
            
            # دریافت پکیج‌های موجود
            packages = PackageManager.get_available_packages()
            
            packages_text = (
                f"💎 **پکیج‌های MrTrader Bot**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 **پکیج فعلی:** `{current_package_type.upper()}`\n"
                f"⏰ **انقضا:** `{current_package.get('expiry_date', 'نامشخص')}`\n\n"
                f"🛒 **پکیج‌های قابل خرید:**"
            )
            
            keyboard = []
            
            for package in packages:
                if package.package_type == PackageType.FREE:
                    continue  # رد کردن پکیج رایگان
                
                # نمایش قیمت ماهانه
                monthly_price = package.pricing.get_effective_price(SubscriptionType.MONTHLY)
                
                # ایموجی بر اساس نوع پکیج
                emoji_map = {
                    PackageType.BASIC: "🥉",
                    PackageType.PREMIUM: "🥈", 
                    PackageType.VIP: "🥇",
                    PackageType.GHOST: "👻"
                }
                
                emoji = emoji_map.get(package.package_type, "📦")
                
                # نشان‌گذاری پکیج ویژه
                featured_mark = " ⭐" if package.is_featured else ""
                
                button_text = f"{emoji} {package.title} - ${monthly_price}/ماه{featured_mark}"
                callback_data = f"pkg_select_{package.package_id}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # دکمه‌های اضافی
            keyboard.extend([
                [InlineKeyboardButton("📊 مقایسه پکیج‌ها", callback_data="packages_compare")],
                [InlineKeyboardButton("💰 تاریخچه خریدها", callback_data="payment_history")],
                [InlineKeyboardButton("🎁 کد تخفیف", callback_data="discount_code")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                packages_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # ثبت لاگ بازدید از پکیج‌ها
            UserLogger.log_user_action(user_id, "packages_view", "مشاهده پکیج‌ها")
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in show_packages_menu: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش پکیج‌ها. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ])
            )
    
    @staticmethod
    async def handle_package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب پکیج"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # استخراج شناسه پکیج
            package_id = query.data.replace("pkg_select_", "")
            
            # دریافت اطلاعات پکیج
            packages = PackageManager.get_available_packages()
            selected_package = None
            
            for package in packages:
                if package.package_id == package_id:
                    selected_package = package
                    break
            
            if not selected_package:
                await query.answer("❌ پکیج یافت نشد!", show_alert=True)
                return
            
            # ذخیره پکیج انتخابی
            context.user_data['selected_package'] = package_id
            
            # نمایش جزئیات پکیج
            package_details = (
                f"📦 **جزئیات پکیج {selected_package.title}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 **توضیحات:**\n{selected_package.description}\n\n"
                f"✨ **ویژگی‌ها:**\n"
            )
            
            # اضافه کردن ویژگی‌ها
            features = selected_package.features
            if features.strategies:
                package_details += f"📊 استراتژی‌ها: `{len(features.strategies)} مورد`\n"
            if features.max_daily_requests:
                package_details += f"📈 درخواست روزانه: `{features.max_daily_requests:,}`\n"
            if features.has_live_support:
                package_details += f"🎧 پشتیبانی زنده: `✅`\n"
            if features.has_priority_support:
                package_details += f"⚡ پشتیبانی اولویت‌دار: `✅`\n"
            if features.has_advanced_analytics:
                package_details += f"📊 تحلیل پیشرفته: `✅`\n"
            
            package_details += f"\n💰 **قیمت‌گذاری:**"
            
            # نمایش انتخاب مدت زمان
            pricing = selected_package.pricing
            keyboard = []
            
            if pricing.monthly_price > 0:
                monthly_price = pricing.get_effective_price(SubscriptionType.MONTHLY)
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 ماهانه - ${monthly_price:.2f}",
                        callback_data=f"pkg_dur_{package_id}_monthly"
                    )
                ])
            
            if pricing.quarterly_price > 0:
                quarterly_price = pricing.get_effective_price(SubscriptionType.QUARTERLY)
                monthly_equiv = quarterly_price / 3
                saving = pricing.monthly_price - monthly_equiv
                save_text = f" (صرفه‌جویی ${saving:.2f}/ماه)" if saving > 0 else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 فصلی - ${quarterly_price:.2f}{save_text}",
                        callback_data=f"pkg_dur_{package_id}_quarterly"
                    )
                ])
            
            if pricing.yearly_price > 0:
                yearly_price = pricing.get_effective_price(SubscriptionType.YEARLY)
                monthly_equiv = yearly_price / 12
                saving = pricing.monthly_price - monthly_equiv
                save_text = f" (صرفه‌جویی ${saving:.2f}/ماه)" if saving > 0 else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 سالانه - ${yearly_price:.2f}{save_text}",
                        callback_data=f"pkg_dur_{package_id}_yearly"
                    )
                ])
            
            if pricing.lifetime_price > 0:
                lifetime_price = pricing.get_effective_price(SubscriptionType.LIFETIME)
                keyboard.append([
                    InlineKeyboardButton(
                        f"♾ مادام‌العمر - ${lifetime_price:.2f}",
                        callback_data=f"pkg_dur_{package_id}_lifetime"
                    )
                ])
            
            # دکمه‌های بازگشت
            keyboard.extend([
                [InlineKeyboardButton("⬅️ بازگشت به پکیج‌ها", callback_data="menu_packages")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                package_details,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return PAYMENT_WAITING_DURATION
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in handle_package_selection: {e}")
            await query.edit_message_text("❌ خطا در انتخاب پکیج")
    
    @staticmethod
    async def handle_duration_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب مدت زمان"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # استخراج اطلاعات
            data_parts = query.data.replace("pkg_dur_", "").split("_")
            package_id = data_parts[0]
            duration = data_parts[1]
            
            # ذخیره مدت زمان
            context.user_data['selected_duration'] = duration
            
            # دریافت اطلاعات پکیج
            packages = PackageManager.get_available_packages()
            selected_package = None
            
            for package in packages:
                if package.package_id == package_id:
                    selected_package = package
                    break
            
            if not selected_package:
                await query.answer("❌ پکیج یافت نشد!", show_alert=True)
                return
            
            # محاسبه قیمت
            subscription_type = SubscriptionType(duration)
            final_price = selected_package.pricing.get_effective_price(subscription_type)
            
            # نمایش روش‌های پرداخت
            payment_text = (
                f"💳 **انتخاب روش پرداخت**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 **پکیج:** {selected_package.title}\n"
                f"⏰ **مدت:** {duration}\n"
                f"💰 **مبلغ:** ${final_price:.2f}\n\n"
                f"💳 **روش‌های پرداخت موجود:**"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("💳 کارت بانکی", callback_data=f"pay_method_bank_{package_id}_{duration}"),
                    InlineKeyboardButton("🔗 زرین‌پال", callback_data=f"pay_method_zarinpal_{package_id}_{duration}")
                ],
                [
                    InlineKeyboardButton("₿ ارز دیجیتال", callback_data=f"pay_method_crypto_{package_id}_{duration}"),
                    InlineKeyboardButton("💰 اعتبار حساب", callback_data=f"pay_method_credit_{package_id}_{duration}")
                ],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data=f"pkg_select_{package_id}")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                payment_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return PAYMENT_WAITING_METHOD
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in handle_duration_selection: {e}")
            await query.edit_message_text("❌ خطا در انتخاب مدت زمان")
    
    @staticmethod
    async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب روش پرداخت"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # استخراج اطلاعات
            data_parts = query.data.replace("pay_method_", "").split("_")
            payment_method = data_parts[0]
            package_id = data_parts[1]
            duration = data_parts[2]
            
            # دریافت اطلاعات پکیج
            packages = PackageManager.get_available_packages()
            selected_package = None
            
            for package in packages:
                if package.package_id == package_id:
                    selected_package = package
                    break
            
            if not selected_package:
                await query.answer("❌ پکیج یافت نشد!", show_alert=True)
                return
            
            # محاسبه قیمت نهایی
            subscription_type = SubscriptionType(duration)
            final_price = selected_package.pricing.get_effective_price(subscription_type)
            
            # ایجاد تراکنش
            payment_method_enum = {
                'bank': PaymentMethod.BANK_TRANSFER,
                'zarinpal': PaymentMethod.ZARINPAL,
                'crypto': PaymentMethod.CRYPTO,
                'credit': PaymentMethod.ADMIN_CREDIT
            }.get(payment_method, PaymentMethod.BANK_TRANSFER)
            
            transaction = TransactionManager.create_purchase_transaction(
                user_id=user_id,
                package_id=package_id,
                package_name=selected_package.title,
                amount=final_price,
                subscription_duration=duration,
                payment_method=payment_method_enum
            )
            
            # ذخیره تراکنش
            PaymentManager.save_transaction(transaction)
            
            # نمایش تأیید نهایی
            confirmation_text = (
                f"✅ **تأیید نهایی خرید**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 **پکیج:** {selected_package.title}\n"
                f"⏰ **مدت:** {duration}\n"
                f"💰 **مبلغ:** ${final_price:.2f}\n"
                f"💳 **روش پرداخت:** {payment_method}\n"
                f"🆔 **شماره تراکنش:** `{transaction.transaction_id}`\n\n"
                f"❓ **آیا از خرید خود اطمینان دارید؟**"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ تأیید و پرداخت", callback_data=f"pay_confirm_{transaction.transaction_id}"),
                    InlineKeyboardButton("❌ لغو", callback_data=f"pay_cancel_{transaction.transaction_id}")
                ],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                confirmation_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # ذخیره شناسه تراکنش
            context.user_data['transaction_id'] = transaction.transaction_id
            
            return PAYMENT_WAITING_CONFIRMATION
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in handle_payment_method: {e}")
            await query.edit_message_text("❌ خطا در انتخاب روش پرداخت")
    
    @staticmethod
    async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش تأیید پرداخت"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # استخراج شناسه تراکنش
            transaction_id = query.data.split("_")[-1]
            
            if query.data.startswith("pay_confirm_"):
                # تأیید پرداخت
                success, result = PaymentManager.process_payment(transaction_id)
                
                if success:
                    # پرداخت موفق
                    transaction = result
                    
                    success_text = (
                        f"🎉 **پرداخت موفقیت‌آمیز!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"✅ پکیج شما با موفقیت فعال شد\n"
                        f"📦 **پکیج:** {transaction.package_name}\n"
                        f"🆔 **شماره تراکنش:** `{transaction.transaction_id}`\n"
                        f"🕒 **زمان فعال‌سازی:** `{TimeManager.to_shamsi(datetime.now())}`\n\n"
                        f"🚀 **اکنون می‌توانید از امکانات جدید استفاده کنید!**"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 شروع استفاده", callback_data="menu_strategy")],
                        [InlineKeyboardButton("📋 جزئیات پکیج", callback_data="user_profile")],
                        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                    ]
                    
                    # ثبت لاگ پرداخت موفق
                    PaymentLogger.log_successful_payment(user_id, transaction.transaction_id, transaction.amount)
                    
                else:
                    # پرداخت ناموفق
                    error_message = result
                    
                    success_text = (
                        f"❌ **خطا در پرداخت**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"متأسفانه پرداخت شما با مشکل مواجه شد:\n"
                        f"`{error_message}`\n\n"
                        f"💡 **راه‌حل‌های پیشنهادی:**\n"
                        f"• دوباره تلاش کنید\n"
                        f"• از روش پرداخت دیگری استفاده کنید\n"
                        f"• با پشتیبانی تماس بگیرید\n"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="menu_packages")],
                        [InlineKeyboardButton("🎧 پشتیبانی", callback_data="support_contact")],
                        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                    ]
                    
                    # ثبت لاگ پرداخت ناموفق
                    PaymentLogger.log_failed_payment(user_id, transaction_id, error_message)
                
            else:
                # لغو پرداخت
                PaymentManager.cancel_transaction(transaction_id)
                
                success_text = (
                    f"❌ **پرداخت لغو شد**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"تراکنش شما لغو شد.\n"
                    f"در صورت تمایل می‌توانید دوباره تلاش کنید."
                )
                
                keyboard = [
                    [InlineKeyboardButton("🛒 خرید مجدد", callback_data="menu_packages")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ]
            
            await query.edit_message_text(
                success_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # پاک کردن داده‌های موقت
            context.user_data.clear()
            
            return ConversationHandler.END
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in handle_payment_confirmation: {e}")
            await query.edit_message_text(
                "❌ خطا در پردازش پرداخت. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
                ])
            )
            return ConversationHandler.END
    
    @staticmethod
    async def show_payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تاریخچه پرداخت‌ها"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # دریافت تاریخچه پرداخت‌ها
            transactions = PaymentManager.get_user_transactions(user_id)
            
            if not transactions:
                history_text = (
                    f"📋 **تاریخچه پرداخت‌ها**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"هنوز هیچ پرداختی ثبت نشده است.\n"
                    f"برای شروع، یکی از پکیج‌ها را خریداری کنید."
                )
            else:
                history_text = (
                    f"📋 **تاریخچه پرداخت‌ها**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                
                for i, transaction in enumerate(transactions[:5]):  # نمایش 5 تراکنش اخیر
                    status_emoji = {
                        'completed': '✅',
                        'pending': '⏳',
                        'failed': '❌',
                        'cancelled': '🚫'
                    }.get(transaction.status.value, '❓')
                    
                    history_text += (
                        f"{status_emoji} **{transaction.package_name}**\n"
                        f"💰 مبلغ: `${transaction.amount:.2f}`\n"
                        f"📅 تاریخ: `{TimeManager.to_shamsi(transaction.created_date)}`\n"
                        f"🆔 شناسه: `{transaction.transaction_id[:8]}...`\n\n"
                    )
                
                if len(transactions) > 5:
                    history_text += f"... و {len(transactions) - 5} تراکنش دیگر"
            
            keyboard = [
                [InlineKeyboardButton("🛒 خرید جدید", callback_data="menu_packages")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                history_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            UserLogger.log_error(user_id, f"Error in show_payment_history: {e}")
    
    @staticmethod
    async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو فرآیند پرداخت"""
        query = update.callback_query
        
        # پاک کردن داده‌های موقت
        context.user_data.clear()
        
        await query.answer("فرآیند پرداخت لغو شد")
        return ConversationHandler.END

# ایجاد conversation handler برای پرداخت
def build_payment_conversation_handler():
    """ایجاد conversation handler برای فرآیند پرداخت"""
    from telegram.ext import ConversationHandler, CallbackQueryHandler
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(PaymentHandlers.handle_package_selection, pattern="^pkg_select_"),
        ],
        states={
            PAYMENT_WAITING_DURATION: [
                CallbackQueryHandler(PaymentHandlers.handle_duration_selection, pattern="^pkg_dur_")
            ],
            PAYMENT_WAITING_METHOD: [
                CallbackQueryHandler(PaymentHandlers.handle_payment_method, pattern="^pay_method_")
            ],
            PAYMENT_WAITING_CONFIRMATION: [
                CallbackQueryHandler(PaymentHandlers.handle_payment_confirmation, pattern="^pay_(confirm|cancel)_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(PaymentHandlers.cancel_payment, pattern="^(menu_packages|main_menu)$"),
        ],
        name="payment_process",
        persistent=True
    )
