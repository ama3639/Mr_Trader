"""
قالب‌های پیام - مدیریت متن‌ها و پیام‌های سیستم
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.time_manager import TimeManager
from utils.helpers import format_currency, format_percentage

class MessageTemplates:
    """کلاس قالب‌های پیام"""
    
    @staticmethod
    def welcome_message(user_name: str, is_new_user: bool = True) -> str:
        """پیام خوش‌آمدگویی"""
        if is_new_user:
            return f"""🎉 **خوش آمدید به MrTrader Bot!**
━━━━━━━━━━━━━━━━━━━━━━

سلام {user_name} عزیز! 👋

🚀 **شما به دنیای تحلیل حرفه‌ای ارزهای دیجیتال خوش آمدید!**

🔥 **امکانات MrTrader Bot:**
📊 35+ استراتژی تحلیل تکنیکال
💰 قیمت‌های زنده صرافی‌ها
📈 سیگنال‌های معاملاتی دقیق
🎯 گزارش‌های تخصصی

💡 **برای شروع:**
• روی دکمه "📊 استراتژی‌ها" کلیک کنید
• پکیج مناسب خود را انتخاب کنید
• از تحلیل‌های حرفه‌ای لذت ببرید

⚠️ **توجه:** تمام تحلیل‌ها صرفاً جنبه آموزشی داشته و توصیه سرمایه‌گذاری محسوب نمی‌شوند.

🎁 **هدیه ویژه:** 5 تحلیل رایگان برای شروع!"""
        else:
            return f"""👋 **خوش برگشتید {user_name}!**
━━━━━━━━━━━━━━━━━━━━━━

خوشحالیم که دوباره با ما هستید! 🎊

🕒 آخرین بازدید: `{TimeManager.to_shamsi(datetime.now())}`

🚀 آماده تحلیل‌های جدید هستید؟"""
    
    @staticmethod
    def strategy_intro(strategy_name: str, user_package: str) -> str:
        """معرفی استراتژی"""
        strategy_descriptions = {
            # استراتژی‌های دمو
            "demo_price_action": {
                "name": "دمو پرایس اکشن",
                "description": "نسخه دمو تحلیل حرکت قیمت - محدود به 5 تحلیل در روز",
                "features": ["تحلیل کندل‌های اصلی", "شناسایی روند کلی", "نقاط حمایت و مقاومت ساده"]
            },
            "demo_rsi": {
                "name": "دمو RSI",
                "description": "نسخه دمو شاخص قدرت نسبی - محدود به 5 تحلیل در روز",
                "features": ["شناسایی اشباع خرید/فروش", "سیگنال‌های ساده", "آموزش مفاهیم پایه"]
            },
            
            # استراتژی‌های BASIC
            "cci_analysis": {
                "name": "تحلیل CCI",
                "description": "شاخص کانال کالا برای تشخیص نقاط اشباع خرید و فروش",
                "features": ["تشخیص اشباع بازار", "نقاط ورود بهینه", "سیگنال‌های برگشت روند"]
            },
            "ema_analysis": {
                "name": "تحلیل EMA",
                "description": "میانگین متحرک نمایی برای تشخیص روند و نقاط ورود",
                "features": ["تشخیص روند اصلی", "سیگنال‌های عبور", "نقاط ورود دقیق"]
            },
            "ichimoku": {
                "name": "ابر ایچیموکو",
                "description": "سیستم جامع تحلیل ژاپنی برای تعیین روند و نقاط ورود",
                "features": ["تشخیص روند", "ابر ایچیموکو", "خطوط حمایت و مقاومت پویا"]
            },
            "rsi": {
                "name": "تحلیل RSI",
                "description": "شاخص قدرت نسبی برای شناسایی شرایط اشباع",
                "features": ["تشخیص واگرایی‌ها", "نقاط اشباع", "سیگنال‌های خرید و فروش"]
            },
            
            # استراتژی‌های PREMIUM
            "momentum": {
                "name": "تحلیل مومنتوم",
                "description": "تحلیل قدرت و سرعت حرکت قیمت برای شناسایی روندهای قوی",
                "features": ["قدرت حرکت قیمت", "سرعت تغییرات", "نقاط شتاب و کاهش سرعت"]
            },
            "double_top_pattern": {
                "name": "الگوی دو قله",
                "description": "شناسایی الگوهای دو قله و دو کف برای پیش‌بینی برگشت روند",
                "features": ["تشخیص الگوی کلاسیک", "نقاط شکست", "اهداف قیمتی دقیق"]
            },
            "fibonacci_strategy": {
                "name": "استراتژی فیبوناچی",
                "description": "استفاده از سطوح فیبوناچی ریتریسمنت برای نقاط ورود",
                "features": ["سطوح بازگشت", "نقاط حمایت پویا", "اهداف فیبوناچی"]
            },
            "bollinger_bands": {
                "name": "باندهای بولینگر",
                "description": "باندهای بولینگر برای تحلیل نوسانات و نقاط ورود",
                "features": ["تحلیل نوسانات", "نقاط اشباع", "شکست از باندها"]
            },
            
            # استراتژی‌های VIP
            "volume_profile": {
                "name": "پروفایل حجم",
                "description": "تحلیل پروفایل حجم معاملات برای شناسایی نواحی مهم",
                "features": ["نواحی حجم بالا", "نقاط ارزش منصفانه", "سطوح کنترل قیمت"]
            },
            "diamond_pattern": {
                "name": "الگوی الماس",
                "description": "تشخیص الگوی نادر و قوی الماس برای پیش‌بینی‌های دقیق",
                "features": ["الگوی نادر", "دقت بالا", "نقاط برگشت مهم"]
            },
            "multi_level_resistance": {
                "name": "مقاومت چند سطحی",
                "description": "تحلیل چند سطحی حمایت و مقاومت برای درک عمیق بازار",
                "features": ["تحلیل چند بعدی", "سطوح متعدد", "قدرت نواحی"]
            }
        }
        
        strategy_info = strategy_descriptions.get(strategy_name, {
            "name": strategy_name.replace('_', ' ').title(),
            "description": "استراتژی پیشرفته تحلیل تکنیکال",
            "features": ["تحلیل دقیق", "سیگنال‌های معتبر", "نقاط ورود مناسب"]
        })
        
        message = f"""📊 **استراتژی {strategy_info['name']}**
━━━━━━━━━━━━━━━━━━━━━━

📝 **توضیحات:**
{strategy_info['description']}

✨ **ویژگی‌های کلیدی:**"""
        
        for feature in strategy_info['features']:
            message += f"\n• {feature}"
        
        if user_package == "free":
            message += f"""

⚠️ **محدودیت پکیج رایگان:**
• 5 تحلیل رایگان در روز
• دسترسی محدود به تایم‌فریم‌ها
• بدون ذخیره گزارش‌ها

💎 برای دسترسی کامل، پکیج خود را ارتقا دهید!"""
        
        return message
    
    @staticmethod
    def analysis_result(symbol: str, currency: str, timeframe: str, 
                       signal_details: Dict[str, Any], current_price: float, 
                       strategy_type: str = "general") -> str:
        """نتیجه تحلیل با قالب‌بندی بر اساس نوع استراتژی"""
        # تبدیل تایم‌فریم به فارسی
        timeframe_fa = {
            "1m": "۱ دقیقه", "5m": "۵ دقیقه", "15m": "۱۵ دقیقه", "30m": "۳۰ دقیقه",
            "1h": "۱ ساعت", "4h": "۴ ساعت", "1d": "۱ روز", "1w": "۱ هفته"
        }.get(timeframe, timeframe)
        
        # ایموجی بر اساس جهت سیگنال
        direction_emoji = {
            "خرید": "🟢", "buy": "🟢", "فروش": "🔴", "sell": "🔴", 
            "خنثی": "🟡", "neutral": "🟡", "انتظار": "⚪", "hold": "⚪"
        }.get(signal_details.get('signal_direction', 'neutral').lower(), "⚪")
        
        # قدرت سیگنال
        strength_emoji = {
            "قوی": "💪", "strong": "💪", "بسیار قوی": "🔥",
            "متوسط": "👌", "medium": "👌", "ضعیف": "🤏", "weak": "🤏"
        }.get(signal_details.get('strength', 'متوسط').lower(), "👌")
        
        # قالب‌بندی بر اساس نوع استراتژی
        if strategy_type == "momentum":
            return MessageTemplates._format_momentum_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "pattern":
            return MessageTemplates._format_pattern_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "ichimoku":
            return MessageTemplates._format_ichimoku_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "fibonacci":
            return MessageTemplates._format_fibonacci_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "bollinger":
            return MessageTemplates._format_bollinger_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "rsi":
            return MessageTemplates._format_rsi_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "volume":
            return MessageTemplates._format_volume_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        elif strategy_type == "candlestick":
            return MessageTemplates._format_candlestick_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
        else:
            return MessageTemplates._format_general_result(
                symbol, currency, timeframe_fa, signal_details, current_price, direction_emoji, strength_emoji
            )
    
    @staticmethod
    def _format_momentum_result(symbol: str, currency: str, timeframe_fa: str, 
                               signal_details: Dict[str, Any], current_price: float, 
                               direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج مومنتوم"""
        rr_ratio = signal_details.get('risk_reward_ratio', 0.0)
        
        return f"""⚡ **سیگنال مومنتوم {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت مومنتوم: {signal_details.get('strength', 'متوسط')}**

💰 **استراتژی مومنتوم:**
🎯 نقطه ورود: `{signal_details.get('entry_price', 0):,.4f}`
🛑 حد ضرر: `{signal_details.get('stop_loss', 0):,.4f}`
💎 هدف قیمتی: `{signal_details.get('take_profit', 0):,.4f}`
⚖️ نسبت ریسک/ریوارد: `{rr_ratio:.2f}`

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_pattern_result(symbol: str, currency: str, timeframe_fa: str, 
                              signal_details: Dict[str, Any], current_price: float, 
                              direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج الگوها"""
        pattern_confidence = signal_details.get('pattern_confidence', 0.0)
        completion = signal_details.get('pattern_completion', 0.0)
        
        return f"""🎯 **تحلیل الگوی {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت الگو: {signal_details.get('strength', 'متوسط')}**

🔍 **جزئیات الگو:**
📊 اطمینان الگو: `{pattern_confidence:.0f}%`
⚙️ تکمیل الگو: `{completion:.0f}%`
💎 هدف قیمتی: `{signal_details.get('take_profit', 0):,.4f}`

📈 **تحلیل تکنیکال:**
🔻 حمایت: `{signal_details.get('support', 0):,.4f}`
🔺 مقاومت: `{signal_details.get('resistance', 0):,.4f}`

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_ichimoku_result(symbol: str, currency: str, timeframe_fa: str, 
                               signal_details: Dict[str, Any], current_price: float, 
                               direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج ایچیموکو"""
        return f"""☁️ **تحلیل ایچیموکو {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت سیگنال: {signal_details.get('strength', 'متوسط')}**

☁️ **سیستم ایچیموکو:**
📊 وضعیت ابر: `{signal_details.get('cloud_status', 'نامشخص')}`
📈 خط تبدیل: `{signal_details.get('tenkan_sen', 0):,.4f}`
📉 خط پایه: `{signal_details.get('kijun_sen', 0):,.4f}`

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_fibonacci_result(symbol: str, currency: str, timeframe_fa: str, 
                                signal_details: Dict[str, Any], current_price: float, 
                                direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج فیبوناچی"""
        fib_levels = signal_details.get('fibonacci_levels', [])
        
        fib_text = ""
        for level in fib_levels[:3]:  # نمایش 3 سطح اول
            if isinstance(level, tuple) and len(level) >= 2:
                fib_text += f"• {level[0]}%: `{level[1]:,.4f}`\n"
        
        return f"""🌊 **تحلیل فیبوناچی {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت سیگنال: {signal_details.get('strength', 'متوسط')}**

🌊 **سطوح فیبوناچی:**
{fib_text if fib_text else "• سطوح در حال محاسبه..."}

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_bollinger_result(symbol: str, currency: str, timeframe_fa: str, 
                                signal_details: Dict[str, Any], current_price: float, 
                                direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج بولینگر"""
        return f"""📊 **تحلیل بولینگر {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت سیگنال: {signal_details.get('strength', 'متوسط')}**

📊 **باندهای بولینگر:**
🔺 باند بالا: `{signal_details.get('upper_band', 0):,.4f}`
📊 باند میانی: `{signal_details.get('middle_band', 0):,.4f}`
🔻 باند پایین: `{signal_details.get('lower_band', 0):,.4f}`

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_rsi_result(symbol: str, currency: str, timeframe_fa: str, 
                          signal_details: Dict[str, Any], current_price: float, 
                          direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج RSI"""
        rsi_value = signal_details.get('rsi_value', 50)
        
        return f"""📈 **تحلیل RSI {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت سیگنال: {signal_details.get('strength', 'متوسط')}**

📊 **شاخص RSI:**
📈 مقدار RSI: `{rsi_value:.2f}`
{'🔴 اشباع خرید' if rsi_value > 70 else '🟢 اشباع فروش' if rsi_value < 30 else '🟡 ناحیه عادی'}

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_volume_result(symbol: str, currency: str, timeframe_fa: str, 
                             signal_details: Dict[str, Any], current_price: float, 
                             direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج تحلیل حجم"""
        volume_status = signal_details.get('volume_status', 'normal')
        
        return f"""📊 **تحلیل حجم {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت سیگنال: {signal_details.get('strength', 'متوسط')}**

📊 **تحلیل حجم:**
📈 وضعیت حجم: `{volume_status}`
💰 ناحیه ارزش: `{signal_details.get('value_area', 'نامشخص')}`
🎯 سطح کنترل: `{signal_details.get('poc', 0):,.4f}`

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_candlestick_result(symbol: str, currency: str, timeframe_fa: str, 
                                  signal_details: Dict[str, Any], current_price: float, 
                                  direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی نتایج کندل استیک"""
        pattern_name = signal_details.get('pattern_name', 'نامشخص')
        
        return f"""🕯️ **تحلیل کندل استیک {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت الگو: {signal_details.get('strength', 'متوسط')}**

🕯️ **الگوی کندلی:**
📛 نام الگو: `{pattern_name}`
🎯 نوع سیگنال: `{signal_details.get('signal_type', 'نامشخص')}`

📊 **اعتماد: {signal_details.get('confidence', 50):.0f}%**

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def _format_general_result(symbol: str, currency: str, timeframe_fa: str, 
                              signal_details: Dict[str, Any], current_price: float, 
                              direction_emoji: str, strength_emoji: str) -> str:
        """قالب‌بندی عمومی نتایج"""
        return f"""🎯 **سیگنال معاملاتی {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

📊 **اطلاعات کلی:**
⏱ تایم‌فریم: `{timeframe_fa}`
💵 قیمت فعلی: `{current_price:,.4f} {currency}`
🕒 زمان تحلیل: `{TimeManager.to_shamsi(datetime.now())}`

{direction_emoji} **سیگنال: {signal_details.get('signal_direction', 'نامشخص').upper()}**
{strength_emoji} **قدرت: {signal_details.get('strength', 'متوسط')}**

💰 **سطوح کلیدی:**
🎯 نقطه ورود: `{signal_details.get('entry_price', 0):,.4f}`
🛑 حد ضرر: `{signal_details.get('stop_loss', 0):,.4f}`
💎 هدف قیمتی: `{signal_details.get('take_profit', 0):,.4f}`

📈 **تحلیل تکنیکال:**
🔻 حمایت: `{signal_details.get('support', 0):,.4f}`
🔺 مقاومت: `{signal_details.get('resistance', 0):,.4f}`
📊 اعتماد: `{signal_details.get('confidence', 50):.0f}%`

⚠️ **یادآوری مهم:** این تحلیل صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری محسوب نمی‌شود."""
    
    @staticmethod
    def package_details(package: Dict[str, Any]) -> str:
        """جزئیات پکیج"""
        features_text = ""
        features = package.get('features', {})
        
        if features.get('strategies'):
            features_text += f"📊 استراتژی‌ها: `{len(features['strategies'])} مورد`\n"
        if features.get('max_daily_requests'):
            features_text += f"📈 درخواست روزانه: `{features['max_daily_requests']:,}`\n"
        if features.get('has_live_support'):
            features_text += f"🎧 پشتیبانی زنده: `✅`\n"
        if features.get('has_priority_support'):
            features_text += f"⚡ پشتیبانی اولویت‌دار: `✅`\n"
        if features.get('has_advanced_analytics'):
            features_text += f"📊 تحلیل پیشرفته: `✅`\n"
        if features.get('has_portfolio_tracking'):
            features_text += f"💼 ردیابی پرتفو: `✅`\n"
        if features.get('concurrent_analyses'):
            features_text += f"🔄 تحلیل همزمان: `{features['concurrent_analyses']} مورد`\n"
        
        return f"""💎 **پکیج {package.get('title', 'نامشخص')}**
━━━━━━━━━━━━━━━━━━━━━━

📝 **توضیحات:**
{package.get('description', 'بدون توضیحات')}

✨ **ویژگی‌ها:**
{features_text}

💰 **قیمت‌گذاری:**
📅 ماهانه: `${package.get('pricing', {}).get('monthly_price', 0):.2f}`
📅 فصلی: `${package.get('pricing', {}).get('quarterly_price', 0):.2f}`
📅 سالانه: `${package.get('pricing', {}).get('yearly_price', 0):.2f}`

🎯 **مناسب برای:** کاربرانی که به دنبال {package.get('title', 'پکیج')} هستند"""
    
    @staticmethod
    def user_profile(user_info: Dict[str, Any]) -> str:
        """پروفایل کاربر"""
        current_package = user_info.get('current_package', {})
        stats = user_info.get('stats', {})
        
        return f"""👤 **پروفایل کاربری**
━━━━━━━━━━━━━━━━━━━━━━

🆔 **اطلاعات کلی:**
👤 نام: `{user_info.get('full_name', 'نامشخص')}`
🆔 شناسه: `{user_info.get('user_id', 'نامشخص')}`
📅 عضویت: `{user_info.get('registration_date', 'نامشخص')}`
🕒 آخرین بازدید: `{user_info.get('last_login', 'نامشخص')}`

📦 **پکیج فعلی:**
💎 نوع: `{current_package.get('package_type', 'Free').upper()}`
📅 انقضا: `{current_package.get('expiry_date', 'نامشخص')}`
📊 روزهای باقی‌مانده: `{current_package.get('days_remaining', 0)} روز`

📊 **آمار استفاده:**
📈 کل درخواست‌ها: `{stats.get('total_signals_requested', 0):,}`
✅ تحلیل‌های موفق: `{stats.get('successful_analyses', 0):,}`
📄 گزارش‌های تولیدی: `{stats.get('total_reports_generated', 0):,}`
🎯 نرخ موفقیت: `{stats.get('success_rate', 0):.1f}%`

⭐ **استراتژی‌های محبوب:**
{', '.join(stats.get('favorite_strategies', ['هنوز استفاده نشده'])[:3])}"""
    
    @staticmethod
    def payment_invoice(transaction_info: Dict[str, Any]) -> str:
        """فاکتور پرداخت"""
        return f"""🧾 **فاکتور پرداخت**
━━━━━━━━━━━━━━━━━━━━━━

🆔 **شماره فاکتور:** `{transaction_info.get('invoice_id', 'نامشخص')}`
📅 **تاریخ صدور:** `{TimeManager.to_shamsi(datetime.now())}`

📦 **جزئیات خرید:**
نام محصول: `{transaction_info.get('package_name', 'نامشخص')}`
مدت زمان: `{transaction_info.get('subscription_duration', 'نامشخص')}`

💰 **جزئیات مالی:**
مبلغ اصلی: `${transaction_info.get('amount', 0):.2f}`
مالیات: `${transaction_info.get('tax_amount', 0):.2f}`
تخفیف: `${transaction_info.get('discount_amount', 0):.2f}`
━━━━━━━━━━━━━━━━━━━━━━
مبلغ نهایی: `${transaction_info.get('final_amount', 0):.2f}`

💳 **روش پرداخت:** {transaction_info.get('payment_method', 'نامشخص')}
⏰ **مهلت پرداخت:** {transaction_info.get('time_remaining_minutes', 0)} دقیقه

⚠️ **توجه:** این فاکتور پس از پرداخت معتبر خواهد بود."""
    
    @staticmethod
    def error_message(error_type: str, details: str = "") -> str:
        """پیام خطا"""
        error_messages = {
            "access_denied": "⛔ **دسترسی غیرمجاز**\n\nشما دسترسی لازم برای این عملیات را ندارید.",
            "package_expired": "⏰ **پکیج منقضی شده**\n\nپکیج شما منقضی شده است. لطفاً پکیج خود را تمدید کنید.",
            "api_error": "🔧 **خطای سرویس**\n\nمتأسفانه در دریافت اطلاعات مشکلی پیش آمد. لطفاً بعداً تلاش کنید.",
            "invalid_input": "❌ **ورودی نامعتبر**\n\nاطلاعات وارد شده صحیح نیست. لطفاً دوباره تلاش کنید.",
            "rate_limit": "⏳ **محدودیت درخواست**\n\nشما زیاد درخواست ارسال کرده‌اید. لطفاً کمی صبر کنید.",
            "maintenance": "🔧 **در حال تعمیر**\n\nسیستم در حال به‌روزرسانی است. لطفاً بعداً مراجعه کنید.",
            "strategy_not_found": "❌ **استراتژی یافت نشد**\n\nاستراتژی درخواستی موجود نیست یا غیرفعال است.",
            "symbol_not_supported": "❌ **نماد پشتیبانی نمی‌شود**\n\nنماد وارد شده در لیست نمادهای پشتیبانی شده نیست.",
            "timeframe_not_allowed": "❌ **تایم‌فریم مجاز نیست**\n\nتایم‌فریم انتخابی برای پکیج شما مجاز نیست."
        }
        
        base_message = error_messages.get(error_type, "❌ **خطای غیرمنتظره**\n\nمتأسفانه مشکلی پیش آمد.")
        
        if details:
            base_message += f"\n\n**جزئیات:** {details}"
        
        return base_message
    
    @staticmethod
    def success_message(action: str, details: str = "") -> str:
        """پیام موفقیت"""
        success_messages = {
            "package_activated": "🎉 **پکیج فعال شد!**\n\nپکیج شما با موفقیت فعال شد.",
            "payment_completed": "✅ **پرداخت موفق**\n\nپرداخت شما با موفقیت انجام شد.",
            "profile_updated": "✅ **پروفایل به‌روزرسانی شد**\n\nاطلاعات شما با موفقیت ذخیره شد.",
            "settings_saved": "✅ **تنظیمات ذخیره شد**\n\nتنظیمات جدید اعمال شد.",
            "backup_created": "💾 **پشتیبان ایجاد شد**\n\nپشتیبان‌گیری با موفقیت انجام شد.",
            "analysis_completed": "✅ **تحلیل تکمیل شد**\n\nتحلیل با موفقیت انجام شد.",
            "alert_set": "🔔 **هشدار تنظیم شد**\n\nهشدار شما با موفقیت ثبت شد."
        }
        
        base_message = success_messages.get(action, "✅ **عملیات موفق**\n\nعملیات با موفقیت انجام شد.")
        
        if details:
            base_message += f"\n\n{details}"
        
        return base_message
    
    @staticmethod
    def help_message(topic: str) -> str:
        """پیام‌های راهنما"""
        help_topics = {
            "getting_started": """🚀 **راهنمای شروع کار**
━━━━━━━━━━━━━━━━━━━━━━

👋 **خوش آمدید به MrTrader Bot!**

📚 **قدم‌های اولیه:**
1️⃣ ثبت‌نام و ایجاد حساب کاربری
2️⃣ انتخاب پکیج مناسب
3️⃣ شروع تحلیل اولین ارز دیجیتال

📊 **نحوه دریافت تحلیل:**
• روی "📊 استراتژی‌ها" کلیک کنید
• استراتژی مورد نظر را انتخاب کنید
• ارز و جفت ارز را مشخص کنید
• تایم‌فریم دلخواه را انتخاب کنید

💡 **نکات مهم:**
• همیشه چند استراتژی را بررسی کنید
• تحلیل‌ها جنبه آموزشی دارند
• مدیریت ریسک را فراموش نکنید""",
            
            "strategies": """📊 **راهنمای استراتژی‌ها**
━━━━━━━━━━━━━━━━━━━━━━

🔍 **انواع استراتژی‌ها:**

🥉 **BASIC (9 استراتژی):**
📈 CCI، EMA، Ichimoku، MACD، RSI
📊 Price Action، Williams R
💰 Live Binance، Ichimoku Low

🥈 **PREMIUM (26 استراتژی):**
📊 همه استراتژی‌های Basic +
🕯️ Candlestick، Pivot، Bollinger
🎯 Cup Handle، Double Top، Fibonacci
📈 Momentum، Head & Shoulders، Triangle

👑 **VIP (35 استراتژی):**
📊 همه استراتژی‌های قبلی +
💎 Diamond، ATR، Volume Profile
🎯 Multi-level Resistance، VWAP
📈 CRT، P3، RTM""",
            
            "packages": """💎 **راهنمای پکیج‌ها**
━━━━━━━━━━━━━━━━━━━━━━

🆓 **رایگان:**
• 5 تحلیل دمو در روز
• 2 استراتژی دمو
• تایم‌فریم محدود

🥉 **بیسیک (50,000 تومان/ماه):**
• 10 درخواست در دقیقه
• 9 استراتژی اصلی
• همه تایم‌فریم‌ها (به جز 1m، 3m)

🥈 **پریمیوم (150,000 تومان/ماه):**
• 20 درخواست در دقیقه
• 26 استراتژی
• همه تایم‌فریم‌ها
• پشتیبانی زنده

👑 **VIP (350,000 تومان/ماه):**
• 30 درخواست در دقیقه
• 35 استراتژی
• همه امکانات
• پشتیبانی اولویت‌دار"""
        }
        
        return help_topics.get(topic, "📚 **راهنما**\n\nموضوع راهنمای درخواستی یافت نشد.")
    
    @staticmethod
    def processing_message(step: str, symbol: str = "", strategy: str = "") -> str:
        """پیام در حال پردازش"""
        messages = {
            "analyzing": f"🔄 **در حال تحلیل {symbol}...**\n\nلطفاً کمی صبر کنید...",
            "fetching_data": f"📡 **دریافت داده‌ها...**\n\nاتصال به سرور تحلیل...",
            "processing": f"⚙️ **پردازش اطلاعات...**\n\nتحلیل با استراتژی {strategy} در حال انجام...",
            "generating_report": "📄 **تولید گزارش...**\n\nآماده‌سازی نتایج نهایی...",
            "caching": "💾 **ذخیره‌سازی...**\n\nذخیره نتایج در کش سیستم..."
        }
        
        return messages.get(step, "⏳ در حال پردازش...")

class AdminMessages:
    """پیام‌های مخصوص ادمین"""
    
    @staticmethod
    def admin_stats_summary(stats: Dict[str, Any]) -> str:
        """خلاصه آمار ادمین"""
        return f"""📊 **خلاصه آمار سیستم**
━━━━━━━━━━━━━━━━━━━━━━

👥 **کاربران:**
• کل: `{stats.get('total_users', 0):,}`
• فعال امروز: `{stats.get('active_today', 0):,}`
• جدید امروز: `{stats.get('new_today', 0):,}`

💰 **درآمد:**
• امروز: `${stats.get('revenue_today', 0):,.2f}`
• این ماه: `${stats.get('revenue_month', 0):,.2f}`
• کل: `${stats.get('revenue_total', 0):,.2f}`

📈 **استفاده:**
• درخواست‌های امروز: `{stats.get('requests_today', 0):,}`
• تحلیل‌های موفق: `{stats.get('successful_analyses', 0):,}`
• نرخ موفقیت: `{stats.get('success_rate', 0):.1f}%`

🔧 **سیستم:**
• آپتایم: `{stats.get('uptime', '99.9%')}`
• حافظه استفاده شده: `{stats.get('memory_usage', 'N/A')}`
• CPU: `{stats.get('cpu_usage', 'N/A')}`

📊 **استراتژی‌های محبوب:**
{chr(10).join([f"• {k}: {v} بار" for k, v in stats.get('popular_strategies', {}).items()][:5])}"""
    
    @staticmethod
    def broadcast_confirmation(target_count: int, message_preview: str) -> str:
        """تأیید ارسال پیام گروهی"""
        return f"""📤 **تأیید ارسال پیام گروهی**
━━━━━━━━━━━━━━━━━━━━━━

👥 **تعداد مخاطب:** `{target_count:,} کاربر`

📝 **پیش‌نمایش پیام:**
{message_preview[:200]}{"..." if len(message_preview) > 200 else ""}

⚠️ **توجه:** این پیام برای همه کاربران ارسال خواهد شد.

❓ آیا از ارسال اطمینان دارید؟"""

class NotificationTemplates:
    """قالب‌های اطلاع‌رسانی"""
    
    @staticmethod
    def format_price_alert(symbol: str, currency: str, 
                          current_price: float, target_price: float,
                          alert_type: str) -> str:
        """فرمت هشدار قیمت"""
        emoji = "🔺" if alert_type == "above" else "🔻"
        direction = "بالاتر از" if alert_type == "above" else "پایین‌تر از"
        
        return f"""{emoji} **هشدار قیمت {symbol}/{currency}**
━━━━━━━━━━━━━━━━━━━━━━

💰 قیمت فعلی: `{current_price:,.4f} {currency}`
🎯 قیمت هدف: `{target_price:,.4f} {currency}`

📊 قیمت {direction} سطح تعیین شده قرار گرفت!

🕒 زمان: `{TimeManager.to_shamsi(datetime.now())}`"""
    
    @staticmethod
    def format_signal_alert(signal_data: Dict[str, Any]) -> str:
        """فرمت هشدار سیگنال"""
        return f"""🚨 **سیگنال جدید دریافت شد!**
━━━━━━━━━━━━━━━━━━━━━━

📊 جفت ارز: `{signal_data.get('symbol')}/{signal_data.get('currency')}`
📈 استراتژی: `{signal_data.get('strategy')}`
🎯 سیگنال: `{signal_data.get('direction').upper()}`
💪 قدرت: `{signal_data.get('strength')}`

🔔 برای مشاهده جزئیات، به بخش تحلیل‌ها مراجعه کنید."""