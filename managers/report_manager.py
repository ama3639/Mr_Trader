"""
مدیریت گزارش‌گیری و آمار MrTrader Bot
"""
import io
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import base64

from core.config import Config
from utils.logger import logger
from database.database_manager import DatabaseManager
from core.cache import cache
from utils.time_manager import TimeManager


@dataclass
class ReportData:
    """مدل داده‌های گزارش"""
    title: str
    data: Dict[str, Any]
    generated_at: datetime
    report_type: str
    period: str
    format: str = 'json'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'data': self.data,
            'generated_at': self.generated_at.isoformat(),
            'report_type': self.report_type,
            'period': self.period,
            'format': self.format
        }


class ReportManager:
    """مدیریت گزارش‌ها و آمار"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.time_manager = TimeManager()
        self._initialize_report_system()
    
    def _initialize_report_system(self):
        """مقداردهی اولیه سیستم گزارش‌گیری"""
        try:
            # ایجاد جدول گزارش‌ها
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    generated_by INTEGER,
                    file_path TEXT,
                    is_automated BOOLEAN DEFAULT 0
                )
            """)
            
            # ایجاد جدول برنامه‌ریزی گزارش‌ها
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS report_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    schedule_pattern TEXT NOT NULL,
                    last_generated TIMESTAMP,
                    next_generation TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    recipients TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ایجاد جدول اشتراک گزارش‌ها
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS report_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    report_type TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, report_type)
                )
            """)
            
            logger.info("Report system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing report system: {e}")
    
    async def generate_daily_report(self, date: datetime = None) -> ReportData:
        """تولید گزارش روزانه"""
        try:
            if date is None:
                date = datetime.now()
            
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            # آمار کاربران
            user_stats = await self._get_user_statistics(start_date, end_date)
            
            # آمار معاملات و سیگنال‌ها
            trading_stats = await self._get_trading_statistics(start_date, end_date)
            
            # آمار سیستم
            system_stats = await self._get_system_statistics(start_date, end_date)
            
            # آمار درآمد
            revenue_stats = await self._get_revenue_statistics(start_date, end_date)
            
            # ساخت گزارش
            report_data = {
                'date': date.strftime('%Y-%m-%d'),
                'period': 'daily',
                'user_statistics': user_stats,
                'trading_statistics': trading_stats,
                'system_statistics': system_stats,
                'revenue_statistics': revenue_stats,
                'summary': await self._generate_daily_summary(user_stats, trading_stats, revenue_stats)
            }
            
            report = ReportData(
                title=f"گزارش روزانه {self.time_manager.format_date_persian(date)}",
                data=report_data,
                generated_at=datetime.now(),
                report_type='daily',
                period=date.strftime('%Y-%m-%d')
            )
            
            # ذخیره گزارش
            await self._save_report(report)
            
            logger.info(f"Generated daily report for {date.strftime('%Y-%m-%d')}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return None
    
    async def generate_weekly_report(self, week_start: datetime = None) -> ReportData:
        """تولید گزارش هفتگی"""
        try:
            if week_start is None:
                today = datetime.now()
                week_start = today - timedelta(days=today.weekday())
            
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=7)
            
            # جمع‌آوری آمار هفتگی
            weekly_data = {
                'week_start': week_start.strftime('%Y-%m-%d'),
                'week_end': (week_end - timedelta(days=1)).strftime('%Y-%m-%d'),
                'period': 'weekly'
            }
            
            # آمار کاربران هفتگی
            weekly_data['user_growth'] = await self._get_user_growth_stats(week_start, week_end)
            
            # آمار عملکرد سیگنال‌ها
            weekly_data['signal_performance'] = await self._get_signal_performance_stats(week_start, week_end)
            
            # آمار محبوب‌ترین نمادها
            weekly_data['popular_symbols'] = await self._get_popular_symbols_stats(week_start, week_end)
            
            # آمار پکیج‌ها
            weekly_data['package_stats'] = await self._get_package_statistics(week_start, week_end)
            
            # روند کلی بازار
            weekly_data['market_trends'] = await self._get_market_trends(week_start, week_end)
            
            report = ReportData(
                title=f"گزارش هفتگی {self.time_manager.format_date_persian(week_start)} تا {self.time_manager.format_date_persian(week_end)}",
                data=weekly_data,
                generated_at=datetime.now(),
                report_type='weekly',
                period=f"{week_start.strftime('%Y-%m-%d')}_to_{week_end.strftime('%Y-%m-%d')}"
            )
            
            await self._save_report(report)
            
            logger.info(f"Generated weekly report for week starting {week_start.strftime('%Y-%m-%d')}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return None
    
    async def generate_monthly_report(self, month: int = None, year: int = None) -> ReportData:
        """تولید گزارش ماهانه"""
        try:
            if month is None or year is None:
                now = datetime.now()
                month = now.month
                year = now.year
            
            # شروع و پایان ماه
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month + 1, 1)
            
            # آمار ماهانه
            monthly_data = {
                'month': month,
                'year': year,
                'period': 'monthly',
                'persian_month': self.time_manager.get_persian_month_name(month),
                'month_start': month_start.strftime('%Y-%m-%d'),
                'month_end': (month_end - timedelta(days=1)).strftime('%Y-%m-%d')
            }
            
            # آمار کاربران ماهانه
            monthly_data['user_analytics'] = await self._get_monthly_user_analytics(month_start, month_end)
            
            # آمار درآمد ماهانه
            monthly_data['revenue_analytics'] = await self._get_monthly_revenue_analytics(month_start, month_end)
            
            # آمار استراتژی‌ها
            monthly_data['strategy_performance'] = await self._get_strategy_performance_monthly(month_start, month_end)
            
            # آمار رفرال‌ها
            monthly_data['referral_analytics'] = await self._get_referral_analytics_monthly(month_start, month_end)
            
            # تحلیل روندها
            monthly_data['trends_analysis'] = await self._analyze_monthly_trends(month_start, month_end)
            
            # پیش‌بینی ماه آینده
            monthly_data['next_month_forecast'] = await self._forecast_next_month(monthly_data)
            
            report = ReportData(
                title=f"گزارش ماهانه {self.time_manager.get_persian_month_name(month)} {year}",
                data=monthly_data,
                generated_at=datetime.now(),
                report_type='monthly',
                period=f"{year}-{month:02d}"
            )
            
            await self._save_report(report)
            
            logger.info(f"Generated monthly report for {year}-{month:02d}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return None
    
    async def generate_user_report(self, user_id: int, days: int = 30) -> ReportData:
        """تولید گزارش شخصی کاربر"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # اطلاعات پایه کاربر
            user_info = self.db.fetch_one("""
                SELECT * FROM users WHERE telegram_id = ?
            """, (user_id,))
            
            if not user_info:
                return None
            
            user_data = {
                'user_id': user_id,
                'period_days': days,
                'report_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_for': user_info.get('username', 'Unknown')
            }
            
            # آمار فعالیت کاربر
            user_data['activity_stats'] = await self._get_user_activity_stats(user_id, start_date, end_date)
            
            # تاریخچه استفاده از سیگنال‌ها
            user_data['signal_history'] = await self._get_user_signal_history(user_id, start_date, end_date)
            
            # آمار پرداخت‌ها
            user_data['payment_history'] = await self._get_user_payment_history(user_id, start_date, end_date)
            
            # آمار رفرال (اگر دارد)
            user_data['referral_stats'] = await self._get_user_referral_stats(user_id)
            
            # پیشنهادات شخصی‌سازی‌شده
            user_data['recommendations'] = await self._generate_user_recommendations(user_id, user_data)
            
            report = ReportData(
                title=f"گزارش شخصی {days} روز گذشته",
                data=user_data,
                generated_at=datetime.now(),
                report_type='user',
                period=f"user_{user_id}_{days}days"
            )
            
            logger.info(f"Generated user report for user {user_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating user report for {user_id}: {e}")
            return None
    
    async def generate_admin_dashboard_report(self) -> ReportData:
        """تولید گزارش داشبورد ادمین"""
        try:
            # آمار فوری سیستم
            dashboard_data = {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'admin_dashboard'
            }
            
            # آمار کلی
            dashboard_data['overview'] = {
                'total_users': self._get_total_users_count(),
                'active_users_today': self._get_active_users_today(),
                'total_revenue': self._get_total_revenue(),
                'pending_payments': self._get_pending_payments_count(),
                'active_signals': self._get_active_signals_count(),
                'system_health': await self._get_system_health_status()
            }
            
            # آمار 24 ساعت گذشته
            yesterday = datetime.now() - timedelta(days=1)
            dashboard_data['last_24h'] = {
                'new_users': self._get_new_users_count(yesterday),
                'revenue': self._get_revenue_since(yesterday),
                'signals_generated': self._get_signals_count_since(yesterday),
                'api_requests': self._get_api_requests_count(yesterday),
                'errors': self._get_errors_count(yesterday)
            }
            
            # آمار عملکرد
            dashboard_data['performance'] = {
                'signal_accuracy': await self._get_recent_signal_accuracy(),
                'user_satisfaction': await self._get_user_satisfaction_score(),
                'system_uptime': await self._get_system_uptime(),
                'response_time': await self._get_average_response_time()
            }
            
            # هشدارها و اعلان‌های مهم
            dashboard_data['alerts'] = await self._get_system_alerts()
            
            # آمار پرفروش‌ترین پکیج‌ها
            dashboard_data['top_packages'] = await self._get_top_selling_packages()
            
            report = ReportData(
                title="داشبورد ادمین",
                data=dashboard_data,
                generated_at=datetime.now(),
                report_type='admin_dashboard',
                period='realtime'
            )
            
            logger.info("Generated admin dashboard report")
            return report
            
        except Exception as e:
            logger.error(f"Error generating admin dashboard report: {e}")
            return None
    
    async def _get_user_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """آمار کاربران در بازه زمانی"""
        try:
            # کاربران جدید
            new_users = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM users 
                WHERE registration_date BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # کاربران فعال
            active_users = self.db.fetch_one("""
                SELECT COUNT(DISTINCT user_id) as count FROM user_activity 
                WHERE activity_date BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # تعداد کل کاربران
            total_users = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM users 
                WHERE registration_date <= ?
            """, (end_date.isoformat(),))
            
            return {
                'new_users': new_users['count'] if new_users else 0,
                'active_users': active_users['count'] if active_users else 0,
                'total_users': total_users['count'] if total_users else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {'new_users': 0, 'active_users': 0, 'total_users': 0}
    
    async def _get_trading_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """آمار معاملات و سیگنال‌ها"""
        try:
            # تعداد سیگنال‌های تولیدشده
            signals_generated = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM signals 
                WHERE created_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # سیگنال‌های موفق
            successful_signals = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM signals 
                WHERE created_at BETWEEN ? AND ? AND success_rate > 0.6
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # نرخ موفقیت میانگین
            avg_success_rate = self.db.fetch_one("""
                SELECT AVG(success_rate) as avg_rate FROM signals 
                WHERE created_at BETWEEN ? AND ? AND success_rate IS NOT NULL
            """, (start_date.isoformat(), end_date.isoformat()))
            
            return {
                'signals_generated': signals_generated['count'] if signals_generated else 0,
                'successful_signals': successful_signals['count'] if successful_signals else 0,
                'average_success_rate': round(avg_success_rate['avg_rate'] * 100, 2) if avg_success_rate and avg_success_rate['avg_rate'] else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting trading statistics: {e}")
            return {'signals_generated': 0, 'successful_signals': 0, 'average_success_rate': 0}
    
    async def _get_system_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """آمار سیستم"""
        try:
            # تعداد درخواست‌های API
            api_requests = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM api_logs 
                WHERE timestamp BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # خطاهای سیستم
            system_errors = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM error_logs 
                WHERE timestamp BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # میانگین زمان پاسخ
            avg_response_time = self.db.fetch_one("""
                SELECT AVG(response_time) as avg_time FROM api_logs 
                WHERE timestamp BETWEEN ? AND ? AND response_time IS NOT NULL
            """, (start_date.isoformat(), end_date.isoformat()))
            
            return {
                'api_requests': api_requests['count'] if api_requests else 0,
                'system_errors': system_errors['count'] if system_errors else 0,
                'average_response_time': round(avg_response_time['avg_time'], 3) if avg_response_time and avg_response_time['avg_time'] else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {'api_requests': 0, 'system_errors': 0, 'average_response_time': 0}
    
    async def _get_revenue_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """آمار درآمد"""
        try:
            # درآمد کل
            total_revenue = self.db.fetch_one("""
                SELECT SUM(amount) as total FROM payments 
                WHERE payment_date BETWEEN ? AND ? AND status = 'completed'
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # تعداد پرداخت‌ها
            payment_count = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM payments 
                WHERE payment_date BETWEEN ? AND ? AND status = 'completed'
            """, (start_date.isoformat(), end_date.isoformat()))
            
            # میانگین پرداخت
            avg_payment = total_revenue['total'] / payment_count['count'] if payment_count['count'] > 0 else 0
            
            return {
                'total_revenue': total_revenue['total'] if total_revenue['total'] else 0,
                'payment_count': payment_count['count'] if payment_count else 0,
                'average_payment': round(avg_payment, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue statistics: {e}")
            return {'total_revenue': 0, 'payment_count': 0, 'average_payment': 0}
    
    async def _generate_daily_summary(self, user_stats: Dict, trading_stats: Dict, revenue_stats: Dict) -> str:
        """تولید خلاصه گزارش روزانه"""
        try:
            summary_parts = []
            
            # خلاصه کاربران
            if user_stats['new_users'] > 0:
                summary_parts.append(f"🆕 {user_stats['new_users']} کاربر جدید")
            
            # خلاصه سیگنال‌ها
            if trading_stats['signals_generated'] > 0:
                summary_parts.append(f"📈 {trading_stats['signals_generated']} سیگنال تولید شد")
                if trading_stats['average_success_rate'] > 0:
                    summary_parts.append(f"✅ نرخ موفقیت: {trading_stats['average_success_rate']}%")
            
            # خلاصه درآمد
            if revenue_stats['total_revenue'] > 0:
                summary_parts.append(f"💰 درآمد: {revenue_stats['total_revenue']:,.0f} تومان")
            
            return " | ".join(summary_parts) if summary_parts else "هیچ فعالیت قابل توجهی نداشتیم"
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return "خطا در تولید خلاصه گزارش"
    
    async def _save_report(self, report: ReportData) -> bool:
        """ذخیره گزارش در دیتابیس"""
        try:
            self.db.execute_query("""
                INSERT INTO reports (title, report_type, period, data_json, generated_at, is_automated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report.title,
                report.report_type,
                report.period,
                json.dumps(report.data, ensure_ascii=False),
                report.generated_at.isoformat(),
                1  # automated
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False
    
    def get_saved_reports(self, report_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """دریافت گزارش‌های ذخیره‌شده"""
        try:
            if report_type:
                reports = self.db.fetch_all("""
                    SELECT id, title, report_type, period, generated_at 
                    FROM reports 
                    WHERE report_type = ?
                    ORDER BY generated_at DESC 
                    LIMIT ?
                """, (report_type, limit))
            else:
                reports = self.db.fetch_all("""
                    SELECT id, title, report_type, period, generated_at 
                    FROM reports 
                    ORDER BY generated_at DESC 
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in reports] if reports else []
            
        except Exception as e:
            logger.error(f"Error getting saved reports: {e}")
            return []
    
    def get_report_by_id(self, report_id: int) -> Optional[ReportData]:
        """دریافت گزارش با شناسه"""
        try:
            report = self.db.fetch_one("""
                SELECT * FROM reports WHERE id = ?
            """, (report_id,))
            
            if report:
                data = json.loads(report['data_json'])
                return ReportData(
                    title=report['title'],
                    data=data,
                    generated_at=datetime.fromisoformat(report['generated_at']),
                    report_type=report['report_type'],
                    period=report['period']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def export_report_to_text(self, report: ReportData) -> str:
        """صادرات گزارش به متن"""
        try:
            text_lines = [
                f"📊 {report.title}",
                f"📅 تولید شده در: {self.time_manager.format_datetime_persian(report.generated_at)}",
                f"🔄 نوع گزارش: {report.report_type}",
                f"📈 دوره: {report.period}",
                "",
                "📋 جزئیات گزارش:",
                "=" * 30
            ]
            
            # تبدیل داده‌ها به متن
            text_lines.extend(self._format_data_to_text(report.data))
            
            return "\n".join(text_lines)
            
        except Exception as e:
            logger.error(f"Error exporting report to text: {e}")
            return f"خطا در صادرات گزارش: {str(e)}"
    
    def _format_data_to_text(self, data: Dict[str, Any], level: int = 0) -> List[str]:
        """تبدیل داده‌ها به فرمت متنی"""
        lines = []
        indent = "  " * level
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent}📂 {key}:")
                lines.extend(self._format_data_to_text(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{indent}📄 {key}: ({len(value)} آیتم)")
                for i, item in enumerate(value[:5]):  # محدود به 5 آیتم اول
                    if isinstance(item, dict):
                        lines.append(f"{indent}  {i+1}. {list(item.values())[0] if item else 'خالی'}")
                    else:
                        lines.append(f"{indent}  {i+1}. {item}")
                if len(value) > 5:
                    lines.append(f"{indent}  ... و {len(value) - 5} آیتم دیگر")
            else:
                # فرمت‌بندی مقادیر عددی
                if isinstance(value, (int, float)) and value > 1000:
                    formatted_value = f"{value:,.0f}" if isinstance(value, int) else f"{value:,.2f}"
                else:
                    formatted_value = str(value)
                
                lines.append(f"{indent}• {key}: {formatted_value}")
        
        return lines
    
    async def schedule_report(self, report_type: str, schedule_pattern: str, 
                            recipients: List[str] = None) -> bool:
        """برنامه‌ریزی تولید خودکار گزارش"""
        try:
            recipients_json = json.dumps(recipients) if recipients else None
            
            self.db.execute_query("""
                INSERT OR REPLACE INTO report_schedules 
                (report_type, schedule_pattern, recipients, is_active)
                VALUES (?, ?, ?, 1)
            """, (report_type, schedule_pattern, recipients_json))
            
            logger.info(f"Scheduled {report_type} report with pattern: {schedule_pattern}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling report: {e}")
            return False
    
    # توابع کمکی برای شبیه‌سازی داده‌ها (در پیاده‌سازی واقعی جایگزین شوند)
    def _get_total_users_count(self) -> int:
        try:
            result = self.db.fetch_one("SELECT COUNT(*) as count FROM users")
            return result['count'] if result else 0
        except:
            return 0
    
    def _get_active_users_today(self) -> int:
        try:
            today = datetime.now().date()
            result = self.db.fetch_one("""
                SELECT COUNT(DISTINCT user_id) as count FROM user_activity 
                WHERE DATE(activity_date) = ?
            """, (today.isoformat(),))
            return result['count'] if result else 0
        except:
            return 0
    
    def _get_total_revenue(self) -> float:
        try:
            result = self.db.fetch_one("""
                SELECT SUM(amount) as total FROM payments 
                WHERE status = 'completed'
            """)
            return result['total'] if result and result['total'] else 0
        except:
            return 0
    
    async def _get_system_health_status(self) -> str:
        """وضعیت سلامت سیستم"""
        try:
            # بررسی‌های سلامت پایه
            db_healthy = True
            api_healthy = True
            
            try:
                self.db.fetch_one("SELECT 1")
            except:
                db_healthy = False
            
            # در پیاده‌سازی واقعی، API هم بررسی شود
            
            if db_healthy and api_healthy:
                return "سالم"
            elif db_healthy or api_healthy:
                return "نیمه‌سالم"
            else:
                return "مشکل‌دار"
                
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return "نامشخص"
    
    # سایر توابع کمکی برای داده‌های مک...
    async def _get_user_growth_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {'weekly_growth': 15, 'retention_rate': 78.5}
    
    async def _get_signal_performance_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {'accuracy': 68.2, 'total_signals': 145, 'profitable_signals': 99}
    
    async def _get_popular_symbols_stats(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        return [
            {'symbol': 'BTC', 'requests': 1250, 'success_rate': 72.1},
            {'symbol': 'ETH', 'requests': 980, 'success_rate': 69.8},
            {'symbol': 'BNB', 'requests': 756, 'success_rate': 71.2}
        ]


# Export
__all__ = ['ReportManager', 'ReportData']