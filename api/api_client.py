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
from core.cache import cache
from utils.logger import logger


class ApiClient:
    """کلاینت یکپارچه برای تمام API ها"""
    
    def __init__(self):
        from managers.settings_manager import settings_manager
        self.settings_manager = settings_manager
        self.session = None
        self._rate_limiter = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """دریافت session HTTP"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'MrTrader-Bot/2.0'
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
    
    async def _make_request(
        self, 
        url: str, 
        method: str = "GET", 
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """درخواست HTTP با مدیریت خطا و تلاش مجدد"""
        
        session = await self._get_session()
        last_error = None
        
        for attempt in range(max_retries):
            try:
                request_headers = headers or {}
                
                # اضافه کردن API key اگر موجود باشد
                if hasattr(Config, 'API_KEY') and Config.API_KEY:
                    request_headers['X-API-Key'] = Config.API_KEY
                
                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers
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
    
    async def fetch_strategy_analysis(
        self, 
        strategy: str, 
        symbol: str, 
        currency: str, 
        timeframe: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        دریافت تحلیل برای استراتژی مشخص
        
        Args:
            strategy: نام استراتژی (price_action, ichimoku, fibonacci, etc.)
            symbol: نماد ارز
            currency: ارز مرجع
            timeframe: تایم‌فریم
            use_cache: استفاده از کش
            
        Returns:
            Dict شامل نتیجه تحلیل یا خطا
        """
        try:
            # بررسی کش ابتدا
            if use_cache:
                cached_result = cache.get_signal(strategy, symbol, currency, timeframe)
                if cached_result:
                    logger.info(f"Cache hit for {strategy} analysis: {symbol}/{currency} @ {timeframe}")
                    return cached_result
            
            # دریافت آدرس API از SettingsManager
            strategy_url = self.settings_manager.get_strategy_url(strategy)
            if not strategy_url:
                return {"error": f"URL not found for strategy: {strategy}"}
            
            # پارامترهای درخواست
            request_data = {
                "symbol": symbol.upper(),
                "currency": currency.upper(),
                "timeframe": timeframe,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Requesting {strategy} analysis for {symbol}/{currency} @ {timeframe}")
            
            # دریافت تنظیمات استراتژی
            timeout = self.settings_manager.get_strategy_timeout(strategy)
            retry_count = self.settings_manager.get_strategy_retry_count(strategy)
            
            # ارسال درخواست
            result = await self._make_request(
                url=strategy_url,
                method="POST",
                data=request_data,
                max_retries=retry_count
            )
            
            if "error" not in result:
                # ذخیره در کش
                cache_duration = self.settings_manager.get_strategy_cache_duration(strategy)
                cache.set_signal(strategy, symbol, currency, timeframe, result, cache_duration)
                logger.info(f"Analysis result cached for {strategy} {symbol}/{currency} @ {timeframe}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fetch_strategy_analysis: {e}")
            return {"error": str(e)}
    
    async def fetch_price_analysis(
        self, 
        symbol: str, 
        currency: str, 
        timeframe: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """دریافت تحلیل پرایس اکشن (سازگاری با کد قبلی)"""
        return await self.fetch_strategy_analysis("price_action", symbol, currency, timeframe, use_cache)
    
    async def fetch_live_price(
        self, 
        symbol: str, 
        currency: str,
        use_cache: bool = True
    ) -> float:
        """
        دریافت قیمت زنده از Binance API یا سرویس محلی
        
        Args:
            symbol: نماد ارز
            currency: ارز مرجع
            use_cache: استفاده از کش
            
        Returns:
            float: قیمت فعلی
        """
        try:
            # بررسی کش
            if use_cache:
                cached_price = cache.get_price(symbol, currency)
                if cached_price:
                    logger.debug(f"Cache hit for price: {symbol}/{currency} = {cached_price}")
                    return cached_price
            
            # ابتدا تلاش برای استفاده از سرویس محلی
            live_price_config = self.settings_manager.get_live_price_config()
            binance_config = live_price_config.get("binance", {})
            
            if binance_config.get("url"):
                # استفاده از سرویس محلی
                url = binance_config["url"]
                params = {
                    "symbol": symbol.upper(),
                    "currency": currency.upper()
                }
                
                logger.debug(f"Requesting live price from local service: {symbol}/{currency}")
                
                result = await self._make_request(
                    url=f"{url}?symbol={params['symbol']}&currency={params['currency']}",
                    method="GET",
                    max_retries=binance_config.get("retry_count", 2)
                )
                
                if "error" not in result and "price" in result:
                    price = float(result["price"])
                    if price > 0:
                        cache.set_price(symbol, currency, price)
                        logger.debug(f"Price cached from local service: {symbol}/{currency} = {price}")
                        return price
            
            # در صورت عدم دسترسی به سرویس محلی، استفاده از Binance API
            binance_symbol = f"{symbol.upper()}{currency.upper()}"
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
            
            logger.debug(f"Requesting live price from Binance: {binance_symbol}")
            
            result = await self._make_request(
                url=url,
                method="GET",
                max_retries=3
            )
            
            if "error" in result:
                raise Exception(result["error"])
            
            price = float(result.get("price", 0))
            
            # ذخیره در کش
            if price > 0:
                cache.set_price(symbol, currency, price)
                logger.debug(f"Price cached from Binance: {symbol}/{currency} = {price}")
            
            return price
            
        except Exception as e:
            logger.error(f"Error fetching live price for {symbol}/{currency}: {e}")
            return 0.0
    
    async def fetch_market_data(
        self, 
        symbol: str, 
        currency: str,
        timeframe: str = "1d",
        limit: int = 100
    ) -> Dict[str, Any]:
        """دریافت داده‌های بازار (کندل‌ها)"""
        try:
            # استفاده از Binance API مستقیم
            binance_symbol = f"{symbol.upper()}{currency.upper()}"
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={timeframe}&limit={limit}"
            
            logger.info(f"Requesting market data for {binance_symbol} @ {timeframe}")
            
            result = await self._make_request(url=url, method="GET")
            
            if "error" in result:
                return result
            
            # پردازش داده‌های کندل
            processed_data = []
            if isinstance(result, list):
                for kline in result:
                    processed_data.append({
                        "timestamp": int(kline[0]),
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5])
                    })
            
            return {
                "symbol": binance_symbol,
                "timeframe": timeframe,
                "data": processed_data,
                "count": len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {"error": str(e)}
    
    async def fetch_symbol_info(
        self, 
        symbol: str, 
        currency: str
    ) -> Dict[str, Any]:
        """دریافت اطلاعات نماد"""
        try:
            binance_symbol = f"{symbol.upper()}{currency.upper()}"
            url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={binance_symbol}"
            
            logger.debug(f"Requesting symbol info for {binance_symbol}")
            
            result = await self._make_request(url=url, method="GET")
            
            if "error" in result:
                return result
            
            # استخراج اطلاعات مفید
            if "symbols" in result and len(result["symbols"]) > 0:
                symbol_info = result["symbols"][0]
                return {
                    "symbol": symbol_info.get("symbol"),
                    "status": symbol_info.get("status"),
                    "base_asset": symbol_info.get("baseAsset"),
                    "quote_asset": symbol_info.get("quoteAsset"),
                    "base_precision": symbol_info.get("baseAssetPrecision"),
                    "quote_precision": symbol_info.get("quotePrecision")
                }
            else:
                return {"error": "Symbol not found"}
            
        except Exception as e:
            logger.error(f"Error fetching symbol info: {e}")
            return {"error": str(e)}
    
    async def validate_symbol_pair(
        self, 
        symbol: str, 
        currency: str
    ) -> bool:
        """اعتبارسنجی جفت ارز"""
        try:
            symbol_info = await self.fetch_symbol_info(symbol, currency)
            return "error" not in symbol_info and symbol_info.get("status") == "TRADING"
            
        except Exception as e:
            logger.error(f"Error validating symbol pair {symbol}/{currency}: {e}")
            return False
    
    async def get_top_symbols(self, limit: int = 20) -> List[Dict[str, Any]]:
        """دریافت نمادهای برتر بر اساس حجم معاملات"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            
            logger.info("Requesting top symbols by volume")
            
            result = await self._make_request(url=url, method="GET")
            
            if "error" in result:
                return []
            
            if not isinstance(result, list):
                return []
            
            # فیلتر کردن فقط جفت‌های USDT
            usdt_pairs = [
                ticker for ticker in result 
                if ticker["symbol"].endswith("USDT") and float(ticker["quoteVolume"]) > 0
            ]
            
            # مرتب‌سازی بر اساس حجم
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
            
            # تبدیل به فرمت مورد نیاز
            top_symbols = []
            for i, ticker in enumerate(sorted_pairs[:limit]):
                symbol = ticker["symbol"].replace("USDT", "")
                top_symbols.append({
                    "rank": i + 1,
                    "symbol": symbol,
                    "currency": "USDT",
                    "price": float(ticker["lastPrice"]),
                    "change_percent_24h": float(ticker["priceChangePercent"]),
                    "volume_24h": float(ticker["volume"]),
                    "quote_volume_24h": float(ticker["quoteVolume"]),
                    "high_24h": float(ticker["highPrice"]),
                    "low_24h": float(ticker["lowPrice"])
                })
            
            logger.info(f"Retrieved top {len(top_symbols)} symbols")
            return top_symbols
            
        except Exception as e:
            logger.error(f"Error getting top symbols: {e}")
            return []
    
    async def get_24hr_ticker(
        self, 
        symbol: str, 
        currency: str
    ) -> Dict[str, Any]:
        """دریافت آمار 24 ساعته"""
        try:
            binance_symbol = f"{symbol.upper()}{currency.upper()}"
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
            
            logger.debug(f"Requesting 24hr ticker for {binance_symbol}")
            
            result = await self._make_request(url=url, method="GET")
            
            if "error" in result:
                return result
            
            # تبدیل به فرمت استاندارد
            return {
                "symbol": symbol.upper(),
                "currency": currency.upper(),
                "price": float(result.get("lastPrice", 0)),
                "change_24h": float(result.get("priceChange", 0)),
                "change_percent_24h": float(result.get("priceChangePercent", 0)),
                "high_24h": float(result.get("highPrice", 0)),
                "low_24h": float(result.get("lowPrice", 0)),
                "volume_24h": float(result.get("volume", 0)),
                "volume_quote_24h": float(result.get("quoteVolume", 0)),
                "count_24h": int(result.get("count", 0)),
                "open_price": float(result.get("openPrice", 0)),
                "prev_close": float(result.get("prevClosePrice", 0)),
                "bid_price": float(result.get("bidPrice", 0)),
                "ask_price": float(result.get("askPrice", 0))
            }
            
        except Exception as e:
            logger.error(f"Error getting 24hr ticker: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت سرویس‌ها"""
        try:
            results = {}
            
            # بررسی تمام استراتژی‌ها
            all_strategies = self.settings_manager.get_all_strategies()
            
            for strategy in all_strategies:
                try:
                    strategy_config = self.settings_manager.get_strategy_config(strategy)
                    health_url = strategy_config.get("health_url")
                    
                    if health_url:
                        result = await self._make_request(health_url, max_retries=1)
                        results[f"strategy_{strategy}"] = "healthy" if "error" not in result else "unhealthy"
                    else:
                        # اگر health URL نداریم، URL اصلی را تست کنیم
                        strategy_url = self.settings_manager.get_strategy_url(strategy)
                        if strategy_url:
                            ping_result = await self._make_request(strategy_url, max_retries=1)
                            results[f"strategy_{strategy}"] = "reachable" if "error" not in ping_result else "unreachable"
                        else:
                            results[f"strategy_{strategy}"] = "no_url_configured"
                        
                except Exception:
                    results[f"strategy_{strategy}"] = "unhealthy"
            
            # بررسی سرویس قیمت زنده
            try:
                live_price_config = self.settings_manager.get_live_price_config()
                binance_config = live_price_config.get("binance", {})
                
                if binance_config.get("url"):
                    # بررسی سرویس محلی
                    health_url = binance_config["url"].replace("/live_price/", "/health/")
                    ping_result = await self._make_request(health_url, max_retries=1)
                    results["live_price_local"] = "healthy" if "error" not in ping_result else "unhealthy"
                
                # بررسی Binance API
                ping_url = "https://api.binance.com/api/v3/ping"
                ping_result = await self._make_request(ping_url, max_retries=1)
                results["binance"] = "healthy" if "error" not in ping_result else "unhealthy"
                
            except Exception:
                results["live_price"] = "unhealthy"
                results["binance"] = "unhealthy"
            
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
    
    async def batch_price_fetch(self, symbols: List[str], currency: str = "USDT") -> Dict[str, float]:
        """دریافت دسته‌ای قیمت‌ها"""
        try:
            # استفاده از API تک درخواست برای همه قیمت‌ها
            url = "https://api.binance.com/api/v3/ticker/price"
            
            result = await self._make_request(url=url, method="GET")
            
            if "error" in result:
                return {}
            
            prices = {}
            for ticker in result:
                symbol_name = ticker["symbol"]
                if symbol_name.endswith(currency.upper()):
                    base_symbol = symbol_name.replace(currency.upper(), "")
                    if base_symbol in [s.upper() for s in symbols]:
                        prices[base_symbol] = float(ticker["price"])
            
            # ذخیره در کش
            for symbol, price in prices.items():
                cache.set_price(symbol, currency, price)
            
            logger.info(f"Batch fetched {len(prices)} prices")
            return prices
            
        except Exception as e:
            logger.error(f"Error in batch price fetch: {e}")
            return {}
    
    def __del__(self):
        """تمیزکاری هنگام نابودی شیء"""
        try:
            if self.session and not self.session.closed:
                # نمی‌توانیم await کنیم در __del__
                # session در garbage collection بسته خواهد شد
                pass
        except:
            pass


# ایجاد نمونه سراسری
api_client = ApiClient()


# توابع helper برای استخراج جزئیات سیگنال
def extract_signal_details(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """استخراج جزئیات سیگنال از نتیجه تحلیل"""
    try:
        analysis_text = analysis_result.get("analysis_text", "")
        
        # مقادیر پیش‌فرض
        signal_details = {
            "signal_direction": "نامشخص",
            "strength": "متوسط", 
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "support": 0.0,
            "resistance": 0.0,
            "confidence": 0.5
        }
        
        # استخراج اطلاعات از متن (باید بر اساس فرمت واقعی API تنظیم شود)
        if analysis_text:
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip().lower()
                
                if any(word in line for word in ['جهت:', 'direction:', 'سیگنال:', 'signal:']):
                    if any(word in line for word in ['خرید', 'buy', 'صعودی', 'bullish']):
                        signal_details["signal_direction"] = "خرید (BUY)"
                    elif any(word in line for word in ['فروش', 'sell', 'نزولی', 'bearish']):
                        signal_details["signal_direction"] = "فروش (SELL)"
                    elif any(word in line for word in ['نگهداری', 'hold', 'انتظار', 'wait']):
                        signal_details["signal_direction"] = "نگهداری (HOLD)"
                
                elif any(word in line for word in ['قدرت:', 'strength:', 'قوی', 'strong']):
                    if any(word in line for word in ['خیلی قوی', 'very strong', 'بسیار قوی']):
                        signal_details["strength"] = "خیلی قوی"
                    elif any(word in line for word in ['قوی', 'strong']):
                        signal_details["strength"] = "قوی"
                    elif any(word in line for word in ['ضعیف', 'weak']):
                        signal_details["strength"] = "ضعیف"
                
                elif any(word in line for word in ['اعتماد:', 'confidence:', 'احتمال:', 'probability:']):
                    # تلاش برای استخراج عدد
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        confidence = float(numbers[0])
                        if confidence > 1:  # اگر درصد باشد
                            confidence = confidence / 100
                        signal_details["confidence"] = min(max(confidence, 0), 1)
        
        # استفاده از سایر فیلدهای analysis_result
        if "signal_type" in analysis_result:
            signal_details["signal_direction"] = analysis_result["signal_type"]
        
        if "confidence" in analysis_result:
            signal_details["confidence"] = float(analysis_result["confidence"])
        
        if "entry_price" in analysis_result:
            signal_details["entry_price"] = float(analysis_result["entry_price"])
        
        if "stop_loss" in analysis_result:
            signal_details["stop_loss"] = float(analysis_result["stop_loss"])
        
        if "take_profit" in analysis_result:
            signal_details["take_profit"] = float(analysis_result["take_profit"])
        
        return signal_details
        
    except Exception as e:
        logger.error(f"Error extracting signal details: {e}")
        return {
            "signal_direction": "نامشخص",
            "strength": "متوسط",
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "support": 0.0,
            "resistance": 0.0,
            "confidence": 0.5
        }


def format_analysis_result(analysis_result: Dict[str, Any], symbol: str, currency: str) -> str:
    """فرمت‌بندی نتیجه تحلیل برای نمایش"""
    try:
        if "error" in analysis_result:
            return f"❌ خطا در تحلیل {symbol}/{currency}:\n{analysis_result['error']}"
        
        details = extract_signal_details(analysis_result)
        
        # انتخاب ایموجی بر اساس سیگنال
        signal_emojis = {
            "خرید (BUY)": "🟢⬆️",
            "فروش (SELL)": "🔴⬇️", 
            "نگهداری (HOLD)": "🟡⏸️"
        }
        
        signal_direction = details["signal_direction"]
        emoji = signal_emojis.get(signal_direction, "⚪")
        
        # ساخت پیام فرمت شده
        formatted_text = f"{emoji} **تحلیل {symbol}/{currency}**\n\n"
        formatted_text += f"📊 **سیگنال:** {signal_direction}\n"
        formatted_text += f"💪 **قدرت:** {details['strength']}\n"
        formatted_text += f"🎯 **اعتماد:** {details['confidence']:.1%}\n"
        
        if details["entry_price"] > 0:
            formatted_text += f"💰 **قیمت ورود:** ${details['entry_price']:,.4f}\n"
        
        if details["stop_loss"] > 0:
            formatted_text += f"🛑 **حد ضرر:** ${details['stop_loss']:,.4f}\n"
            
        if details["take_profit"] > 0:
            formatted_text += f"🎯 **هدف سود:** ${details['take_profit']:,.4f}\n"
        
        # اضافه کردن متن تحلیل اصلی اگر موجود باشد
        if "analysis_text" in analysis_result:
            formatted_text += f"\n📝 **جزئیات تحلیل:**\n{analysis_result['analysis_text']}"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting analysis result: {e}")
        return f"❌ خطا در فرمت‌بندی تحلیل {symbol}/{currency}"


# Export
__all__ = ['ApiClient', 'api_client', 'extract_signal_details', 'format_analysis_result']