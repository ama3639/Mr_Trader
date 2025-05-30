"""
مدیریت تنظیمات و بارگذاری فایل‌های پیکربندی
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.config import Config
from utils.logger import logger


class SettingsManager:
    """مدیریت تنظیمات سیستم و API ها"""
    
    def __init__(self):
        self._api_config: Dict[str, Any] = {}
        self._environment_config: Dict[str, Any] = {}
        self._loaded = False
        self._config_file_path = Config.CONFIG_DIR / "api_servers_config.json"
        self._environment = Config.ENVIRONMENT.lower()
        
        # بارگذاری تنظیمات
        self.load_configs()
    
    def load_configs(self):
        """بارگذاری تمام فایل‌های تنظیمات"""
        try:
            # بارگذاری تنظیمات اصلی API
            self._load_main_api_config()
            
            # بارگذاری تنظیمات محیط
            self._load_environment_config()
            
            self._loaded = True
            logger.info("All configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            self._loaded = False
    
    def _load_main_api_config(self):
        """بارگذاری فایل تنظیمات اصلی API"""
        try:
            if not self._config_file_path.exists():
                logger.error(f"API config file not found: {self._config_file_path}")
                return
            
            with open(self._config_file_path, 'r', encoding='utf-8') as file:
                self._api_config = json.load(file)
                
            logger.info("Main API configuration loaded")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in API config file: {e}")
        except Exception as e:
            logger.error(f"Error loading API config: {e}")
    
    def _load_environment_config(self):
        """بارگذاری تنظیمات محیط (development/production)"""
        try:
            env_file = Config.CONFIG_DIR / f"{self._environment}.json"
            
            if not env_file.exists():
                logger.warning(f"Environment config file not found: {env_file}")
                return
            
            with open(env_file, 'r', encoding='utf-8') as file:
                self._environment_config = json.load(file)
                
            logger.info(f"Environment configuration loaded: {self._environment}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in environment config file: {e}")
        except Exception as e:
            logger.error(f"Error loading environment config: {e}")
    
    def get_strategy_url(self, strategy_name: str) -> Optional[str]:
        """دریافت URL استراتژی"""
        try:
            # ابتدا از تنظیمات محیط چک کن
            if self._environment_config:
                env_strategies = self._environment_config.get("api_servers", {}).get("strategies", {})
                if strategy_name in env_strategies:
                    return env_strategies[strategy_name].get("url")
            
            # سپس از تنظیمات اصلی
            strategies = self._api_config.get("api_servers", {}).get("strategies", {})
            if strategy_name in strategies:
                return strategies[strategy_name].get("url")
            
            logger.warning(f"Strategy URL not found: {strategy_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting strategy URL: {e}")
            return None
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """دریافت تنظیمات کامل استراتژی"""
        try:
            # ابتدا از تنظیمات محیط
            if self._environment_config:
                env_strategies = self._environment_config.get("api_servers", {}).get("strategies", {})
                if strategy_name in env_strategies:
                    env_config = env_strategies[strategy_name]
                    # ترکیب با تنظیمات اصلی
                    main_config = self._api_config.get("api_servers", {}).get("strategies", {}).get(strategy_name, {})
                    return {**main_config, **env_config}
            
            # تنظیمات اصلی
            strategies = self._api_config.get("api_servers", {}).get("strategies", {})
            return strategies.get(strategy_name, {})
            
        except Exception as e:
            logger.error(f"Error getting strategy config: {e}")
            return {}
    
    def get_strategy_timeout(self, strategy_name: str) -> int:
        """دریافت timeout استراتژی"""
        config = self.get_strategy_config(strategy_name)
        return config.get("timeout", Config.REQUEST_TIMEOUT)
    
    def get_strategy_retry_count(self, strategy_name: str) -> int:
        """دریافت تعداد retry استراتژی"""
        config = self.get_strategy_config(strategy_name)
        return config.get("retry_count", Config.MAX_RETRIES)
    
    def get_strategy_cache_duration(self, strategy_name: str) -> int:
        """دریافت مدت کش استراتژی"""
        config = self.get_strategy_config(strategy_name)
        return config.get("cache_duration", Config.SIGNAL_CACHE_DURATION)
    
    def get_strategy_package_levels(self, strategy_name: str) -> List[str]:
        """دریافت سطوح پکیج مجاز برای استراتژی"""
        config = self.get_strategy_config(strategy_name)
        return config.get("package_levels", [])
    
    def is_strategy_allowed_for_package(self, strategy_name: str, package_name: str) -> bool:
        """بررسی مجاز بودن استراتژی برای پکیج"""
        try:
            # بررسی از طریق package_hierarchy
            package_hierarchy = self._api_config.get("api_servers", {}).get("package_hierarchy", {})
            if package_name in package_hierarchy:
                allowed_strategies = package_hierarchy[package_name].get("strategies", [])
                return strategy_name in allowed_strategies
            
            # بررسی از طریق package_levels استراتژی
            strategy_levels = self.get_strategy_package_levels(strategy_name)
            return package_name in strategy_levels
            
        except Exception as e:
            logger.error(f"Error checking strategy access: {e}")
            return False
    
    def get_package_strategies(self, package_name: str) -> List[str]:
        """دریافت استراتژی‌های مجاز برای پکیج"""
        try:
            package_hierarchy = self._api_config.get("api_servers", {}).get("package_hierarchy", {})
            if package_name in package_hierarchy:
                return package_hierarchy[package_name].get("strategies", [])
            return []
            
        except Exception as e:
            logger.error(f"Error getting package strategies: {e}")
            return []
    
    def get_package_level(self, package_name: str) -> int:
        """دریافت سطح پکیج"""
        try:
            package_hierarchy = self._api_config.get("api_servers", {}).get("package_hierarchy", {})
            if package_name in package_hierarchy:
                return package_hierarchy[package_name].get("level", 0)
            return 0
            
        except Exception as e:
            logger.error(f"Error getting package level: {e}")
            return 0
    
    def get_all_strategies(self) -> List[str]:
        """دریافت لیست تمام استراتژی‌ها"""
        try:
            strategies = self._api_config.get("api_servers", {}).get("strategies", {})
            return list(strategies.keys())
            
        except Exception as e:
            logger.error(f"Error getting all strategies: {e}")
            return []
    
    def get_all_packages(self) -> List[str]:
        """دریافت لیست تمام پکیج‌ها"""
        try:
            package_hierarchy = self._api_config.get("api_servers", {}).get("package_hierarchy", {})
            return list(package_hierarchy.keys())
            
        except Exception as e:
            logger.error(f"Error getting all packages: {e}")
            return []
    
    def get_live_price_config(self) -> Dict[str, Any]:
        """دریافت تنظیمات قیمت زنده"""
        try:
            # ابتدا از تنظیمات محیط
            if self._environment_config:
                env_live_price = self._environment_config.get("live_price", {})
                if env_live_price:
                    main_live_price = self._api_config.get("live_price", {})
                    return {**main_live_price, **env_live_price}
            
            # تنظیمات اصلی
            return self._api_config.get("live_price", {})
            
        except Exception as e:
            logger.error(f"Error getting live price config: {e}")
            return {}
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """دریافت تنظیمات کش"""
        try:
            # ابتدا از تنظیمات محیط
            if self._environment_config:
                env_cache = self._environment_config.get("cache_settings", {})
                if env_cache:
                    main_cache = self._api_config.get("cache_settings", {})
                    return {**main_cache, **env_cache}
            
            # تنظیمات اصلی
            return self._api_config.get("cache_settings", {})
            
        except Exception as e:
            logger.error(f"Error getting cache settings: {e}")
            return {}
    
    def is_strategy_healthy(self, strategy_name: str) -> bool:
        """بررسی سلامت استراتژی (health check)"""
        try:
            config = self.get_strategy_config(strategy_name)
            health_url = config.get("health_url")
            
            if not health_url:
                return True  # اگر health URL نداشته باشد، فرض بر سلامت است
            
            # اینجا می‌توان درخواست HTTP به health endpoint ارسال کرد
            # فعلاً فقط وجود URL را چک می‌کنیم
            return bool(health_url)
            
        except Exception as e:
            logger.error(f"Error checking strategy health: {e}")
            return False
    
    def reload_configs(self):
        """بارگذاری مجدد تنظیمات"""
        logger.info("Reloading configurations...")
        self.load_configs()
    
    def is_loaded(self) -> bool:
        """بررسی بارگذاری موفق تنظیمات"""
        return self._loaded
    
    def get_config_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات کلی تنظیمات"""
        try:
            strategies_count = len(self.get_all_strategies())
            packages_count = len(self.get_all_packages())
            
            return {
                "loaded": self._loaded,
                "environment": self._environment,
                "strategies_count": strategies_count,
                "packages_count": packages_count,
                "config_file": str(self._config_file_path),
                "api_config_loaded": bool(self._api_config),
                "environment_config_loaded": bool(self._environment_config)
            }
            
        except Exception as e:
            logger.error(f"Error getting config info: {e}")
            return {"loaded": False, "error": str(e)}
    
    def get_full_config(self) -> Dict[str, Any]:
        """دریافت کامل تنظیمات (برای سازگاری با کد قدیمی)"""
        return self._api_config
    
    async def get_message(self, message_type: str) -> Optional[str]:
        """دریافت پیام سیستم"""
        try:
            return Config.MESSAGES.get(message_type)
        except Exception as e:
            logger.error(f"Error getting message {message_type}: {e}")
            return None
    
    async def set_message(self, message_type: str, message: str) -> bool:
        """تنظیم پیام سیستم"""
        try:
            # در پیاده‌سازی کامل، در دیتابیس ذخیره شود
            # فعلاً فقط لاگ می‌کنیم
            logger.info(f"Message {message_type} updated")
            return True
        except Exception as e:
            logger.error(f"Error setting message {message_type}: {e}")
            return False


# ایجاد نمونه سراسری
settings_manager = SettingsManager()