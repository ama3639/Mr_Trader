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
import httpx


class ApiClient:
    """کلاینت یکپارچه برای تمام API ها"""
    
    def __init__(self):
        self.session = None
        self._rate_limiter = {}
        # ✅ دیگر نیازی به دیکشنری هاردکد شده نیست
        # self.strategy_endpoints = { ... }
        # self.base_url = "..."
    
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
        """دریافت URL استراتژی از فایل کانفیگ"""
        try:
            config = Config.get_api_server_config('crypto_analysis')
            endpoint = config['endpoints'].get(strategy)
            if endpoint:
                return f"{config['base_url']}{endpoint}"
            return None
        except Exception as e:
            logger.error(f"Could not get URL for strategy '{strategy}': {e}")
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
    
    @staticmethod
    async def fetch_live_price(symbol: str):
        """
        قیمت لحظه‌ای را با انتخاب هوشمند سرور (طلا/ارز یا کریپتو) دریافت کرده
        و نتیجه را به صورت یک پیام آماده برای کاربر برمی‌گرداند.
        """
        try:
            # لیست نمادهای مربوط به سرور طلا و ارز
            gold_currency_symbols = ['USD', 'EUR', 'GBP', 'XAUUSD']
            is_gold_server_request = symbol.startswith('IR_') or symbol in gold_currency_symbols

            # خواندن آدرس‌ها از فایل کانفیگ مرکزی
            live_price_config = Config.get_api_server_config('live_price')
            if not live_price_config:
                return None, "❌ تنظیمات سرور قیمت لحظه‌ای یافت نشد."

            # انتخاب سرور و ساخت URL نهایی
            if is_gold_server_request:
                url = f"{live_price_config.get('gold')}{symbol}"
                logger.info(f"Fetching live price for '{symbol}' from GOLD server.")
            else:
                # برای کریپتو، جفت ارز با USDT ساخته می‌شود
                url = f"{live_price_config.get('crypto')}{symbol.upper()}USDT"
                logger.info(f"Fetching live price for '{symbol}' from CRYPTO server.")
            
            # ارسال درخواست به سرور
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status() # در صورت بروز خطای HTTP، استثنا ایجاد می‌کند
                price_data = response.json()
                
            # فرمت‌بندی قیمت برای نمایش بهتر
            price_value = price_data.get('price', 'N/A')
            if is_gold_server_request:
                try:
                    # برای قیمت‌های ریالی، فرمت را با کاما جدا می‌کنیم
                    price_value = f"{int(float(price_value)):,}"
                except (ValueError, TypeError):
                    pass # اگر تبدیل ممکن نبود، همان مقدار رشته‌ای باقی می‌ماند
            
            # ساخت پیام نهایی برای نمایش به کاربر
            formatted_text = (
                f"💹 **قیمت لحظه‌ای {price_data.get('symbol', symbol)}**\n\n"
                f"📈 قیمت: **{price_value}**\n"
                f"🕒 زمان: {price_data.get('time', 'N/A')}\n"
            )
            return formatted_text, None # خروجی موفق: (متن پیام, بدون خطا)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching live price for {symbol}: {e}")
            return None, f"❌ قیمت برای نماد **{symbol}** یافت نشد. لطفاً از وجود آن مطمئن شوید."
        except Exception as e:
            logger.error(f"General error fetching live price for {symbol}: {e}")
            return None, "❌ خطا در ارتباط با سرور قیمت لحظه‌ای. لطفاً بعداً تلاش کنید."

    
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

    @staticmethod
    async def fetch_gold_analysis(symbol: str):
        """Fetches analysis for gold and currency symbols."""
        config = Config.get_api_server_config('gold_analysis')
        url = f"{config['base_url']}{config['endpoint']}"
        payload = {"symbol": symbol, "currency": "IRT", "timeframe": "1d"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json(), None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during gold analysis for {symbol}: {e}")
            return None, f"خطا در ارتباط با سرور تحلیل: {e.response.status_code}"
        except Exception as e:
            logger.error(f"General error during gold analysis for {symbol}: {e}")
            return None, "یک خطای غیرمنتظره در سرور تحلیل رخ داد."

    @staticmethod
    async def fetch_backtest_results(symbol: str):
        """Fetches backtest results for a given symbol."""
        config = Config.get_api_server_config('backtest')
        url = f"{config['base_url']}{config['endpoint']}{symbol}"
        
        try:
            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json(), None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during backtest for {symbol}: {e}")
            error_detail = e.response.json().get("detail", e.response.text)
            return None, f"خطا در اجرای بک‌تست: {error_detail}"
        except Exception as e:
            logger.error(f"General error during backtest for {symbol}: {e}")
            return None, "یک خطای غیرمنتظره در سرور بک‌تست رخ داد."

    
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