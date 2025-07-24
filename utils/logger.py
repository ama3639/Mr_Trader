"""
سیستم لاگ‌گیری MrTrader Bot
"""
import logging
import logging.handlers
from pathlib import Path
from core.config import Config


def setup_logging():
    """تنظیم سیستم لاگ‌گیری"""
    # ایجاد پوشه لاگ‌ها
    Config.LOGS_DIR.mkdir(exist_ok=True)
    
    # تنظیم فرمت لاگ
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # تنظیم logger اصلی
    logger = logging.getLogger("MrTrader")
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # جلوگیری از تکرار handler ها
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler با rotation
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOGS_DIR / "mrtrader.log",
        maxBytes=Config.LOG_FILE_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        Config.LOGS_DIR / "errors.log",
        maxBytes=Config.LOG_FILE_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# ایجاد logger اصلی
logger = setup_logging()


def log_user_action(user_id: int, action: str, details: str = ""):
    """لاگ اعمال کاربران"""
    logger.info(f"USER_ACTION | UserID: {user_id} | Action: {action} | Details: {details}")


def log_admin_action(admin_id: int, action: str, target: str = "", details: str = ""):
    """لاگ اعمال ادمین‌ها"""
    logger.info(f"ADMIN_ACTION | AdminID: {admin_id} | Action: {action} | Target: {target} | Details: {details}")


def log_payment_action(user_id: int, action: str, amount: float = 0, payment_code: str = "", details: str = ""):
    """لاگ اعمال پرداخت"""
    logger.info(f"PAYMENT | UserID: {user_id} | Action: {action} | Amount: {amount} | Code: {payment_code} | Details: {details}")


def log_api_call(endpoint: str, params: dict = None, response_time: float = 0, status: str = ""):
    """لاگ فراخوانی API ها"""
    logger.info(f"API_CALL | Endpoint: {endpoint} | Params: {params} | ResponseTime: {response_time}s | Status: {status}")


def log_database_action(action: str, table: str = "", details: str = ""):
    """لاگ اعمال دیتابیس"""
    logger.info(f"DATABASE | Action: {action} | Table: {table} | Details: {details}")


def log_security_event(event_type: str, user_id: int = 0, ip_address: str = "", details: str = ""):
    """لاگ رویدادهای امنیتی"""
    logger.warning(f"SECURITY | Type: {event_type} | UserID: {user_id} | IP: {ip_address} | Details: {details}")


def log_error(error: Exception, context: str = "", user_id: int = 0):
    """لاگ خطاها"""
    logger.error(f"ERROR | Context: {context} | UserID: {user_id} | Error: {str(error)}", exc_info=True)


def log_performance(operation: str, duration: float, details: str = ""):
    """لاگ عملکرد سیستم"""
    logger.info(f"PERFORMANCE | Operation: {operation} | Duration: {duration}s | Details: {details}")


class DatabaseLogger:
    """کلاس لاگ‌گیری اعمال دیتابیس"""
    
    @staticmethod
    def log_query(query: str, params: tuple = None, execution_time: float = 0):
        """لاگ کوئری‌های دیتابیس"""
        logger.debug(f"DB_QUERY | Query: {query} | Params: {params} | Time: {execution_time}s")
    
    @staticmethod
    def log_connection_status(status: str, details: str = ""):
        """لاگ وضعیت اتصال دیتابیس"""
        logger.info(f"DB_CONNECTION | Status: {status} | Details: {details}")
    
    @staticmethod
    def log_migration(version: str, status: str):
        """لاگ migration های دیتابیس"""
        logger.info(f"DB_MIGRATION | Version: {version} | Status: {status}")


class ApiLogger:
    """کلاس لاگ‌گیری API ها"""
    
    @staticmethod
    def log_request(url: str, method: str, headers: dict = None, data: dict = None):
        """لاگ درخواست‌های API"""
        logger.debug(f"API_REQUEST | URL: {url} | Method: {method} | Headers: {headers} | Data: {data}")
    
    @staticmethod
    def log_response(url: str, status_code: int, response_time: float, response_size: int = 0):
        """لاگ پاسخ‌های API"""
        logger.info(f"API_RESPONSE | URL: {url} | Status: {status_code} | Time: {response_time}s | Size: {response_size} bytes")
    
    @staticmethod
    def log_error(url: str, error: Exception):
        """لاگ خطاهای API"""
        logger.error(f"API_ERROR | URL: {url} | Error: {str(error)}", exc_info=True)


class TelegramLogger:
    """کلاس لاگ‌گیری پیام‌های تلگرام"""
    
    @staticmethod
    def log_message_received(user_id: int, message_type: str, content: str = ""):
        """لاگ پیام‌های دریافتی"""
        logger.info(f"TG_MESSAGE_IN | UserID: {user_id} | Type: {message_type} | Content: {content[:50]}...")
    
    @staticmethod
    def log_message_sent(user_id: int, message_type: str, success: bool = True):
        """لاگ پیام‌های ارسالی"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"TG_MESSAGE_OUT | UserID: {user_id} | Type: {message_type} | Status: {status}")
    
    @staticmethod
    def log_callback_query(user_id: int, callback_data: str):
        """لاگ callback query ها"""
        logger.info(f"TG_CALLBACK | UserID: {user_id} | Data: {callback_data}")


# Export logger برای استفاده در سایر ماژول‌ها
__all__ = [
    'logger', 
    'log_user_action', 
    'log_admin_action', 
    'log_payment_action',
    'log_api_call',
    'log_database_action',
    'log_security_event',
    'log_error',
    'log_performance',
    'DatabaseLogger',
    'ApiLogger', 
    'TelegramLogger'
]
