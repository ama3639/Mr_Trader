"""
مدیریت دیتابیس SQLite برای MrTrader Bot
"""
import sqlite3
import asyncio
from threading import Lock
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from contextlib import contextmanager

from core.config import Config
from utils.logger import logger, DatabaseLogger


class DatabaseManager:
    """کلاس مدیریت دیتابیس SQLite"""
    
    _instance = None
    _lock = Lock()
    _connection_pool = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = Config.DATABASE_FILE
            self.initialized = True
            self._create_tables()
            DatabaseLogger.log_connection_status("initialized", str(self.db_path))
    
    @contextmanager
    def get_connection(self):
        """Context manager برای مدیریت اتصال دیتابیس"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # برای دسترسی ستون‌ها با نام
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self):
        """ایجاد جداول دیتابیس"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول کاربران
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    package TEXT DEFAULT 'none',
                    package_expiry DATETIME,
                    balance REAL DEFAULT 0.0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    is_blocked BOOLEAN DEFAULT 0,
                    is_premium BOOLEAN DEFAULT 0,
                    entry_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    api_calls_count INTEGER DEFAULT 0,
                    daily_limit INTEGER DEFAULT 10,
                    security_token TEXT,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until DATETIME,
                    FOREIGN KEY (referred_by) REFERENCES users (telegram_id)
                )
            """)
            
            # جدول ادمین‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    level INTEGER DEFAULT 1,
                    permissions TEXT,
                    added_by INTEGER,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    last_login DATETIME,
                    FOREIGN KEY (added_by) REFERENCES admins (telegram_id)
                )
            """)
            
            # جدول پرداخت‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    payment_code TEXT UNIQUE NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'IRR',
                    package_type TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    transaction_id TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_date DATETIME,
                    processed_by INTEGER,
                    notes TEXT,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            """)
            
            # جدول لاگ‌های کاربری
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            """)
            
            # جدول سیگنال‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    strength INTEGER,
                    accuracy REAL,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_date DATETIME,
                    status TEXT DEFAULT 'active',
                    created_by INTEGER,
                    analysis_data TEXT
                )
            """)
            
            # جدول تیکت‌های پشتیبانی
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    ticket_id TEXT UNIQUE NOT NULL,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    priority TEXT DEFAULT 'normal',
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    assigned_to INTEGER,
                    closed_date DATETIME,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (assigned_to) REFERENCES admins (telegram_id)
                )
            """)
            
            # جدول پیام‌های تیکت
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    sender_id INTEGER NOT NULL,
                    sender_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    attachment_path TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets (ticket_id)
                )
            """)
            
            # جدول تنظیمات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    category TEXT,
                    description TEXT,
                    updated_by INTEGER,
                    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول کش
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    expires_at DATETIME,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            DatabaseLogger.log_migration("initial", "completed")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Union[List[Dict], int, None]:
        """اجرای کوئری دیتابیس
        
        Args:
            query: کوئری SQL
            params: پارامترهای کوئری
            fetch: آیا نتیجه برگردانده شود
            
        Returns:
            نتیجه کوئری یا تعداد ردیف‌های تاثیر یافته
        """
        start_time = datetime.now()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch:
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    execution_time = (datetime.now() - start_time).total_seconds()
                    DatabaseLogger.log_query(query, params, execution_time)
                    return result
                else:
                    conn.commit()
                    affected_rows = cursor.rowcount
                    execution_time = (datetime.now() - start_time).total_seconds()
                    DatabaseLogger.log_query(query, params, execution_time)
                    return affected_rows
                    
        except sqlite3.Error as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            DatabaseLogger.log_query(f"ERROR: {query}", params, execution_time)
            logger.error(f"Database query error: {e}")
            return None
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """دریافت یک رکورد از دیتابیس (برای سازگاری با main.py)
        
        Args:
            query: کوئری SQL
            params: پارامترهای کوئری
            
        Returns:
            یک رکورد یا None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Database fetch_one error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in fetch_one: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """دریافت همه رکوردها از دیتابیس
        
        Args:
            query: کوئری SQL
            params: پارامترهای کوئری
            
        Returns:
            لیست رکوردها
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database fetch_all error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_all: {e}")
            return []
    
    def execute(self, query: str, params: tuple = ()) -> bool:
        """اجرای کوئری بدون بازگشت نتیجه
        
        Args:
            query: کوئری SQL
            params: پارامترهای کوئری
            
        Returns:
            True در صورت موفقیت
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Database execute error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in execute: {e}")
            return False
    
    def close_connection(self):
        """بستن اتصال دیتابیس (برای سازگاری با main.py)"""
        # در این implementation اتصالات خودکار بسته می‌شوند
        # این متد فقط برای سازگاری با main.py اضافه شده
        logger.info("Database connections closed")
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """دریافت کاربر با آیدی تلگرام"""
        query = "SELECT * FROM users WHERE telegram_id = ?"
        return self.fetch_one(query, (telegram_id,))
    
    def create_user(self, telegram_id: int, username: str = None, first_name: str = None, 
                   last_name: str = None, referral_code: str = None) -> bool:
        """ایجاد کاربر جدید"""
        query = """
            INSERT INTO users (telegram_id, username, first_name, last_name, referral_code)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (telegram_id, username, first_name, last_name, referral_code))
        return result is not None and result > 0
    
    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات کاربر"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE users SET {set_clause}, last_activity = CURRENT_TIMESTAMP WHERE telegram_id = ?"
        
        params = list(kwargs.values()) + [telegram_id]
        result = self.execute_query(query, params)
        return result is not None and result > 0
    
    def add_user_log(self, telegram_id: int, action: str, details: str = None, 
                     ip_address: str = None, user_agent: str = None) -> bool:
        """افزودن لاگ کاربری"""
        query = """
            INSERT INTO user_logs (telegram_id, action, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (telegram_id, action, details, ip_address, user_agent))
        return result is not None and result > 0
    
    def get_user_logs(self, telegram_id: int, limit: int = 50) -> List[Dict]:
        """دریافت لاگ‌های کاربر"""
        query = """
            SELECT * FROM user_logs 
            WHERE telegram_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        return self.fetch_all(query, (telegram_id, limit))
    
    def is_admin(self, telegram_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        query = "SELECT id FROM admins WHERE telegram_id = ? AND is_active = 1"
        result = self.fetch_one(query, (telegram_id,))
        return bool(result)
    
    def get_admin_level(self, telegram_id: int) -> int:
        """دریافت سطح دسترسی ادمین"""
        query = "SELECT level FROM admins WHERE telegram_id = ? AND is_active = 1"
        result = self.fetch_one(query, (telegram_id,))
        return result['level'] if result else 0
    
    def add_admin(self, telegram_id: int, level: int = 1, added_by: int = None) -> bool:
        """افزودن ادمین جدید"""
        query = """
            INSERT OR REPLACE INTO admins (telegram_id, level, added_by)
            VALUES (?, ?, ?)
        """
        result = self.execute_query(query, (telegram_id, level, added_by))
        return result is not None and result > 0
    
    def create_payment(self, telegram_id: int, payment_code: str, amount: float,
                      package_type: str = None, payment_method: str = None) -> bool:
        """ایجاد پرداخت جدید"""
        query = """
            INSERT INTO payments (telegram_id, payment_code, amount, package_type, payment_method)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (telegram_id, payment_code, amount, package_type, payment_method))
        return result is not None and result > 0
    
    def get_payment_by_code(self, payment_code: str) -> Optional[Dict]:
        """دریافت پرداخت با کد پیگیری"""
        query = "SELECT * FROM payments WHERE payment_code = ?"
        return self.fetch_one(query, (payment_code,))
    
    def update_payment_status(self, payment_code: str, status: str, processed_by: int = None,
                             transaction_id: str = None, notes: str = None) -> bool:
        """به‌روزرسانی وضعیت پرداخت"""
        query = """
            UPDATE payments 
            SET status = ?, processed_date = CURRENT_TIMESTAMP, processed_by = ?, 
                transaction_id = ?, notes = ?
            WHERE payment_code = ?
        """
        result = self.execute_query(query, (status, processed_by, transaction_id, notes, payment_code))
        return result is not None and result > 0
    
    def get_pending_payments(self, limit: int = 100) -> List[Dict]:
        """دریافت پرداخت‌های در انتظار"""
        query = """
            SELECT p.*, u.username, u.first_name 
            FROM payments p
            LEFT JOIN users u ON p.telegram_id = u.telegram_id
            WHERE p.status = 'pending'
            ORDER BY p.created_date DESC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))
    
    def create_signal(self, symbol: str, base_currency: str, timeframe: str,
                     signal_type: str, direction: str, entry_price: float = None,
                     stop_loss: float = None, take_profit: float = None,
                     strength: int = None, created_by: int = None,
                     analysis_data: str = None) -> bool:
        """ایجاد سیگنال جدید"""
        query = """
            INSERT INTO signals 
            (symbol, base_currency, timeframe, signal_type, direction, entry_price,
             stop_loss, take_profit, strength, created_by, analysis_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (symbol, base_currency, timeframe, signal_type, direction,
                 entry_price, stop_loss, take_profit, strength, created_by, analysis_data)
        result = self.execute_query(query, params)
        return result is not None and result > 0
    
    def get_active_signals(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """دریافت سیگنال‌های فعال"""
        if symbol:
            query = """
                SELECT * FROM signals 
                WHERE status = 'active' AND symbol = ?
                ORDER BY created_date DESC 
                LIMIT ?
            """
            params = (symbol, limit)
        else:
            query = """
                SELECT * FROM signals 
                WHERE status = 'active'
                ORDER BY created_date DESC 
                LIMIT ?
            """
            params = (limit,)
        
        return self.fetch_all(query, params)
    
    def create_support_ticket(self, telegram_id: int, ticket_id: str, subject: str,
                             message: str, priority: str = 'normal') -> bool:
        """ایجاد تیکت پشتیبانی"""
        query = """
            INSERT INTO support_tickets (telegram_id, ticket_id, subject, message, priority)
            VALUES (?, ?, ?, ?, ?)
        """
        result = self.execute_query(query, (telegram_id, ticket_id, subject, message, priority))
        return result is not None and result > 0
    
    def get_user_tickets(self, telegram_id: int) -> List[Dict]:
        """دریافت تیکت‌های کاربر"""
        query = """
            SELECT * FROM support_tickets 
            WHERE telegram_id = ? 
            ORDER BY created_date DESC
        """
        return self.fetch_all(query, (telegram_id,))
    
    def get_open_tickets(self, limit: int = 100) -> List[Dict]:
        """دریافت تیکت‌های باز"""
        query = """
            SELECT st.*, u.username, u.first_name
            FROM support_tickets st
            LEFT JOIN users u ON st.telegram_id = u.telegram_id
            WHERE st.status = 'open'
            ORDER BY st.created_date ASC
            LIMIT ?
        """
        return self.fetch_all(query, (limit,))
    
    def set_cache(self, key: str, value: str, expires_minutes: int = 60) -> bool:
        """تنظیم کش"""
        expires_at = datetime.now().timestamp() + (expires_minutes * 60)
        query = """
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, datetime(?, 'unixepoch'))
        """
        result = self.execute_query(query, (key, value, expires_at))
        return result is not None and result > 0
    
    def get_cache(self, key: str) -> Optional[str]:
        """دریافت کش"""
        query = """
            SELECT value FROM cache 
            WHERE key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
        """
        result = self.fetch_one(query, (key,))
        return result['value'] if result else None
    
    def clear_expired_cache(self) -> int:
        """پاکسازی کش منقضی شده"""
        query = "DELETE FROM cache WHERE expires_at < datetime('now')"
        return self.execute_query(query) or 0
    
    def get_statistics(self) -> Dict[str, int]:
        """دریافت آمار کلی سیستم"""
        stats = {}
        
        # تعداد کاربران
        result = self.fetch_one("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result['count'] if result else 0
        
        # کاربران فعال امروز
        result = self.fetch_one("""
            SELECT COUNT(*) as count FROM users 
            WHERE date(last_activity) = date('now')
        """)
        stats['active_today'] = result['count'] if result else 0
        
        # پرداخت‌های در انتظار
        result = self.fetch_one("""
            SELECT COUNT(*) as count FROM payments WHERE status = 'pending'
        """)
        stats['pending_payments'] = result['count'] if result else 0
        
        # تیکت‌های باز
        result = self.fetch_one("""
            SELECT COUNT(*) as count FROM support_tickets WHERE status = 'open'
        """)
        stats['open_tickets'] = result['count'] if result else 0
        
        return stats
    
    def cleanup_old_data(self, days: int = 90):
        """پاکسازی داده‌های قدیمی"""
        cleanup_queries = [
            ("DELETE FROM user_logs WHERE timestamp < datetime('now', '-{} days')".format(days), "user_logs"),
            ("DELETE FROM cache WHERE expires_at < datetime('now', '-1 days')", "expired_cache"),
            ("DELETE FROM signals WHERE status = 'expired' AND created_date < datetime('now', '-{} days')".format(days), "old_signals")
        ]
        
        total_cleaned = 0
        for query, table in cleanup_queries:
            result = self.execute_query(query)
            if result:
                total_cleaned += result
                logger.info(f"Cleaned {result} records from {table}")
        
        return total_cleaned
    
    @classmethod
    def ensure_user_table_exists(cls):
        """اطمینان از وجود جدول کاربران"""
        instance = cls()
        # جدول از قبل در _create_tables ایجاد شده است
        return True
    
    @classmethod
    def ensure_token_column_in_users(cls):
        """اطمینان از وجود ستون token در جدول users"""
        instance = cls()
        try:
            with instance.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'security_token' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN security_token TEXT")
                    conn.commit()
                    logger.info("Added security_token column to users table")
                    
        except sqlite3.Error as e:
            logger.error(f"Error ensuring token column: {e}")
    
    @classmethod
    def add_description_column_to_user_logs(cls):
        """اضافه کردن ستون description به جدول user_logs"""
        instance = cls()
        try:
            with instance.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(user_logs)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'description' not in columns:
                    cursor.execute("ALTER TABLE user_logs ADD COLUMN description TEXT")
                    conn.commit()
                    logger.info("Added description column to user_logs table")
                    
        except sqlite3.Error as e:
            logger.error(f"Error adding description column: {e}")

    def count_users(self) -> int:
        """تعداد کل کاربران را شمارش می‌کند."""
        query = "SELECT COUNT(id) as total FROM users"
        result = self.fetch_one(query)
        return result['total'] if result and 'total' in result else 0

    def get_users_paginated(self, page: int = 1, per_page: int = 5) -> List[Dict]:
        """لیستی از کاربران را به صورت صفحه‌بندی شده برمی‌گرداند."""
        offset = (page - 1) * per_page
        query = "SELECT telegram_id, first_name, last_name, username FROM users ORDER BY id DESC LIMIT ? OFFSET ?"
        params = (per_page, offset)
        return self.fetch_all(query, params)
    
# Export برای استفاده آسان‌تر
database_manager = DatabaseManager()

__all__ = ['DatabaseManager', 'database_manager']