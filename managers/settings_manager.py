"""
مدیریت تنظیمات و پیکربندی API ها
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.config import Config
from utils.logger import logger


class SettingsManager:
    """مدیریت تنظیمات سیستم و API ها"""
    
    def __init__(self):
        self.config_file = Config.CONFIG_DIR / "api_servers_config.json"
        self._config_cache = None
        self._last_modified = None
        self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """بارگیری تنظیمات از فایل"""
        try:
            if not self.config_file.exists():
                logger.error(f"Config file not found: {self.config_file}")
                return {}
            
            # بررسی تغییر فایل
            current_modified = self.config_file.stat().st_mtime
            if self._last_modified != current_modified:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                self._last_modified = current_modified
                logger.info("API configuration reloaded")
            
            return self._config_cache or {}
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def get_config(self) -> Dict[str, Any]:
        """دریافت کل تنظیمات"""
        return self._load_config()
    
    def get_api_servers_config(self) -> Dict[str, Any]:
        """دریافت تنظیمات سرورهای API"""
        config = self.get_config()
        return config.get("api_servers", {})
    
    def get_strategies_config(self) -> Dict[str, Any]:
        """دریافت تنظیمات استراتژی‌ها"""
        api_config = self.get_api_servers_config()
        return api_config.get("strategies", {})
    
    def get_strategy_config(self, strategy: str) -> Optional[Dict[str, Any]]:
        """دریافت تنظیمات یک استراتژی خاص"""
        strategies = self.get_strategies_config()
        return strategies.get(strategy)
    
    def get_strategy_url(self, strategy: str) -> Optional[str]:
        """دریافت URL استراتژی"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("url")
        return None
    
    def get_strategy_health_url(self, strategy: str) -> Optional[str]:
        """دریافت URL سلامت استراتژی"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("health_url")
        return None
    
    def get_strategy_timeout(self, strategy: str) -> int:
        """دریافت timeout استراتژی"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("timeout", 30)
        return 30
    
    def get_strategy_retry_count(self, strategy: str) -> int:
        """دریافت تعداد تلاش مجدد"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("retry_count", 3)
        return 3
    
    def get_strategy_cache_duration(self, strategy: str) -> int:
        """دریافت مدت کش استراتژی"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("cache_duration", 60)
        return 60
    
    def get_strategy_package_levels(self, strategy: str) -> List[str]:
        """دریافت سطوح پکیج مجاز برای استراتژی"""
        strategy_config = self.get_strategy_config(strategy)
        if strategy_config:
            return strategy_config.get("package_levels", [])
        return []
    
    def is_strategy_allowed_for_package(self, strategy: str, package: str) -> bool:
        """بررسی مجاز بودن استراتژی برای پکیج"""
        allowed_packages = self.get_strategy_package_levels(strategy)
        return package in allowed_packages
    
    def get_all_strategies(self) -> List[str]:
        """دریافت لیست همه استراتژی‌ها"""
        strategies = self.get_strategies_config()
        return list(strategies.keys())
    
    def get_package_strategies(self, package: str) -> List[str]:
        """دریافت استراتژی‌های یک پکیج"""
        config = self.get_config()
        package_hierarchy = config.get("api_servers", {}).get("package_hierarchy", {})
        
        if package in package_hierarchy:
            return package_hierarchy[package].get("strategies", [])
        
        # اگر در hierarchy نبود، از تنظیمات استراتژی‌ها استخراج کن
        strategies = []
        for strategy, strategy_config in self.get_strategies_config().items():
            if package in strategy_config.get("package_levels", []):
                strategies.append(strategy)
        
        return strategies
    
    def get_all_packages(self) -> List[str]:
        """دریافت لیست همه پکیج‌ها"""
        config = self.get_config()
        package_hierarchy = config.get("api_servers", {}).get("package_hierarchy", {})
        return list(package_hierarchy.keys())
    
    def get_package_level(self, package: str) -> int:
        """دریافت سطح پکیج"""
        config = self.get_config()
        package_hierarchy = config.get("api_servers", {}).get("package_hierarchy", {})
        
        if package in package_hierarchy:
            return package_hierarchy[package].get("level", 0)
        
        # سطح پیش‌فرض
        level_map = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "vip": 3,
            "ghost": 4
        }
        return level_map.get(package, 0)
    
    def get_live_price_config(self) -> Dict[str, Any]:
        """دریافت تنظیمات قیمت زنده"""
        config = self.get_config()
        return config.get("live_price", {})
    
    def get_live_price_url(self, exchange: str = "binance") -> Optional[str]:
        """دریافت URL قیمت زنده"""
        live_price_config = self.get_live_price_config()
        exchange_config = live_price_config.get(exchange, {})
        return exchange_config.get("url")
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """دریافت تنظیمات کش"""
        config = self.get_config()
        return config.get("cache_settings", {
            "default_duration": 60,
            "min_request_interval": 60,
            "max_cache_size": 1000
        })
    
    def is_strategy_healthy(self, strategy: str) -> bool:
        """بررسی سلامت استراتژی (فعلاً بر اساس وجود URL)"""
        strategy_url = self.get_strategy_url(strategy)
        return strategy_url is not None
    
    def update_strategy_config(self, strategy: str, config_updates: Dict[str, Any]) -> bool:
        """بروزرسانی تنظیمات یک استراتژی"""
        try:
            config = self.get_config()
            
            if "api_servers" not in config:
                config["api_servers"] = {}
            if "strategies" not in config["api_servers"]:
                config["api_servers"]["strategies"] = {}
            
            # بروزرسانی تنظیمات
            if strategy not in config["api_servers"]["strategies"]:
                config["api_servers"]["strategies"][strategy] = {}
            
            config["api_servers"]["strategies"][strategy].update(config_updates)
            
            # ذخیره در فایل
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # بروزرسانی کش
            self._config_cache = config
            self._last_modified = self.config_file.stat().st_mtime
            
            logger.info(f"Strategy {strategy} config updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating strategy config: {e}")
            return False
    
    def add_new_strategy(self, strategy: str, strategy_config: Dict[str, Any]) -> bool:
        """اضافه کردن استراتژی جدید"""
        try:
            # تنظیمات پیش‌فرض
            default_config = {
                "name": strategy.replace("_", " ").title(),
                "url": f"http://localhost:8000/analyze_{strategy}/",
                "health_url": f"http://localhost:8000/health/",
                "timeout": 30,
                "retry_count": 3,
                "package_levels": ["basic", "premium", "vip", "ghost"],
                "cache_duration": 60
            }
            
            # ترکیب با تنظیمات ارسالی
            default_config.update(strategy_config)
            
            return self.update_strategy_config(strategy, default_config)
            
        except Exception as e:
            logger.error(f"Error adding new strategy: {e}")
            return False
    
    def remove_strategy(self, strategy: str) -> bool:
        """حذف استراتژی"""
        try:
            config = self.get_config()
            
            if ("api_servers" in config and 
                "strategies" in config["api_servers"] and 
                strategy in config["api_servers"]["strategies"]):
                
                del config["api_servers"]["strategies"][strategy]
                
                # حذف از package hierarchy
                package_hierarchy = config["api_servers"].get("package_hierarchy", {})
                for package, package_config in package_hierarchy.items():
                    strategies = package_config.get("strategies", [])
                    if strategy in strategies:
                        strategies.remove(strategy)
                
                # ذخیره در فایل
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                # بروزرسانی کش
                self._config_cache = config
                self._last_modified = self.config_file.stat().st_mtime
                
                logger.info(f"Strategy {strategy} removed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing strategy: {e}")
            return False
    
    def update_base_url(self, new_base_url: str) -> bool:
        """بروزرسانی URL پایه سرورها"""
        try:
            config = self.get_config()
            
            if "api_servers" not in config:
                config["api_servers"] = {}
            
            old_base_url = config["api_servers"].get("base_url", "http://localhost")
            config["api_servers"]["base_url"] = new_base_url
            
            # بروزرسانی URL های همه استراتژی‌ها
            strategies = config["api_servers"].get("strategies", {})
            for strategy, strategy_config in strategies.items():
                if "url" in strategy_config:
                    strategy_config["url"] = strategy_config["url"].replace(old_base_url, new_base_url)
                if "health_url" in strategy_config:
                    strategy_config["health_url"] = strategy_config["health_url"].replace(old_base_url, new_base_url)
            
            # ذخیره در فایل
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # بروزرسانی کش
            self._config_cache = config
            self._last_modified = self.config_file.stat().st_mtime
            
            logger.info(f"Base URL updated from {old_base_url} to {new_base_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating base URL: {e}")
            return False
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """آمار استراتژی‌ها"""
        try:
            strategies = self.get_strategies_config()
            packages = self.get_all_packages()
            
            stats = {
                "total_strategies": len(strategies),
                "total_packages": len(packages),
                "strategies_by_package": {},
                "healthy_strategies": 0,
                "unhealthy_strategies": 0
            }
            
            # آمار بر اساس پکیج
            for package in packages:
                package_strategies = self.get_package_strategies(package)
                stats["strategies_by_package"][package] = len(package_strategies)
            
            # آمار سلامت
            for strategy in strategies:
                if self.is_strategy_healthy(strategy):
                    stats["healthy_strategies"] += 1
                else:
                    stats["unhealthy_strategies"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting strategy statistics: {e}")
            return {}
    
    def validate_config(self) -> Dict[str, List[str]]:
        """اعتبارسنجی تنظیمات"""
        errors = []
        warnings = []
        
        try:
            config = self.get_config()
            
            if not config:
                errors.append("Config file is empty or invalid")
                return {"errors": errors, "warnings": warnings}
            
            # بررسی ساختار اصلی
            if "api_servers" not in config:
                errors.append("api_servers section missing")
            else:
                api_config = config["api_servers"]
                
                # بررسی base_url
                if "base_url" not in api_config:
                    warnings.append("base_url not defined")
                
                # بررسی strategies
                if "strategies" not in api_config:
                    errors.append("strategies section missing")
                else:
                    strategies = api_config["strategies"]
                    
                    for strategy, strategy_config in strategies.items():
                        # بررسی فیلدهای ضروری
                        required_fields = ["name", "url"]
                        for field in required_fields:
                            if field not in strategy_config:
                                errors.append(f"Strategy {strategy}: missing {field}")
                        
                        # بررسی URL
                        url = strategy_config.get("url", "")
                        if url and not (url.startswith("http://") or url.startswith("https://")):
                            warnings.append(f"Strategy {strategy}: invalid URL format")
                
                # بررسی package_hierarchy
                if "package_hierarchy" not in api_config:
                    warnings.append("package_hierarchy section missing")
            
            return {
                "errors": errors,
                "warnings": warnings,
                "is_valid": len(errors) == 0
            }
            
        except Exception as e:
            errors.append(f"Config validation error: {e}")
            return {"errors": errors, "warnings": warnings}


# نمونه سراسری
settings_manager = SettingsManager()
