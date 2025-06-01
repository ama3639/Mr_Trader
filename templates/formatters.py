"""
فرمت‌کننده‌ها - تبدیل و فرمت‌بندی داده‌ها
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

class NumberFormatter:
    """فرمت‌کننده اعداد"""
    
    @staticmethod
    def format_price(price: Union[int, float, str], 
                    currency: str = "USD",
                    decimal_places: int = 2,
                    use_comma: bool = True) -> str:
        """فرمت‌بندی قیمت"""
        try:
            price_float = float(price)
            
            # تعیین تعداد رقم اعشار بر اساس قیمت
            if price_float < 0.01:
                decimal_places = 6
            elif price_float < 1:
                decimal_places = 4
            elif price_float < 100:
                decimal_places = 2
            else:
                decimal_places = 2
            
            # فرمت‌بندی عدد
            if use_comma:
                formatted = f"{price_float:,.{decimal_places}f}"
            else:
                formatted = f"{price_float:.{decimal_places}f}"
            
            # اضافه کردن نماد ارز
            currency_symbols = {
                "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
                "USDT": " USDT", "BTC": " ₿", "ETH": " ETH",
                "BNB": " BNB", "IRR": " ریال"
            }
            
            symbol = currency_symbols.get(currency.upper(), f" {currency}")
            
            if currency.upper() in ["IRR"]:
                return f"{formatted}{symbol}"
            else:
                return f"{symbol}{formatted}" if symbol.startswith("$") else f"{formatted}{symbol}"
                
        except (ValueError, TypeError):
            return f"0.00 {currency}"
    
    @staticmethod
    def format_percentage(value: Union[int, float, str], 
                         decimal_places: int = 2,
                         show_sign: bool = True) -> str:
        """فرمت‌بندی درصد"""
        try:
            value_float = float(value)
            
            if show_sign:
                sign = "+" if value_float > 0 else ""
                return f"{sign}{value_float:.{decimal_places}f}%"
            else:
                return f"{value_float:.{decimal_places}f}%"
                
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def format_large_number(number: Union[int, float, str],
                           unit_system: str = "si") -> str:
        """فرمت‌بندی اعداد بزرگ"""
        try:
            num = float(number)
            
            if unit_system == "si":
                # سیستم SI (K, M, B, T)
                if abs(num) >= 1e12:
                    return f"{num/1e12:.1f}T"
                elif abs(num) >= 1e9:
                    return f"{num/1e9:.1f}B"
                elif abs(num) >= 1e6:
                    return f"{num/1e6:.1f}M"
                elif abs(num) >= 1e3:
                    return f"{num/1e3:.1f}K"
                else:
                    return f"{num:.0f}"
            
            elif unit_system == "persian":
                # سیستم فارسی (هزار، میلیون، میلیارد)
                if abs(num) >= 1e12:
                    return f"{num/1e12:.1f} تریلیون"
                elif abs(num) >= 1e9:
                    return f"{num/1e9:.1f} میلیارد"
                elif abs(num) >= 1e6:
                    return f"{num/1e6:.1f} میلیون"
                elif abs(num) >= 1e3:
                    return f"{num/1e3:.1f} هزار"
                else:
                    return f"{num:,.0f}"
            
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def format_volume(volume: Union[int, float, str]) -> str:
        """فرمت‌بندی حجم معاملات"""
        try:
            vol = float(volume)
            if vol >= 1e9:
                return f"{vol/1e9:.2f}B"
            elif vol >= 1e6:
                return f"{vol/1e6:.2f}M"
            elif vol >= 1e3:
                return f"{vol/1e3:.2f}K"
            else:
                return f"{vol:.2f}"
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def round_to_precision(number: Union[int, float, str], 
                          precision: int = 8) -> str:
        """گرد کردن با دقت مشخص"""
        try:
            decimal_num = Decimal(str(number))
            rounded = decimal_num.quantize(
                Decimal('0.' + '0' * precision), 
                rounding=ROUND_HALF_UP
            )
            return str(rounded)
        except:
            return "0"

class TimeFormatter:
    """فرمت‌کننده زمان"""
    
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """فرمت‌بندی مدت زمان"""
        try:
            total_seconds = int(seconds)
            
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            
            parts = []
            if days > 0:
                parts.append(f"{days} روز")
            if hours > 0:
                parts.append(f"{hours} ساعت")
            if minutes > 0:
                parts.append(f"{minutes} دقیقه")
            if secs > 0 or not parts:
                parts.append(f"{secs} ثانیه")
            
            return " و ".join(parts[:2])  # نمایش حداکثر 2 واحد
            
        except (ValueError, TypeError):
            return "0 ثانیه"
    
    @staticmethod
    def format_timestamp(timestamp: Union[int, float, str],
                        format_type: str = "full") -> str:
        """فرمت‌بندی timestamp"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(float(timestamp))
            
            if format_type == "full":
                return dt.strftime("%Y/%m/%d %H:%M:%S")
            elif format_type == "date":
                return dt.strftime("%Y/%m/%d")
            elif format_type == "time":
                return dt.strftime("%H:%M:%S")
            elif format_type == "relative":
                return TimeFormatter.relative_time(dt)
            else:
                return dt.strftime(format_type)
                
        except (ValueError, TypeError):
            return "نامعتبر"
    
    @staticmethod
    def relative_time(dt: datetime) -> str:
        """زمان نسبی (چند دقیقه پیش)"""
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
    def format_countdown(target_datetime: datetime) -> str:
        """شمارش معکوس تا زمان مشخص"""
        now = datetime.now()
        diff = target_datetime - now
        
        if diff.total_seconds() <= 0:
            return "منقضی شده"
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} روز")
        if hours > 0:
            parts.append(f"{hours} ساعت")
        if minutes > 0:
            parts.append(f"{minutes} دقیقه")
        
        return " و ".join(parts) if parts else "کمتر از یک دقیقه"

class TextFormatter:
    """فرمت‌کننده متن"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """پاکسازی متن"""
        if not text:
            return ""
        
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text)  # چند space را به یکی تبدیل
        text = re.sub(r'\n+', '\n', text)  # چند line break را به یکی تبدیل
        text = text.strip()
        
        return text
    
    @staticmethod
    def truncate_text(text: str, 
                     max_length: int = 100,
                     suffix: str = "...") -> str:
        """کوتاه کردن متن"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape کردن کاراکترهای Markdown"""
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape کردن کاراکترهای HTML"""
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape_table.get(c, c) for c in text)
    
    @staticmethod
    def format_username(username: str) -> str:
        """فرمت‌بندی نام کاربری"""
        if not username:
            return "کاربر مهمان"
        
        # حذف @ از ابتدا
        username = username.lstrip('@')
        
        # محدود کردن طول
        if len(username) > 20:
            username = username[:17] + "..."
        
        return f"@{username}"
    
    @staticmethod
    def mask_sensitive_info(text: str, 
                           mask_type: str = "email") -> str:
        """پوشاندن اطلاعات حساس"""
        if not text:
            return ""
        
        if mask_type == "email":
            # email@domain.com -> e***l@d***n.com
            if "@" in text:
                local, domain = text.split("@", 1)
                if len(local) > 2:
                    local = local[0] + "*" * (len(local) - 2) + local[-1]
                if "." in domain:
                    domain_parts = domain.split(".")
                    domain_name = domain_parts[0]
                    if len(domain_name) > 2:
                        domain_name = domain_name[0] + "*" * (len(domain_name) - 2) + domain_name[-1]
                    domain = domain_name + "." + ".".join(domain_parts[1:])
                return f"{local}@{domain}"
        
        elif mask_type == "phone":
            # 09123456789 -> 091****6789
            if len(text) >= 8:
                return text[:3] + "*" * (len(text) - 6) + text[-3:]
        
        elif mask_type == "card":
            # 1234567890123456 -> 1234****3456
            if len(text) >= 8:
                return text[:4] + "*" * (len(text) - 8) + text[-4:]
        
        return text

class DataFormatter:
    """فرمت‌کننده داده‌ها"""
    
    @staticmethod
    def format_signal_strength(strength: str) -> str:
        """فرمت‌بندی قدرت سیگنال"""
        strength_map = {
            "very_weak": "🔴 بسیار ضعیف",
            "weak": "🟠 ضعیف", 
            "medium": "🟡 متوسط",
            "strong": "🟢 قوی",
            "very_strong": "🔵 بسیار قوی"
        }
        return strength_map.get(strength.lower(), "🟡 متوسط")
    
    @staticmethod
    def format_signal_direction(direction: str) -> str:
        """فرمت‌بندی جهت سیگنال"""
        direction_map = {
            "buy": "🟢 خرید",
            "sell": "🔴 فروش", 
            "hold": "🟡 نگه‌داری",
            "neutral": "⚪ خنثی"
        }
        return direction_map.get(direction.lower(), "⚪ خنثی")
    
    @staticmethod
    def format_package_type(package_type: str) -> str:
        """فرمت‌بندی نوع پکیج"""
        package_map = {
            "free": "🆓 رایگان",
            "basic": "🥉 پایه",
            "premium": "🥈 ویژه",
            "vip": "🥇 VIP",
            "ghost": "👻 شبح"
        }
        return package_map.get(package_type.lower(), "📦 نامشخص")
    
    @staticmethod
    def format_user_status(status: str) -> str:
        """فرمت‌بندی وضعیت کاربر"""
        status_map = {
            "active": "🟢 فعال",
            "inactive": "🟡 غیرفعال",
            "suspended": "🔴 معلق",
            "banned": "⛔ مسدود"
        }
        return status_map.get(status.lower(), "❓ نامشخص")
    
    @staticmethod
    def format_payment_status(status: str) -> str:
        """فرمت‌بندی وضعیت پرداخت"""
        status_map = {
            "pending": "⏳ در انتظار",
            "processing": "🔄 در حال پردازش",
            "completed": "✅ تکمیل شده",
            "failed": "❌ ناموفق",
            "cancelled": "🚫 لغو شده",
            "refunded": "↩️ بازگشت داده شده"
        }
        return status_map.get(status.lower(), "❓ نامشخص")

class JSONFormatter:
    """فرمت‌کننده JSON"""
    
    @staticmethod
    def pretty_json(data: Union[Dict, List], 
                   ensure_ascii: bool = False,
                   indent: int = 2) -> str:
        """فرمت‌بندی زیبای JSON"""
        try:
            return json.dumps(
                data, 
                ensure_ascii=ensure_ascii,
                indent=indent,
                default=str,
                sort_keys=True
            )
        except (TypeError, ValueError):
            return "{}"
    
    @staticmethod
    def minify_json(data: Union[Dict, List]) -> str:
        """فشرده‌سازی JSON"""
        try:
            return json.dumps(data, separators=(',', ':'), default=str)
        except (TypeError, ValueError):
            return "{}"
    
    @staticmethod
    def safe_json_loads(json_string: str, 
                       default: Any = None) -> Any:
        """بارگذاری امن JSON"""
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default or {}

class TableFormatter:
    """فرمت‌کننده جدول"""
    
    @staticmethod
    def format_table(data: List[Dict[str, Any]], 
                    headers: Optional[List[str]] = None,
                    max_width: int = 20) -> str:
        """فرمت‌بندی جدول ASCII"""
        if not data:
            return "داده‌ای موجود نیست"
        
        if not headers:
            headers = list(data[0].keys())
        
        # محاسبه عرض ستون‌ها
        widths = {}
        for header in headers:
            widths[header] = min(max_width, max(
                len(str(header)),
                max(len(str(row.get(header, ''))) for row in data)
            ))
        
        # ایجاد خط جداکننده
        separator = "+" + "+".join("-" * (widths[h] + 2) for h in headers) + "+"
        
        # ایجاد header
        header_row = "|" + "|".join(f" {str(h):<{widths[h]}} " for h in headers) + "|"
        
        # ایجاد ردیف‌های داده
        rows = []
        for row in data:
            formatted_row = "|" + "|".join(
                f" {str(row.get(h, '')):<{widths[h]}} " for h in headers
            ) + "|"
            rows.append(formatted_row)
        
        # ترکیب همه قسمت‌ها
        table = [separator, header_row, separator] + rows + [separator]
        return "\n".join(table)
    
    @staticmethod
    def format_simple_table(data: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی جدول ساده"""
        if not data:
            return "داده‌ای موجود نیست"
        
        result = []
        for i, row in enumerate(data, 1):
            result.append(f"{i:2d}. " + " | ".join(f"{k}: {v}" for k, v in row.items()))
        
        return "\n".join(result)

class ProgressFormatter:
    """فرمت‌کننده نوار پیشرفت"""
    
    @staticmethod
    def create_progress_bar(current: int, 
                           total: int,
                           length: int = 20,
                           fill_char: str = "█",
                           empty_char: str = "░") -> str:
        """ایجاد نوار پیشرفت"""
        if total == 0:
            return f"[{empty_char * length}] 0%"
        
        percent = min(100, (current / total) * 100)
        filled_length = int(length * percent / 100)
        
        bar = fill_char * filled_length + empty_char * (length - filled_length)
        return f"[{bar}] {percent:.1f}%"
    
    @staticmethod
    def format_loading_animation(step: int, 
                                total_steps: int = 4) -> str:
        """انیمیشن بارگذاری"""
        animations = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        return animations[step % len(animations)]

class ValidationFormatter:
    """فرمت‌کننده پیام‌های اعتبارسنجی"""
    
    @staticmethod
    def format_error_list(errors: List[str]) -> str:
        """فرمت‌بندی لیست خطاها"""
        if not errors:
            return ""
        
        formatted_errors = []
        for i, error in enumerate(errors, 1):
            formatted_errors.append(f"{i}. {error}")
        
        return "❌ خطاهای یافت شده:\n" + "\n".join(formatted_errors)
    
    @staticmethod
    def format_validation_result(is_valid: bool, 
                                message: str = "") -> str:
        """فرمت‌بندی نتیجه اعتبارسنجی"""
        if is_valid:
            return f"✅ معتبر" + (f": {message}" if message else "")
        else:
            return f"❌ نامعتبر" + (f": {message}" if message else "")

# کلاس اصلی Formatter
class Formatter:
    """کلاس اصلی فرمت‌کننده"""
    
    number = NumberFormatter()
    time = TimeFormatter()
    text = TextFormatter()
    data = DataFormatter()
    json = JSONFormatter()
    table = TableFormatter()
    progress = ProgressFormatter()
    validation = ValidationFormatter()
    
    @staticmethod
    def auto_format(value: Any, format_type: str = "auto") -> str:
        """فرمت‌بندی خودکار بر اساس نوع داده"""
        if value is None:
            return "نامشخص"
        
        if format_type == "auto":
            if isinstance(value, (int, float)):
                return Formatter.number.format_price(value)
            elif isinstance(value, datetime):
                return Formatter.time.format_timestamp(value.timestamp())
            elif isinstance(value, str):
                return Formatter.text.clean_text(value)
            else:
                return str(value)
        
        # فرمت‌های خاص
        format_map = {
            "price": lambda v: Formatter.number.format_price(v),
            "percentage": lambda v: Formatter.number.format_percentage(v),
            "volume": lambda v: Formatter.number.format_volume(v),
            "timestamp": lambda v: Formatter.time.format_timestamp(v),
            "duration": lambda v: Formatter.time.format_duration(v),
            "text": lambda v: Formatter.text.clean_text(str(v)),
            "json": lambda v: Formatter.json.pretty_json(v)
        }
        
        formatter_func = format_map.get(format_type)
        if formatter_func:
            try:
                return formatter_func(value)
            except:
                return str(value)
        
        return str(value)
