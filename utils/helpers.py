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
import logging

# تنظیم logger
logger = logging.getLogger(__name__)

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

def extract_signal_details(strategy_type: str, api_response: Dict[str, Any]) -> Dict[str, Any]:
    """استخراج جزئیات سیگنال از پاسخ API - نسخه کامل"""
    try:
        # ساختار پیش‌فرض سیگنال
        signal_details = {
            "signal_type": "NEUTRAL",
            "signal_direction": "خنثی", 
            "strength": "متوسط",
            "confidence": 0.5,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward_ratio": None,
            "description": "",
            "analysis_text": "",
            "has_detailed_signal": False
        }
        
        # بررسی وجود خطا
        if "error" in api_response:
            signal_details["description"] = api_response["error"]
            return signal_details
        
        # استخراج متن تحلیل از فایل گزارش یا مستقیم از API response
        analysis_text = _extract_analysis_text_from_response(api_response)
        signal_details["analysis_text"] = analysis_text
        
        if analysis_text:
            signal_details["has_detailed_signal"] = True
            
            # پردازش استراتژی‌های خاص ابتدا
            _process_specific_strategy(strategy_type, analysis_text, signal_details)
            
            # اگر سیگنال تعین نشده، از الگوی عمومی استفاده کن
            if signal_details["signal_type"] == "NEUTRAL":
                _extract_general_signal(analysis_text, signal_details)
            
            # استخراج قیمت‌ها
            _extract_prices(analysis_text, signal_details)
            
            # محاسبه اعتماد نهایی
            _calculate_final_confidence(signal_details, analysis_text)
        
        return signal_details
        
    except Exception as e:
        logger.error(f"Error extracting signal details: {e}")
        return {
            "signal_type": "ERROR",
            "signal_direction": "خطا", 
            "description": f"خطا در پردازش: {str(e)}",
            "has_detailed_signal": False
        }


def _extract_analysis_text_from_response(api_response: Dict[str, Any]) -> str:
    """استخراج متن تحلیل از پاسخ API - روش‌های مختلف"""
    try:
        # روش اول: کلیدهای استاندارد
        analysis_text = api_response.get("analysis_text", "") or api_response.get("raw_report", "")
        
        if analysis_text and len(analysis_text) > 50:
            return analysis_text
        
        # روش دوم: جستجو در تمام کلیدهای response برای محتوای تحلیل
        if isinstance(api_response, dict):
            for key, value in api_response.items():
                if isinstance(value, str) and len(value) > 100:
                    # بررسی اینکه آیا این متن شامل کلمات کلیدی تحلیل است
                    if any(keyword in value for keyword in ["تحلیل", "سیگنال", "نتیجه", "توصیه", "Entry", "Signal"]):
                        return value
        
        # روش سوم: اگر کل response یک رشته است (برای موارد خاص)
        if isinstance(api_response, str) and len(api_response) > 100:
            return api_response
        
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting analysis text: {e}")
        return ""


def _process_specific_strategy(strategy_type: str, analysis_text: str, signal_details: Dict[str, Any]):
    """پردازش استراتژی‌های خاص با الگوهای دقیق - نسخه بهبود یافته"""
    try:
        text_upper = analysis_text.upper()
        
        # ✅ اصلاح: افزودن استراتژی‌های جدید
        
        # استراتژی Ichimoku - بر اساس لاگ جدید
        if strategy_type in ["ichimoku", "ichimoku_low_signal"] or "ICHIMOKU" in strategy_type.upper():
            # الگوهای خاص ichimoku
            ichimoku_patterns = [
                r"نتیجه نهایی تحلیل[:\s]*([^\.]+)",
                r"Signal[:\s]*([^\.]+)",
                r"📍 نتیجه نهایی[:\s]*([^\.]+)"
            ]
            
            for pattern in ichimoku_patterns:
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    result_text = match.group(1).strip()
                    signal_details["description"] = result_text
                    
                    # تحلیل سیگنال‌های ترکیبی مثل "NEUTRAL/صعودی"
                    if "NEUTRAL" in result_text.upper() and ("صعودی" in result_text or "BULLISH" in result_text.upper()):
                        signal_details["signal_type"] = "BUY"
                        signal_details["signal_direction"] = "خرید ضعیف"
                        signal_details["strength"] = "ضعیف"
                        signal_details["confidence"] = 0.4
                    elif "NEUTRAL" in result_text.upper() and ("نزولی" in result_text or "BEARISH" in result_text.upper()):
                        signal_details["signal_type"] = "SELL"
                        signal_details["signal_direction"] = "فروش ضعیف"
                        signal_details["strength"] = "ضعیف"
                        signal_details["confidence"] = 0.4
                    elif "SELL" in result_text.upper():
                        signal_details["signal_type"] = "SELL"
                        signal_details["signal_direction"] = "فروش"
                    elif "BUY" in result_text.upper():
                        signal_details["signal_type"] = "BUY"
                        signal_details["signal_direction"] = "خرید"
                    break
            
            # تحلیل وضعیت ابر کومو
            if "بالای ابر" in analysis_text or "above cloud" in text_upper:
                if signal_details["signal_type"] == "NEUTRAL":
                    signal_details["signal_type"] = "BUY"
                    signal_details["signal_direction"] = "خرید"
            elif "زیر ابر" in analysis_text or "below cloud" in text_upper:
                if signal_details["signal_type"] == "NEUTRAL":
                    signal_details["signal_type"] = "SELL"
                    signal_details["signal_direction"] = "فروش"
                    
        # ✅ اضافه: استراتژی CCI با پردازش بهتر
        elif strategy_type == "cci_analysis" or "CCI" in strategy_type.upper():
            # الگوهای مختلف برای CCI
            cci_patterns = [
                r"سیگنال:\s*(SELL|BUY|HOLD)",
                r"سیگنال\*\*\s*(SELL|BUY|HOLD)",
                r"نتیجه نهایی[:\s]*.*?(SELL|BUY|HOLD)",
                r"CCI.*?(SELL|BUY|HOLD)"
            ]
            
            for pattern in cci_patterns:
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    signal_word = match.group(1).upper()
                    if signal_word == "SELL":
                        signal_details["signal_type"] = "SELL"
                        signal_details["signal_direction"] = "فروش"
                    elif signal_word == "BUY":
                        signal_details["signal_type"] = "BUY" 
                        signal_details["signal_direction"] = "خرید"
                    elif signal_word == "HOLD":
                        signal_details["signal_type"] = "HOLD"
                        signal_details["signal_direction"] = "نگه‌داری"
                    break
                    
        # ✅ اضافه: استراتژی RSI با بررسی سطوح
        elif strategy_type == "rsi" or "RSI" in strategy_type.upper():
            # بررسی سطوح RSI
            rsi_value_match = re.search(r"RSI.*?(\d+\.?\d*)", analysis_text)
            if rsi_value_match:
                rsi_value = float(rsi_value_match.group(1))
                if rsi_value < 30:
                    signal_details["signal_type"] = "BUY"
                    signal_details["signal_direction"] = "خرید"
                    signal_details["description"] = "RSI در ناحیه اشباع فروش"
                elif rsi_value > 70:
                    signal_details["signal_type"] = "SELL"
                    signal_details["signal_direction"] = "فروش"
                    signal_details["description"] = "RSI در ناحیه اشباع خرید"
            
            # بررسی متنی
            if "اشباع فروش" in analysis_text or "RSI < 30" in analysis_text:
                signal_details["signal_type"] = "BUY"
                signal_details["signal_direction"] = "خرید"
            elif "اشباع خرید" in analysis_text or "RSI > 70" in analysis_text:
                signal_details["signal_type"] = "SELL"
                signal_details["signal_direction"] = "فروش"
                
        # ✅ اضافه: استراتژی MACD با جزئیات بیشتر
        elif strategy_type == "macd" or "MACD" in strategy_type.upper():
            macd_patterns = [
                r"سیگنال صعودی|MACD بالای سیگنال|MACD.*?positive",
                r"سیگنال نزولی|MACD زیر سیگنال|MACD.*?negative"
            ]
            
            if any(re.search(pattern, analysis_text, re.IGNORECASE) for pattern in macd_patterns[:1]):
                signal_details["signal_type"] = "BUY"
                signal_details["signal_direction"] = "خرید"
            elif any(re.search(pattern, analysis_text, re.IGNORECASE) for pattern in macd_patterns[1:]):
                signal_details["signal_type"] = "SELL"
                signal_details["signal_direction"] = "فروش"
                
        # ✅ اضافه: سایر استراتژی‌ها
        elif strategy_type == "ema_analysis" or "EMA" in strategy_type.upper():
            if "روند صعودی" in analysis_text or "قیمت بالای EMA" in analysis_text:
                signal_details["signal_type"] = "BUY"
                signal_details["signal_direction"] = "خرید"
            elif "روند نزولی" in analysis_text or "قیمت زیر EMA" in analysis_text:
                signal_details["signal_type"] = "SELL"
                signal_details["signal_direction"] = "فروش"
                
        elif strategy_type == "williams_r_analysis" or "WILLIAMS" in strategy_type.upper():
            if "اشباع فروش" in analysis_text or "Williams %R < -80" in analysis_text:
                signal_details["signal_type"] = "BUY"
                signal_details["signal_direction"] = "خرید"
            elif "اشباع خرید" in analysis_text or "Williams %R > -20" in analysis_text:
                signal_details["signal_type"] = "SELL"
                signal_details["signal_direction"] = "فروش"
                
        # ✅ اضافه: الگوی گوه (Wedge Pattern)
        elif strategy_type == "wedge_pattern":
            if "شکست صعودی" in analysis_text or "bullish breakout" in text_upper:
                signal_details["signal_type"] = "BUY"
                signal_details["signal_direction"] = "خرید"
                signal_details["description"] = "شکست صعودی الگوی گوه"
            elif "شکست نزولی" in analysis_text or "bearish breakout" in text_upper:
                signal_details["signal_type"] = "SELL"
                signal_details["signal_direction"] = "فروش"
                signal_details["description"] = "شکست نزولی الگوی گوه"
                
        # ✅ اضافه: استراتژی‌های جدید در strategy_manager
        elif strategy_type in ["bollinger_bands", "fibonacci_strategy", "head_shoulders_analysis", 
                               "double_top_pattern", "macd_divergence", "atr", "diamond_pattern", 
                               "crt", "vwap", "volume_profile"]:
            # استفاده از الگوهای عمومی برای استراتژی‌های پیچیده
            general_patterns = [
                (r"STRONG.*?(BUY|SELL)", "قوی"),
                (r"(BUY|SELL).*?STRONG", "قوی"),
                (r"نتیجه.*?(خرید|فروش).*?قوی", "قوی"),
                (r"سیگنال.*?(BUY|SELL)", "متوسط"),
                (r"توصیه.*?(خرید|فروش)", "متوسط")
            ]
            
            for pattern, strength in general_patterns:
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    signal_word = match.group(1).upper()
                    if signal_word in ["BUY", "خرید"]:
                        signal_details["signal_type"] = "BUY"
                        signal_details["signal_direction"] = "خرید"
                        signal_details["strength"] = strength
                    elif signal_word in ["SELL", "فروش"]:
                        signal_details["signal_type"] = "SELL"
                        signal_details["signal_direction"] = "فروش"  
                        signal_details["strength"] = strength
                    break
        
        # استخراج قدرت سیگنال
        _extract_signal_strength(analysis_text, signal_details)
        
    except Exception as e:
        logger.error(f"Error processing specific strategy {strategy_type}: {e}")

def _extract_general_signal(analysis_text: str, signal_details: Dict[str, Any]):
    """استخراج سیگنال از الگوهای عمومی"""
    try:
        text_upper = analysis_text.upper()
        
        # الگوهای کلی برای تشخیص سیگنال
        signal_patterns = [
            # الگوهای مستقیم
            (r"نتیجه نهایی[:\s]*([^\.]+)", "direct"),
            (r"Signal[:\s]*([^\.]+)", "direct"),
            (r"سیگنال[:\s]*([^\.]+)", "direct"),
            (r"توصیه[:\s]*([^\.]+)", "direct"),
            
            # الگوهای خط آخر
            (r"Signal:\s*([^\n]+)", "final"),
            (r"نتیجه:\s*([^\n]+)", "final")
        ]
        
        for pattern, pattern_type in signal_patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                matched_text = match.group(1).strip()
                
                # پردازش سیگنال‌های ترکیبی
                if _process_complex_signal(matched_text, signal_details):
                    break
                
                # پردازش سیگنال‌های ساده
                if _process_simple_signal(matched_text, signal_details):
                    break
        
        # اگر هنوز سیگنال پیدا نشد، از الگوهای کلمات کلیدی استفاده کن
        if signal_details["signal_type"] == "NEUTRAL":
            _extract_keyword_based_signal(analysis_text, signal_details)
            
    except Exception as e:
        logger.error(f"Error extracting general signal: {e}")


def _process_complex_signal(matched_text: str, signal_details: Dict[str, Any]) -> bool:
    """پردازش سیگنال‌های پیچیده مثل NEUTRAL/صعودی"""
    try:
        text_upper = matched_text.upper()
        
        # سیگنال‌های ترکیبی
        complex_patterns = [
            (r"NEUTRAL.*صعودی", "BUY", "خرید ضعیف", "ضعیف", 0.4),
            (r"NEUTRAL.*نزولی", "SELL", "فروش ضعیف", "ضعیف", 0.4),
            (r"NEUTRAL.*BULLISH", "BUY", "خرید ضعیف", "ضعیف", 0.4),
            (r"NEUTRAL.*BEARISH", "SELL", "فروش ضعیف", "ضعیف", 0.4),
            (r"صعودی.*ضعیف", "BUY", "خرید ضعیف", "ضعیف", 0.3),
            (r"نزولی.*ضعیف", "SELL", "فروش ضعیف", "ضعیف", 0.3),
        ]
        
        for pattern, signal_type, direction, strength, confidence in complex_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                signal_details["signal_type"] = signal_type
                signal_details["signal_direction"] = direction
                signal_details["strength"] = strength
                signal_details["confidence"] = confidence
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error processing complex signal: {e}")
        return False


def _process_simple_signal(matched_text: str, signal_details: Dict[str, Any]) -> bool:
    """پردازش سیگنال‌های ساده"""
    try:
        text_upper = matched_text.upper()
        
        # سیگنال‌های ساده
        simple_patterns = [
            (["STRONG BUY", "خرید قوی"], "BUY", "خرید قوی", "قوی", 0.8),
            (["STRONG SELL", "فروش قوی"], "SELL", "فروش قوی", "قوی", 0.8),
            (["BUY", "خرید"], "BUY", "خرید", "متوسط", 0.6),
            (["SELL", "فروش"], "SELL", "فروش", "متوسط", 0.6),
            (["HOLD", "نگه‌داری", "نگهداری"], "HOLD", "نگه‌داری", "متوسط", 0.5),
            (["BULLISH", "صعودی"], "BUY", "خرید", "متوسط", 0.6),
            (["BEARISH", "نزولی"], "SELL", "فروش", "متوسط", 0.6),
        ]
        
        for keywords, signal_type, direction, strength, confidence in simple_patterns:
            if any(keyword in text_upper for keyword in keywords):
                signal_details["signal_type"] = signal_type
                signal_details["signal_direction"] = direction
                signal_details["strength"] = strength
                signal_details["confidence"] = confidence
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error processing simple signal: {e}")
        return False


def _extract_keyword_based_signal(analysis_text: str, signal_details: Dict[str, Any]):
    """استخراج سیگنال بر اساس کلمات کلیدی در کل متن"""
    try:
        text_upper = analysis_text.upper()
        
        # شمارش کلمات کلیدی
        buy_keywords = ["خرید", "BUY", "صعودی", "BULLISH", "خرید قوی", "سیگنال مثبت", "صعود", "LONG"]
        sell_keywords = ["فروش", "SELL", "نزولی", "BEARISH", "فروش قوی", "سیگنال منفی", "نزول", "SHORT"]
        hold_keywords = ["نگه‌داری", "HOLD", "خنثی", "NEUTRAL", "صبر", "انتظار"]
        
        buy_count = sum(1 for keyword in buy_keywords if keyword in text_upper)
        sell_count = sum(1 for keyword in sell_keywords if keyword in text_upper)
        hold_count = sum(1 for keyword in hold_keywords if keyword in text_upper)
        
        # تعیین سیگنال بر اساس اکثریت
        if buy_count > sell_count and buy_count > hold_count:
            signal_details["signal_type"] = "BUY"
            signal_details["signal_direction"] = "خرید"
            signal_details["confidence"] = min(0.7, 0.4 + (buy_count * 0.1))
        elif sell_count > buy_count and sell_count > hold_count:
            signal_details["signal_type"] = "SELL" 
            signal_details["signal_direction"] = "فروش"
            signal_details["confidence"] = min(0.7, 0.4 + (sell_count * 0.1))
        elif hold_count > 0:
            signal_details["signal_type"] = "HOLD"
            signal_details["signal_direction"] = "نگه‌داری"
            signal_details["confidence"] = 0.5
            
    except Exception as e:
        logger.error(f"Error extracting keyword-based signal: {e}")


def _extract_signal_strength(analysis_text: str, signal_details: Dict[str, Any]):
    """استخراج قدرت سیگنال از متن"""
    try:
        # الگوهای قدرت
        strength_patterns = [
            (["بسیار قوی", "خیلی قوی", "VERY STRONG"], "بسیار قوی", 0.9),
            (["قوی", "STRONG"], "قوی", 0.8),
            (["متوسط", "MEDIUM", "MODERATE"], "متوسط", 0.6),
            (["ضعیف", "WEAK"], "ضعیف", 0.3),
            (["خیلی ضعیف", "VERY WEAK"], "خیلی ضعیف", 0.2)
        ]
        
        for keywords, strength, confidence in strength_patterns:
            if any(keyword in analysis_text for keyword in keywords):
                signal_details["strength"] = strength
                signal_details["confidence"] = max(signal_details.get("confidence", 0.5), confidence)
                break
        else:
            # اگر قدرت مشخص نشد، بر اساس نوع سیگنال تخمین بزن
            if signal_details["signal_type"] in ["BUY", "SELL"]:
                signal_details["strength"] = "متوسط"
                signal_details["confidence"] = max(signal_details.get("confidence", 0.5), 0.6)
            
    except Exception as e:
        logger.error(f"Error extracting signal strength: {e}")


def _extract_prices(analysis_text: str, signal_details: Dict[str, Any]):
    """استخراج قیمت‌ها با regex بهبود یافته"""
    try:
        # الگوهای قیمت Entry
        entry_patterns = [
            r'Entry Price[:\s]*(\d+\.?\d*)',
            r'قیمت ورود[:\s]*(\d+\.?\d*)',
            r'قیمت آخر[:\s]*(\d+\.?\d*)',
            r'ورود[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in entry_patterns:
            entry_match = re.search(pattern, analysis_text, re.IGNORECASE)
            if entry_match:
                signal_details["entry_price"] = float(entry_match.group(1))
                break
        
        # الگوهای Stop Loss
        sl_patterns = [
            r'SL[:\s]*(\d+\.?\d*)',
            r'Stop.*?Loss[:\s]*(\d+\.?\d*)',
            r'حد ضرر[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in sl_patterns:
            sl_match = re.search(pattern, analysis_text, re.IGNORECASE)
            if sl_match:
                signal_details["stop_loss"] = float(sl_match.group(1))
                break
        
        # الگوهای Take Profit
        tp_patterns = [
            r'TP[:\s]*(\d+\.?\d*)',
            r'Take.*?Profit[:\s]*(\d+\.?\d*)',
            r'هدف سود[:\s]*(\d+\.?\d*)',
            r'حد سود[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in tp_patterns:
            tp_match = re.search(pattern, analysis_text, re.IGNORECASE)
            if tp_match:
                signal_details["take_profit"] = float(tp_match.group(1))
                break
        
        # الگوی Risk/Reward
        rr_patterns = [
            r'Risk.*?Reward[:\s]*(\d+\.?\d*)',
            r'نسبت ریسک به ریوارد[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in rr_patterns:
            rr_match = re.search(pattern, analysis_text, re.IGNORECASE)
            if rr_match:
                signal_details["risk_reward_ratio"] = float(rr_match.group(1))
                break
            
    except (ValueError, AttributeError) as e:
        logger.error(f"Error extracting prices: {e}")


def _calculate_final_confidence(signal_details: Dict[str, Any], analysis_text: str):
    """محاسبه اعتماد نهایی بر اساس فاکتورهای مختلف"""
    try:
        base_confidence = signal_details.get("confidence", 0.5)
        
        # افزایش اعتماد اگر قیمت‌ها موجود باشد
        if signal_details.get("entry_price"):
            base_confidence += 0.05
        if signal_details.get("stop_loss"):
            base_confidence += 0.05
        if signal_details.get("take_profit"):
            base_confidence += 0.05
        
        # افزایش اعتماد بر اساس طول تحلیل
        if len(analysis_text) > 500:
            base_confidence += 0.05
        
        # افزایش اعتماد اگر جزئیات استراتژی موجود باشد
        strategy_keywords = ["تحلیل", "اندیکاتور", "سیگنال", "روند", "الگو"]
        keyword_count = sum(1 for keyword in strategy_keywords if keyword in analysis_text)
        base_confidence += keyword_count * 0.02
        
        # محدود کردن اعتماد بین 0 و 1
        signal_details["confidence"] = min(1.0, max(0.0, base_confidence))
        
    except Exception as e:
        logger.error(f"Error calculating confidence: {e}")


# در فایل utils/helpers.py

def format_signal_message(signal_details: Dict[str, Any], symbol: str, currency: str,
                         timeframe: str, strategy: str) -> str:
    """فرمت‌بندی پیام سیگنال برای نمایش - مطابق تصویر مطلوب"""
    try:
        # تشخیص ایموجی و متن بر اساس نوع سیگنال
        signal_type = signal_details.get("signal_type", "NEUTRAL")
        direction_text = signal_details.get('signal_direction', 'خنثی')
        main_emoji = "🟡"  # Default
        if signal_type == "BUY":
            main_emoji = "🟢"
            direction_text = "خرید صعودی"
        elif signal_type == "SELL":
            main_emoji = "🔴"
            direction_text = "فروش نزولی"

        # ساخت پیام اصلی مطابق تصاویر
        strategy_display = _format_strategy_name(strategy)
        
        # فرمت تایم‌فریم به فارسی
        timeframe_fa = {
            "1m": "۱ دقیقه", "3m": "۳ دقیقه", "5m": "۵ دقیقه", "15m": "۱۵ دقیقه", "30m": "۳۰ دقیقه",
            "1h": "۱ ساعت", "2h": "۲ ساعت", "4h": "۴ ساعت", "6h": "۶ ساعت", "8h": "۸ ساعت",
            "12h": "۱۲ ساعت", "1d": "۱ روز", "3d": "۳ روز", "1w": "۱ هفته", "1M": "۱ ماه"
        }.get(timeframe, timeframe)

        message = f"""{main_emoji} **سیگنال معاملاتی {symbol}/{currency}**

📊 **تایم‌فریم:** {timeframe_fa}
🎯 **جهت:** {direction_text}

"""
        # اضافه کردن اطلاعات معاملاتی کلیدی با دقت بالا
        entry_price = signal_details.get('entry_price')
        stop_loss = signal_details.get('stop_loss')
        take_profit = signal_details.get('take_profit')
        support = signal_details.get('support')
        resistance = signal_details.get('resistance')
        current_price = signal_details.get('current_price')

        # تعریف تابع کمکی برای فرمت‌بندی قیمت با دقت متغیر
        def format_price_dynamic(price: Optional[float]) -> str:
            if price is None:
                return ""
            if price >= 100:
                return f"{price:,.2f}"
            elif price >= 1:
                return f"{price:,.4f}"
            else:
                return f"{price:,.8f}"

        if entry_price:
            message += f"🔴 **نقطه ورود:** {format_price_dynamic(entry_price)}\n"
        
        if stop_loss:
            message += f"🛑 **حد ضرر:** {format_price_dynamic(stop_loss)}\n"
            
        if take_profit:
            message += f"🎯 **هدف قیمتی:** {format_price_dynamic(take_profit)}\n"
            
        if current_price:
            message += f"💰 **قیمت فعلی:** {format_price_dynamic(current_price)}\n"
            
        if support:
            message += f"🟢 **حمایت:** {format_price_dynamic(support)}\n"
            
        if resistance:
            message += f"🔴 **مقاومت:** {format_price_dynamic(resistance)}\n"

        # محاسبه ریسک/ریوارد
        if entry_price and stop_loss and take_profit:
            try:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                if risk > 0:
                    rr_ratio = reward / risk
                    message += f"⚖️ **ریسک/ریوارد:** 1:{rr_ratio:.2f}\n"
            except Exception as rr_error:
                logger.warning(f"Error calculating risk/reward: {rr_error}")

        # اضافه کردن اطلاعات استراتژی، قدرت و اعتماد
        message += f"\n📈 **استراتژی:** {strategy_display}"
        strength = signal_details.get('strength', 'متوسط')
        confidence = signal_details.get('confidence', 0.5)
        message += f"\n💪 **قدرت:** {strength}"
        message += f"\n🎲 **اعتماد:** {confidence:.1%}"

        # اضافه کردن لینک چارت (اصلاح جدید)
        chart_url = signal_details.get('chart_url')
        if chart_url:
            message += f"\n\n🔗 **لینک تحلیل و چارت:**\n{chart_url}"

        # زمان تحلیل
        current_time = datetime.now().strftime("%H:%M")
        message += f"\n\n🕒 **زمان تحلیل:** {current_time}"
        
        # هشدار ریسک
        message += f"\n\n⚠️ **یادآوری:** این تحلیل جنبه آموزشی داشته و توصیه سرمایه‌گذاری نیست."
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting signal message: {e}")
        return f"❌ خطا در فرمت‌بندی پیام: {str(e)}"    
    
def _format_strategy_name(strategy: str) -> str:
    """فرمت‌بندی نام استراتژی"""
    strategy_names = {
        "cci_analysis": "CCI (شاخص کانال کالا)",
        "rsi": "RSI (شاخص قدرت نسبی)",
        "macd": "MACD (همگرایی واگرایی)",
        "ema_analysis": "EMA (میانگین متحرک نمایی)",
        "williams_r_analysis": "Williams %R",
        "ichimoku": "Ichimoku (ابر ایچی‌موکو)",
        "ichimoku_low_signal": "Ichimoku کم ریسک",
        "bollinger_bands": "Bollinger Bands",
        "fibonacci_strategy": "Fibonacci Retracement",
        "head_shoulders_analysis": "سر و شانه",
        "wedge_pattern": "الگوی گوه (Wedge)",
        "cup_handle": "کاپ اند هندل",
        "double_top_pattern": "دو قله/دو کف",
        "macd_divergence": "واگرایی MACD",
        "price_action_pandas_ta": "Price Action"
    }
    
    return strategy_names.get(strategy, strategy.replace('_', ' ').title())


def _extract_key_points(analysis_text: str, max_length: int = 150) -> str:
    """استخراج نکات کلیدی از متن تحلیل"""
    try:
        # جستجو برای جملات کلیدی
        key_patterns = [
            r'نتیجه نهایی[:\s]*(.*?)[\n\.]',
            r'توصیه[:\s]*(.*?)[\n\.]',
            r'سیگنال[:\s]*(.*?)[\n\.]',
            r'نکته مهم[:\s]*(.*?)[\n\.]',
            r'🔍[^:]*[:\s]*(.*?)[\n\.]'
        ]
        
        key_points = []
        
        for pattern in key_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if clean_match and len(clean_match) > 10:
                    key_points.append(clean_match)
        
        if key_points:
            # انتخاب بهترین نکته
            best_point = max(key_points, key=len)
            return best_point[:max_length] + ("..." if len(best_point) > max_length else "")
        
        # اگر نکته خاصی پیدا نشد، اولین جمله مفید را برگردان
        sentences = analysis_text.split('.')
        for sentence in sentences:
            clean_sentence = sentence.strip()
            if len(clean_sentence) > 20 and any(word in clean_sentence for word in ["سیگنال", "توصیه", "تحلیل", "نتیجه"]):
                return clean_sentence[:max_length] + ("..." if len(clean_sentence) > max_length else "")
        
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting key points: {e}")
        return ""


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

# سایر توابع کمکی بدون تغییر
def validate_signal_data(signal_details: Dict[str, Any]) -> bool:
    """اعتبارسنجی داده‌های سیگنال"""
    try:
        required_fields = ["signal_type", "signal_direction", "strength", "confidence"]
        
        for field in required_fields:
            if field not in signal_details:
                return False
        
        confidence = signal_details.get("confidence", 0)
        if not (0 <= confidence <= 1):
            return False
        
        valid_signal_types = ["BUY", "SELL", "HOLD", "NEUTRAL", "ERROR"]
        if signal_details.get("signal_type") not in valid_signal_types:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating signal data: {e}")
        return False

def get_signal_summary(signal_details: Dict[str, Any]) -> str:
    """دریافت خلاصه کوتاه سیگنال"""
    try:
        signal_type = signal_details.get("signal_type", "NEUTRAL")
        signal_direction = signal_details.get("signal_direction", "نامشخص")
        strength = signal_details.get("strength", "متوسط")
        
        if signal_type == "BUY":
            return f"🟢 خرید ({strength})"
        elif signal_type == "SELL":
            return f"🔴 فروش ({strength})"
        elif signal_type == "HOLD":
            return f"🟡 نگه‌داری ({strength})"
        else:
            return f"⚪ {signal_direction} ({strength})"
            
    except Exception as e:
        logger.error(f"Error getting signal summary: {e}")
        return "⚪ نامشخص"

def format_price(price: Union[float, int], precision: int = 4) -> str:
    """فرمت‌بندی قیمت"""
    try:
        if price is None:
            return "نامشخص"
        
        price = float(price)
        if price >= 1000:
            return f"${price:,.2f}"
        else:
            return f"${price:.{precision}f}"
            
    except (ValueError, TypeError):
        return "نامعتبر"

def is_valid_symbol(symbol: str) -> bool:
    """بررسی اعتبار نماد ارز"""
    try:
        if not symbol or len(symbol) < 2:
            return False
        return re.match(r'^[A-Za-z0-9]+$', symbol) is not None
    except Exception:
        return False

def is_valid_timeframe(timeframe: str) -> bool:
    """بررسی اعتبار تایم‌فریم"""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
    return timeframe in valid_timeframes

# Export توابع اصلی
__all__ = [
    'extract_signal_details',
    'format_signal_message', 
    'validate_signal_data',
    'get_signal_summary',
    'format_price',
    'format_currency',
    'format_percentage',
    'is_valid_symbol',
    'is_valid_timeframe',
    'generate_random_string',
    'generate_referral_code',
    'generate_transaction_id',
    'hash_string',
    'mask_sensitive_data',
    'format_number',
    'format_time_delta',
    'parse_user_input',
    'safe_dict_get',
    'deep_merge_dicts',
    'clean_html_tags',
    'escape_markdown',
    'truncate_text',
    'chunk_list',
    'flatten_list',
    'remove_duplicates',
    'calculate_percentage_change',
    'calculate_moving_average',
    'convert_persian_numbers',
    'convert_english_numbers',
    'create_progress_bar',
    'Timer',
    'DataProcessor'
]