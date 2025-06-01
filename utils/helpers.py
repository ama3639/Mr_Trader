"""
ابزارهای کمکی - توابع عمومی و کاربردی
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

def extract_signal_details(analysis_data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """استخراج جزئیات سیگنال از داده‌های تحلیل (پشتیبانی از انواع مختلف)"""
    details = {
        "signal_direction": "neutral",
        "entry_price": 0.0,
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "support": 0.0,
        "resistance": 0.0,
        "strength": "medium",
        "confidence": 50.0,
        "strategy_type": "unknown",
        "pattern_confidence": 0.0,
        "risk_reward_ratio": 0.0
    }
    
    # دریافت متن تحلیل
    analysis_text = ""
    if isinstance(analysis_data, dict):
        analysis_text = analysis_data.get("analysis_text", str(analysis_data))
        # بررسی وجود فیلدهای مستقیم در JSON
        if "signal_direction" in analysis_data:
            details["signal_direction"] = analysis_data["signal_direction"]
        if "entry_price" in analysis_data:
            details["entry_price"] = float(analysis_data["entry_price"])
        if "stop_loss" in analysis_data:
            details["stop_loss"] = float(analysis_data["stop_loss"])
        if "take_profit" in analysis_data:
            details["take_profit"] = float(analysis_data["take_profit"])
        if "confidence" in analysis_data:
            details["confidence"] = float(analysis_data["confidence"])
    else:
        analysis_text = str(analysis_data)
    
    text = analysis_text.lower()
    
    # تشخیص نوع استراتژی بر اساس محتوا
    if "momentum" in text or "مومنتوم" in text:
        details["strategy_type"] = "momentum"
        details.update(_extract_momentum_details(analysis_text))
    elif "double top" in text or "دو قله" in text or "double bottom" in text or "دو کف" in text:
        details["strategy_type"] = "pattern"
        details.update(_extract_pattern_details(analysis_text))
    elif "ichimoku" in text or "ایچیموکو" in text:
        details["strategy_type"] = "ichimoku"
        details.update(_extract_ichimoku_details(analysis_text))
    elif "fibonacci" in text or "فیبوناچی" in text:
        details["strategy_type"] = "fibonacci"
        details.update(_extract_fibonacci_details(analysis_text))
    elif "bollinger" in text or "بولینگر" in text:
        details["strategy_type"] = "bollinger"
        details.update(_extract_bollinger_details(analysis_text))
    elif "rsi" in text:
        details["strategy_type"] = "rsi"
        details.update(_extract_rsi_details(analysis_text))
    elif "macd" in text:
        details["strategy_type"] = "macd"
        details.update(_extract_macd_details(analysis_text))
    elif "candlestick" in text or "کندل" in text:
        details["strategy_type"] = "candlestick"
        details.update(_extract_candlestick_details(analysis_text))
    elif "triangle" in text or "مثلث" in text:
        details["strategy_type"] = "triangle"
        details.update(_extract_triangle_details(analysis_text))
    elif "wedge" in text or "گوه" in text:
        details["strategy_type"] = "wedge"
        details.update(_extract_wedge_details(analysis_text))
    elif "diamond" in text or "الماس" in text:
        details["strategy_type"] = "diamond"
        details.update(_extract_diamond_details(analysis_text))
    elif "head" in text and "shoulder" in text:
        details["strategy_type"] = "head_shoulders"
        details.update(_extract_head_shoulders_details(analysis_text))
    elif "volume" in text or "حجم" in text:
        details["strategy_type"] = "volume"
        details.update(_extract_volume_details(analysis_text))
    else:
        # تحلیل عمومی
        details.update(_extract_general_details(analysis_text))
    
    return details

def _extract_momentum_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص استراتژی مومنتوم"""
    details = {}
    
    # تشخیص جهت سیگنال
    if "خرید" in analysis_text or "buy" in analysis_text.lower():
        details["signal_direction"] = "خرید"
    elif "فروش" in analysis_text or "sell" in analysis_text.lower():
        details["signal_direction"] = "فروش"
    elif "خنثی" in analysis_text or "neutral" in analysis_text.lower():
        details["signal_direction"] = "خنثی"
    
    # استخراج قیمت‌ها با regex بهتر
    entry_match = re.search(r'entry price:\s*([\d,]+\.?\d*)', analysis_text, re.IGNORECASE)
    sl_match = re.search(r'sl:\s*([\d,]+\.?\d*)', analysis_text, re.IGNORECASE)
    tp_match = re.search(r'tp:\s*([\d,]+\.?\d*)', analysis_text, re.IGNORECASE)
    
    if entry_match:
        details["entry_price"] = float(entry_match.group(1).replace(',', ''))
    if sl_match:
        details["stop_loss"] = float(sl_match.group(1).replace(',', ''))
    if tp_match:
        details["take_profit"] = float(tp_match.group(1).replace(',', ''))
    
    # استخراج Risk/Reward
    rr_match = re.search(r'risk/reward:\s*([\d.]+)', analysis_text, re.IGNORECASE)
    if rr_match:
        details["risk_reward_ratio"] = float(rr_match.group(1))
    
    # تشخیص قدرت
    if "قوی" in analysis_text or "strong" in analysis_text.lower():
        details["strength"] = "قوی"
        details["confidence"] = 85.0
    elif "ضعیف" in analysis_text or "weak" in analysis_text.lower():
        details["strength"] = "ضعیف"
        details["confidence"] = 35.0
    else:
        details["strength"] = "متوسط"
        details["confidence"] = 60.0
    
    return details

def _extract_pattern_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص الگوهای قیمتی"""
    details = {}
    
    # استخراج درصد اطمینان الگو
    confidence_match = re.search(r'اطمینان:\s*(\d+)%', analysis_text)
    if confidence_match:
        details["pattern_confidence"] = float(confidence_match.group(1))
        details["confidence"] = float(confidence_match.group(1))
    
    # استخراج تکمیل الگو
    completion_match = re.search(r'تکمیل الگو:\s*(\d+)%', analysis_text)
    if completion_match:
        details["pattern_completion"] = float(completion_match.group(1))
    
    # تشخیص سیگنال از وضعیت الگو
    if "فعال شده" in analysis_text or "شکست" in analysis_text:
        if "double bottom" in analysis_text.lower() or "دو کف" in analysis_text:
            details["signal_direction"] = "خرید"
            details["strength"] = "بسیار قوی"
        elif "double top" in analysis_text.lower() or "دو قله" in analysis_text:
            details["signal_direction"] = "فروش"
            details["strength"] = "بسیار قوی"
    elif "تشکیل شده" in analysis_text:
        details["signal_direction"] = "انتظار"
        details["strength"] = "متوسط"
    
    # استخراج هدف قیمتی
    target_match = re.search(r'هدف قیمتی:\s*([\d,]+\.?\d*)', analysis_text)
    if target_match:
        details["take_profit"] = float(target_match.group(1).replace(',', ''))
    
    return details

def _extract_ichimoku_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص ایچیموکو"""
    details = {}
    
    # تشخیص وضعیت ابر
    if "بالای ابر" in analysis_text:
        details["signal_direction"] = "خرید"
        details["strength"] = "قوی"
    elif "زیر ابر" in analysis_text:
        details["signal_direction"] = "فروش"
        details["strength"] = "قوی"
    elif "داخل ابر" in analysis_text:
        details["signal_direction"] = "خنثی"
        details["strength"] = "ضعیف"
    
    # استخراج خطوط ایچیموکو
    tenkan_match = re.search(r'tenkan[_\s]sen:\s*([\d,]+\.?\d*)', analysis_text, re.IGNORECASE)
    kijun_match = re.search(r'kijun[_\s]sen:\s*([\d,]+\.?\d*)', analysis_text, re.IGNORECASE)
    
    if tenkan_match:
        details["tenkan_sen"] = float(tenkan_match.group(1).replace(',', ''))
    if kijun_match:
        details["kijun_sen"] = float(kijun_match.group(1).replace(',', ''))
    
    return details

def _extract_fibonacci_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص فیبوناچی"""
    details = {}
    
    # استخراج سطوح فیبوناچی
    fib_levels = re.findall(r'(\d+\.?\d*)%.*?([\d,]+\.?\d*)', analysis_text)
    if fib_levels:
        details["fibonacci_levels"] = fib_levels
    
    # تشخیص بازگشت یا شکست
    if "بازگشت" in analysis_text:
        details["signal_direction"] = "خرید" if "صعودی" in analysis_text else "فروش"
        details["strength"] = "متوسط"
    elif "شکست" in analysis_text:
        details["signal_direction"] = "ادامه روند"
        details["strength"] = "قوی"
    
    return details

def _extract_bollinger_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص باندهای بولینگر"""
    details = {}
    
    if "باند بالا" in analysis_text:
        details["signal_direction"] = "فروش"
        details["strength"] = "متوسط"
    elif "باند پایین" in analysis_text:
        details["signal_direction"] = "خرید"
        details["strength"] = "متوسط"
    elif "باند میانی" in analysis_text:
        details["signal_direction"] = "خنثی"
        details["strength"] = "ضعیف"
    
    return details

def _extract_rsi_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص RSI"""
    details = {}
    
    # استخراج مقدار RSI
    rsi_match = re.search(r'rsi.*?:\s*(\d+\.?\d*)', analysis_text, re.IGNORECASE)
    if rsi_match:
        rsi_value = float(rsi_match.group(1))
        details["rsi_value"] = rsi_value
        
        if rsi_value > 70:
            details["signal_direction"] = "فروش"
            details["strength"] = "قوی"
        elif rsi_value < 30:
            details["signal_direction"] = "خرید"
            details["strength"] = "قوی"
        else:
            details["signal_direction"] = "خنثی"
            details["strength"] = "متوسط"
    
    return details

def _extract_macd_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص MACD"""
    details = {}
    
    if "تقاطع صعودی" in analysis_text or "بالای سیگنال" in analysis_text:
        details["signal_direction"] = "خرید"
        details["strength"] = "قوی"
    elif "تقاطع نزولی" in analysis_text or "زیر سیگنال" in analysis_text:
        details["signal_direction"] = "فروش"
        details["strength"] = "قوی"
    
    return details

def _extract_candlestick_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص کندل استیک"""
    details = {}
    
    # الگوهای کندلی صعودی
    bullish_patterns = ["hammer", "doji", "engulfing bullish", "morning star"]
    bearish_patterns = ["shooting star", "engulfing bearish", "evening star", "hanging man"]
    
    text_lower = analysis_text.lower()
    
    for pattern in bullish_patterns:
        if pattern in text_lower:
            details["signal_direction"] = "خرید"
            details["strength"] = "قوی"
            details["pattern_name"] = pattern
            break
    
    for pattern in bearish_patterns:
        if pattern in text_lower:
            details["signal_direction"] = "فروش"
            details["strength"] = "قوی"
            details["pattern_name"] = pattern
            break
    
    return details

def _extract_triangle_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص الگوی مثلث"""
    details = {}
    
    if "ascending triangle" in analysis_text.lower() or "مثلث صعودی" in analysis_text:
        details["signal_direction"] = "خرید"
        details["triangle_type"] = "ascending"
    elif "descending triangle" in analysis_text.lower() or "مثلث نزولی" in analysis_text:
        details["signal_direction"] = "فروش"
        details["triangle_type"] = "descending"
    elif "symmetrical triangle" in analysis_text.lower() or "مثلث متقارن" in analysis_text:
        details["signal_direction"] = "انتظار شکست"
        details["triangle_type"] = "symmetrical"
    
    return details

def _extract_wedge_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص الگوی گوه"""
    details = {}
    
    if "rising wedge" in analysis_text.lower() or "گوه صعودی" in analysis_text:
        details["signal_direction"] = "فروش"
        details["wedge_type"] = "rising"
    elif "falling wedge" in analysis_text.lower() or "گوه نزولی" in analysis_text:
        details["signal_direction"] = "خرید"
        details["wedge_type"] = "falling"
    
    return details

def _extract_diamond_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص الگوی الماس"""
    details = {}
    
    if "diamond top" in analysis_text.lower() or "الماس بالا" in analysis_text:
        details["signal_direction"] = "فروش"
        details["diamond_type"] = "top"
    elif "diamond bottom" in analysis_text.lower() or "الماس پایین" in analysis_text:
        details["signal_direction"] = "خرید"
        details["diamond_type"] = "bottom"
    
    return details

def _extract_head_shoulders_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص الگوی سر و شانه"""
    details = {}
    
    if "head and shoulders" in analysis_text.lower() or "سر و شانه" in analysis_text:
        details["signal_direction"] = "فروش"
        details["pattern_type"] = "head_shoulders"
    elif "inverse head and shoulders" in analysis_text.lower() or "سر و شانه معکوس" in analysis_text:
        details["signal_direction"] = "خرید"
        details["pattern_type"] = "inverse_head_shoulders"
    
    return details

def _extract_volume_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات مخصوص تحلیل حجم"""
    details = {}
    
    if "volume spike" in analysis_text.lower() or "افزایش حجم" in analysis_text:
        details["volume_status"] = "spike"
        details["strength"] = "قوی"
    elif "low volume" in analysis_text.lower() or "حجم کم" in analysis_text:
        details["volume_status"] = "low"
        details["strength"] = "ضعیف"
    
    return details

def _extract_general_details(analysis_text: str) -> Dict[str, Any]:
    """استخراج جزئیات عمومی از هر نوع تحلیل"""
    details = {}
    
    # تشخیص جهت کلی
    buy_words = ["خرید", "buy", "long", "صعودی", "بولیش"]
    sell_words = ["فروش", "sell", "short", "نزولی", "بریش"]
    neutral_words = ["خنثی", "neutral", "hold", "انتظار"]
    
    text_lower = analysis_text.lower()
    
    buy_count = sum(1 for word in buy_words if word in text_lower)
    sell_count = sum(1 for word in sell_words if word in text_lower)
    neutral_count = sum(1 for word in neutral_words if word in text_lower)
    
    if buy_count > sell_count and buy_count > neutral_count:
        details["signal_direction"] = "خرید"
    elif sell_count > buy_count and sell_count > neutral_count:
        details["signal_direction"] = "فروش"
    else:
        details["signal_direction"] = "خنثی"
    
    # استخراج قیمت‌ها (روش عمومی)
    prices = re.findall(r'[\d,]+\.?\d*', analysis_text)
    if prices:
        try:
            price_values = [float(p.replace(',', '')) for p in prices if p.replace(',', '').replace('.', '').isdigit()]
            if len(price_values) >= 3:
                details["entry_price"] = price_values[0]
                details["stop_loss"] = price_values[1] if len(price_values) > 1 else price_values[0] * 0.98
                details["take_profit"] = price_values[2] if len(price_values) > 2 else price_values[0] * 1.02
        except (ValueError, IndexError):
            pass
    
    # تشخیص قدرت عمومی
    if any(word in text_lower for word in ["قوی", "strong", "بسیار", "high"]):
        details["strength"] = "قوی"
        details["confidence"] = 80.0
    elif any(word in text_lower for word in ["ضعیف", "weak", "کم", "low"]):
        details["strength"] = "ضعیف"
        details["confidence"] = 40.0
    else:
        details["strength"] = "متوسط"
        details["confidence"] = 60.0
    
    return details

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