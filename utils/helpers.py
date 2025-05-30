"""
توابع کمکی عمومی برای MrTrader Bot
"""
import hashlib
import secrets
import string
import uuid
import random
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
import json
import base64
from urllib.parse import urlparse
import logging


logger = logging.getLogger(__name__)


class StringHelper:
    """توابع کمکی رشته"""
    
    @staticmethod
    def generate_random_string(length: int = 8, include_digits: bool = True, 
                             include_uppercase: bool = True, include_lowercase: bool = True) -> str:
        """تولید رشته تصادفی"""
        chars = ""
        if include_lowercase:
            chars += string.ascii_lowercase
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_digits:
            chars += string.digits
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_referral_code(user_id: int, length: int = 8) -> str:
        """تولید کد رفرال"""
        # ترکیب user_id با رشته تصادفی
        random_part = StringHelper.generate_random_string(length - 4, include_lowercase=False)
        user_part = str(user_id)[-4:].zfill(4)
        return f"{random_part}{user_part}"
    
    @staticmethod
    def generate_transaction_id(prefix: str = "TXN") -> str:
        """تولید شناسه تراکنش"""
        timestamp = int(datetime.now().timestamp())
        random_part = StringHelper.generate_random_string(6, include_lowercase=False)
        return f"{prefix}_{timestamp}_{random_part}"
    
    @staticmethod
    def generate_subscription_id() -> str:
        """تولید شناسه اشتراک"""
        return f"SUB_{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """کوتاه کردن متن"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """پاک‌سازی نام فایل"""
        # حذف کاراکترهای خطرناک
        dangerous_chars = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        return filename.strip()
    
    @staticmethod
    def extract_mention(text: str) -> Optional[str]:
        """استخراج منشن از متن"""
        import re
        pattern = r'@([a-zA-Z0-9_]{5,32})'
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """پنهان کردن داده حساس"""
        if len(data) <= visible_chars * 2:
            return '*' * len(data)
        
        return data[:visible_chars] + '*' * (len(data) - visible_chars * 2) + data[-visible_chars:]


class CryptoHelper:
    """توابع کمکی رمزنگاری"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """هش کردن رمز عبور"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """تولید کلید API"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """تولید کلید مخفی"""
        return secrets.token_hex(length)
    
    @staticmethod
    def encode_data(data: str) -> str:
        """رمزگذاری ساده داده"""
        return base64.b64encode(data.encode()).decode()
    
    @staticmethod
    def decode_data(encoded_data: str) -> str:
        """رمزگشایی داده"""
        try:
            return base64.b64decode(encoded_data.encode()).decode()
        except Exception:
            return ""
    
    @staticmethod
    def create_checksum(data: str) -> str:
        """ایجاد checksum"""
        return hashlib.md5(data.encode()).hexdigest()
    
    @staticmethod
    def verify_checksum(data: str, checksum: str) -> bool:
        """تأیید checksum"""
        return CryptoHelper.create_checksum(data) == checksum


class TimeHelper:
    """توابع کمکی زمان"""
    
    @staticmethod
    def get_timestamp() -> int:
        """دریافت timestamp فعلی"""
        return int(datetime.now().timestamp())
    
    @staticmethod
    def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
        """تبدیل timestamp به datetime"""
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def is_weekend(dt: datetime = None) -> bool:
        """بررسی آخر هفته"""
        if dt is None:
            dt = datetime.now()
        return dt.weekday() >= 5  # شنبه = 5, یکشنبه = 6
    
    @staticmethod
    def get_market_hours() -> Tuple[bool, str]:
        """بررسی ساعات کاری بازار"""
        now = datetime.now()
        
        # بازار کریپتو 24/7 فعال است
        if True:  # کریپتو
            return True, "بازار کریپتو همیشه فعال است"
        
        # برای بازارهای سنتی
        if TimeHelper.is_weekend(now):
            return False, "بازار در آخر هفته بسته است"
        
        # ساعات کاری 9 تا 17
        if 9 <= now.hour < 17:
            return True, "بازار فعال است"
        else:
            return False, "بازار در خارج از ساعات کاری است"
    
    @staticmethod
    def get_next_market_open() -> datetime:
        """زمان بازگشایی بعدی بازار"""
        now = datetime.now()
        
        # برای کریپتو همیشه باز است
        return now
    
    @staticmethod
    def add_business_days(start_date: datetime, days: int) -> datetime:
        """اضافه کردن روزهای کاری"""
        current_date = start_date
        added_days = 0
        
        while added_days < days:
            current_date += timedelta(days=1)
            if not TimeHelper.is_weekend(current_date):
                added_days += 1
        
        return current_date


class DataHelper:
    """توابع کمکی داده"""
    
    @staticmethod
    def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
        """دریافت ایمن از dictionary"""
        try:
            return dictionary.get(key, default)
        except (AttributeError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """تبدیل ایمن به int"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """تبدیل ایمن به float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_bool(value: Any, default: bool = False) -> bool:
        """تبدیل ایمن به bool"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        if isinstance(value, (int, float)):
            return bool(value)
        return default
    
    @staticmethod
    def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
        """ادغام عمیق دو dictionary"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataHelper.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """تخت کردن dictionary تودرتو"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataHelper.flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def group_by(data: List[Dict], key: str) -> Dict[str, List[Dict]]:
        """گروه‌بندی داده‌ها بر اساس کلید"""
        result = {}
        for item in data:
            group_key = str(DataHelper.safe_get(item, key, 'unknown'))
            if group_key not in result:
                result[group_key] = []
            result[group_key].append(item)
        return result


class FileHelper:
    """توابع کمکی فایل"""
    
    @staticmethod
    def safe_json_load(file_path: str) -> Optional[Dict]:
        """بارگذاری ایمن JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            return None
    
    @staticmethod
    def safe_json_save(data: Dict, file_path: str) -> bool:
        """ذخیره ایمن JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """دریافت اندازه فایل"""
        try:
            import os
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def ensure_directory(directory_path: str):
        """اطمینان از وجود دایرکتوری"""
        try:
            import os
            os.makedirs(directory_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")


class URLHelper:
    """توابع کمکی URL"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """بررسی اعتبار URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """استخراج دامنه از URL"""
        try:
            return urlparse(url).netloc
        except Exception:
            return None
    
    @staticmethod
    def build_query_string(params: Dict[str, Any]) -> str:
        """ساخت query string"""
        from urllib.parse import urlencode
        return urlencode({k: v for k, v in params.items() if v is not None})


class MathHelper:
    """توابع کمکی ریاضی"""
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """محاسبه درصد تغییر"""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def calculate_profit_loss(entry_price: float, exit_price: float, quantity: float) -> float:
        """محاسبه سود/زیان"""
        return (exit_price - entry_price) * quantity
    
    @staticmethod
    def calculate_win_rate(wins: int, total: int) -> float:
        """محاسبه نرخ موفقیت"""
        if total == 0:
            return 0.0
        return (wins / total) * 100
    
    @staticmethod
    def calculate_average(values: List[Union[int, float]]) -> float:
        """محاسبه میانگین"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def calculate_moving_average(values: List[float], period: int) -> List[float]:
        """محاسبه میانگین متحرک"""
        if len(values) < period:
            return []
        
        result = []
        for i in range(period - 1, len(values)):
            avg = sum(values[i - period + 1:i + 1]) / period
            result.append(avg)
        
        return result
    
    @staticmethod
    def normalize_value(value: float, min_val: float, max_val: float) -> float:
        """نرمال‌سازی مقدار بین 0 و 1"""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)


class AsyncHelper:
    """توابع کمکی async"""
    
    @staticmethod
    def retry_async(max_attempts: int = 3, delay: float = 1.0):
        """دکوریتور تلاش مجدد برای توابع async"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(delay * (attempt + 1))
                        else:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                
                raise last_exception
            
            return wrapper
        return decorator
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float):
        """اجرای coroutine با timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise
    
    @staticmethod
    async def gather_with_limit(tasks: List, limit: int = 10):
        """اجرای محدود تسک‌های همزمان"""
        semaphore = asyncio.Semaphore(limit)
        
        async def limited_task(task):
            async with semaphore:
                return await task
        
        limited_tasks = [limited_task(task) for task in tasks]
        return await asyncio.gather(*limited_tasks, return_exceptions=True)


class CacheHelper:
    """توابع کمکی کش"""
    
    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """تولید کلید کش"""
        # ترکیب تمام آرگومان‌ها برای ساخت کلید یکتا
        key_parts = []
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def is_cache_expired(cache_time: datetime, ttl_seconds: int) -> bool:
        """بررسی انقضای کش"""
        return datetime.now() > cache_time + timedelta(seconds=ttl_seconds)


class ValidationHelper:
    """توابع کمکی اعتبارسنجی"""
    
    @staticmethod
    def is_valid_telegram_id(telegram_id: Union[int, str]) -> bool:
        """بررسی اعتبار شناسه تلگرام"""
        try:
            telegram_id = int(telegram_id)
            return 1 <= telegram_id <= 9007199254740991
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_positive_number(value: Union[int, float, str]) -> bool:
        """بررسی عدد مثبت"""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_percentage(value: Union[int, float, str]) -> bool:
        """بررسی درصد معتبر"""
        try:
            val = float(value)
            return 0 <= val <= 100
        except (ValueError, TypeError):
            return False


class DebugHelper:
    """توابع کمکی دیباگ"""
    
    @staticmethod
    def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None):
        """لاگ فراخوانی تابع"""
        args_str = str(args) if args else "()"
        kwargs_str = str(kwargs) if kwargs else "{}"
        logger.debug(f"Function call: {func_name}{args_str} {kwargs_str}")
    
    @staticmethod
    def measure_time(func: Callable):
        """دکوریتور اندازه‌گیری زمان اجرا"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"Function {func.__name__} took {duration:.3f} seconds")
            return result
        return wrapper
    
    @staticmethod
    async def measure_time_async(func: Callable):
        """دکوریتور اندازه‌گیری زمان برای توابع async"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = await func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"Async function {func.__name__} took {duration:.3f} seconds")
            return result
        return wrapper


# Export
__all__ = [
    'StringHelper',
    'CryptoHelper', 
    'TimeHelper',
    'DataHelper',
    'FileHelper',
    'URLHelper',
    'MathHelper',
    'AsyncHelper',
    'CacheHelper',
    'ValidationHelper',
    'DebugHelper'
]