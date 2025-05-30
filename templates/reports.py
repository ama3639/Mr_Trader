"""
قالب‌های گزارش برای MrTrader Bot
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.formatters import NumberFormatter, DateTimeFormatter, TableFormatter


class ReportTemplates:
    """قالب‌های گزارش عمومی"""
    
    @staticmethod
    def daily_summary_report(data: Dict[str, Any]) -> str:
        """گزارش خلاصه روزانه"""
        date_str = DateTimeFormatter.format_date_persian(datetime.now())
        
        return f"""
📊 <b>گزارش خلاصه روزانه</b>
📅 تاریخ: {date_str}

👥 <b>کاربران:</b>
• کل کاربران: {NumberFormatter.format_number_persian(data.get('total_users', 0))}
• کاربران فعال: {NumberFormatter.format_number_persian(data.get('active_users', 0))}
• کاربران جدید: {NumberFormatter.format_number_persian(data.get('new_users', 0))}

📈 <b>سیگنال‌ها:</b>
• تعداد سیگنال: {NumberFormatter.format_number_persian(data.get('total_signals', 0))}
• نرخ موفقیت: {NumberFormatter.format_percentage(data.get('success_rate', 0))}

💰 <b>مالی:</b>
• درآمد روزانه: ${NumberFormatter.format_number_persian(data.get('daily_revenue', 0))}
• تراکنش‌های موفق: {NumberFormatter.format_number_persian(data.get('successful_transactions', 0))}

🔍 <b>محبوب‌ترین نمادها:</b>
{ReportTemplates._format_top_symbols(data.get('top_symbols', []))}
"""
    
    @staticmethod
    def weekly_report(data: Dict[str, Any]) -> str:
        """گزارش هفتگی"""
        week_start = datetime.now() - timedelta(days=7)
        week_start_str = DateTimeFormatter.format_date_persian(week_start)
        week_end_str = DateTimeFormatter.format_date_persian(datetime.now())
        
        return f"""
📊 <b>گزارش هفتگی</b>
📅 بازه: {week_start_str} تا {week_end_str}

📈 <b>رشد کاربران:</b>
• کاربران جدید: {NumberFormatter.format_number_persian(data.get('new_users_week', 0))}
• نرخ رشد: {NumberFormatter.format_percentage(data.get('growth_rate', 0))}
• نرخ بازگشت: {NumberFormatter.format_percentage(data.get('retention_rate', 0))}

💹 <b>عملکرد سیگنال‌ها:</b>
• کل سیگنال‌ها: {NumberFormatter.format_number_persian(data.get('total_signals_week', 0))}
• سیگنال‌های موفق: {NumberFormatter.format_number_persian(data.get('successful_signals', 0))}
• میانگین اطمینان: {NumberFormatter.format_percentage(data.get('avg_confidence', 0))}

💰 <b>آمار مالی:</b>
• درآمد هفتگی: ${NumberFormatter.format_number_persian(data.get('weekly_revenue', 0))}
• میانگین روزانه: ${NumberFormatter.format_number_persian(data.get('avg_daily_revenue', 0))}
• رشد درآمد: {NumberFormatter.format_percentage(data.get('revenue_growth', 0))}

🎯 <b>پکیج‌های پرفروش:</b>
{ReportTemplates._format_top_packages(data.get('top_packages', []))}
"""
    
    @staticmethod
    def monthly_report(data: Dict[str, Any]) -> str:
        """گزارش ماهانه"""
        month_start = datetime.now().replace(day=1)
        month_start_str = DateTimeFormatter.format_date_persian(month_start)
        month_end_str = DateTimeFormatter.format_date_persian(datetime.now())
        
        return f"""
📊 <b>گزارش ماهانه</b>
📅 بازه: {month_start_str} تا {month_end_str}

👥 <b>آمار کاربران:</b>
• کل کاربران: {NumberFormatter.format_number_persian(data.get('total_users_month', 0))}
• کاربران فعال: {NumberFormatter.format_number_persian(data.get('active_users_month', 0))}
• کاربران جدید: {NumberFormatter.format_number_persian(data.get('new_users_month', 0))}
• نرخ چرن: {NumberFormatter.format_percentage(data.get('churn_rate', 0))}

📊 <b>توزیع پکیج‌ها:</b>
• رایگان: {NumberFormatter.format_percentage(data.get('free_users_percent', 0))}
• ابتدایی: {NumberFormatter.format_percentage(data.get('basic_users_percent', 0))}
• پریمیوم: {NumberFormatter.format_percentage(data.get('premium_users_percent', 0))}
• VIP: {NumberFormatter.format_percentage(data.get('vip_users_percent', 0))}

💰 <b>عملکرد مالی:</b>
• درآمد ماهانه: ${NumberFormatter.format_number_persian(data.get('monthly_revenue', 0))}
• ARR: ${NumberFormatter.format_number_persian(data.get('arr', 0))}
• ARPU: ${NumberFormatter.format_number_persian(data.get('arpu', 0))}
• LTV: ${NumberFormatter.format_number_persian(data.get('ltv', 0))}

🏆 <b>بهترین عملکردها:</b>
{ReportTemplates._format_best_performances(data.get('best_performances', {}))}
"""
    
    @staticmethod
    def _format_top_symbols(symbols: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی نمادهای برتر"""
        if not symbols:
            return "• داده‌ای موجود نیست"
        
        result = ""
        for i, symbol in enumerate(symbols[:5], 1):
            name = symbol.get('symbol', 'نامشخص')
            count = symbol.get('count', 0)
            result += f"• {i}. {name}: {NumberFormatter.format_number_persian(count)} بار\n"
        
        return result.rstrip()
    
    @staticmethod
    def _format_top_packages(packages: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی پکیج‌های برتر"""
        if not packages:
            return "• داده‌ای موجود نیست"
        
        result = ""
        for i, package in enumerate(packages[:3], 1):
            name = package.get('name_persian', 'نامشخص')
            sales = package.get('sales', 0)
            revenue = package.get('revenue', 0)
            result += f"• {i}. {name}: {NumberFormatter.format_number_persian(sales)} فروش (${NumberFormatter.format_number_persian(revenue)})\n"
        
        return result.rstrip()
    
    @staticmethod
    def _format_best_performances(performances: Dict[str, Any]) -> str:
        """فرمت‌بندی بهترین عملکردها"""
        if not performances:
            return "• داده‌ای موجود نیست"
        
        result = ""
        if performances.get('best_signal'):
            signal = performances['best_signal']
            result += f"• بهترین سیگنال: {signal.get('symbol')} ({NumberFormatter.format_percentage(signal.get('accuracy', 0))} دقت)\n"
        
        if performances.get('most_active_user'):
            user = performances['most_active_user']
            result += f"• فعال‌ترین کاربر: {user.get('name', 'نامشخص')} ({NumberFormatter.format_number_persian(user.get('signals_count', 0))} سیگنال)\n"
        
        if performances.get('highest_profit'):
            profit = performances['highest_profit']
            result += f"• بیشترین سود: {NumberFormatter.format_percentage(profit.get('percentage', 0))} ({profit.get('symbol', 'نامشخص')})\n"
        
        return result.rstrip() if result else "• داده‌ای موجود نیست"


class AdminReportTemplates:
    """قالب‌های گزارش ادمین"""
    
    @staticmethod
    def system_health_report(data: Dict[str, Any]) -> str:
        """گزارش سلامت سیستم"""
        current_time = DateTimeFormatter.format_datetime_persian(datetime.now())
        
        # تعیین وضعیت سلامت
        health_status = data.get('health_status', 'unknown')
        health_emoji = {
            'excellent': '🟢',
            'good': '🟡', 
            'warning': '🟠',
            'critical': '🔴',
            'unknown': '⚪'
        }.get(health_status, '⚪')
        
        return f"""
🖥️ <b>گزارش سلامت سیستم</b>
🕐 زمان گزارش: {current_time}

{health_emoji} <b>وضعیت کلی:</b> {health_status.title()}

💾 <b>منابع سیستم:</b>
• CPU: {NumberFormatter.format_percentage(data.get('cpu_usage', 0))}
• RAM: {NumberFormatter.format_percentage(data.get('memory_usage', 0))}
• دیسک: {NumberFormatter.format_percentage(data.get('disk_usage', 0))}

🌐 <b>اتصالات:</b>
• دیتابیس: {AdminReportTemplates._status_emoji(data.get('database_status'))} {data.get('database_status', 'نامشخص')}
• API خارجی: {AdminReportTemplates._status_emoji(data.get('api_status'))} {data.get('api_status', 'نامشخص')}
• اینترنت: {AdminReportTemplates._status_emoji(data.get('internet_status'))} {data.get('internet_status', 'نامشخص')}

📊 <b>عملکرد:</b>
• میانگین پاسخ: {data.get('avg_response_time', 0):.2f}ms
• درخواست‌های فعال: {NumberFormatter.format_number_persian(data.get('active_requests', 0))}
• خطاهای 24 ساعت: {NumberFormatter.format_number_persian(data.get('errors_24h', 0))}

🔄 <b>بکاپ:</b>
• آخرین بکاپ: {DateTimeFormatter.format_datetime_persian(data.get('last_backup'))}
• حجم بکاپ: {AdminReportTemplates._format_file_size(data.get('backup_size', 0))}
• وضعیت: {AdminReportTemplates._status_emoji(data.get('backup_status'))} {data.get('backup_status', 'نامشخص')}
"""
    
    @staticmethod
    def user_activity_report(data: Dict[str, Any]) -> str:
        """گزارش فعالیت کاربران"""
        return f"""
👥 <b>گزارش فعالیت کاربران</b>

📈 <b>آمار کلی:</b>
• کل کاربران: {NumberFormatter.format_number_persian(data.get('total_users', 0))}
• کاربران فعال امروز: {NumberFormatter.format_number_persian(data.get('active_today', 0))}
• کاربران فعال این هفته: {NumberFormatter.format_number_persian(data.get('active_week', 0))}
• کاربران فعال این ماه: {NumberFormatter.format_number_persian(data.get('active_month', 0))}

🆕 <b>کاربران جدید:</b>
• امروز: {NumberFormatter.format_number_persian(data.get('new_today', 0))}
• این هفته: {NumberFormatter.format_number_persian(data.get('new_week', 0))}
• این ماه: {NumberFormatter.format_number_persian(data.get('new_month', 0))}

📊 <b>توزیع استفاده:</b>
• متوسط سیگنال/کاربر: {data.get('avg_signals_per_user', 0):.1f}
• متوسط ورود/روز: {data.get('avg_logins_per_day', 0):.1f}
• زمان متوسط استفاده: {data.get('avg_session_time', 0):.1f} دقیقه

🚫 <b>کاربران غیرفعال:</b>
• مسدود شده: {NumberFormatter.format_number_persian(data.get('blocked_users', 0))}
• بیش از 30 روز غیرفعال: {NumberFormatter.format_number_persian(data.get('inactive_30d', 0))}

{AdminReportTemplates._format_top_active_users(data.get('top_active_users', []))}
"""
    
    @staticmethod
    def financial_report(data: Dict[str, Any]) -> str:
        """گزارش مالی"""
        return f"""
💰 <b>گزارش مالی</b>

📊 <b>درآمد:</b>
• امروز: ${NumberFormatter.format_number_persian(data.get('revenue_today', 0))}
• این هفته: ${NumberFormatter.format_number_persian(data.get('revenue_week', 0))}
• این ماه: ${NumberFormatter.format_number_persian(data.get('revenue_month', 0))}
• این سال: ${NumberFormatter.format_number_persian(data.get('revenue_year', 0))}

💳 <b>تراکنش‌ها:</b>
• موفق امروز: {NumberFormatter.format_number_persian(data.get('successful_transactions_today', 0))}
• ناموفق امروز: {NumberFormatter.format_number_persian(data.get('failed_transactions_today', 0))}
• نرخ موفقیت: {NumberFormatter.format_percentage(data.get('success_rate', 0))}
• میانگین مبلغ: ${NumberFormatter.format_number_persian(data.get('avg_transaction_amount', 0))}

📦 <b>فروش پکیج‌ها:</b>
• ابتدایی: {NumberFormatter.format_number_persian(data.get('basic_sales', 0))} (${NumberFormatter.format_number_persian(data.get('basic_revenue', 0))})
• پریمیوم: {NumberFormatter.format_number_persian(data.get('premium_sales', 0))} (${NumberFormatter.format_number_persian(data.get('premium_revenue', 0))})
• VIP: {NumberFormatter.format_number_persian(data.get('vip_sales', 0))} (${NumberFormatter.format_number_persian(data.get('vip_revenue', 0))})

💸 <b>تخفیفات و رفرال:</b>
• کل تخفیفات: ${NumberFormatter.format_number_persian(data.get('total_discounts', 0))}
• پاداش رفرال: ${NumberFormatter.format_number_persian(data.get('referral_rewards', 0))}
• درآمد خالص: ${NumberFormatter.format_number_persian(data.get('net_revenue', 0))}

📈 <b>پیش‌بینی:</b>
• درآمد پیش‌بینی ماه: ${NumberFormatter.format_number_persian(data.get('projected_monthly_revenue', 0))}
• رشد ماه به ماه: {NumberFormatter.format_percentage(data.get('mom_growth', 0))}
"""
    
    @staticmethod
    def security_report(data: Dict[str, Any]) -> str:
        """گزارش امنیت"""
        return f"""
🔒 <b>گزارش امنیت</b>

⚠️ <b>تهدیدات شناسایی شده:</b>
• تلاش‌های ورود مشکوک: {NumberFormatter.format_number_persian(data.get('suspicious_logins', 0))}
• IP های مسدود شده: {NumberFormatter.format_number_persian(data.get('blocked_ips', 0))}
• کاربران مسدود شده: {NumberFormatter.format_number_persian(data.get('blocked_users', 0))}

🚨 <b>حملات امنیتی:</b>
• Rate limiting triggers: {NumberFormatter.format_number_persian(data.get('rate_limit_triggers', 0))}
• تلاش‌های SQL injection: {NumberFormatter.format_number_persian(data.get('sql_injection_attempts', 0))}
• تلاش‌های XSS: {NumberFormatter.format_number_persian(data.get('xss_attempts', 0))}

🔐 <b>وضعیت امنیت:</b>
• SSL: {AdminReportTemplates._status_emoji(data.get('ssl_status'))} {data.get('ssl_status', 'نامشخص')}
• Firewall: {AdminReportTemplates._status_emoji(data.get('firewall_status'))} {data.get('firewall_status', 'نامشخص')}
• آخرین به‌روزرسانی امنیتی: {DateTimeFormatter.format_date_persian(data.get('last_security_update'))}

📊 <b>احراز هویت:</b>
• ورودهای موفق: {NumberFormatter.format_number_persian(data.get('successful_logins', 0))}
• ورودهای ناموفق: {NumberFormatter.format_number_persian(data.get('failed_logins', 0))}
• نرخ موفقیت: {NumberFormatter.format_percentage(data.get('login_success_rate', 0))}

{AdminReportTemplates._format_security_alerts(data.get('recent_alerts', []))}
"""
    
    @staticmethod
    def _status_emoji(status: str) -> str:
        """ایموجی وضعیت"""
        status_map = {
            'online': '🟢',
            'offline': '🔴',
            'warning': '🟡',
            'error': '❌',
            'ok': '✅',
            'active': '🟢',
            'inactive': '🔴'
        }
        return status_map.get(status, '⚪')
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """فرمت‌بندی اندازه فایل"""
        if size_bytes >= 1024**3:
            return f"{size_bytes / (1024**3):.2f} GB"
        elif size_bytes >= 1024**2:
            return f"{size_bytes / (1024**2):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} bytes"
    
    @staticmethod
    def _format_top_active_users(users: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی کاربران فعال"""
        if not users:
            return "\n🏆 <b>فعال‌ترین کاربران:</b>\n• داده‌ای موجود نیست"
        
        result = "\n🏆 <b>فعال‌ترین کاربران:</b>\n"
        for i, user in enumerate(users[:5], 1):
            name = user.get('name', 'نامشخص')
            activity_count = user.get('activity_count', 0)
            result += f"• {i}. {name}: {NumberFormatter.format_number_persian(activity_count)} فعالیت\n"
        
        return result.rstrip()
    
    @staticmethod
    def _format_security_alerts(alerts: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی هشدارهای امنیتی"""
        if not alerts:
            return "\n🚨 <b>هشدارهای اخیر:</b>\n• هیچ هشداری وجود ندارد"
        
        result = "\n🚨 <b>هشدارهای اخیر:</b>\n"
        for alert in alerts[:3]:
            time_str = DateTimeFormatter.format_datetime_persian(alert.get('timestamp'))
            message = alert.get('message', 'نامشخص')
            severity = alert.get('severity', 'info')
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
            result += f"• {severity_emoji} {time_str}: {message}\n"
        
        return result.rstrip()


class UserReportTemplates:
    """قالب‌های گزارش کاربر"""
    
    @staticmethod
    def user_performance_report(data: Dict[str, Any]) -> str:
        """گزارش عملکرد کاربر"""
        return f"""
📊 <b>گزارش عملکرد شما</b>

📈 <b>آمار کلی:</b>
• سیگنال‌های دریافتی: {NumberFormatter.format_number_persian(data.get('signals_received', 0))}
• معاملات انجام شده: {NumberFormatter.format_number_persian(data.get('trades_executed', 0))}
• نرخ موفقیت: {NumberFormatter.format_percentage(data.get('success_rate', 0))}
• میانگین سود: {NumberFormatter.format_percentage(data.get('avg_profit', 0))}

💰 <b>عملکرد مالی:</b>
• کل سود: {NumberFormatter.format_price(data.get('total_profit', 0))}
• کل زیان: {NumberFormatter.format_price(data.get('total_loss', 0))}
• سود خالص: {NumberFormatter.format_price(data.get('net_profit', 0))}
• بهترین معامله: {NumberFormatter.format_percentage(data.get('best_trade', 0))}
• بدترین معامله: {NumberFormatter.format_percentage(data.get('worst_trade', 0))}

📊 <b>تحلیل ریسک:</b>
• سطح ریسک فعلی: {data.get('current_risk_level', 'متوسط')}
• حداکثر ضرر: {NumberFormatter.format_percentage(data.get('max_drawdown', 0))}
• نسبت شارپ: {data.get('sharpe_ratio', 0):.2f}

🎯 <b>نمادهای برتر:</b>
{UserReportTemplates._format_user_top_symbols(data.get('top_symbols', []))}

🏆 <b>دستاوردها:</b>
{UserReportTemplates._format_user_achievements(data.get('achievements', []))}
"""
    
    @staticmethod
    def user_activity_summary(data: Dict[str, Any]) -> str:
        """خلاصه فعالیت کاربر"""
        return f"""
📱 <b>خلاصه فعالیت شما</b>

⏰ <b>زمان استفاده:</b>
• کل زمان: {data.get('total_time_hours', 0):.1f} ساعت
• میانگین روزانه: {data.get('avg_daily_time', 0):.1f} دقیقه
• آخرین ورود: {DateTimeFormatter.format_datetime_persian(data.get('last_login'))}
• تعداد جلسات: {NumberFormatter.format_number_persian(data.get('total_sessions', 0))}

📊 <b>استفاده از امکانات:</b>
• تحلیل‌های درخواستی: {NumberFormatter.format_number_persian(data.get('analyses_requested', 0))}
• هشدارهای تنظیم شده: {NumberFormatter.format_number_persian(data.get('alerts_set', 0))}
• گزارش‌های مشاهده شده: {NumberFormatter.format_number_persian(data.get('reports_viewed', 0))}

🎁 <b>امتیازات:</b>
• امتیاز فعلی: {NumberFormatter.format_number_persian(data.get('current_points', 0))}
• کل امتیاز کسب شده: {NumberFormatter.format_number_persian(data.get('total_points_earned', 0))}
• امتیاز مصرف شده: {NumberFormatter.format_number_persian(data.get('points_spent', 0))}

📈 <b>وضعیت پکیج:</b>
• پکیج فعلی: {data.get('current_package', 'رایگان')}
• تاریخ انقضا: {DateTimeFormatter.format_date_persian(data.get('expiry_date'))}
• روزهای باقیمانده: {data.get('days_remaining', 0)}
"""
    
    @staticmethod
    def user_referral_report(data: Dict[str, Any]) -> str:
        """گزارش رفرال کاربر"""
        return f"""
🎁 <b>گزارش رفرال شما</b>

👥 <b>آمار دعوت:</b>
• کل دعوت‌ها: {NumberFormatter.format_number_persian(data.get('total_referrals', 0))}
• دعوت‌های موفق: {NumberFormatter.format_number_persian(data.get('successful_referrals', 0))}
• دعوت‌های فعال: {NumberFormatter.format_number_persian(data.get('active_referrals', 0))}
• نرخ موفقیت: {NumberFormatter.format_percentage(data.get('referral_success_rate', 0))}

💰 <b>درآمد رفرال:</b>
• کل درآمد: {NumberFormatter.format_price(data.get('total_referral_income', 0))}
• درآمد این ماه: {NumberFormatter.format_price(data.get('monthly_referral_income', 0))}
• میانگین درآمد/رفرال: {NumberFormatter.format_price(data.get('avg_income_per_referral', 0))}

🏆 <b>رتبه‌بندی:</b>
• رتبه شما: {data.get('referral_rank', 'نامشخص')}
• امتیاز رفرال: {NumberFormatter.format_number_persian(data.get('referral_score', 0))}

📊 <b>عملکرد ماهانه:</b>
{UserReportTemplates._format_monthly_referral_performance(data.get('monthly_performance', []))}

🎯 <b>اهداف:</b>
• هدف ماه جاری: {data.get('monthly_goal', 0)} دعوت
• پیشرفت: {NumberFormatter.format_percentage(data.get('goal_progress', 0))}
• پاداش بعدی: {NumberFormatter.format_price(data.get('next_reward', 0))} در {data.get('referrals_needed', 0)} دعوت
"""
    
    @staticmethod
    def _format_user_top_symbols(symbols: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی نمادهای برتر کاربر"""
        if not symbols:
            return "• داده‌ای موجود نیست"
        
        result = ""
        for i, symbol in enumerate(symbols[:3], 1):
            name = symbol.get('symbol', 'نامشخص')
            profit = symbol.get('profit_percentage', 0)
            trades = symbol.get('trades_count', 0)
            result += f"• {i}. {name}: {NumberFormatter.format_percentage(profit)} سود ({trades} معامله)\n"
        
        return result.rstrip()
    
    @staticmethod
    def _format_user_achievements(achievements: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی دستاوردهای کاربر"""
        if not achievements:
            return "• هنوز دستاوردی کسب نکرده‌اید"
        
        result = ""
        for achievement in achievements[:3]:
            title = achievement.get('title', 'نامشخص')
            date = achievement.get('date')
            date_str = DateTimeFormatter.format_date_persian(date) if date else 'نامشخص'
            result += f"🏆 {title} ({date_str})\n"
        
        return result.rstrip()
    
    @staticmethod
    def _format_monthly_referral_performance(performance: List[Dict[str, Any]]) -> str:
        """فرمت‌بندی عملکرد ماهانه رفرال"""
        if not performance:
            return "• داده‌ای موجود نیست"
        
        result = ""
        for month_data in performance[-3:]:  # آخرین 3 ماه
            month = month_data.get('month', 'نامشخص')
            referrals = month_data.get('referrals', 0)
            income = month_data.get('income', 0)
            result += f"• {month}: {referrals} دعوت، ${NumberFormatter.format_number_persian(income)} درآمد\n"
        
        return result.rstrip()


# Export
__all__ = [
    'ReportTemplates',
    'AdminReportTemplates',
    'UserReportTemplates'
]