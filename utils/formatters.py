"""
ابزارهای فرمت‌بندی خروجی‌ها برای MrTrader Bot
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal
import jdatetime
from models.signal import Signal, SignalType, RiskLevel, TrendDirection


class NumberFormatter:
    """فرمت‌بندی اعداد"""
    
    @staticmethod
    def format_price(price: Union[float, Decimal], precision: int = 4) -> str:
        """فرمت‌بندی قیمت"""
        if price == 0:
            return "0"
        
        try:
            price = float(price)
            if price >= 1:
                # برای قیمت‌های بالای 1 دلار
                if price >= 1000:
                    return f"${price:,.2f}"
                else:
                    return f"${price:.4f}"
            else:
                # برای قیمت‌های زیر 1 دلار
                return f"${price:.{precision}f}"
        except (ValueError, TypeError):
            return "نامعتبر"
    
    @staticmethod
    def format_percentage(percentage: Union[float, Decimal], precision: int = 2) -> str:
        """فرمت‌بندی درصد"""
        try:
            percentage = float(percentage)
            sign = "+" if percentage > 0 else ""
            return f"{sign}{percentage:.{precision}f}%"
        except (ValueError, TypeError):
            return "0%"
    
    @staticmethod
    def format_volume(volume: Union[float, Decimal]) -> str:
        """فرمت‌بندی حجم معاملات"""
        try:
            volume = float(volume)
            if volume >= 1_000_000_000:
                return f"{volume/1_000_000_000:.2f}B"
            elif volume >= 1_000_000:
                return f"{volume/1_000_000:.2f}M"
            elif volume >= 1_000:
                return f"{volume/1_000:.2f}K"
            else:
                return f"{volume:.2f}"
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def format_number_persian(number: Union[int, float]) -> str:
        """فرمت‌بندی عدد با اعداد فارسی"""
        try:
            # نقشه تبدیل اعداد انگلیسی به فارسی
            persian_digits = {
                '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
            }
            
            # فرمت کردن عدد با کاما
            formatted = f"{number:,}"
            
            # تبدیل به فارسی
            for eng, per in persian_digits.items():
                formatted = formatted.replace(eng, per)
            
            return formatted
        except (ValueError, TypeError):
            return "نامعتبر"
    
    @staticmethod
    def format_large_number(number: Union[int, float], use_persian: bool = True) -> str:
        """فرمت‌بندی اعداد بزرگ"""
        try:
            number = float(number)
            if number >= 1_000_000_000:
                result = f"{number/1_000_000_000:.1f} میلیارد"
            elif number >= 1_000_000:
                result = f"{number/1_000_000:.1f} میلیون"
            elif number >= 1_000:
                result = f"{number/1_000:.1f} هزار"
            else:
                result = str(int(number))
            
            if use_persian:
                return NumberFormatter.format_number_persian(result)
            return result
        except (ValueError, TypeError):
            return "نامعتبر"


class DateTimeFormatter:
    """فرمت‌بندی تاریخ و زمان"""
    
    @staticmethod
    def format_datetime_persian(dt: datetime, include_time: bool = True) -> str:
        """فرمت‌بندی تاریخ و زمان به شمسی"""
        if not dt:
            return "نامشخص"
        
        try:
            jdt = jdatetime.datetime.fromgregorian(datetime=dt)
            if include_time:
                return jdt.strftime("%Y/%m/%d - %H:%M")
            else:
                return jdt.strftime("%Y/%m/%d")
        except:
            if include_time:
                return dt.strftime("%Y/%m/%d - %H:%M")
            else:
                return dt.strftime("%Y/%m/%d")
    
    @staticmethod
    def format_date_persian(dt: datetime) -> str:
        """فرمت‌بندی تاریخ شمسی"""
        return DateTimeFormatter.format_datetime_persian(dt, include_time=False)
    
    @staticmethod
    def format_time_ago(dt: datetime) -> str:
        """فرمت‌بندی زمان گذشته"""
        if not dt:
            return "نامشخص"
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} روز پیش"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ساعت پیش"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} دقیقه پیش"
        else:
            return "همین الان"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """فرمت‌بندی مدت زمان"""
        if seconds < 60:
            return f"{seconds} ثانیه"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} دقیقه"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ساعت و {minutes} دقیقه"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} روز و {hours} ساعت"
    
    @staticmethod
    def format_expiry_countdown(expiry_date: datetime) -> str:
        """فرمت‌بندی شمارش معکوس انقضا"""
        if not expiry_date:
            return "نامحدود"
        
        now = datetime.now()
        if expiry_date <= now:
            return "منقضی شده"
        
        diff = expiry_date - now
        
        if diff.days > 0:
            return f"{diff.days} روز باقی‌مانده"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ساعت باقی‌مانده"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} دقیقه باقی‌مانده"


class SignalFormatter:
    """فرمت‌بندی سیگنال‌ها"""
    
    @staticmethod
    def format_signal_emoji(signal_type: SignalType) -> str:
        """ایموجی سیگنال"""
        emoji_map = {
            SignalType.STRONG_BUY: "🟢🚀",
            SignalType.BUY: "🟢",
            SignalType.HOLD: "🟡",
            SignalType.SELL: "🔴",
            SignalType.STRONG_SELL: "🔴💥"
        }
        return emoji_map.get(signal_type, "⚪")
    
    @staticmethod
    def format_risk_emoji(risk_level: RiskLevel) -> str:
        """ایموجی ریسک"""
        emoji_map = {
            RiskLevel.VERY_LOW: "🟢",
            RiskLevel.LOW: "🟡",
            RiskLevel.MEDIUM: "🟠",
            RiskLevel.HIGH: "🔴",
            RiskLevel.VERY_HIGH: "⚫"
        }
        return emoji_map.get(risk_level, "⚪")
    
    @staticmethod
    def format_trend_emoji(trend: TrendDirection) -> str:
        """ایموجی ترند"""
        emoji_map = {
            TrendDirection.BULLISH: "📈",
            TrendDirection.BEARISH: "📉",
            TrendDirection.SIDEWAYS: "➡️"
        }
        return emoji_map.get(trend, "➡️")
    
    @staticmethod
    def format_signal_summary(signal: Signal) -> str:
        """خلاصه سیگنال"""
        signal_emoji = SignalFormatter.format_signal_emoji(signal.signal_type)
        risk_emoji = SignalFormatter.format_risk_emoji(signal.risk_level)
        trend_emoji = SignalFormatter.format_trend_emoji(signal.trend_direction)
        
        return f"""
{signal_emoji} <b>{signal.signal_type.value.upper()}</b>
💰 قیمت: {NumberFormatter.format_price(signal.current_price)}
💪 قدرت: {signal.strength.value}/5
🎯 اطمینان: {NumberFormatter.format_percentage(signal.confidence * 100)}
{trend_emoji} ترند: {signal.trend_direction.value}
{risk_emoji} ریسک: {signal.risk_level.value}
"""
    
    @staticmethod
    def format_signal_detailed(signal: Signal) -> str:
        """سیگنال تفصیلی"""
        basic_info = SignalFormatter.format_signal_summary(signal)
        
        indicators_text = ""
        if signal.indicators:
            indicators_text = "\n📊 <b>شاخص‌های تکنیکال:</b>\n"
            for indicator in signal.indicators[:5]:  # نمایش 5 شاخص اول
                indicators_text += f"• {indicator.name}: {indicator.signal.value} ({NumberFormatter.format_percentage(indicator.confidence * 100)})\n"
        
        targets_text = ""
        if signal.price_targets:
            targets_text = "\n🎯 <b>اهداف قیمتی:</b>\n"
            for i, target in enumerate(signal.price_targets[:3], 1):
                targets_text += f"• هدف {i}: {NumberFormatter.format_price(target)}\n"
        
        return basic_info + indicators_text + targets_text


class MessageFormatter:
    """فرمت‌بندی پیام‌ها"""
    
    @staticmethod
    def format_user_profile(user_data: Dict[str, Any]) -> str:
        """فرمت‌بندی پروفایل کاربر"""
        name = user_data.get('first_name', 'کاربر')
        package = user_data.get('package_type', 'رایگان')
        points = user_data.get('user_points', 0)
        registration_date = user_data.get('registration_date')
        
        reg_date_str = DateTimeFormatter.format_date_persian(registration_date) if registration_date else "نامشخص"
        
        return f"""
👤 <b>پروفایل کاربری</b>

🏷️ <b>نام:</b> {name}
🎟️ <b>پکیج:</b> {package}
⭐ <b>امتیاز:</b> {NumberFormatter.format_number_persian(points)}
📅 <b>تاریخ عضویت:</b> {reg_date_str}
🆔 <b>شناسه:</b> <code>{user_data.get('telegram_id', 'نامشخص')}</code>
"""
    
    @staticmethod
    def format_package_info(package_data: Dict[str, Any]) -> str:
        """فرمت‌بندی اطلاعات پکیج"""
        name = package_data.get('name_persian', package_data.get('name', ''))
        description = package_data.get('description_persian', '')
        price_monthly = package_data.get('price_monthly', 0)
        daily_limit = package_data.get('daily_signals_limit', 0)
        
        price_str = "رایگان" if price_monthly == 0 else f"${price_monthly}"
        
        return f"""
💎 <b>{name}</b>

📝 {description}
💰 قیمت ماهانه: {price_str}
📊 سیگنال روزانه: {daily_limit}
"""
    
    @staticmethod
    def format_transaction_summary(transaction_data: Dict[str, Any]) -> str:
        """فرمت‌بندی خلاصه تراکنش"""
        transaction_id = transaction_data.get('transaction_id', '')
        amount = transaction_data.get('amount', 0)
        currency = transaction_data.get('currency', 'USD')
        status = transaction_data.get('status', 'نامشخص')
        created_at = transaction_data.get('created_at')
        
        date_str = DateTimeFormatter.format_datetime_persian(created_at) if created_at else "نامشخص"
        
        status_emoji = {
            'completed': '✅',
            'pending': '⏳',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(status.lower(), '❓')
        
        return f"""
🧾 <b>تراکنش {transaction_id[:8]}...</b>

💰 مبلغ: {amount} {currency}
{status_emoji} وضعیت: {status}
📅 تاریخ: {date_str}
"""
    
    @staticmethod
    def format_market_overview(market_data: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی نمای کلی بازار"""
        if not market_data:
            return "❌ اطلاعات بازار در دسترس نیست"
        
        result = "📊 <b>نمای کلی بازار</b>\n\n"
        
        for item in market_data[:10]:  # نمایش 10 ارز اول
            symbol = item.get('symbol', 'نامشخص')
            price = item.get('price', 0)
            change_24h = item.get('change_24h', 0)
            
            change_emoji = "📈" if change_24h >= 0 else "📉"
            
            result += f"{symbol}: {NumberFormatter.format_price(price)} {change_emoji} {NumberFormatter.format_percentage(change_24h)}\n"
        
        return result
    
    @staticmethod
    def clean_html_tags(text: str) -> str:
        """حذف تگ‌های HTML"""
        if not text:
            return ""
        
        # حذف تگ‌های HTML
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape کردن کاراکترهای MarkdownV2"""
        if not text:
            return ""
        
        # کاراکترهای خاص MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text


class TableFormatter:
    """فرمت‌بندی جدول‌ها"""
    
    @staticmethod
    def format_simple_table(headers: List[str], rows: List[List[str]], max_width: int = 30) -> str:
        """فرمت‌بندی جدول ساده"""
        if not headers or not rows:
            return "❌ داده‌ای برای نمایش وجود ندارد"
        
        # محدود کردن طول ستون‌ها
        def truncate(text: str, width: int) -> str:
            return text[:width-3] + "..." if len(text) > width else text
        
        result = ""
        col_width = max_width // len(headers)
        
        # هدر جدول
        header_row = " | ".join(truncate(h, col_width) for h in headers)
        result += f"<code>{header_row}</code>\n"
        result += f"<code>{'-' * len(header_row)}</code>\n"
        
        # ردیف‌های داده
        for row in rows[:20]:  # نمایش حداکثر 20 ردیف
            if len(row) >= len(headers):
                data_row = " | ".join(truncate(str(cell), col_width) for cell in row[:len(headers)])
                result += f"<code>{data_row}</code>\n"
        
        return result
    
    @staticmethod
    def format_portfolio_table(portfolio_data: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی جدول پورتفولیو"""
        if not portfolio_data:
            return "📝 پورتفولیو شما خالی است"
        
        result = "💼 <b>پورتفولیو شما</b>\n\n"
        
        for item in portfolio_data:
            symbol = item.get('symbol', 'نامشخص')
            amount = item.get('amount', 0)
            current_price = item.get('current_price', 0)
            profit_loss = item.get('profit_loss', 0)
            
            profit_emoji = "📈" if profit_loss >= 0 else "📉"
            
            result += f"• <b>{symbol}</b>\n"
            result += f"  مقدار: {NumberFormatter.format_volume(amount)}\n"
            result += f"  قیمت: {NumberFormatter.format_price(current_price)}\n"
            result += f"  {profit_emoji} سود/زیان: {NumberFormatter.format_percentage(profit_loss)}\n\n"
        
        return result


class ReportFormatter:
    """فرمت‌بندی گزارش‌ها"""
    
    @staticmethod
    def format_daily_report(data: Dict[str, Any]) -> str:
        """فرمت‌بندی گزارش روزانه"""
        date_str = DateTimeFormatter.format_date_persian(datetime.now())
        
        total_users = data.get('total_users', 0)
        active_users = data.get('active_users', 0)
        new_users = data.get('new_users', 0)
        total_signals = data.get('total_signals', 0)
        revenue = data.get('revenue', 0)
        
        return f"""
📊 <b>گزارش روزانه</b>
📅 تاریخ: {date_str}

👥 <b>کاربران:</b>
• کل کاربران: {NumberFormatter.format_number_persian(total_users)}
• کاربران فعال: {NumberFormatter.format_number_persian(active_users)}
• کاربران جدید: {NumberFormatter.format_number_persian(new_users)}

📈 <b>سیگنال‌ها:</b>
• تعداد سیگنال: {NumberFormatter.format_number_persian(total_signals)}

💰 <b>درآمد:</b>
• درآمد روزانه: ${NumberFormatter.format_number_persian(revenue)}
"""
    
    @staticmethod
    def format_user_stats(stats: Dict[str, Any]) -> str:
        """فرمت‌بندی آمار کاربر"""
        signals_received = stats.get('signals_received', 0)
        successful_trades = stats.get('successful_trades', 0)
        total_trades = stats.get('total_trades', 0)
        win_rate = stats.get('win_rate', 0)
        total_profit = stats.get('total_profit', 0)
        
        return f"""
📊 <b>آمار شما</b>

📈 <b>سیگنال‌ها:</b>
• دریافت شده: {NumberFormatter.format_number_persian(signals_received)}
• معاملات موفق: {NumberFormatter.format_number_persian(successful_trades)}
• کل معاملات: {NumberFormatter.format_number_persian(total_trades)}

🎯 <b>عملکرد:</b>
• نرخ موفقیت: {NumberFormatter.format_percentage(win_rate)}
• سود کل: {NumberFormatter.format_price(total_profit)}
"""


# Export
__all__ = [
    'NumberFormatter',
    'DateTimeFormatter', 
    'SignalFormatter',
    'MessageFormatter',
    'TableFormatter',
    'ReportFormatter'
]