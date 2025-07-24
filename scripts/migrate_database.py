#!/usr/bin/env python3
"""
اسکریپت مهاجرت پایگاه داده MrTrader Bot
"""
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# اضافه کردن پوشه پروژه به path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from utils.logger import logger


class DatabaseMigrator:
    """کلاس مهاجرت پایگاه داده"""
    
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        
        # ایجاد جدول مهاجرت‌ها
        self._create_migrations_table()
    
    def _create_migrations_table(self):
        """ایجاد جدول مهاجرت‌ها"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT UNIQUE NOT NULL,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Migrations table created/verified")
        except Exception as e:
            logger.error(f"Error creating migrations table: {e}")
            raise
    
    def get_applied_migrations(self):
        """دریافت لیست مهاجرت‌های اعمال شده"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT version FROM migrations ORDER BY id")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def apply_migration(self, version: str, description: str, sql_statements: list):
        """اعمال یک مهاجرت"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # شروع transaction
                conn.execute("BEGIN")
                
                # اعمال statements
                for statement in sql_statements:
                    conn.execute(statement)
                
                # ثبت مهاجرت
                conn.execute(
                    "INSERT INTO migrations (version, description) VALUES (?, ?)",
                    (version, description)
                )
                
                # commit
                conn.commit()
                logger.info(f"Migration {version} applied successfully: {description}")
                
        except Exception as e:
            logger.error(f"Error applying migration {version}: {e}")
            raise
    
    def run_migrations(self):
        """اجرای تمام مهاجرت‌های معلق"""
        applied_migrations = self.get_applied_migrations()
        
        # مهاجرت‌های تعریف شده
        migrations = [
            {
                'version': '001_initial_schema',
                'description': 'Initial database schema',
                'statements': self._get_initial_schema()
            },
            {
                'version': '002_add_user_points',
                'description': 'Add user points and referral system',
                'statements': self._get_user_points_schema()
            },
            {
                'version': '003_add_transactions',
                'description': 'Add transaction and payment tables', 
                'statements': self._get_transactions_schema()
            },
            {
                'version': '004_add_signals',
                'description': 'Add signals and analysis tables',
                'statements': self._get_signals_schema()
            },
            {
                'version': '005_add_indexes',
                'description': 'Add performance indexes',
                'statements': self._get_indexes()
            }
        ]
        
        # اعمال مهاجرت‌های جدید
        for migration in migrations:
            if migration['version'] not in applied_migrations:
                logger.info(f"Applying migration: {migration['version']}")
                self.apply_migration(
                    migration['version'],
                    migration['description'], 
                    migration['statements']
                )
            else:
                logger.info(f"Migration {migration['version']} already applied")
        
        logger.info("All migrations completed")
    
    def _get_initial_schema(self):
        """اسکیما اولیه"""
        return [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                email TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE,
                package_type TEXT DEFAULT 'free',
                expiry_date TIMESTAMP,
                language TEXT DEFAULT 'fa',
                timezone TEXT DEFAULT 'Asia/Tehran'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT '{}',
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    
    def _get_user_points_schema(self):
        """اسکیما امتیازات و رفرال"""
        return [
            """
            ALTER TABLE users ADD COLUMN user_points INTEGER DEFAULT 0
            """,
            """
            ALTER TABLE users ADD COLUMN referrer_id INTEGER
            """,
            """
            ALTER TABLE users ADD COLUMN referral_code TEXT UNIQUE
            """,
            """
            ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0
            """,
            """
            ALTER TABLE users ADD COLUMN referral_earnings REAL DEFAULT 0.0
            """,
            """
            CREATE TABLE IF NOT EXISTS referral_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
            )
            """
        ]
    
    def _get_transactions_schema(self):
        """اسکیما تراکنش‌ها"""
        return [
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                user_telegram_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                payment_method TEXT,
                package_id TEXT,
                package_duration_months INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                expires_at TIMESTAMP,
                gateway_transaction_id TEXT,
                notes TEXT,
                FOREIGN KEY (user_telegram_id) REFERENCES users (telegram_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS payment_proofs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                file_id TEXT,
                message_text TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
            )
            """
        ]
    
    def _get_signals_schema(self):
        """اسکیما سیگنال‌ها"""
        return [
            """
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                base_asset TEXT NOT NULL,
                quote_asset TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                strength INTEGER NOT NULL,
                confidence REAL NOT NULL,
                current_price REAL NOT NULL,
                timeframe TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS signal_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                indicator_value REAL,
                signal_direction TEXT,
                confidence REAL,
                FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                signal_id TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                viewed_at TIMESTAMP,
                feedback TEXT,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
            )
            """
        ]
    
    def _get_indexes(self):
        """ایندکس‌های عملکردی"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_package_type ON users (package_type)",
            "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users (referral_code)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status)",
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_signals_user_id ON user_signals (user_id)"
        ]
    
    def backup_database(self):
        """بکاپ پایگاه داده قبل از مهاجرت"""
        try:
            backup_dir = project_root / "backups" / "migrations"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"db_backup_{timestamp}.db"
            
            # کپی فایل دیتابیس
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            logger.info(f"Database backed up to: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            raise
    
    def verify_database_integrity(self):
        """بررسی یکپارچگی پایگاه داده"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # بررسی PRAGMA integrity_check
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                
                if result == "ok":
                    logger.info("Database integrity check passed")
                    return True
                else:
                    logger.error(f"Database integrity check failed: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return False


def main():
    """تابع اصلی"""
    print("🔄 شروع مهاجرت پایگاه داده...")
    
    try:
        # ایجاد migrator
        migrator = DatabaseMigrator()
        
        # بکاپ پایگاه داده
        print("📦 بکاپ‌گیری از پایگاه داده...")
        backup_file = migrator.backup_database()
        
        # بررسی یکپارچگی
        print("🔍 بررسی یکپارچگی پایگاه داده...")
        if not migrator.verify_database_integrity():
            print("❌ پایگاه داده دارای مشکل است!")
            return False
        
        # اجرای مهاجرت‌ها
        print("🚀 اعمال مهاجرت‌ها...")
        migrator.run_migrations()
        
        # بررسی نهایی
        print("✅ بررسی نهایی...")
        if migrator.verify_database_integrity():
            print("✅ مهاجرت با موفقیت تکمیل شد!")
            return True
        else:
            print("❌ خطا در مهاجرت!")
            return False
            
    except Exception as e:
        print(f"❌ خطا در مهاجرت: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)