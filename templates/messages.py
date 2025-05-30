"""
قالب‌های پیام برای MrTrader Bot
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.formatters import NumberFormatter, DateTimeFormatter


class WelcomeMessages:
    """پیام‌های خوش‌آمدگویی"""
    
    @staticmethod
    def new_user_welcome(first_name: str, referral_code: Optional[str] = None) -> str:
        """پیام خوش‌آمدگویی کاربر جدید"""
        referral_text = ""
        if referral_code:
            referral_text = f"\n\n🎉 شما با کد رفرال <code>{referral_code}</code> دعوت شده‌اید!"
            referral_text += "\n💰 پس از ثبت‌نام پاداش دریافت خواهید کرد."
        
        return f"""
🤖 <b>سلام {first_name}، به ربات MrTrader خوش آمدید!</b>

🚀 <b>امکانات ربات:</b>
📊 تحلیل تکنیکال ارزهای دیجیتال
📈 سیگنال‌های معاملاتی هوشمند
💰 مدیریت ریسک پیشرفته
📱 اعلان‌های قیمتی
📊 گزارش‌های تفصیلی عملکرد
🎯 استراتژی‌های متنوع تحلیل

💎 <b>ویژگی‌های ویژه:</b>
✅ تحلیل real-time بازار
✅ هوش مصنوعی پیشرفته
✅ پشتیبانی 24/7
✅ رابط کاربری ساده{referral_text}

برای شروع، روی دکمه ثبت‌نام کلیک کنید 👇
"""
    
    @staticmethod
    def registration_success(user_id: int, welcome_bonus: int, free_trial_days: int) -> str:
        """پیام موفقیت ثبت‌نام"""
        current_time = DateTimeFormatter.format_datetime_persian(datetime.now())
        
        return f"""
✅ <b>ثبت‌نام با موفقیت انجام شد!</b>

🎉 خوش آمدید به خانواده MrTrader
🆔 شناسه کاربری: <code>{user_id}</code>
📅 تاریخ ثبت‌نام: {current_time}

💰 <b>پاداش خوش‌آمدگویی:</b>
🎁 {NumberFormatter.format_number_persian(welcome_bonus)} امتیاز هدیه
📊 {free_trial_days} روز دسترسی رایگان

حالا می‌توانید از تمام امکانات ربات استفاده کنید!
"""
    
    @staticmethod
    def returning_user_welcome(first_name: str, package_type: str, points: int, last_login: datetime) -> str:
        """پیام خوش‌آمدگویی کاربر بازگشتی"""
        last_login_str = DateTimeFormatter.format_datetime_persian(last_login)
        
        return f"""
👋 سلام مجدد <b>{first_name}</b>!

📊 <b>وضعیت حساب شما:</b>
🎟️ پکیج فعال: {package_type}
⭐ امتیاز: {NumberFormatter.format_number_persian(points)} امتیاز

🕐 آخرین ورود: {last_login_str}

از منوی زیر گزینه مورد نظر را انتخاب کنید:
"""


class ErrorMessages:
    """پیام‌های خطا"""
    
    @staticmethod
    def generic_error() -> str:
        """خطای عمومی"""
        return "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید."
    
    @staticmethod
    def user_not_registered() -> str:
        """کاربر ثبت‌نام نکرده"""
        return "❌ ابتدا باید در ربات ثبت‌نام کنید.\nاز دستور /start استفاده کنید."
    
    @staticmethod
    def access_denied() -> str:
        """دسترسی مرفوض"""
        return "❌ شما مجوز دسترسی به این بخش را ندارید."
    
    @staticmethod
    def user_blocked() -> str:
        """کاربر مسدود"""
        return "🚫 حساب کاربری شما مسدود شده است.\nبرای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
    
    @staticmethod
    def package_expired() -> str:
        """پکیج منقضی"""
        return "⏰ پکیج شما منقضی شده است.\nبرای ادامه استفاده، پکیج خود را تمدید کنید."
    
    @staticmethod
    def daily_limit_reached() -> str:
        """محدودیت روزانه"""
        return "📊 شما به حد مجاز درخواست‌های روزانه رسیده‌اید.\nفردا دوباره تلاش کنید یا پکیج خود را ارتقاء دهید."
    
    @staticmethod
    def invalid_symbol(symbol: str) -> str:
        """نماد نامعتبر"""
        return f"❌ نماد {symbol} یافت نشد یا در دسترس نیست.\nلطفاً نماد صحیح وارد کنید."
    
    @staticmethod
    def network_error() -> str:
        """خطای شبکه"""
        return "🌐 مشکل در اتصال به شبکه.\nلطفاً چند لحظه صبر کنید و دوباره تلاش کنید."
    
    @staticmethod
    def timeout_error() -> str:
        """خطای timeout"""
        return "⏱️ درخواست شما زمان‌بر بود.\nلطفاً دوباره تلاش کنید."
    
    @staticmethod
    def maintenance_mode() -> str:
        """حالت تعمیرات"""
        return "🔧 ربات در حال تعمیرات است.\nلطفاً چند دقیقه دیگر مراجعه کنید."


class SuccessMessages:
    """پیام‌های موفقیت"""
    
    @staticmethod
    def operation_successful() -> str:
        """عملیات موفق"""
        return "✅ عملیات با موفقیت انجام شد."
    
    @staticmethod
    def settings_saved() -> str:
        """ذخیره تنظیمات"""
        return "✅ تنظیمات شما ذخیره شد."
    
    @staticmethod
    def alert_set(symbol: str, price: float) -> str:
        """تنظیم هشدار"""
        price_str = NumberFormatter.format_price(price)
        return f"🔔 هشدار برای {symbol} در قیمت {price_str} تنظیم شد."
    
    @staticmethod
    def payment_successful(package_name: str, duration: int) -> str:
        """پرداخت موفق"""
        return f"""
✅ <b>پرداخت با موفقیت انجام شد!</b>

📦 پکیج {package_name} برای {duration} ماه فعال شد.
🎉 از امکانات جدید لذت ببرید!
"""
    
    @staticmethod
    def referral_bonus_received(amount: float) -> str:
        """دریافت پاداش رفرال"""
        return f"🎁 پاداش رفرال {NumberFormatter.format_price(amount)} به حساب شما اضافه شد!"


class HelpMessages:
    """پیام‌های راهنما"""
    
    @staticmethod
    def main_help() -> str:
        """راهنمای اصلی"""
        return """
📚 <b>راهنمای کامل ربات MrTrader</b>

🔧 <b>دستورات اصلی:</b>
/start - شروع یا منوی اصلی
/help - نمایش این راهنما
/menu - منوی سریع
/analysis - تحلیل سریع
/signals - سیگنال‌های فعال
/portfolio - پورتفولیو شما
/settings - تنظیمات

📊 <b>نحوه استفاده:</b>
1️⃣ ابتدا ارز مورد نظر را انتخاب کنید
2️⃣ نوع تحلیل را مشخص کنید
3️⃣ تایم فریم دلخواه را انتخاب کنید
4️⃣ نتایج را دریافت و بررسی کنید

💡 <b>نکات مهم:</b>
• همیشه مدیریت ریسک را رعایت کنید
• از چند تحلیل برای تصمیم‌گیری استفاده کنید
• بازارهای مالی ریسک دارند

❓ برای کسب اطلاعات بیشتر از منوی زیر استفاده کنید.
"""
    
    @staticmethod
    def analysis_help() -> str:
        """راهنمای تحلیل"""
        return """
📊 <b>راهنمای تحلیل</b>

🎯 <b>انواع سیگنال:</b>
🟢 خرید قوی - سیگنال قوی برای خرید
🟢 خرید - سیگنال خرید
🟡 نگهداری - بدون عمل خاص
🔴 فروش - سیگنال فروش
🔴 فروش قوی - سیگنال قوی برای فروش

📈 <b>شاخص‌های تکنیکال:</b>
• RSI - شاخص قدرت نسبی
• MACD - تشخیص تغییر ترند
• Bollinger Bands - نوسانات قیمت
• Moving Average - میانگین متحرک

⚠️ <b>سطوح ریسک:</b>
🟢 خیلی کم - ریسک بسیار پایین
🟡 کم - ریسک پایین
🟠 متوسط - ریسک متوسط
🔴 زیاد - ریسک بالا
⚫ خیلی زیاد - ریسک بسیار بالا

💡 <b>توصیه:</b> همیشه چند شاخص را بررسی کنید.
"""
    
    @staticmethod
    def packages_help() -> str:
        """راهنمای پکیج‌ها"""
        return """
💎 <b>راهنمای پکیج‌ها</b>

🆓 <b>رایگان:</b>
• 5 سیگنال در روز
• تحلیل ساده
• پشتیبانی عمومی

💰 <b>ابتدایی ($19.99/ماه):</b>
• 15 سیگنال در روز
• تحلیل تکنیکال
• پشتیبانی اولویت‌دار

⭐ <b>پریمیوم ($49.99/ماه):</b>
• 30 سیگنال در روز
• تحلیل پیشرفته
• مدیریت ریسک
• پشتیبانی سریع

👑 <b>VIP ($99.99/ماه):</b>
• 100 سیگنال در روز
• تحلیل هوش مصنوعی
• پورتفولیو شخصی
• پشتیبانی اختصاصی

💡 <b>نکته:</b> خرید سالانه تا 25% تخفیف دارد!
"""


class AnalysisMessages:
    """پیام‌های تحلیل"""
    
    @staticmethod
    def analysis_in_progress(symbol: str) -> str:
        """تحلیل در حال انجام"""
        return f"🔄 در حال تحلیل {symbol}... لطفاً صبر کنید."
    
    @staticmethod
    def no_analysis_available(symbol: str) -> str:
        """عدم وجود تحلیل"""
        return f"❌ تحلیلی برای {symbol} در دسترس نیست."
    
    @staticmethod
    def analysis_completed(symbol: str, signal_type: str, confidence: float) -> str:
        """تکمیل تحلیل"""
        confidence_percent = confidence * 100
        return f"""
📊 <b>تحلیل {symbol} تکمیل شد</b>

🎯 سیگنال: {signal_type}
💪 اطمینان: {confidence_percent:.1f}%

جزئیات کامل در زیر 👇
"""
    
    @staticmethod
    def market_overview_header() -> str:
        """هدر نمای کلی بازار"""
        current_time = DateTimeFormatter.format_datetime_persian(datetime.now())
        return f"""
📊 <b>نمای کلی بازار</b>

🕐 آخرین بروزرسانی: {current_time}

💹 <b>وضعیت بازار:</b>
"""


class PackageMessages:
    """پیام‌های پکیج"""
    
    @staticmethod
    def package_details(package_data: Dict[str, Any]) -> str:
        """جزئیات پکیج"""
        name = package_data.get('name_persian', '')
        description = package_data.get('description_persian', '')
        price_monthly = package_data.get('price_monthly', 0)
        daily_limit = package_data.get('daily_signals_limit', 0)
        features = package_data.get('features', [])
        
        features_text = ""
        for feature in features:
            if feature.get('included', False):
                limit_text = f" (حداکثر {feature['limit']})" if feature.get('limit') else ""
                features_text += f"✅ {feature['description']}{limit_text}\n"
        
        price_text = f"${price_monthly}" if price_monthly > 0 else "رایگان"
        
        return f"""
💎 <b>{name}</b>

📝 <b>توضیحات:</b>
{description}

💰 <b>قیمت ماهانه:</b> {price_text}
📊 <b>سیگنال روزانه:</b> {daily_limit}

✨ <b>ویژگی‌ها:</b>
{features_text}
انتخاب مدت اشتراک:
"""
    
    @staticmethod
    def payment_instructions(payment_method: str, amount: float, transaction_id: str) -> str:
        """دستورالعمل پرداخت"""
        payment_info = {
            'credit_card': "💳 از درگاه امن پرداخت استفاده کنید",
            'bank_transfer': "🏦 به شماره حساب مشخص شده واریز کنید",
            'bitcoin': "₿ به آدرس بیت‌کوین مشخص شده ارسال کنید",
            'tether': "💰 به آدرس USDT مشخص شده ارسال کنید"
        }
        
        instruction = payment_info.get(payment_method, "پرداخت طبق دستورالعمل")
        
        return f"""
💳 <b>جزئیات پرداخت</b>

🆔 شناسه تراکنش: <code>{transaction_id}</code>
💰 مبلغ: ${amount}

📋 <b>دستورالعمل:</b>
{instruction}

⚠️ نکات مهم:
• فقط مبلغ دقیق را پرداخت کنید
• شناسه تراکنش را در توضیحات ذکر کنید
• پس از پرداخت، رسید را ارسال کنید
"""
    
    @staticmethod
    def payment_proof_received(transaction_id: str) -> str:
        """تأیید دریافت رسید"""
        current_time = DateTimeFormatter.format_datetime_persian(datetime.now())
        
        return f"""
✅ <b>رسید پرداخت دریافت شد</b>

🆔 شناسه تراکنش: <code>{transaction_id}</code>
📅 زمان ارسال: {current_time}

رسید شما به تیم مالی ارسال شد و در اولین فرصت بررسی خواهد شد.

⏱️ زمان بررسی: معمولاً کمتر از 24 ساعت
📱 پس از تأیید، پکیج شما فعال خواهد شد.
"""


class NotificationMessages:
    """پیام‌های اعلان"""
    
    @staticmethod
    def price_alert(symbol: str, current_price: float, target_price: float, direction: str) -> str:
        """هشدار قیمت"""
        current_price_str = NumberFormatter.format_price(current_price)
        target_price_str = NumberFormatter.format_price(target_price)
        direction_emoji = "🔺" if direction == "above" else "🔻"
        direction_text = "بالای" if direction == "above" else "زیر"
        
        return f"""
🔔 <b>هشدار قیمت</b>

{direction_emoji} قیمت {symbol} به {direction_text} {target_price_str} رسید!

💰 قیمت فعلی: {current_price_str}
🎯 قیمت هدف: {target_price_str}

📊 برای تحلیل دقیق‌تر کلیک کنید.
"""
    
    @staticmethod
    def new_signal_alert(symbol: str, signal_type: str, confidence: float) -> str:
        """اعلان سیگنال جدید"""
        confidence_percent = confidence * 100
        
        signal_emojis = {
            'STRONG_BUY': '🟢🚀',
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴',
            'STRONG_SELL': '🔴💥'
        }
        
        emoji = signal_emojis.get(signal_type, '⚪')
        
        return f"""
📈 <b>سیگنال جدید</b>

{emoji} {symbol}: {signal_type}
💪 اطمینان: {confidence_percent:.1f}%

⏰ همین الان تولید شد!
"""
    
    @staticmethod
    def package_expiry_warning(days_left: int) -> str:
        """هشدار انقضای پکیج"""
        if days_left == 0:
            return """
⏰ <b>پکیج شما امروز منقضی می‌شود!</b>

برای ادامه استفاده از امکانات، پکیج خود را تمدید کنید.
"""
        else:
            return f"""
⚠️ <b>پکیج شما {days_left} روز دیگر منقضی می‌شود</b>

برای جلوگیری از قطع سرویس، هر چه زودتر تمدید کنید.
"""


class SystemMessages:
    """پیام‌های سیستم"""
    
    @staticmethod
    def bot_updated(version: str) -> str:
        """بروزرسانی ربات"""
        return f"""
🔄 <b>ربات بروزرسانی شد!</b>

📋 نسخه جدید: {version}

🆕 ویژگی‌های جدید و بهبودهای عملکرد اضافه شده است.
"""
    
    @staticmethod
    def maintenance_notice() -> str:
        """اطلاعیه تعمیرات"""
        return """
🔧 <b>اطلاعیه تعمیرات</b>

ربات برای بهبود عملکرد در حال تعمیرات است.
مدت زمان تقریبی: 30 دقیقه

متشکریم از صبر شما.
"""
    
    @staticmethod
    def server_status(status: str, uptime: str) -> str:
        """وضعیت سرور"""
        status_emoji = "🟢" if status == "online" else "🔴"
        
        return f"""
🖥️ <b>وضعیت سرور</b>

{status_emoji} وضعیت: {status}
⏱️ مدت کارکرد: {uptime}

همه سرویس‌ها عادی کار می‌کنند.
"""


# Export
__all__ = [
    'WelcomeMessages',
    'ErrorMessages', 
    'SuccessMessages',
    'HelpMessages',
    'AnalysisMessages',
    'PackageMessages',
    'NotificationMessages',
    'SystemMessages'
]