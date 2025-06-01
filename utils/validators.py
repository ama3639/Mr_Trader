"""
ماژول اعتبارسنجی - تأیید صحت داده‌های ورودی
"""

import re
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

class ValidationError(Exception):
    """خطای اعتبارسنجی"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class Validators:
    """کلاس اعتبارسنجی‌ها"""
    
    # الگوهای regex
    PHONE_PATTERN = re.compile(r'^(\+98|0)?9\d{9}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,32}$')
    REFERRAL_CODE_PATTERN = re.compile(r'^[A-Z0-9]{6,12}$')
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}$')
    CURRENCY_PATTERN = re.compile(r'^[A-Z]{3,10}$')
    TIMEFRAME_PATTERN = re.compile(r'^(1m|5m|15m|30m|1h|4h|1d|1w)$')
    
    # لیست ارزهای مجاز
    VALID_SYMBOLS = [
        'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'DOT', 'MATIC',
        'LINK', 'UNI', 'LTC', 'BCH', 'XLM', 'ATOM', 'TRX', 'AVAX', 'NEAR'
    ]
    
    VALID_CURRENCIES = ['USDT', 'BUSD', 'BTC', 'ETH', 'BNB', 'USD', 'EUR']
    
    VALID_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    
    VALID_STRATEGIES = [
        'price_action', 'simple_ma', 'rsi_basic', 'ichimoku', 'fibonacci',
        'macd', 'bollinger_bands', 'elliott_wave', 'harmonic_patterns',
        'volume_analysis', 'ai_predictions', 'market_sentiment'
    ]
    
    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        """اعتبارسنجی شناسه کاربر"""
        try:
            user_id = int(user_id)
            if user_id <= 0:
                raise ValidationError("user_id", "شناسه کاربر باید مثبت باشد")
            return user_id
        except (ValueError, TypeError):
            raise ValidationError("user_id", "شناسه کاربر باید عدد صحیح باشد")
    
    @staticmethod
    def validate_username(username: str) -> str:
        """اعتبارسنجی نام کاربری"""
        if not username:
            raise ValidationError("username", "نام کاربری نمی‌تواند خالی باشد")
        
        username = username.strip().replace('@', '')
        
        if not Validators.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "username", 
                "نام کاربری باید بین 3 تا 32 کاراکتر و شامل حروف انگلیسی، اعداد یا _ باشد"
            )
        
        return username
    
    @staticmethod
    def validate_email(email: str) -> str:
        """اعتبارسنجی ایمیل"""
        if not email:
            raise ValidationError("email", "ایمیل نمی‌تواند خالی باشد")
        
        try:
            validated_email = validate_email(email.strip())
            return validated_email.email
        except EmailNotValidError:
            raise ValidationError("email", "فرمت ایمیل نامعتبر است")
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """اعتبارسنجی شماره تلفن"""
        if not phone:
            raise ValidationError("phone", "شماره تلفن نمی‌تواند خالی باشد")
        
        phone = phone.strip().replace(' ', '').replace('-', '')
        
        if not Validators.PHONE_PATTERN.match(phone):
            raise ValidationError(
                "phone", 
                "شماره تلفن باید معتبر باشد (مثال: 09123456789)"
            )
        
        # تبدیل به فرمت استاندارد
        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('98'):
            phone = '0' + phone[2:]
        
        return phone
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name") -> str:
        """اعتبارسنجی نام"""
        if not name:
            raise ValidationError(field_name, f"{field_name} نمی‌تواند خالی باشد")
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationError(field_name, f"{field_name} باید حداقل 2 کاراکتر باشد")
        
        if len(name) > 50:
            raise ValidationError(field_name, f"{field_name} نباید بیش از 50 کاراکتر باشد")
        
        return name
    
    @staticmethod
    def validate_referral_code(code: str) -> str:
        """اعتبارسنجی کد رفرال"""
        if not code:
            raise ValidationError("referral_code", "کد رفرال نمی‌تواند خالی باشد")
        
        code = code.strip().upper()
        
        if not Validators.REFERRAL_CODE_PATTERN.match(code):
            raise ValidationError(
                "referral_code", 
                "کد رفرال باید بین 6 تا 12 کاراکتر و شامل حروف انگلیسی بزرگ و اعداد باشد"
            )
        
        return code
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """اعتبارسنجی نماد ارز"""
        if not symbol:
            raise ValidationError("symbol", "نماد ارز نمی‌تواند خالی باشد")
        
        symbol = symbol.strip().upper()
        
        if not Validators.SYMBOL_PATTERN.match(symbol):
            raise ValidationError(
                "symbol", 
                "نماد ارز باید بین 2 تا 10 کاراکتر و شامل حروف انگلیسی باشد"
            )
        
        # اختیاری: بررسی در لیست نمادهای مجاز
        # if symbol not in Validators.VALID_SYMBOLS:
        #     raise ValidationError("symbol", f"نماد {symbol} پشتیبانی نمی‌شود")
        
        return symbol
    
    @staticmethod
    def validate_currency(currency: str) -> str:
        """اعتبارسنجی ارز مرجع"""
        if not currency:
            raise ValidationError("currency", "ارز مرجع نمی‌تواند خالی باشد")
        
        currency = currency.strip().upper()
        
        if not Validators.CURRENCY_PATTERN.match(currency):
            raise ValidationError(
                "currency", 
                "ارز مرجع باید بین 3 تا 10 کاراکتر و شامل حروف انگلیسی باشد"
            )
        
        if currency not in Validators.VALID_CURRENCIES:
            raise ValidationError(
                "currency", 
                f"ارز {currency} پشتیبانی نمی‌شود. ارزهای مجاز: {', '.join(Validators.VALID_CURRENCIES)}"
            )
        
        return currency
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """اعتبارسنجی تایم‌فریم"""
        if not timeframe:
            raise ValidationError("timeframe", "تایم‌فریم نمی‌تواند خالی باشد")
        
        timeframe = timeframe.strip().lower()
        
        if timeframe not in Validators.VALID_TIMEFRAMES:
            raise ValidationError(
                "timeframe", 
                f"تایم‌فریم نامعتبر. تایم‌فریم‌های مجاز: {', '.join(Validators.VALID_TIMEFRAMES)}"
            )
        
        return timeframe
    
    @staticmethod
    def validate_strategy(strategy: str) -> str:
        """اعتبارسنجی استراتژی"""
        if not strategy:
            raise ValidationError("strategy", "استراتژی نمی‌تواند خالی باشد")
        
        strategy = strategy.strip().lower()
        
        if strategy not in Validators.VALID_STRATEGIES:
            raise ValidationError(
                "strategy", 
                f"استراتژی نامعتبر. استراتژی‌های مجاز: {', '.join(Validators.VALID_STRATEGIES)}"
            )
        
        return strategy
    
    @staticmethod
    def validate_amount(amount: Any, min_amount: float = 0.0) -> float:
        """اعتبارسنجی مبلغ"""
        try:
            amount = float(amount)
            if amount < min_amount:
                raise ValidationError("amount", f"مبلغ باید حداقل {min_amount} باشد")
            return amount
        except (ValueError, TypeError):
            raise ValidationError("amount", "مبلغ باید عدد معتبر باشد")
    
    @staticmethod
    def validate_package_type(package_type: str) -> str:
        """اعتبارسنجی نوع پکیج"""
        valid_packages = ['free', 'basic', 'premium', 'vip', 'ghost']
        
        if not package_type:
            raise ValidationError("package_type", "نوع پکیج نمی‌تواند خالی باشد")
        
        package_type = package_type.strip().lower()
        
        if package_type not in valid_packages:
            raise ValidationError(
                "package_type", 
                f"نوع پکیج نامعتبر. پکیج‌های مجاز: {', '.join(valid_packages)}"
            )
        
        return package_type
    
    @staticmethod
    def validate_subscription_duration(duration: str) -> str:
        """اعتبارسنجی مدت اشتراک"""
        valid_durations = ['monthly', 'quarterly', 'yearly', 'lifetime']
        
        if not duration:
            raise ValidationError("subscription_duration", "مدت اشتراک نمی‌تواند خالی باشد")
        
        duration = duration.strip().lower()
        
        if duration not in valid_durations:
            raise ValidationError(
                "subscription_duration", 
                f"مدت اشتراک نامعتبر. مدت‌های مجاز: {', '.join(valid_durations)}"
            )
        
        return duration
    
    @staticmethod
    def validate_date_string(date_str: str, field_name: str = "date") -> datetime:
        """اعتبارسنجی رشته تاریخ"""
        if not date_str:
            raise ValidationError(field_name, f"{field_name} نمی‌تواند خالی باشد")
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(field_name, f"فرمت {field_name} نامعتبر است")
    
    @staticmethod
    def validate_json_string(json_str: str, field_name: str = "json") -> Dict[str, Any]:
        """اعتبارسنجی رشته JSON"""
        if not json_str:
            return {}
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise ValidationError(field_name, f"فرمت JSON {field_name} نامعتبر است")
    
    @staticmethod
    def validate_text_length(text: str, 
                           min_length: int = 0, 
                           max_length: int = 1000, 
                           field_name: str = "text") -> str:
        """اعتبارسنجی طول متن"""
        if not text:
            text = ""
        
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(field_name, f"{field_name} باید حداقل {min_length} کاراکتر باشد")
        
        if len(text) > max_length:
            raise ValidationError(field_name, f"{field_name} نباید بیش از {max_length} کاراکتر باشد")
        
        return text
    
    @staticmethod
    def validate_url(url: str, field_name: str = "url") -> str:
        """اعتبارسنجی URL"""
        if not url:
            raise ValidationError(field_name, f"{field_name} نمی‌تواند خالی باشد")
        
        url = url.strip()
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError(field_name, f"{field_name} باید URL معتبر باشد")
        
        return url

class TradingValidators:
    """اعتبارسنجی‌های مربوط به معاملات"""
    
    @staticmethod
    def validate_price(price: Any, field_name: str = "price") -> float:
        """اعتبارسنجی قیمت"""
        try:
            price = float(price)
            if price <= 0:
                raise ValidationError(field_name, f"{field_name} باید مثبت باشد")
            return price
        except (ValueError, TypeError):
            raise ValidationError(field_name, f"{field_name} باید عدد معتبر باشد")
    
    @staticmethod
    def validate_percentage(percentage: Any, field_name: str = "percentage") -> float:
        """اعتبارسنجی درصد"""
        try:
            percentage = float(percentage)
            if not 0 <= percentage <= 100:
                raise ValidationError(field_name, f"{field_name} باید بین 0 تا 100 درصد باشد")
            return percentage
        except (ValueError, TypeError):
            raise ValidationError(field_name, f"{field_name} باید عدد معتبر باشد")
    
    @staticmethod
    def validate_signal_direction(direction: str) -> str:
        """اعتبارسنجی جهت سیگنال"""
        valid_directions = ['buy', 'sell', 'hold', 'neutral']
        
        if not direction:
            raise ValidationError("signal_direction", "جهت سیگنال نمی‌تواند خالی باشد")
        
        direction = direction.strip().lower()
        
        if direction not in valid_directions:
            raise ValidationError(
                "signal_direction", 
                f"جهت سیگنال نامعتبر. جهت‌های مجاز: {', '.join(valid_directions)}"
            )
        
        return direction
    
    @staticmethod
    def validate_risk_level(risk_level: str) -> str:
        """اعتبارسنجی سطح ریسک"""
        valid_levels = ['very_low', 'low', 'medium', 'high', 'very_high']
        
        if not risk_level:
            raise ValidationError("risk_level", "سطح ریسک نمی‌تواند خالی باشد")
        
        risk_level = risk_level.strip().lower()
        
        if risk_level not in valid_levels:
            raise ValidationError(
                "risk_level", 
                f"سطح ریسک نامعتبر. سطوح مجاز: {', '.join(valid_levels)}"
            )
        
        return risk_level
    
    @staticmethod
    def validate_trading_pair(symbol: str, currency: str) -> Tuple[str, str]:
        """اعتبارسنجی جفت معاملاتی"""
        symbol = Validators.validate_symbol(symbol)
        currency = Validators.validate_currency(currency)
        
        # بررسی عدم تکراری بودن
        if symbol == currency:
            raise ValidationError("trading_pair", "نماد و ارز مرجع نمی‌توانند یکسان باشند")
        
        return symbol, currency

class FormValidators:
    """اعتبارسنجی‌های فرم‌ها"""
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی ثبت‌نام کاربر"""
        validated_data = {}
        
        # شناسه کاربر (اجباری)
        validated_data['user_id'] = Validators.validate_user_id(data.get('user_id'))
        
        # نام کاربری (اختیاری)
        if data.get('username'):
            validated_data['username'] = Validators.validate_username(data['username'])
        
        # نام (اختیاری)
        if data.get('first_name'):
            validated_data['first_name'] = Validators.validate_name(data['first_name'], 'first_name')
        
        if data.get('last_name'):
            validated_data['last_name'] = Validators.validate_name(data['last_name'], 'last_name')
        
        # ایمیل (اختیاری)
        if data.get('email'):
            validated_data['email'] = Validators.validate_email(data['email'])
        
        # تلفن (اختیاری)
        if data.get('phone'):
            validated_data['phone'] = Validators.validate_phone(data['phone'])
        
        # کد رفرال (اختیاری)
        if data.get('referral_code'):
            validated_data['referral_code'] = Validators.validate_referral_code(data['referral_code'])
        
        return validated_data
    
    @staticmethod
    def validate_strategy_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی درخواست تحلیل استراتژی"""
        validated_data = {}
        
        # کاربر (اجباری)
        validated_data['user_id'] = Validators.validate_user_id(data.get('user_id'))
        
        # استراتژی (اجباری)
        validated_data['strategy'] = Validators.validate_strategy(data.get('strategy'))
        
        # نماد و ارز (اجباری)
        symbol, currency = TradingValidators.validate_trading_pair(
            data.get('symbol'), 
            data.get('currency')
        )
        validated_data['symbol'] = symbol
        validated_data['currency'] = currency
        
        # تایم‌فریم (اجباری)
        validated_data['timeframe'] = Validators.validate_timeframe(data.get('timeframe'))
        
        return validated_data
    
    @staticmethod
    def validate_package_purchase(data: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی خرید پکیج"""
        validated_data = {}
        
        # کاربر (اجباری)
        validated_data['user_id'] = Validators.validate_user_id(data.get('user_id'))
        
        # پکیج (اجباری)
        validated_data['package_type'] = Validators.validate_package_type(data.get('package_type'))
        
        # مدت اشتراک (اجباری)
        validated_data['subscription_duration'] = Validators.validate_subscription_duration(
            data.get('subscription_duration')
        )
        
        # مبلغ (اجباری)
        validated_data['amount'] = Validators.validate_amount(data.get('amount'), min_amount=0.01)
        
        return validated_data

def validate_with_schema(data: Dict[str, Any], 
                        schema: Dict[str, Any]) -> Dict[str, Any]:
    """اعتبارسنجی با استفاده از schema"""
    validated_data = {}
    errors = []
    
    for field, rules in schema.items():
        value = data.get(field)
        
        # بررسی اجباری بودن
        if rules.get('required', False) and not value:
            errors.append(ValidationError(field, f"{field} اجباری است"))
            continue
        
        # اگر مقدار وجود ندارد و اختیاری است
        if not value:
            if 'default' in rules:
                validated_data[field] = rules['default']
            continue
        
        try:
            # اعمال validator
            if 'validator' in rules:
                validated_data[field] = rules['validator'](value)
            else:
                validated_data[field] = value
                
        except ValidationError as e:
            errors.append(e)
    
    if errors:
        error_messages = [str(e) for e in errors]
        raise ValidationError("validation", "; ".join(error_messages))
    
    return validated_data

# نمونه schema برای اعتبارسنجی
USER_REGISTRATION_SCHEMA = {
    'user_id': {'required': True, 'validator': Validators.validate_user_id},
    'username': {'required': False, 'validator': Validators.validate_username},
    'first_name': {'required': False, 'validator': lambda x: Validators.validate_name(x, 'first_name')},
    'last_name': {'required': False, 'validator': lambda x: Validators.validate_name(x, 'last_name')},
    'email': {'required': False, 'validator': Validators.validate_email},
    'phone': {'required': False, 'validator': Validators.validate_phone},
    'referral_code': {'required': False, 'validator': Validators.validate_referral_code}
}

STRATEGY_REQUEST_SCHEMA = {
    'user_id': {'required': True, 'validator': Validators.validate_user_id},
    'strategy': {'required': True, 'validator': Validators.validate_strategy},
    'symbol': {'required': True, 'validator': Validators.validate_symbol},
    'currency': {'required': True, 'validator': Validators.validate_currency},
    'timeframe': {'required': True, 'validator': Validators.validate_timeframe}
}
