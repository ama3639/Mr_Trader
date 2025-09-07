"""
کلاینت API برای ارتباط با سرویس‌های تحلیل و قیمت‌گذاری
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from core.config import Config
from utils.logger import logger
from utils.helpers import extract_signal_details


class ApiClient:
    """کلاینت یکپارچه برای تمام API ها"""
    
    def __init__(self):
        self.session = None
        self._rate_limiter = {}
        # نقشه‌برداری استراتژی‌ها به URL های API
        self.strategy_endpoints = {
            # Demo strategies
            "demo_price_action": "/analyze_price_action_pandas_ta/",
            "demo_rsi": "/analyze_RSI_basic/",
            
            # Basic Package strategies
            "cci_analysis": "/analyze_CCI_strategy/",
            "ema_analysis": "/analyze_EMA_strategy/",
            "ichimoku": "/analyze_ichimoku_strategy/",
            "ichimoku_low_signal": "/analyze_ichimoku_strategy/",
            "macd": "/analyze_MACD_basic/",
            "price_action_pandas_ta": "/analyze_price_action_pandas_ta/",
            "project_price_live_binance": "/live_price/",
            "rsi": "/analyze_RSI_basic/",
            "williams_r_analysis": "/analyze_WilliamsR/",
            
            # Premium Package strategies
            "a_candlestick": "/analyze_price_action_pandas_ta/",
            "b_pivot": "/analyze_fibonacci/",
            "bollinger_bands": "/analyze_bollinger_bands_strategy/",
            "c_trend_lines": "/analyze_price_action_pandas_ta/",
            "double_top_pattern": "/analyze_double_top_strategy/",
            "fibonacci_strategy": "/analyze_fibonacci/",
            "flag_pattern": "/analyze_flag_pattern/",
            "head_shoulders_analysis": "/analyze_head_shoulders_analysis/",
            "heikin_ashi": "/analyze_heikin_ashi_strategy/",
            "macd_divergence": "/analyze_macd_divergence_strategy/",
            "martingale_low": "/analyze_momentum_strategy/",
            "momentum": "/analyze_momentum_strategy/",
            "stochastic": "/analyze_RSI_basic/",
            "triangle_pattern": "/analyze_double_top_strategy/",
            "wedge_pattern": "/analyze_double_top_strategy/",
            "support_resistance": "/analyze_price_action_pandas_ta/",
            "stoch_rsi": "/analyze_RSI_basic/",
            "williams_alligator": "/analyze_WilliamsR/",
            "parabolic_sar": "/analyze_price_action_pandas_ta/",
            
            # VIP Package strategies
            "atr": "/analyze_atr/",
            "sma_advanced": "/analyze_EMA_strategy/",
            "volume_profile": "/analyze_price_action_pandas_ta/",
            "vwap": "/analyze_price_action_pandas_ta/",
            "diamond_pattern": "/analyze_Diamond_Pattern/",
            "crt": "/analyze_CRT_strategy/",
            "p3": "/analyze_momentum_strategy/",
            "rtm": "/analyze_momentum_strategy/",
            "multi_resistance": "/analyze_price_action_pandas_ta/"
        }
        
        # Base URL برای API
        self.base_url = "http://91.198.77.208:8000"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """دریافت session HTTP"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': f'MrTrader-Bot/{Config.BOT_VERSION}'
            }
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        
        return self.session
    
    async def close(self):
        """بستن session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def _make_request(
        self, 
        url: str, 
        method: str = "POST", 
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """درخواست HTTP با مدیریت خطا و تلاش مجدد"""
        
        last_error = None
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                request_headers = headers or {}
                
                # اضافه کردن API key اگر موجود باشد
                if hasattr(Config, 'API_KEY') and Config.API_KEY:
                    request_headers['X-API-Key'] = Config.API_KEY
                
                request_headers.update({
                    'Content-Type': 'application/json',
                    'User-Agent': f'MrTrader-Bot/{Config.BOT_VERSION}'
                })
                
                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"API request successful: {method} {url}")
                        return result
                    
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
            
            except asyncio.TimeoutError as e:
                last_error = f"Timeout error: {e}"
                logger.warning(f"Request timeout (attempt {attempt + 1}): {url}")
                
            except aiohttp.ClientError as e:
                last_error = f"Client error: {e}"
                logger.warning(f"Client error (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
            
            # انتظار قبل از تلاش مجدد
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        logger.error(f"All retry attempts failed for {url}. Last error: {last_error}")
        return {"error": last_error}
    
    def get_strategy_url(self, strategy: str) -> Optional[str]:
        """دریافت URL استراتژی"""
        endpoint = self.strategy_endpoints.get(strategy)
        if endpoint:
            return f"{self.base_url}{endpoint}"
        return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """تبدیل تایم‌فریم کاربری به فرمت API"""
        timeframe_mapping = {
            # دقیقه‌ای
            "1m": "histominute",
            "5m": "histominute", 
            "15m": "histominute",
            "30m": "histominute",
            
            # ساعتی
            "1h": "histohour",
            "4h": "histohour",
            "12h": "histohour",
            
            # روزانه
            "1d": "histoday",
            "1w": "histoday",
            "1M": "histoday"
        }
        
        return timeframe_mapping.get(timeframe, "histohour")  # پیش‌فرض ساعتی
    
    async def fetch_analysis(
        self, 
        strategy: str, 
        symbol: str, 
        currency: str, 
        timeframe: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        دریافت تحلیل برای استراتژی مشخص (متد اصلی)
        """
        try:
            # دریافت آدرس API
            strategy_url = self.get_strategy_url(strategy)
            if not strategy_url:
                return {"error": f"URL not found for strategy: {strategy}"}
            
            # تبدیل تایم‌فریم به فرمت API
            api_timeframe = self._convert_timeframe(timeframe)
            
            # پارامترهای درخواست مطابق با مستندات API
            request_data = {
                "symbol": symbol.upper(),
                "currency": currency.upper(),
                "timeframe": api_timeframe
            }
                        
            logger.info(f"Requesting {strategy} analysis for {symbol}/{currency} @ {timeframe} (API: {api_timeframe})")
            
            # ارسال درخواست
            result = await self._make_request(
                url=strategy_url,
                method="POST",
                data=request_data,
                max_retries=3,
                timeout=30
            )
            
            # بررسی خطا در پاسخ
            if "error" in result:
                return result
            
            # چک کردن هر دو کلید ممکن برای فایل گزارش
            report_file_path = result.get('report') or result.get('report_file')
            
            if result.get('ok') and report_file_path:
                try:
                    logger.info(f"Reading report file via API: {report_file_path}")
                    
                    # استفاده از endpoint مخصوص خواندن فایل
                    read_file_url = f"{self.base_url}/read_report_file/"
                    file_request_data = {
                        "file_path": report_file_path
                    }
                    
                    file_response = await self._make_request(
                        url=read_file_url,
                        method="POST",
                        data=file_request_data,
                        max_retries=2,
                        timeout=15
                    )
                    
                    if "error" not in file_response and file_response.get('success'):
                        report_content = file_response.get('content', '')
                        logger.info(f"=== REPORT CONTENT START ===")
                        logger.info(f"{report_content}")
                        logger.info(f"=== REPORT CONTENT END ===")
                        
                        # اضافه کردن محتوا و سایر اطلاعات به نتیجه
                        result.update({
                            "analysis_text": report_content,
                            "raw_report": report_content,
                            "symbol": symbol,
                            "currency": currency,
                            "timeframe": timeframe,
                            "strategy": strategy,
                            "report_size": file_response.get('size', 0)
                        })
                        
                    else:
                        logger.error(f"Failed to read report file: {file_response}")
                            
                except Exception as e:
                    logger.error(f"Error reading report file: {e}")
            
            # اضافه کردن لینک چارت از پاسخ API (اصلاح جدید)
            if 'chart_url' in result and result['chart_url']:
                logger.info(f"Chart URL found in API response: {result['chart_url']}")
                result['chart_url'] = result['chart_url']
            
            result["is_cached"] = False
            logger.info(f"Analysis completed for {strategy} {symbol}/{currency} @ {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fetch_analysis: {e}")
            return {"error": str(e)}
        
    async def fetch_strategy_analysis(
        self, 
        strategy: str, 
        symbol: str, 
        currency: str, 
        timeframe: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """دریافت تحلیل برای استراتژی مشخص (alias برای سازگاری)"""
        return await self.fetch_analysis(strategy, symbol, currency, timeframe, use_cache)
    
    async def fetch_price_analysis(
        self, 
        symbol: str, 
        currency: str, 
        timeframe: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """دریافت تحلیل پرایس اکشن (سازگاری با کد قبلی)"""
        return await self.fetch_analysis("price_action_pandas_ta", symbol, currency, timeframe, use_cache)
    
    async def fetch_live_price(
        self, 
        symbol: str, 
        currency: str = "USDT",
        use_cache: bool = True
    ) -> float:
        """
        دریافت قیمت زنده - غیرفعال شده
        """
        logger.warning(f"fetch_live_price called for {symbol}/{currency} - returning 0.0")
        return 0.0

    
    async def fetch_market_data(
        self, 
        symbol: str, 
        currency: str,
        timeframe: str = "1d",
        limit: int = 100
    ) -> Dict[str, Any]:
        """دریافت داده‌های بازار - استفاده از API تحلیل"""
        try:
            logger.info(f"Requesting market data for {symbol}/{currency} @ {timeframe}")
            
            # استفاده از API تحلیل برای دریافت داده‌های بازار
            analysis_result = await self.fetch_analysis("price_action_pandas_ta", symbol, currency, timeframe)
            
            if "error" not in analysis_result:
                # استخراج داده‌های کندل از نتیجه تحلیل
                return {
                    "symbol": f"{symbol.upper()}{currency.upper()}",
                    "timeframe": timeframe,
                    "data": analysis_result.get("market_data", []),
                    "analysis": analysis_result
                }
            else:
                return analysis_result
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {"error": str(e)}
    
    async def validate_symbol_pair(
        self, 
        symbol: str, 
        currency: str
    ) -> bool:
        """اعتبارسنجی جفت ارز"""
        try:
            # بررسی از طریق تحلیل ساده
            result = await self.fetch_analysis("price_action_pandas_ta", symbol, currency, "1h", use_cache=False)
            return "error" not in result
            
        except Exception as e:
            logger.error(f"Error validating symbol pair {symbol}/{currency}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت سرویس‌ها"""
        try:
            results = {}
            
            # بررسی سرویس محلی
            try:
                health_url = f"{self.base_url}/health/"
                ping_result = await self._make_request(health_url, method="GET", max_retries=1, timeout=5)
                results["local_service"] = "healthy" if "error" not in ping_result else "unhealthy"
            except Exception:
                results["local_service"] = "unhealthy"
            
            # بررسی چند استراتژی کلیدی
            key_strategies = ["rsi", "macd", "ema_analysis"]
            for strategy in key_strategies:
                try:
                    strategy_url = self.get_strategy_url(strategy)
                    if strategy_url:
                        # تست ساده endpoint
                        test_result = await self._make_request(strategy_url, method="GET", max_retries=1, timeout=5)
                        results[f"strategy_{strategy}"] = "reachable" if "error" not in test_result else "unreachable"
                    else:
                        results[f"strategy_{strategy}"] = "no_url_configured"
                except Exception:
                    results[f"strategy_{strategy}"] = "unreachable"
            
            # محاسبه وضعیت کلی
            healthy_services = sum(1 for status in results.values() if status in ["healthy", "reachable"])
            total_services = len(results)
            
            if healthy_services == total_services:
                overall_status = "healthy"
            elif healthy_services > total_services / 2:
                overall_status = "partial"
            else:
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "services": results,
                "summary": {
                    "healthy": healthy_services,
                    "total": total_services,
                    "health_percentage": round((healthy_services / total_services) * 100, 1) if total_services > 0 else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def __aenter__(self):
        """ورود به context manager"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """خروج از context manager"""
        await self.close()


# ایجاد نمونه سراسری
api_client = ApiClient()


# توابع helper برای سازگاری
def format_analysis_result(analysis_result: Dict[str, Any], symbol: str, currency: str) -> str:
    """فرمت‌بندی نتیجه تحلیل برای نمایش"""
    try:
        if "error" in analysis_result:
            return f"❌ خطا در تحلیل {symbol}/{currency}:\n{analysis_result['error']}"
        
        # استفاده از توابع جدید
        from utils.helpers import extract_signal_details, format_signal_message
        
        # استخراج جزئیات سیگنال
        strategy_type = analysis_result.get('strategy', 'unknown')
        signal_details = extract_signal_details(strategy_type, analysis_result)
        
        # فرمت‌بندی پیام
        timeframe = analysis_result.get('timeframe', '1h')
        formatted_message = format_signal_message(
            signal_details, symbol, currency, timeframe, strategy_type
        )
        
        return formatted_message
        
    except Exception as e:
        logger.error(f"Error formatting analysis result: {e}")
        return f"❌ خطا در فرمت‌بندی تحلیل {symbol}/{currency}"

# Export
__all__ = ['ApiClient', 'api_client', 'format_analysis_result']