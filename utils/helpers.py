"""
ابزارهای کمکی - توابع عمومی و کاربردی
نسخه بهبود یافته با Parser پیکربندی‌محور برای استخراج سیگنال‌ها
"""

import re
import json
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import time

# =========================
# پیکربندی Parser برای استخراج سیگنال‌ها
# =========================

# پیکربندی patterns برای استخراج داده‌ها از همه استراتژی‌ها
EXTRACTION_PATTERNS = {
    # الگوهای استخراج قیمت - از عمومی به خاص
    "price_patterns": [
        r"قیمت لایو[:\s]*([0-9,]+\.?[0-9]*)",
        r"آخرین قیمت[:\s]*([0-9,]+\.?[0-9]*)", 
        r"قیمت فعلی[:\s]*([0-9,]+\.?[0-9]*)",
        r"قیمت آخر[:\s]*([0-9,]+\.?[0-9]*)",
        r"آخرین قیمت بسته شدن[:\s]*([0-9,]+\.?[0-9]*)",
        r"قیمت بسته شدن[:\s]*([0-9,]+\.?[0-9]*)"
    ],
    
    # الگوهای استخراج سیگنال - چندین pattern با mapping
    "signal_patterns": [
        {
            "pattern": r"نتیجه نهایی تحلیل[:\s]*([^\n]+)",
            "mapping": {
                r"سیگنال صعودی|BUY": "خرید",
                r"سیگنال نزولی|SELL": "فروش", 
                r"HOLD|نگهداری|تعادل": "نگهداری"
            }
        },
        {
            "pattern": r"آخرین سیگنال[:\s]*([A-Z_]+)",
            "mapping": {
                r"SELL_DIVERGENCE|STRONG_SELL": "فروش",
                r"BUY_DIVERGENCE|STRONG_BUY": "خرید",
                r"HOLD": "نگهداری"
            }
        },
        {
            "pattern": r"فرصت\s+(\w+)\s+مناسب",
            "mapping": {
                r"فروش": "فروش",
                r"خرید": "خرید"
            }
        },
        {
            "pattern": r"قدرت سیگنال[:\s]*([^\n]+)",
            "mapping": {
                r"STRONG SELL|قوی.*فروش": "فروش",
                r"STRONG BUY|قوی.*خرید": "خرید",
                r"SELL": "فروش",
                r"BUY": "خرید"
            }
        }
    ],
    
    # الگوهای استخراج قدرت سیگنال
    "strength_patterns": [
        {
            "pattern": r"قدرت سیگنال[:\s]*([^\n]+)",
            "mapping": {
                r"STRONG|قوی|بسیار": "قوی",
                r"WEAK|ضعیف": "ضعیف",
                r"متوسط|MEDIUM": "متوسط"
            }
        },
        {
            "pattern": r"قدرت[:\s]*([^)]+)",
            "mapping": {
                r"قوی|STRONG": "قوی",
                r"ضعیف|WEAK": "ضعیف",
                r"متوسط": "متوسط"
            }
        }
    ],
    
    # الگوهای استخراج سطوح معاملاتی
    "trading_levels": {
        "entry_price": [
            r"Entry[:\s]*([0-9,]+\.?[0-9]*)",
            r"نقطه ورود[:\s]*([0-9,]+\.?[0-9]*)",
            r"قیمت ورود[:\s]*([0-9,]+\.?[0-9]*)"
        ],
        "stop_loss": [
            r"SL[:\s]*([0-9,]+\.?[0-9]*)",
            r"حد ضرر[:\s]*([0-9,]+\.?[0-9]*)",
            r"stop\s*loss[:\s]*([0-9,]+\.?[0-9]*)"
        ],
        "take_profit": [
            r"TP[:\s]*([0-9,]+\.?[0-9]*)",
            r"هدف قیمتی[:\s]*([0-9,]+\.?[0-9]*)",
            r"حد سود[:\s]*([0-9,]+\.?[0-9]*)",
            r"take\s*profit[:\s]*([0-9,]+\.?[0-9]*)"
        ],
        "support": [
            r"سطح حمایت[^:]*[:\s]*([0-9,]+\.?[0-9]*)",
            r"Support[^:]*[:\s]*([0-9,]+\.?[0-9]*)",
            r"حمایت[^:]*[:\s]*([0-9,]+\.?[0-9]*)"
        ],
        "resistance": [
            r"سطح مقاومت[^:]*[:\s]*([0-9,]+\.?[0-9]*)",
            r"Resistance[^:]*[:\s]*([0-9,]+\.?[0-9]*)",
            r"مقاومت[^:]*[:\s]*([0-9,]+\.?[0-9]*)"
        ]
    }
}

# =========================
# توابع اصلی استخراج سیگنال
# =========================

def extract_signal_details(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parser جامع مبتنی بر پیکربندی برای همه استراتژی‌ها
    این تابع می‌تواند داده‌های تحلیلی را از هر استراتژی استخراج کند
    """
    try:
        from utils.logger import logger
        
        details = {
            "signal_direction": "نامشخص",
            "strength": "متوسط", 
            "confidence": 0.5,
            "current_price": 0.0,
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "support": 0.0,
            "resistance": 0.0
        }
        
        # 1. استخراج از structured data (اگر موجود باشد)
        if "analysis" in analysis_result and isinstance(analysis_result["analysis"], dict):
            details.update(_extract_from_structured_data(analysis_result["analysis"]))
        
        # 2. استخراج از محتوای متنی
        text_content = analysis_result.get("analysis_text") or analysis_result.get("raw_report", "")
        
        if text_content:
            details.update(_extract_from_text_universal(text_content))
        
        # 3. استخراج قیمت از فیلدهای اضافی
        if details["current_price"] == 0.0:
            details["current_price"] = _extract_price_from_fields(analysis_result)
        
        # 4. محاسبه confidence
        details["confidence"] = _calculate_confidence(details["strength"])
        
        # 5. محاسبه سطوح fallback
        _calculate_fallback_levels(details)
        
        return details
        
    except Exception as e:
        try:
            from utils.logger import logger
            logger.error(f"Error extracting signal details: {e}")
        except:
            print(f"Error extracting signal details: {e}")
        return _get_default_details()

def _extract_from_structured_data(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """استخراج از داده‌های ساختاریافته JSON"""
    details = {}
    
    # قیمت
    if "last_price" in analysis_data:
        details["current_price"] = float(analysis_data["last_price"])
    
    # سیگنال
    if "signal" in analysis_data:
        signal_mapping = {
            "BUY": "خرید", "SELL": "فروش", "HOLD": "نگهداری",
            "خرید": "خرید", "فروش": "فروش", "نگهداری": "نگهداری"
        }
        details["signal_direction"] = signal_mapping.get(
            str(analysis_data["signal"]).upper(), "نامشخص"
        )
    
    # قدرت
    if "signal_strength" in analysis_data:
        details["strength"] = str(analysis_data["signal_strength"])
    
    return details

def _extract_from_text_universal(text: str) -> Dict[str, Any]:
    """Parser جامع مبتنی بر patterns برای همه متون"""
    details = {}
    
    # استخراج قیمت
    for pattern in EXTRACTION_PATTERNS["price_patterns"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details["current_price"] = float(match.group(1).replace(',', ''))
            break
    
    # استخراج سیگنال
    for signal_config in EXTRACTION_PATTERNS["signal_patterns"]:
        match = re.search(signal_config["pattern"], text, re.IGNORECASE)
        if match:
            matched_text = match.group(1).strip() if match.groups() else match.group(0).strip()
            
            for pattern_key, signal_value in signal_config["mapping"].items():
                if re.search(pattern_key, matched_text, re.IGNORECASE):
                    details["signal_direction"] = signal_value
                    break
            
            if "signal_direction" in details:
                break
    
    # استخراج قدرت
    for strength_config in EXTRACTION_PATTERNS["strength_patterns"]:
        match = re.search(strength_config["pattern"], text, re.IGNORECASE)
        if match:
            matched_text = match.group(1).strip()
            
            for pattern_key, strength_value in strength_config["mapping"].items():
                if re.search(pattern_key, matched_text, re.IGNORECASE):
                    details["strength"] = strength_value
                    break
            
            if "strength" in details:
                break
    
    # استخراج سطوح معاملاتی
    for level_name, patterns in EXTRACTION_PATTERNS["trading_levels"].items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details[level_name] = float(match.group(1).replace(',', ''))
                break
        
        # اگر پیدا شد، به pattern بعدی برو
        if level_name in details:
            continue
    
    return details

def _extract_price_from_fields(analysis_result: Dict[str, Any]) -> float:
    """استخراج قیمت از فیلدهای مختلف"""
    price_fields = ["current_price", "price", "close", "last_price"]
    
    for field in price_fields:
        if field in analysis_result:
            try:
                return float(analysis_result[field])
            except (ValueError, TypeError):
                continue
    
    return 0.0

def _calculate_confidence(strength: str) -> float:
    """محاسبه درصد اعتماد بر اساس قدرت"""
    confidence_map = {
        "بسیار قوی": 0.9,
        "قوی": 0.8, 
        "متوسط": 0.6,
        "ضعیف": 0.4,
        "خیلی ضعیف": 0.2
    }
    
    for key, value in confidence_map.items():
        if key in strength:
            return value
    
    return 0.5

def _calculate_fallback_levels(details: Dict[str, Any]) -> None:
    """محاسبه سطوح fallback برای فیلدهای خالی"""
    current_price = details.get("current_price", 0.0)
    
    if current_price <= 0:
        return
    
    # Entry price fallback
    if details.get("entry_price", 0.0) == 0.0:
        details["entry_price"] = current_price
    
    entry_price = details["entry_price"]
    signal_direction = details.get("signal_direction", "نامشخص")
    
    # Stop Loss fallback
    if details.get("stop_loss", 0.0) == 0.0:
        if signal_direction == "فروش":
            details["stop_loss"] = entry_price * 1.02  # 2% بالاتر
        else:
            details["stop_loss"] = entry_price * 0.98  # 2% پایین‌تر
    
    # Take Profit fallback  
    if details.get("take_profit", 0.0) == 0.0:
        if signal_direction == "فروش":
            details["take_profit"] = entry_price * 0.97  # 3% پایین‌تر
        else:
            details["take_profit"] = entry_price * 1.03  # 3% بالاتر
    
    # Support/Resistance fallback
    if details.get("support", 0.0) == 0.0:
        details["support"] = current_price * 0.995  # 0.5% پایین‌تر
    
    if details.get("resistance", 0.0) == 0.0:
        details["resistance"] = current_price * 1.005  # 0.5% بالاتر

def _get_default_details() -> Dict[str, Any]:
    """مقادیر پیش‌فرض در صورت خطا"""
    return {
        "signal_direction": "نامشخص",
        "strength": "متوسط",
        "confidence": 0.5,
        "current_price": 0.0,
        "entry_price": 0.0,
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "support": 0.0,
        "resistance": 0.0
    }

# تابع کمکی برای اضافه کردن patterns جدید
def add_extraction_pattern(category: str, pattern: str, mapping: Dict[str, str] = None):
    """اضافه کردن pattern جدید بدون تغییر کد"""
    if category == "price":
        EXTRACTION_PATTERNS["price_patterns"].append(pattern)
    elif category == "signal":
        EXTRACTION_PATTERNS["signal_patterns"].append({
            "pattern": pattern,
            "mapping": mapping or {}
        })
    elif category == "strength":
        EXTRACTION_PATTERNS["strength_patterns"].append({
            "pattern": pattern, 
            "mapping": mapping or {}
        })
    elif category in EXTRACTION_PATTERNS["trading_levels"]:
        EXTRACTION_PATTERNS["trading_levels"][category].append(pattern)

def format_signal_message(signal_details: Dict[str, Any], symbol: str, currency: str, timeframe: str, strategy: str) -> str:
    """
    فرمت کامل پیام سیگنال با جزئیات
    """
    try:
        # انتخاب ایموجی بر اساس سیگنال
        signal_emojis = {
            "خرید": "🟢⬆️",
            "فروش": "🔴⬇️", 
            "نگهداری": "🟡⏸️",
            "نامشخص": "⚪"
        }
        
        signal_direction = signal_details.get("signal_direction", "نامشخص")
        emoji = signal_emojis.get(signal_direction, "⚪")
        current_price = signal_details.get("current_price", 0.0)
        
        # ساخت پیام اصلی
        message = f"🎯 سیگنال معاملاتی {symbol}/{currency}\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "📊 اطلاعات کلی:\n"
        message += f"⏱ تایم‌فریم: {timeframe}\n"
        message += f"💵 قیمت فعلی: {current_price:,.4f} {currency}\n"
        message += f"🕒 زمان تحلیل: 1404/06/15 - 04:27:29\n"
        message += f"{emoji} سیگنال: {signal_direction}\n"
        message += f"👌 قدرت: {signal_details.get('strength', 'متوسط')}\n"
        
        # سطوح کلیدی
        message += "💰 سطوح کلیدی:\n"
        entry_price = signal_details.get("entry_price", current_price)
        stop_loss = signal_details.get("stop_loss", 0.0)
        take_profit = signal_details.get("take_profit", 0.0)
        
        message += f"🎯 نقطه ورود: {entry_price:,.4f}\n"
        message += f"🛑 حد ضرر: {stop_loss:,.4f}\n"
        message += f"💎 هدف قیمتی: {take_profit:,.4f}\n"
        
        # تحلیل تکنیکال
        message += "📈 تحلیل تکنیکال:\n"
        support = signal_details.get("support", 0.0)
        resistance = signal_details.get("resistance", 0.0)
        confidence = signal_details.get("confidence", 0.5)
        
        message += f"🔻 حمایت: {support:,.4f}\n"
        message += f"🔺 مقاومت: {resistance:,.4f}\n"
        message += f"📊 اعتماد: {confidence:.0%}\n"
        
        # یادآوری
        message += "\n⚠️ یادآوری مهم: این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."
        
        return message
        
    except Exception as e:
        try:
            from utils.logger import logger
            logger.error(f"Error formatting signal message: {e}")
        except:
            print(f"Error formatting signal message: {e}")
        return f"❌ خطا در فرمت‌بندی پیام سیگنال {symbol}/{currency}"

# =========================
# سایر توابع کمکی (بدون تغییر)
# =========================

def generate_random_string(length: int = 8, 
                         use_uppercase: bool = True,
                         use_lowercase: bool = True, 
                         use_digits: bool = True,
                         use_special: bool = False) -> str:
    """تولید رشته تصادفی"""
    chars = ""
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_digits:
        chars += string.digits
    if use_special:
        chars += "!@#$%^&*"
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_referral_code(length: int = 8) -> str:
    """تولید کد رفرال"""
    return generate_random_string(length, use_lowercase=False, use_special=False)

def generate_transaction_id() -> str:
    """تولید شناسه تراکنش"""
    timestamp = str(int(time.time()))
    random_part = generate_random_string(6, use_lowercase=False)
    return f"TXN{timestamp}{random_part}"

def hash_string(text: str, salt: str = "") -> str:
    """هش کردن رشته با SHA256"""
    combined = f"{text}{salt}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def mask_sensitive_data(data: str, 
                       show_first: int = 2, 
                       show_last: int = 2, 
                       mask_char: str = "*") -> str:
    """پنهان کردن داده‌های حساس"""
    if len(data) <= show_first + show_last:
        return mask_char * len(data)
    
    masked_length = len(data) - show_first - show_last
    return f"{data[:show_first]}{mask_char * masked_length}{data[-show_last:]}"

def format_number(number: Union[int, float], 
                 decimal_places: int = 2,
                 use_comma: bool = True) -> str:
    """فرمت‌بندی اعداد"""
    if isinstance(number, int):
        formatted = f"{number:,}" if use_comma else str(number)
    else:
        formatted = f"{number:,.{decimal_places}f}" if use_comma else f"{number:.{decimal_places}f}"
    
    return formatted

def format_currency(amount: float, 
                   currency: str = "USD",
                   decimal_places: int = 2) -> str:
    """فرمت‌بندی ارز"""
    formatted_amount = format_number(amount, decimal_places)
    
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "IRR": "ریال",
        "USDT": "USDT",
        "BTC": "₿"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency in ["IRR"]:
        return f"{formatted_amount} {symbol}"
    else:
        return f"{symbol}{formatted_amount}"

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """فرمت‌بندی درصد"""
    return f"{value:.{decimal_places}f}%"

def format_time_delta(delta: timedelta) -> str:
    """فرمت‌بندی مدت زمان"""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} ثانیه"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} دقیقه"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} ساعت و {minutes} دقیقه"
        return f"{hours} ساعت"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        if hours > 0:
            return f"{days} روز و {hours} ساعت"
        return f"{days} روز"

def parse_user_input(text: str) -> Dict[str, Any]:
    """پارس کردن ورودی کاربر"""
    result = {
        "original": text,
        "cleaned": text.strip(),
        "words": text.strip().split(),
        "numbers": re.findall(r'\d+\.?\d*', text),
        "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    }
    
    # استخراج نمادهای ارز
    symbols = re.findall(r'\b[A-Z]{2,10}\b', text.upper())
    result["symbols"] = list(set(symbols))
    
    return result

def safe_dict_get(dictionary: Dict[str, Any], 
                 key_path: str, 
                 default: Any = None) -> Any:
    """دریافت امن از دیکشنری با مسیر کلید"""
    keys = key_path.split('.')
    current = dictionary
    
    try:
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except (KeyError, TypeError):
        return default

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """ترکیب عمیق دو دیکشنری"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def clean_html_tags(text: str) -> str:
    """پاک کردن تگ‌های HTML"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def escape_markdown(text: str) -> str:
    """Escape کردن کاراکترهای Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text: str, 
                 max_length: int = 100, 
                 suffix: str = "...") -> str:
    """کوتاه کردن متن"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """تقسیم لیست به قطعات کوچکتر"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """تبدیل لیست تودرتو به لیست ساده"""
    return [item for sublist in nested_list for item in sublist]

def remove_duplicates(lst: List[Any], key_func=None) -> List[Any]:
    """حذف موارد تکراری از لیست"""
    if key_func:
        seen = set()
        result = []
        for item in lst:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
    else:
        return list(dict.fromkeys(lst))

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """محاسبه درصد تغییر"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100

def calculate_moving_average(values: List[float], window: int) -> List[float]:
    """محاسبه میانگین متحرک"""
    if len(values) < window:
        return []
    
    result = []
    for i in range(window - 1, len(values)):
        avg = sum(values[i - window + 1:i + 1]) / window
        result.append(avg)
    
    return result

def retry_on_failure(max_retries: int = 3, 
                    delay: float = 1.0,
                    exponential_backoff: bool = True):
    """دکوراتور برای تلاش مجدد در صورت خطا"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    await asyncio.sleep(wait_time)
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    time.sleep(wait_time)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def rate_limit(calls_per_minute: int = 60):
    """دکوراتور برای محدود کردن نرخ فراخوانی"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        return wrapper
    return decorator

def memoize(maxsize: int = 128, ttl: int = 300):
    """دکوراتور برای cache کردن نتایج"""
    def decorator(func):
        cache = {}
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # ایجاد کلید cache
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # بررسی وجود در cache و انقضا
            if key in cache:
                if current_time - cache_times[key] < ttl:
                    return cache[key]
                else:
                    # حذف آیتم منقضی
                    del cache[key]
                    del cache_times[key]
            
            # محدود کردن اندازه cache
            if len(cache) >= maxsize:
                # حذف قدیمی‌ترین آیتم
                oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                del cache[oldest_key]
                del cache_times[oldest_key]
            
            # محاسبه و ذخیره نتیجه
            result = func(*args, **kwargs)
            cache[key] = result
            cache_times[key] = current_time
            
            return result
        
        # اضافه کردن متد پاک کردن cache
        wrapper.clear_cache = lambda: cache.clear() or cache_times.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'maxsize': maxsize,
            'ttl': ttl,
            'hits': getattr(wrapper, '_hits', 0),
            'misses': getattr(wrapper, '_misses', 0)
        }
        
        return wrapper
    return decorator

class Timer:
    """کلاس برای اندازه‌گیری زمان"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """شروع تایمر"""
        self.start_time = time.time()
        return self
    
    def stop(self):
        """پایان تایمر"""
        self.end_time = time.time()
        return self
    
    def elapsed(self) -> float:
        """زمان سپری شده"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, *args):
        self.stop()

class DataProcessor:
    """کلاس برای پردازش داده‌ها"""
    
    @staticmethod
    def normalize_data(data: List[float], 
                      min_val: float = 0.0, 
                      max_val: float = 1.0) -> List[float]:
        """نرمال‌سازی داده‌ها"""
        if not data:
            return []
        
        data_min = min(data)
        data_max = max(data)
        data_range = data_max - data_min
        
        if data_range == 0:
            return [min_val] * len(data)
        
        normalized = []
        for value in data:
            norm_val = (value - data_min) / data_range
            scaled_val = norm_val * (max_val - min_val) + min_val
            normalized.append(scaled_val)
        
        return normalized
    
    @staticmethod
    def calculate_statistics(data: List[float]) -> Dict[str, float]:
        """محاسبه آمار توصیفی"""
        if not data:
            return {}
        
        sorted_data = sorted(data)
        n = len(data)
        
        mean = sum(data) / n
        median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        
        variance = sum((x - mean) ** 2 for x in data) / n
        std_dev = variance ** 0.5
        
        return {
            'count': n,
            'mean': mean,
            'median': median,
            'min': min(data),
            'max': max(data),
            'variance': variance,
            'std_dev': std_dev,
            'range': max(data) - min(data)
        }
    
    @staticmethod
    def smooth_data(data: List[float], window_size: int = 3) -> List[float]:
        """هموار کردن داده‌ها"""
        if len(data) < window_size:
            return data.copy()
        
        smoothed = []
        half_window = window_size // 2
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            smoothed.append(sum(data[start:end]) / (end - start))
        
        return smoothed

def convert_persian_numbers(text: str) -> str:
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    
    for persian, english in zip(persian_digits, english_digits):
        text = text.replace(persian, english)
    
    return text

def convert_english_numbers(text: str) -> str:
    """تبدیل اعداد انگلیسی به فارسی"""
    english_digits = '0123456789'
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    
    for english, persian in zip(english_digits, persian_digits):
        text = text.replace(english, persian)
    
    return text

def create_progress_bar(current: int, 
                       total: int, 
                       length: int = 20,
                       fill_char: str = "█",
                       empty_char: str = "░") -> str:
    """ایجاد نوار پیشرفت"""
    if total == 0:
        return empty_char * length
    
    percent = current / total
    filled_length = int(length * percent)
    
    bar = fill_char * filled_length + empty_char * (length - filled_length)
    return f"{bar} {percent:.1%}"