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
from typing import List, Tuple

class SymbolManager:
    """
    این کلاس لیست‌های ثابت نمادها را برای بازارهای مختلف به صورت هاردکد مدیریت می‌کند
    تا پروژه هیچ وابستگی به فایل‌های خارجی نداشته باشد.
    """
    
# لیست کامل نمادهای طلا و سکه استخراج شده از CSV
    _GOLD_SYMBOLS: List[Tuple[str, str]] = [
        ("طلای 18 عیار", "IR_GOLD_18K"),
        ("طلای 24 عیار", "IR_GOLD_24K"),
        ("سکه امامی", "IR_COIN_EMAMI"),
        ("سکه بهار آزادی", "IR_COIN_BAHAR"),
        ("نیم سکه", "IR_COIN_HALF"),
        ("ربع سکه", "IR_COIN_QUARTER"),
        ("سکه گرمی", "IR_COIN_GERAMI"),
        ("مثقال طلا", "IR_MITHQAL"),
    ]

    # لیست کامل نمادهای ارز استخراج شده از CSV
    _CURRENCY_SYMBOLS: List[Tuple[str, str]] = [
        ("دلار آمریکا", "USD"),
        ("یورو", "EUR"),
        ("درهم امارات", "AED"),
        ("پوند انگلیس", "GBP"),
        ("لیر ترکیه", "TRY"),
        ("یوان چین", "CNY"),
        ("ین ژاپن", "JPY"),
        ("دلار کانادا", "CAD"),
        ("دلار استرالیا", "AUD"),
        ("فرانک سوئیس", "CHF"),
        ("روبل روسيه", "RUB"),
        ("انس طلا جهانی", "XAUUSD")
    ]
    # لیست نمادهای محبوب کریپتو
    _CRYPTO_SYMBOLS: List[Tuple[str, str]] = [
        ("Bitcoin", "BTC"), ("Ethereum", "ETH"), ("BNB", "BNB"),
        ("Solana", "SOL"), ("XRP", "XRP"), ("Cardano", "ADA"),
        ("Dogecoin", "DOGE"), ("Polygon", "MATIC")
    ]
    
    # لیست کامل نمادهای بایننس
    _FULL_BINANCE_SYMBOLS: List[Tuple[str, str]] = [
        ('Bitcoin', 'BTC'), ('Ethereum', 'ETH'), ('BNB', 'BNB'), ('XRP', 'XRP'), 
        ('Cardano', 'ADA'), ('Solana', 'SOL'), ('Dogecoin', 'DOGE'), ('TRON', 'TRX'), 
        ('Toncoin', 'TON'), ('Polygon', 'MATIC'), ('Avalanche', 'AVAX'), ('Polkadot', 'DOT'), 
        ('Uniswap', 'UNI'), ('Chainlink', 'LINK'), ('Cosmos', 'ATOM'), ('ICP', 'ICP'), 
        ('Litecoin', 'LTC'), ('Bitcoin Cash', 'BCH'), ('Ethereum Classic', 'ETC'), 
        ('Filecoin', 'FIL'), ('NEAR Protocol', 'NEAR'), ('Fantom', 'FTM'), 
        ('Algorand', 'ALGO'), ('Shiba Inu', 'SHIB'), ('Pepe', 'PEPE'), ('Floki', 'FLOKI'), 
        ('Axie Infinity', 'AXS'), ('The Sandbox', 'SAND'), ('Gala', 'GALA')
    ]

    def get_symbols_by_market(self, market_type: str) -> List[Tuple[str, str]]:
        """
        لیست نمادها را برای یک بازار خاص برمی‌گرداند.
        """
        if market_type == 'gold':
            return self._GOLD_SYMBOLS
        elif market_type == 'currency':
            return self._CURRENCY_SYMBOLS
        elif market_type == 'crypto':
            return self._CRYPTO_SYMBOLS
        elif market_type == 'crypto_full':
            return self._FULL_BINANCE_SYMBOLS
        else:
            return []

# ایجاد یک نمونه سراسری برای دسترسی آسان در کل پروژه
symbol_manager = SymbolManager()

