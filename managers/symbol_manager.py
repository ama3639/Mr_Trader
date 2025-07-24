"""
مدیریت نمادهای ارز و اطلاعات بازار MrTrader Bot
"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import json

from core.config import Config
from utils.logger import logger
from database.database_manager import DatabaseManager
from core.cache import cache
from api.api_client import ApiClient


class SymbolManager:
    """مدیریت نمادهای ارز دیجیتال"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.popular_symbols = self._get_default_symbols()
        self.symbol_cache = {}
        self.market_data_cache = {}
        self._initialize_symbol_manager()
    
    def _initialize_symbol_manager(self):
        """مقداردهی اولیه مدیر نمادها"""
        try:
            # ایجاد جدول نمادها اگر وجود نداشته باشد
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    name TEXT,
                    category TEXT,
                    market_cap REAL,
                    volume_24h REAL,
                    price REAL,
                    change_24h REAL,
                    rank_position INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    is_popular BOOLEAN DEFAULT 0,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ایجاد جدول watchlist
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS user_watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, symbol)
                )
            """)
            
            # ایجاد جدول قیمت‌های تاریخی
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    timeframe TEXT DEFAULT '1h'
                )
            """)
            
            logger.info("Symbol manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing symbol manager: {e}")
    
    def _get_default_symbols(self) -> List[str]:
        """نمادهای پیش‌فرض محبوب"""
        return [
            'BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE',
            'AVAX', 'SHIB', 'MATIC', 'LTC', 'UNI', 'LINK', 'ATOM',
            'FTM', 'ALGO', 'VET', 'ICP', 'FIL', 'TRX', 'ETC', 'THETA',
            'XLM', 'BCH', 'NEAR', 'FLOW', 'MANA', 'SAND', 'AXS'
        ]
    
    async def update_symbol_data(self, symbol: str, force_update: bool = False) -> Dict[str, Any]:
        """بروزرسانی اطلاعات یک نماد"""
        try:
            # بررسی کش اگر force_update نباشد
            cache_key = f"symbol_data_{symbol}"
            if not force_update:
                cached_data = cache.get(cache_key)
                if cached_data:
                    return cached_data
            
            # دریافت اطلاعات از API
            market_data = await ApiClient.fetch_market_data(symbol, 'USDT')
            if 'error' in market_data:
                logger.warning(f"Failed to fetch market data for {symbol}: {market_data['error']}")
                return {}
            
            symbol_info = await ApiClient.fetch_symbol_info(symbol, 'USDT')
            
            # ساخت دیتای کامل
            symbol_data = {
                'symbol': symbol,
                'name': symbol,  # در API واقعی نام کامل دریافت می‌شود
                'price': market_data.get('price', 0),
                'change_24h': market_data.get('change_percent_24h', 0),
                'volume_24h': market_data.get('volume_24h', 0),
                'high_24h': market_data.get('high_24h', 0),
                'low_24h': market_data.get('low_24h', 0),
                'volume_quote_24h': market_data.get('volume_quote_24h', 0),
                'count_24h': market_data.get('count_24h', 0),
                'status': symbol_info.get('status', 'TRADING') if symbol_info and 'error' not in symbol_info else 'UNKNOWN',
                'base_precision': symbol_info.get('base_precision', 8) if symbol_info and 'error' not in symbol_info else 8,
                'quote_precision': symbol_info.get('quote_precision', 8) if symbol_info and 'error' not in symbol_info else 8,
                'last_updated': datetime.now().isoformat()
            }
            
            # ذخیره در دیتابیس
            await self._save_symbol_to_db(symbol_data)
            
            # ذخیره در کش (5 دقیقه)
            cache.set(cache_key, symbol_data, 300)
            
            logger.debug(f"Updated symbol data for {symbol}")
            return symbol_data
            
        except Exception as e:
            logger.error(f"Error updating symbol data for {symbol}: {e}")
            return {}
    
    async def _save_symbol_to_db(self, symbol_data: Dict[str, Any]):
        """ذخیره اطلاعات نماد در دیتابیس"""
        try:
            # بروزرسانی یا درج
            self.db.execute_query("""
                INSERT OR REPLACE INTO symbols 
                (symbol, name, price, change_24h, volume_24h, market_cap, last_updated, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol_data['symbol'],
                symbol_data['name'],
                symbol_data['price'],
                symbol_data['change_24h'],
                symbol_data['volume_24h'],
                symbol_data.get('market_cap', 0),
                datetime.now().isoformat(),
                1
            ))
            
            # ذخیره قیمت تاریخی
            self.db.execute_query("""
                INSERT INTO price_history (symbol, price, volume, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                symbol_data['symbol'],
                symbol_data['price'],
                symbol_data['volume_24h'],
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"Error saving symbol to database: {e}")
    
    async def get_symbol_info(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """دریافت اطلاعات کامل یک نماد"""
        try:
            # بررسی کش
            cache_key = f"symbol_info_{symbol}"
            if use_cache:
                cached_info = cache.get(cache_key)
                if cached_info:
                    return cached_info
            
            # دریافت از دیتابیس
            db_result = self.db.fetch_one("""
                SELECT * FROM symbols WHERE symbol = ? AND is_active = 1
            """, (symbol,))
            
            if db_result:
                symbol_info = dict(db_result)
                
                # بروزرسانی اگر داده قدیمی باشد (بیش از 5 دقیقه)
                last_updated = datetime.fromisoformat(symbol_info['last_updated'])
                if datetime.now() - last_updated > timedelta(minutes=5):
                    updated_data = await self.update_symbol_data(symbol, force_update=True)
                    if updated_data:
                        symbol_info.update(updated_data)
                
                # ذخیره در کش
                if use_cache:
                    cache.set(cache_key, symbol_info, 300)
                
                return symbol_info
            else:
                # اگر در دیتابیس نیست، از API دریافت کن
                return await self.update_symbol_data(symbol)
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
    
    async def get_popular_symbols(self, limit: int = 20) -> List[Dict[str, Any]]:
        """دریافت نمادهای محبوب"""
        try:
            # دریافت از API
            top_symbols = await ApiClient.get_top_symbols(limit)
            
            if top_symbols:
                # بروزرسانی اطلاعات در دیتابیس
                for symbol_data in top_symbols:
                    symbol = symbol_data['symbol']
                    
                    # بروزرسانی رتبه در دیتابیس
                    self.db.execute_query("""
                        UPDATE symbols SET 
                            rank_position = ?,
                            is_popular = 1,
                            last_updated = ?
                        WHERE symbol = ?
                    """, (symbol_data['rank'], datetime.now().isoformat(), symbol))
                
                logger.info(f"Retrieved {len(top_symbols)} popular symbols")
                return top_symbols
            else:
                # اگر API در دسترس نیست، از دیتابیس استفاده کن
                db_symbols = self.db.fetch_all("""
                    SELECT symbol, name, price, change_24h, volume_24h, rank_position
                    FROM symbols 
                    WHERE is_popular = 1 AND is_active = 1
                    ORDER BY rank_position ASC, volume_24h DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in db_symbols] if db_symbols else []
            
        except Exception as e:
            logger.error(f"Error getting popular symbols: {e}")
            return []
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """جستجوی نمادها"""
        try:
            query = query.upper().strip()
            
            # جستجو در دیتابیس
            results = self.db.fetch_all("""
                SELECT symbol, name, price, change_24h, volume_24h 
                FROM symbols 
                WHERE (symbol LIKE ? OR name LIKE ?) AND is_active = 1
                ORDER BY 
                    CASE WHEN symbol = ? THEN 1 ELSE 2 END,
                    volume_24h DESC
                LIMIT ?
            """, (f"{query}%", f"%{query}%", query, limit))
            
            search_results = [dict(row) for row in results] if results else []
            
            # اگر نتیجه‌ای نیافت، از نمادهای پیش‌فرض جستجو کن
            if not search_results and query in self.popular_symbols:
                symbol_data = await self.update_symbol_data(query)
                if symbol_data:
                    search_results = [symbol_data]
            
            logger.debug(f"Symbol search for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching symbols with query '{query}': {e}")
            return []
    
    async def add_to_watchlist(self, user_id: int, symbol: str) -> bool:
        """افزودن نماد به watchlist کاربر"""
        try:
            # بررسی معتبر بودن نماد
            is_valid = await ApiClient.validate_symbol_pair(symbol, 'USDT')
            if not is_valid:
                logger.warning(f"Invalid symbol {symbol} for user {user_id}")
                return False
            
            # افزودن به watchlist
            self.db.execute_query("""
                INSERT OR IGNORE INTO user_watchlist (user_id, symbol, added_date)
                VALUES (?, ?, ?)
            """, (user_id, symbol.upper(), datetime.now().isoformat()))
            
            # بروزرسانی اطلاعات نماد
            await self.update_symbol_data(symbol)
            
            logger.info(f"Added {symbol} to watchlist for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist for user {user_id}: {e}")
            return False
    
    async def remove_from_watchlist(self, user_id: int, symbol: str) -> bool:
        """حذف نماد از watchlist کاربر"""
        try:
            self.db.execute_query("""
                DELETE FROM user_watchlist 
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol.upper()))
            
            logger.info(f"Removed {symbol} from watchlist for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing {symbol} from watchlist for user {user_id}: {e}")
            return False
    
    async def get_user_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """دریافت watchlist کاربر"""
        try:
            watchlist_symbols = self.db.fetch_all("""
                SELECT uw.symbol, uw.added_date, s.price, s.change_24h, s.volume_24h
                FROM user_watchlist uw
                LEFT JOIN symbols s ON uw.symbol = s.symbol
                WHERE uw.user_id = ?
                ORDER BY uw.added_date DESC
            """, (user_id,))
            
            if not watchlist_symbols:
                return []
            
            watchlist = []
            for row in watchlist_symbols:
                symbol_data = dict(row)
                
                # اگر اطلاعات قیمت موجود نیست، از API دریافت کن
                if not symbol_data.get('price'):
                    updated_data = await self.get_symbol_info(symbol_data['symbol'])
                    if updated_data:
                        symbol_data.update(updated_data)
                
                watchlist.append(symbol_data)
            
            logger.debug(f"Retrieved watchlist for user {user_id}: {len(watchlist)} symbols")
            return watchlist
            
        except Exception as e:
            logger.error(f"Error getting watchlist for user {user_id}: {e}")
            return []
    
    async def get_price_history(self, symbol: str, timeframe: str = '1h', 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """دریافت تاریخچه قیمت"""
        try:
            history = self.db.fetch_all("""
                SELECT price, volume, timestamp 
                FROM price_history 
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol.upper(), timeframe, limit))
            
            if history:
                return [dict(row) for row in history]
            else:
                # اگر تاریخچه‌ای نداریم، قیمت فعلی را برگردان
                current_data = await self.get_symbol_info(symbol)
                if current_data:
                    return [{
                        'price': current_data.get('price', 0),
                        'volume': current_data.get('volume_24h', 0),
                        'timestamp': datetime.now().isoformat()
                    }]
                return []
            
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return []
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """نمای کلی بازار"""
        try:
            # آمار کلی
            total_symbols = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM symbols WHERE is_active = 1
            """)['count']
            
            # نمادهای برتر بر اساس تغییر قیمت
            top_gainers = self.db.fetch_all("""
                SELECT symbol, change_24h, price 
                FROM symbols 
                WHERE is_active = 1 AND change_24h > 0
                ORDER BY change_24h DESC
                LIMIT 5
            """)
            
            top_losers = self.db.fetch_all("""
                SELECT symbol, change_24h, price 
                FROM symbols 
                WHERE is_active = 1 AND change_24h < 0
                ORDER BY change_24h ASC
                LIMIT 5
            """)
            
            # نمادهای با بالاترین حجم
            top_volume = self.db.fetch_all("""
                SELECT symbol, volume_24h, price 
                FROM symbols 
                WHERE is_active = 1
                ORDER BY volume_24h DESC
                LIMIT 5
            """)
            
            market_overview = {
                'total_symbols': total_symbols,
                'top_gainers': [dict(row) for row in top_gainers] if top_gainers else [],
                'top_losers': [dict(row) for row in top_losers] if top_losers else [],
                'top_volume': [dict(row) for row in top_volume] if top_volume else [],
                'last_updated': datetime.now().isoformat()
            }
            
            # محاسبه شاخص کلی بازار
            avg_change = self.db.fetch_one("""
                SELECT AVG(change_24h) as avg_change 
                FROM symbols 
                WHERE is_active = 1 AND is_popular = 1
            """)
            
            if avg_change and avg_change['avg_change'] is not None:
                market_overview['market_sentiment'] = {
                    'average_change': round(avg_change['avg_change'], 2),
                    'trend': 'bullish' if avg_change['avg_change'] > 1 else 'bearish' if avg_change['avg_change'] < -1 else 'neutral'
                }
            
            logger.info("Market overview generated successfully")
            return market_overview
            
        except Exception as e:
            logger.error(f"Error generating market overview: {e}")
            return {}
    
    async def get_symbol_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """دریافت هشدارهای قیمتی کاربر"""
        try:
            # در پیاده‌سازی کامل، جدول price_alerts ایجاد شود
            alerts = self.db.fetch_all("""
                SELECT symbol, target_price, alert_type, created_date
                FROM price_alerts 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_date DESC
            """, (user_id,))
            
            return [dict(row) for row in alerts] if alerts else []
            
        except Exception as e:
            # اگر جدول price_alerts وجود نداشته باشد
            if "no such table" in str(e).lower():
                return []
            logger.error(f"Error getting alerts for user {user_id}: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30):
        """پاکسازی داده‌های قدیمی"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # حذف تاریخچه قیمت قدیمی
            deleted_count = self.db.execute_query("""
                DELETE FROM price_history 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            logger.info(f"Cleaned up {deleted_count} old price history records older than {days} days")
            
            # پاکسازی کش
            cache.clear_pattern("symbol_*")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def batch_update_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """بروزرسانی دسته‌ای نمادها"""
        try:
            results = {}
            
            # محدود کردن تعداد درخواست‌های همزمان
            semaphore = asyncio.Semaphore(5)
            
            async def update_single_symbol(symbol: str) -> Tuple[str, bool]:
                async with semaphore:
                    try:
                        data = await self.update_symbol_data(symbol, force_update=True)
                        return symbol, bool(data)
                    except Exception as e:
                        logger.error(f"Error updating {symbol}: {e}")
                        return symbol, False
            
            # اجرای همزمان
            tasks = [update_single_symbol(symbol) for symbol in symbols]
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # پردازش نتایج
            for result in completed_tasks:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                else:
                    symbol, success = result
                    results[symbol] = success
            
            successful_updates = sum(1 for success in results.values() if success)
            logger.info(f"Batch update completed: {successful_updates}/{len(symbols)} symbols updated")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return {}
    
    async def get_symbol_statistics(self, symbol: str) -> Dict[str, Any]:
        """آمار تفصیلی یک نماد"""
        try:
            # اطلاعات فعلی
            current_info = await self.get_symbol_info(symbol)
            if not current_info:
                return {}
            
            # آمار تاریخی (7 روز گذشته)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            historical_prices = self.db.fetch_all("""
                SELECT price, timestamp 
                FROM price_history 
                WHERE symbol = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (symbol.upper(), week_ago))
            
            stats = {
                'symbol': symbol,
                'current_price': current_info.get('price', 0),
                'change_24h': current_info.get('change_24h', 0),
                'volume_24h': current_info.get('volume_24h', 0),
                'high_24h': current_info.get('high_24h', 0),
                'low_24h': current_info.get('low_24h', 0)
            }
            
            if historical_prices:
                prices = [float(row['price']) for row in historical_prices]
                stats.update({
                    'week_high': max(prices),
                    'week_low': min(prices),
                    'week_change': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] > 0 else 0,
                    'volatility': self._calculate_volatility(prices),
                    'price_trend': 'up' if len(prices) > 1 and prices[-1] > prices[0] else 'down' if len(prices) > 1 else 'stable'
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics for {symbol}: {e}")
            return {}
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """محاسبه نوسان قیمت"""
        try:
            if len(prices) < 2:
                return 0.0
            
            # محاسبه درصد تغییرات
            changes = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    change = (prices[i] - prices[i-1]) / prices[i-1] * 100
                    changes.append(abs(change))
            
            # میانگین تغییرات مطلق
            return sum(changes) / len(changes) if changes else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    async def validate_symbol(self, symbol: str) -> bool:
        """اعتبارسنجی نماد"""
        try:
            return await ApiClient.validate_symbol_pair(symbol, 'USDT')
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False


# Export
__all__ = ['SymbolManager']