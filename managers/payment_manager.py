"""
مدیریت پرداخت‌ها و پکیج‌ها MrTrader Bot
"""
import csv
import os
import uuid
import random
import string
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.config import Config
from utils.logger import logger, log_payment_action
from utils.time_manager import TimeManager
from database.database_manager import database_manager
from managers.user_manager import UserManager


class PaymentManager:
    """کلاس مدیریت پرداخت‌ها و پکیج‌ها"""
    
    @classmethod
    def ensure_payment_files_exist(cls):
        """اطمینان از وجود فایل‌های پرداخت"""
        try:
            Config.DATA_DIR.mkdir(exist_ok=True)
            
            # فایل پرداخت‌های در انتظار
            if not os.path.exists(Config.PENDING_PAYMENTS_CSV):
                headers = [
                    'telegram_id', 'payment_code', 'amount', 'currency', 'package',
                    'payment_method', 'timestamp', 'status', 'notes'
                ]
                
                with open(Config.PENDING_PAYMENTS_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
            
            # فایل لاگ پرداخت‌ها
            if not os.path.exists(Config.PAYMENT_LOG_CSV):
                headers = [
                    'telegram_id', 'payment_code', 'amount', 'currency', 'package',
                    'status', 'processed_by', 'processed_date', 'notes'
                ]
                
                with open(Config.PAYMENT_LOG_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
            
            logger.info("Payment files ensured")
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring payment files exist: {e}")
            return False
    
    @classmethod
    def generate_payment_code(cls) -> str:
        """تولید کد پیگیری پرداخت منحصربه‌فرد
        
        Returns:
            کد پیگیری 12 کاراکتری
        """
        while True:
            # ترکیب حروف بزرگ و اعداد
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            
            # بررسی یکتا بودن
            if not cls.payment_code_exists(code):
                return code
    
    @classmethod
    def payment_code_exists(cls, payment_code: str) -> bool:
        """بررسی وجود کد پیگیری
        
        Args:
            payment_code: کد پیگیری
            
        Returns:
            آیا کد وجود دارد
        """
        try:
            # بررسی در دیتابیس
            db_payment = database_manager.get_payment_by_code(payment_code)
            if db_payment:
                return True
            
            # بررسی در فایل CSV
            cls.ensure_payment_files_exist()
            
            with open(Config.PENDING_PAYMENTS_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('payment_code') == payment_code:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking payment code existence: {e}")
            return True  # در صورت خطا، فرض کنیم وجود دارد
    
    @classmethod
    def create_payment(cls, telegram_id: int, package: str, amount: float,
                      currency: str = 'IRR', payment_method: str = 'bank_transfer') -> Optional[str]:
        """ایجاد پرداخت جدید
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            package: نوع پکیج
            amount: مبلغ
            currency: نوع ارز
            payment_method: روش پرداخت
            
        Returns:
            کد پیگیری پرداخت یا None
        """
        try:
            payment_code = cls.generate_payment_code()
            current_time = TimeManager.get_current_shamsi()
            
            # ایجاد در دیتابیس
            db_success = database_manager.create_payment(
                telegram_id=telegram_id,
                payment_code=payment_code,
                amount=amount,
                package_type=package,
                payment_method=payment_method
            )
            
            # ایجاد در CSV
            cls.ensure_payment_files_exist()
            
            payment_data = {
                'telegram_id': str(telegram_id),
                'payment_code': payment_code,
                'amount': str(amount),
                'currency': currency,
                'package': package,
                'payment_method': payment_method,
                'timestamp': current_time,
                'status': 'pending',
                'notes': ''
            }
            
            # افزودن به فایل پرداخت‌های در انتظار
            with open(Config.PENDING_PAYMENTS_CSV, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=payment_data.keys())
                writer.writerow(payment_data)
            
            log_payment_action(
                telegram_id, 
                "payment_created", 
                amount, 
                payment_code, 
                f"Package: {package}, Method: {payment_method}"
            )
            
            logger.info(f"Created payment {payment_code} for user {telegram_id}")
            return payment_code
            
        except Exception as e:
            logger.error(f"Error creating payment for user {telegram_id}: {e}")
            return None
    
    @classmethod
    def get_pending_payments(cls, limit: int = 100) -> List[Dict[str, str]]:
        """دریافت پرداخت‌های در انتظار
        
        Args:
            limit: حداکثر تعداد
            
        Returns:
            لیست پرداخت‌های در انتظار
        """
        try:
            # ابتدا از دیتابیس
            db_payments = database_manager.get_pending_payments(limit)
            if db_payments:
                return db_payments
            
            # در صورت عدم وجود، از CSV
            cls.ensure_payment_files_exist()
            payments = []
            
            with open(Config.PENDING_PAYMENTS_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('status', '').lower() == 'pending':
                        payments.append(dict(row))
                        
                        if len(payments) >= limit:
                            break
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return payments
            
        except Exception as e:
            logger.error(f"Error getting pending payments: {e}")
            return []
    
    @classmethod
    def get_payment_by_code(cls, payment_code: str) -> Optional[Dict[str, Any]]:
        """دریافت پرداخت با کد پیگیری
        
        Args:
            payment_code: کد پیگیری
            
        Returns:
            اطلاعات پرداخت یا None
        """
        try:
            # ابتدا از دیتابیس
            db_payment = database_manager.get_payment_by_code(payment_code)
            if db_payment:
                return db_payment
            
            # سپس از CSV
            cls.ensure_payment_files_exist()
            
            # بررسی فایل در انتظار
            with open(Config.PENDING_PAYMENTS_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('payment_code') == payment_code:
                        return dict(row)
            
            # بررسی فایل لاگ
            with open(Config.PAYMENT_LOG_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('payment_code') == payment_code:
                        return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting payment by code {payment_code}: {e}")
            return None
    
    @classmethod
    def process_payment(cls, telegram_id: int, payment_code: str, 
                       approved_by: int = None, notes: str = "") -> Optional[Dict[str, Any]]:
        """پردازش و تأیید پرداخت
        
        Args:
            telegram_id: شناسه تلگرام کاربر
            payment_code: کد پیگیری
            approved_by: شناسه تلگرام تأیید کننده
            notes: یادداشت‌ها
            
        Returns:
            اطلاعات پرداخت پردازش شده یا None
        """
        try:
            # دریافت اطلاعات پرداخت
            payment = cls.get_payment_by_code(payment_code)
            if not payment:
                logger.warning(f"Payment {payment_code} not found")
                return None
            
            # بررسی تطابق کاربر
            if str(payment.get('telegram_id')) != str(telegram_id):
                logger.warning(f"Payment {payment_code} user mismatch")
                return None
            
            # بررسی وضعیت پرداخت
            if payment.get('status', '').lower() != 'pending':
                logger.warning(f"Payment {payment_code} is not pending")
                return None
            
            package = payment.get('package', '')
            amount = float(payment.get('amount', 0))
            
            # پردازش بر اساس نوع پرداخت
            success = False
            
            if package.startswith(('basic', 'premium', 'vip', 'guest')):
                # پکیج‌های اشتراک
                success = cls._process_package_payment(telegram_id, package, payment_code)
            elif package == 'charge' or package.startswith('balance'):
                # شارژ حساب
                success = cls._process_balance_charge(telegram_id, amount, payment_code)
            else:
                logger.error(f"Unknown package type: {package}")
                return None
            
            if success:
                # به‌روزرسانی وضعیت پرداخت
                cls._update_payment_status(
                    payment_code, 
                    'approved', 
                    approved_by, 
                    notes
                )
                
                log_payment_action(
                    telegram_id, 
                    "payment_approved", 
                    amount, 
                    payment_code, 
                    f"Package: {package}, Approved by: {approved_by}"
                )
                
                logger.info(f"Processed payment {payment_code} for user {telegram_id}")
                return payment
            else:
                logger.error(f"Failed to process payment {payment_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing payment {payment_code}: {e}")
            return None
    
    @classmethod
    def _process_package_payment(cls, telegram_id: int, package: str, payment_code: str) -> bool:
        """پردازش پرداخت پکیج
        
        Args:
            telegram_id: شناسه کاربر
            package: نوع پکیج
            payment_code: کد پیگیری
            
        Returns:
            موفقیت عملیات
        """
        try:
            # دریافت تنظیمات پکیج
            package_info = Config.PACKAGES.get(package.split('_')[0])  # حذف پسوند احتمالی
            if not package_info:
                logger.error(f"Package info not found for: {package}")
                return False
            
            duration_days = package_info['duration_days']
            
            # تنظیم پکیج برای کاربر
            success = UserManager.set_user_package(telegram_id, package.split('_')[0], duration_days)
            
            if success:
                log_payment_action(
                    telegram_id, 
                    "package_activated", 
                    0, 
                    payment_code, 
                    f"Package: {package}, Duration: {duration_days} days"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing package payment: {e}")
            return False
    
    @classmethod
    def _process_balance_charge(cls, telegram_id: int, amount: float, payment_code: str) -> bool:
        """پردازش شارژ حساب
        
        Args:
            telegram_id: شناسه کاربر
            amount: مبلغ شارژ
            payment_code: کد پیگیری
            
        Returns:
            موفقیت عملیات
        """
        try:
            # افزایش موجودی کاربر
            success = UserManager.add_balance(telegram_id, amount)
            
            if success:
                log_payment_action(
                    telegram_id, 
                    "balance_charged", 
                    amount, 
                    payment_code, 
                    f"Amount: {amount}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing balance charge: {e}")
            return False
    
    @classmethod
    def _update_payment_status(cls, payment_code: str, status: str, 
                              processed_by: int = None, notes: str = ""):
        """به‌روزرسانی وضعیت پرداخت
        
        Args:
            payment_code: کد پیگیری
            status: وضعیت جدید
            processed_by: پردازش کننده
            notes: یادداشت‌ها
        """
        try:
            current_time = TimeManager.get_current_shamsi()
            
            # به‌روزرسانی در دیتابیس
            database_manager.update_payment_status(
                payment_code, 
                status, 
                processed_by, 
                notes=notes
            )
            
            # حذف از فایل pending و افزودن به لاگ
            cls._move_payment_to_log(payment_code, status, processed_by, current_time, notes)
            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
    
    @classmethod
    def _move_payment_to_log(cls, payment_code: str, status: str, 
                            processed_by: int = None, processed_date: str = "", notes: str = ""):
        """انتقال پرداخت از pending به لاگ
        
        Args:
            payment_code: کد پیگیری
            status: وضعیت نهایی
            processed_by: پردازش کننده
            processed_date: تاریخ پردازش
            notes: یادداشت‌ها
        """
        try:
            cls.ensure_payment_files_exist()
            
            # خواندن فایل pending
            pending_payments = []
            target_payment = None
            
            with open(Config.PENDING_PAYMENTS_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('payment_code') == payment_code:
                        target_payment = dict(row)
                    else:
                        pending_payments.append(row)
            
            if not target_payment:
                return
            
            # بازنویسی فایل pending بدون پرداخت پردازش شده
            with open(Config.PENDING_PAYMENTS_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                if pending_payments:
                    fieldnames = pending_payments[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(pending_payments)
                else:
                    # اگر هیچ پرداختی نمانده، فقط header بنویس
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        'telegram_id', 'payment_code', 'amount', 'currency', 'package',
                        'payment_method', 'timestamp', 'status', 'notes'
                    ])
            
            # افزودن به فایل لاگ
            log_entry = {
                'telegram_id': target_payment.get('telegram_id', ''),
                'payment_code': target_payment.get('payment_code', ''),
                'amount': target_payment.get('amount', ''),
                'currency': target_payment.get('currency', 'IRR'),
                'package': target_payment.get('package', ''),
                'status': status,
                'processed_by': str(processed_by) if processed_by else '',
                'processed_date': processed_date,
                'notes': notes
            }
            
            with open(Config.PAYMENT_LOG_CSV, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=log_entry.keys())
                writer.writerow(log_entry)
            
        except Exception as e:
            logger.error(f"Error moving payment to log: {e}")
    
    @classmethod
    def reject_payment(cls, payment_code: str, rejected_by: int = None, reason: str = "") -> bool:
        """رد پرداخت
        
        Args:
            payment_code: کد پیگیری
            rejected_by: رد کننده
            reason: دلیل رد
            
        Returns:
            موفقیت عملیات
        """
        try:
            # دریافت اطلاعات پرداخت
            payment = cls.get_payment_by_code(payment_code)
            if not payment:
                return False
            
            telegram_id = int(payment.get('telegram_id', 0))
            amount = float(payment.get('amount', 0))
            
            # به‌روزرسانی وضعیت
            cls._update_payment_status(payment_code, 'rejected', rejected_by, reason)
            
            log_payment_action(
                telegram_id, 
                "payment_rejected", 
                amount, 
                payment_code, 
                f"Reason: {reason}, Rejected by: {rejected_by}"
            )
            
            logger.info(f"Rejected payment {payment_code}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting payment {payment_code}: {e}")
            return False
    
    @classmethod
    def get_user_payments(cls, telegram_id: int, limit: int = 20) -> List[Dict[str, str]]:
        """دریافت پرداخت‌های کاربر
        
        Args:
            telegram_id: شناسه تلگرام
            limit: حداکثر تعداد
            
        Returns:
            لیست پرداخت‌های کاربر
        """
        try:
            payments = []
            
            # دریافت از فایل لاگ
            cls.ensure_payment_files_exist()
            
            with open(Config.PAYMENT_LOG_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('telegram_id') == str(telegram_id):
                        payments.append(dict(row))
            
            # دریافت از فایل pending
            with open(Config.PENDING_PAYMENTS_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('telegram_id') == str(telegram_id):
                        payments.append(dict(row))
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return payments[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user payments for {telegram_id}: {e}")
            return []
    
    @classmethod
    def get_payment_statistics(cls) -> Dict[str, Any]:
        """آمار پرداخت‌ها
        
        Returns:
            آمار کلی پرداخت‌ها
        """
        try:
            stats = {
                'pending_payments': 0,
                'approved_payments': 0,
                'rejected_payments': 0,
                'total_amount_approved': 0.0,
                'packages_sold': {'basic': 0, 'premium': 0, 'vip': 0, 'guest': 0},
                'balance_charges': 0,
                'today_payments': 0
            }
            
            today = datetime.now().date()
            
            # آمار از فایل pending
            pending_payments = cls.get_pending_payments(1000)
            stats['pending_payments'] = len(pending_payments)
            
            # آمار از فایل لاگ
            cls.ensure_payment_files_exist()
            
            with open(Config.PAYMENT_LOG_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    status = row.get('status', '').lower()
                    package = row.get('package', '')
                    amount = float(row.get('amount', 0))
                    processed_date = row.get('processed_date', '')
                    
                    if status == 'approved':
                        stats['approved_payments'] += 1
                        stats['total_amount_approved'] += amount
                        
                        # آمار پکیج‌ها
                        if package in stats['packages_sold']:
                            stats['packages_sold'][package] += 1
                        elif package in ['charge', 'balance']:
                            stats['balance_charges'] += 1
                    
                    elif status == 'rejected':
                        stats['rejected_payments'] += 1
                    
                    # پرداخت‌های امروز
                    try:
                        if processed_date and TimeManager.from_shamsi(processed_date).date() == today:
                            stats['today_payments'] += 1
                    except:
                        pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting payment statistics: {e}")
            return {}
    
    @classmethod
    def cleanup_old_payments(cls, days: int = 90) -> int:
        """پاکسازی پرداخت‌های قدیمی
        
        Args:
            days: حذف پرداخت‌های قدیمی‌تر از این تعداد روز
            
        Returns:
            تعداد آیتم‌های حذف شده
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            # پاکسازی فایل لاگ
            cls.ensure_payment_files_exist()
            
            payments_to_keep = []
            
            with open(Config.PAYMENT_LOG_CSV, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    processed_date = row.get('processed_date', '')
                    try:
                        if processed_date:
                            payment_date = TimeManager.from_shamsi(processed_date)
                            if payment_date and payment_date >= cutoff_date:
                                payments_to_keep.append(row)
                            else:
                                cleaned_count += 1
                        else:
                            payments_to_keep.append(row)  # حفظ پرداخت‌های بدون تاریخ
                    except:
                        payments_to_keep.append(row)  # حفظ در صورت خطا
            
            # بازنویسی فایل
            if payments_to_keep:
                with open(Config.PAYMENT_LOG_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = payments_to_keep[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(payments_to_keep)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old payments")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old payments: {e}")
            return 0


# کلاس کمکی برای پردازش پرداخت‌ها
class PaymentProcessor:
    """کلاس پردازش پرداخت‌های خاص"""
    
    @staticmethod
    def calculate_package_price(package: str, duration: str = "monthly", currency: str = "IRR") -> float:
        """محاسبه قیمت پکیج
        
        Args:
            package: نوع پکیج
            duration: مدت زمان
            currency: نوع ارز
            
        Returns:
            قیمت محاسبه شده
        """
        try:
            package_info = Config.PACKAGES.get(package)
            if not package_info:
                return 0.0
            
            if currency.upper() == "IRR":
                return package_info['price_irr']
            elif currency.upper() == "USD":
                return package_info['price_usd']
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating package price: {e}")
            return 0.0
    
    @staticmethod
    def validate_payment_amount(package: str, amount: float, currency: str = "IRR") -> bool:
        """اعتبارسنجی مبلغ پرداخت
        
        Args:
            package: نوع پکیج
            amount: مبلغ پرداخت شده
            currency: نوع ارز
            
        Returns:
            معتبر بودن مبلغ
        """
        try:
            expected_amount = PaymentProcessor.calculate_package_price(package, "monthly", currency)
            
            # تلرانس 5 درصدی
            tolerance = expected_amount * 0.05
            
            return abs(amount - expected_amount) <= tolerance
            
        except Exception as e:
            logger.error(f"Error validating payment amount: {e}")
            return False


# Export برای استفاده آسان‌تر
__all__ = ['PaymentManager', 'PaymentProcessor']
