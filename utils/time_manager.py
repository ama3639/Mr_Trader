"""
مدیریت زمان و تقویم شمسی MrTrader Bot
"""
import jdatetime
from datetime import datetime, timedelta
from typing import Optional, Union
from utils.logger import logger


class TimeManager:
    """کلاس مدیریت زمان و تقویم شمسی"""
    
    @staticmethod
    def to_shamsi(dt: datetime, include_time: bool = True) -> str:
        """تبدیل تاریخ میلادی به شمسی
        
        Args:
            dt: تاریخ میلادی
            include_time: شامل کردن ساعت در خروجی
            
        Returns:
            str: تاریخ شمسی به فرمت رشته
        """
        try:
            jdt = jdatetime.datetime.fromgregorian(datetime=dt)
            if include_time:
                return jdt.strftime("%Y/%m/%d - %H:%M:%S")
            else:
                return jdt.strftime("%Y/%m/%d")
        except Exception as e:
            logger.error(f"Error converting to Shamsi: {e}")
            return dt.strftime("%Y/%m/%d - %H:%M:%S")
    
    @staticmethod
    def from_shamsi(shamsi_str: str) -> Optional[datetime]:
        """تبدیل تاریخ شمسی به میلادی
        
        Args:
            shamsi_str: تاریخ شمسی به فرمت رشته
            
        Returns:
            datetime یا None در صورت خطا
        """
        try:
            # پردازش فرمت‌های مختلف تاریخ شمسی
            formats = [
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d - %H:%M:%S", 
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    jdt = jdatetime.datetime.strptime(shamsi_str, fmt)
                    return jdt.togregorian()
                except ValueError:
                    continue
                    
            logger.warning(f"Could not parse Shamsi date: {shamsi_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error converting from Shamsi: {e}")
            return None
    
    @staticmethod
    def get_current_shamsi() -> str:
        """دریافت تاریخ شمسی فعلی"""
        return TimeManager.to_shamsi(datetime.now())
    
    @staticmethod
    def get_current_shamsi_date() -> str:
        """دریافت تاریخ شمسی فعلی بدون ساعت"""
        return TimeManager.to_shamsi(datetime.now(), include_time=False)
    
    @staticmethod
    def get_current_time_persian() -> str:
        """دریافت زمان فعلی به فرمت فارسی (برای سازگاری با main.py)
        
        Returns:
            str: زمان فعلی به فرمت شمسی
        """
        return TimeManager.get_current_shamsi()
    
    @staticmethod
    def get_current_timestamp() -> float:
        """دریافت timestamp فعلی
        
        Returns:
            float: timestamp فعلی
        """
        return datetime.now().timestamp()
    
    @staticmethod
    def add_shamsi_days(shamsi_str: str, days: int) -> Optional[str]:
        """اضافه کردن روز به تاریخ شمسی
        
        Args:
            shamsi_str: تاریخ شمسی اولیه
            days: تعداد روزهای اضافه
            
        Returns:
            تاریخ شمسی جدید یا None در صورت خطا
        """
        try:
            dt = TimeManager.from_shamsi(shamsi_str)
            if dt:
                new_dt = dt + timedelta(days=days)
                return TimeManager.to_shamsi(new_dt)
            return None
        except Exception as e:
            logger.error(f"Error adding days to Shamsi date: {e}")
            return None
    
    @staticmethod
    def subtract_shamsi_days(shamsi_str: str, days: int) -> Optional[str]:
        """کم کردن روز از تاریخ شمسی
        
        Args:
            shamsi_str: تاریخ شمسی اولیه
            days: تعداد روزهای کم شده
            
        Returns:
            تاریخ شمسی جدید یا None در صورت خطا
        """
        try:
            dt = TimeManager.from_shamsi(shamsi_str)
            if dt:
                new_dt = dt - timedelta(days=days)
                return TimeManager.to_shamsi(new_dt)
            return None
        except Exception as e:
            logger.error(f"Error subtracting days from Shamsi date: {e}")
            return None
    
    @staticmethod
    def days_difference(date1: Union[str, datetime], date2: Union[str, datetime]) -> Optional[int]:
        """محاسبه تفاوت روزها بین دو تاریخ
        
        Args:
            date1: تاریخ اول (شمسی یا میلادی)
            date2: تاریخ دوم (شمسی یا میلادی)
            
        Returns:
            تعداد روزهای تفاوت یا None در صورت خطا
        """
        try:
            # تبدیل به datetime اگر string است
            if isinstance(date1, str):
                dt1 = TimeManager.from_shamsi(date1)
                if not dt1:
                    dt1 = datetime.strptime(date1, "%Y-%m-%d %H:%M:%S")
            else:
                dt1 = date1
                
            if isinstance(date2, str):
                dt2 = TimeManager.from_shamsi(date2)
                if not dt2:
                    dt2 = datetime.strptime(date2, "%Y-%m-%d %H:%M:%S")
            else:
                dt2 = date2
            
            return (dt2 - dt1).days
            
        except Exception as e:
            logger.error(f"Error calculating days difference: {e}")
            return None
    
    @staticmethod
    def is_expired(expiry_date: Union[str, datetime]) -> bool:
        """بررسی انقضای تاریخ
        
        Args:
            expiry_date: تاریخ انقضا
            
        Returns:
            True اگر منقضی شده باشد
        """
        try:
            now = datetime.now()
            
            if isinstance(expiry_date, str):
                exp_dt = TimeManager.from_shamsi(expiry_date)
                if not exp_dt:
                    exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            else:
                exp_dt = expiry_date
                
            return now >= exp_dt
            
        except Exception as e:
            logger.error(f"Error checking expiry: {e}")
            return True  # در صورت خطا، منقضی در نظر گرفته شود
    
    @staticmethod
    def time_until_expiry(expiry_date: Union[str, datetime]) -> Optional[dict]:
        """محاسبه زمان باقیمانده تا انقضا
        
        Args:
            expiry_date: تاریخ انقضا
            
        Returns:
            dict شامل روز، ساعت، دقیقه باقیمانده
        """
        try:
            now = datetime.now()
            
            if isinstance(expiry_date, str):
                exp_dt = TimeManager.from_shamsi(expiry_date)
                if not exp_dt:
                    exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            else:
                exp_dt = expiry_date
            
            if now >= exp_dt:
                return {"days": 0, "hours": 0, "minutes": 0, "expired": True}
            
            delta = exp_dt - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return {
                "days": days,
                "hours": hours, 
                "minutes": minutes,
                "expired": False
            }
            
        except Exception as e:
            logger.error(f"Error calculating time until expiry: {e}")
            return None
    
    @staticmethod
    def format_duration(duration_dict: dict) -> str:
        """فرمت‌بندی مدت زمان به فارسی
        
        Args:
            duration_dict: dict شامل days, hours, minutes
            
        Returns:
            مدت زمان به فرمت فارسی
        """
        try:
            if duration_dict.get("expired", False):
                return "منقضی شده"
            
            days = duration_dict.get("days", 0)
            hours = duration_dict.get("hours", 0)
            minutes = duration_dict.get("minutes", 0)
            
            parts = []
            if days > 0:
                parts.append(f"{days} روز")
            if hours > 0:
                parts.append(f"{hours} ساعت")
            if minutes > 0:
                parts.append(f"{minutes} دقیقه")
            
            if not parts:
                return "کمتر از یک دقیقه"
            
            return " و ".join(parts)
            
        except Exception as e:
            logger.error(f"Error formatting duration: {e}")
            return "نامشخص"
    
    @staticmethod
    def get_shamsi_month_name(month: int) -> str:
        """دریافت نام ماه شمسی
        
        Args:
            month: شماره ماه (1-12)
            
        Returns:
            نام ماه به فارسی
        """
        months = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد",
            4: "تیر", 5: "مرداد", 6: "شهریور",
            7: "مهر", 8: "آبان", 9: "آذر",
            10: "دی", 11: "بهمن", 12: "اسفند"
        }
        return months.get(month, "نامشخص")
    
    @staticmethod
    def get_weekday_name(dt: datetime) -> str:
        """دریافت نام روز هفته به فارسی
        
        Args:
            dt: تاریخ
            
        Returns:
            نام روز هفته به فارسی
        """
        weekdays = {
            0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه",
            3: "پنج‌شنبه", 4: "جمعه", 5: "شنبه", 6: "یکشنبه"
        }
        return weekdays.get(dt.weekday(), "نامشخص")
    
    @staticmethod
    def create_expiry_date(days: int = 30) -> str:
        """ایجاد تاریخ انقضا با روزهای مشخص
        
        Args:
            days: تعداد روزهای اعتبار
            
        Returns:
            تاریخ انقضا به فرمت شمسی
        """
        try:
            future_date = datetime.now() + timedelta(days=days)
            return TimeManager.to_shamsi(future_date)
        except Exception as e:
            logger.error(f"Error creating expiry date: {e}")
            return TimeManager.get_current_shamsi()
    
    @staticmethod
    def validate_shamsi_date(shamsi_str: str) -> bool:
        """اعتبارسنجی تاریخ شمسی
        
        Args:
            shamsi_str: تاریخ شمسی
            
        Returns:
            True اگر تاریخ معتبر باشد
        """
        return TimeManager.from_shamsi(shamsi_str) is not None


# Export functions برای استفاده آسان‌تر
to_shamsi = TimeManager.to_shamsi
from_shamsi = TimeManager.from_shamsi
get_current_shamsi = TimeManager.get_current_shamsi
get_current_time_persian = TimeManager.get_current_time_persian  # متد جدید
is_expired = TimeManager.is_expired
create_expiry_date = TimeManager.create_expiry_date

__all__ = [
    'TimeManager',
    'to_shamsi',
    'from_shamsi', 
    'get_current_shamsi',
    'get_current_time_persian',  # متد جدید اضافه شده
    'is_expired',
    'create_expiry_date'
]