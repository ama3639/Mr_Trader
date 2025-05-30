#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست imports و ساختار ماژول‌ها"""

import sys
import os

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """تست import همه ماژول‌ها"""
    print("🔍 تست import ماژول‌ها...")
    
    modules_to_test = [
        ('core.config', 'Config'),
        ('core.globals', 'MANAGER_IDS'),
        ('utils.cache', 'SimpleCache'),
        ('utils.time_utils', 'to_shamsi'),
        ('managers.database', 'DatabaseManager'),
        ('managers.csv_manager', 'CSVManager'),
        ('managers.user_manager', 'UserManager'),
    ]
    
    success_count = 0
    fail_count = 0
    
    for module_name, attribute in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[attribute])
            if hasattr(module, attribute):
                print(f"  ✅ {module_name}.{attribute}")
                success_count += 1
            else:
                print(f"  ❌ {module_name}.{attribute} - attribute not found")
                fail_count += 1
        except ImportError as e:
            print(f"  ❌ {module_name} - {e}")
            fail_count += 1
    
    print(f"\n📊 نتیجه: {success_count} موفق، {fail_count} ناموفق")
    return fail_count == 0


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
