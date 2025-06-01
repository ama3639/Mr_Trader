"""
قالب‌های گزارش - تولید گزارش‌های تخصصی
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.time_manager import TimeManager
from utils.helpers import format_currency, format_percentage, format_number

class ReportTemplates:
    """کلاس قالب‌های گزارش"""
    
    @staticmethod
    def technical_analysis_report(analysis_data: Dict[str, Any]) -> str:
        """گزارش تحلیل تکنیکال کامل"""
        symbol = analysis_data.get('symbol', 'N/A')
        currency = analysis_data.get('currency', 'N/A')
        timeframe = analysis_data.get('timeframe', 'N/A')
        strategy = analysis_data.get('strategy', 'N/A')
        current_price = analysis_data.get('current_price', 0)
        signal_details = analysis_data.get('signal_details', {})
        
        # تاریخ و زمان فارسی
        persian_datetime = TimeManager.to_shamsi(datetime.now())
        
        report = f"""📊 گزارش تحلیل تکنیکال MrTrader Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ نماد: {symbol}/{currency}
📈 استراتژی: {strategy.upper()}
⏱️ تایم‌فریم: {timeframe}
🕒 تاریخ تحلیل: {persian_datetime}
💰 قیمت فعلی: {current_price:,.2f} {currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 خلاصه سیگنال:
• جهت: {signal_details.get('signal_direction', 'N/A').upper()}
• قدرت: {signal_details.get('strength', 'N/A')}
• اعتماد: {signal_details.get('confidence', 50):.0f}%

💰 سطوح کلیدی:
• نقطه ورود: {signal_details.get('entry_price', 0):,.2f}
• حد ضرر: {signal_details.get('stop_loss', 0):,.2f}
• هدف قیمتی: {signal_details.get('take_profit', 0):,.2f}

📊 حمایت و مقاومت:
• حمایت اولیه: {signal_details.get('support', 0):,.2f}
• مقاومت اولیه: {signal_details.get('resistance', 0):,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 تحلیل تفصیلی:

{analysis_data.get('detailed_analysis', 'تحلیل تفصیلی در دسترس نیست.')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ هشدارها و نکات:
• این تحلیل صرفاً جنبه آموزشی دارد
• همیشه تحقیقات شخصی انجام دهید
• مدیریت ریسک را رعایت کنید
• از حد ضرر استفاده کنید

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏢 تولید شده توسط: MrTrader Bot
🌐 وب‌سایت: https://mrtrader.bot
📧 پشتیبانی: support@mrtrader.bot

© 2024 MrTrader Bot. تمامی حقوق محفوظ است.
"""
        return report
    
    @staticmethod
    def portfolio_analysis_report(portfolio_data: Dict[str, Any]) -> str:
        """گزارش تحلیل پرتفو"""
        positions = portfolio_data.get('positions', [])
        total_value = portfolio_data.get('total_value', 0)
        total_pnl = portfolio_data.get('total_pnl', 0)
        total_pnl_percent = portfolio_data.get('total_pnl_percent', 0)
        
        report = f"""💼 گزارش تحلیل پرتفو
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 تاریخ گزارش: {TimeManager.to_shamsi(datetime.now())}

📊 خلاصه پرتفو:
• ارزش کل: ${total_value:,.2f}
• سود/زیان کل: ${total_pnl:,.2f} ({total_pnl_percent:+.2f}%)
• تعداد موقعیت‌ها: {len(positions)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 جزئیات موقعیت‌ها:
"""
        
        for i, position in enumerate(positions, 1):
            symbol = position.get('symbol', 'N/A')
            quantity = position.get('quantity', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            pnl = position.get('pnl', 0)
            pnl_percent = position.get('pnl_percent', 0)
            
            report += f"""
{i}. {symbol}:
   • مقدار: {quantity:,.4f}
   • قیمت ورود: ${entry_price:,.2f}
   • قیمت فعلی: ${current_price:,.2f}
   • سود/زیان: ${pnl:,.2f} ({pnl_percent:+.2f}%)
"""
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 آمار عملکرد:
• بهترین موقعیت: {portfolio_data.get('best_position', 'N/A')}
• بدترین موقعیت: {portfolio_data.get('worst_position', 'N/A')}
• میانگین بازدهی: {portfolio_data.get('avg_return', 0):.2f}%

🏢 تولید شده توسط: MrTrader Bot
"""
        return report
    
    @staticmethod
    def daily_summary_report(daily_data: Dict[str, Any]) -> str:
        """گزارش خلاصه روزانه"""
        date = daily_data.get('date', datetime.now().date())
        total_analyses = daily_data.get('total_analyses', 0)
        successful_analyses = daily_data.get('successful_analyses', 0)
        top_symbols = daily_data.get('top_symbols', [])
        top_strategies = daily_data.get('top_strategies', [])
        
        success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        report = f"""📅 گزارش خلاصه روزانه
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 تاریخ: {TimeManager.to_shamsi(datetime.combine(date, datetime.min.time()))}

📊 آمار کلی:
• کل تحلیل‌ها: {total_analyses:,}
• تحلیل‌های موفق: {successful_analyses:,}
• نرخ موفقیت: {success_rate:.1f}%

🔥 محبوب‌ترین نمادها:
"""
        
        for i, symbol_data in enumerate(top_symbols[:5], 1):
            symbol = symbol_data.get('symbol', 'N/A')
            count = symbol_data.get('count', 0)
            report += f"{i}. {symbol}: {count:,} تحلیل\n"
        
        report += f"""
⭐ محبوب‌ترین استراتژی‌ها:
"""
        
        for i, strategy_data in enumerate(top_strategies[:5], 1):
            strategy = strategy_data.get('strategy', 'N/A')
            count = strategy_data.get('count', 0)
            report += f"{i}. {strategy}: {count:,} تحلیل\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 نکات روز:
{daily_data.get('daily_insights', 'بدون نکته خاص برای امروز.')}

🏢 تولید شده توسط: MrTrader Bot
"""
        return report
    
    @staticmethod
    def user_activity_report(user_data: Dict[str, Any]) -> str:
        """گزارش فعالیت کاربر"""
        user_id = user_data.get('user_id', 'N/A')
        username = user_data.get('username', 'N/A')
        period = user_data.get('period', '30 روز گذشته')
        
        report = f"""👤 گزارش فعالیت کاربر
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 کاربر: {username} (ID: {user_id})
📅 دوره: {period}
🕒 تاریخ گزارش: {TimeManager.to_shamsi(datetime.now())}

📊 آمار فعالیت:
• کل درخواست‌ها: {user_data.get('total_requests', 0):,}
• درخواست‌های موفق: {user_data.get('successful_requests', 0):,}
• نرخ موفقیت: {user_data.get('success_rate', 0):.1f}%
• میانگین روزانه: {user_data.get('daily_average', 0):.1f}

📈 استراتژی‌های استفاده شده:
"""
        
        strategies = user_data.get('strategies_used', [])
        for strategy_data in strategies:
            strategy = strategy_data.get('strategy', 'N/A')
            count = strategy_data.get('count', 0)
            report += f"• {strategy}: {count:,} بار\n"
        
        report += f"""
🪙 نمادهای تحلیل شده:
"""
        
        symbols = user_data.get('symbols_analyzed', [])
        for symbol_data in symbols[:10]:  # نمایش 10 نماد برتر
            symbol = symbol_data.get('symbol', 'N/A')
            count = symbol_data.get('count', 0)
            report += f"• {symbol}: {count:,} بار\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ الگوی استفاده:
• ساعت فعالیت بیشتر: {user_data.get('peak_hour', 'N/A')}
• روز فعالیت بیشتر: {user_data.get('peak_day', 'N/A')}
• آخرین فعالیت: {user_data.get('last_activity', 'N/A')}

🏢 تولید شده توسط: MrTrader Bot
"""
        return report
    
    @staticmethod
    def market_overview_report(market_data: Dict[str, Any]) -> str:
        """گزارش کلی بازار"""
        date = market_data.get('date', datetime.now())
        total_market_cap = market_data.get('total_market_cap', 0)
        btc_dominance = market_data.get('btc_dominance', 0)
        fear_greed_index = market_data.get('fear_greed_index', 50)
        
        report = f"""🌍 گزارش کلی بازار ارزهای دیجیتال
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 تاریخ: {TimeManager.to_shamsi(date)}

📊 آمار کلی بازار:
• کل ارزش بازار: ${total_market_cap:,.0f} تریلیون
• تسلط بیت‌کوین: {btc_dominance:.1f}%
• شاخص ترس و طمع: {fear_greed_index}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔝 برترین ارزها (بر اساس ارزش بازار):
"""
        
        top_coins = market_data.get('top_coins', [])
        for i, coin in enumerate(top_coins[:10], 1):
            name = coin.get('name', 'N/A')
            symbol = coin.get('symbol', 'N/A')
            price = coin.get('price', 0)
            change_24h = coin.get('change_24h', 0)
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            
            report += f"""{i:2d}. {name} ({symbol}):
     قیمت: ${price:,.2f}
     تغییر 24h: {change_emoji} {change_24h:+.2f}%

"""
        
        report += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 تحلیل روند:
{market_data.get('trend_analysis', 'تحلیل روند در دسترس نیست.')}

🔮 چشم‌انداز:
{market_data.get('market_outlook', 'چشم‌انداز بازار در دسترس نیست.')}

🏢 تولید شده توسط: MrTrader Bot
🕒 آخرین به‌روزرسانی: {TimeManager.to_shamsi(datetime.now())}
"""
        return report
    
    @staticmethod
    def performance_report(performance_data: Dict[str, Any]) -> str:
        """گزارش عملکرد سیستم"""
        period = performance_data.get('period', '30 روز گذشته')
        
        report = f"""⚡ گزارش عملکرد سیستم
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 دوره: {period}
🕒 تاریخ گزارش: {TimeManager.to_shamsi(datetime.now())}

📊 آمار کلی:
• کل درخواست‌ها: {performance_data.get('total_requests', 0):,}
• درخواست‌های موفق: {performance_data.get('successful_requests', 0):,}
• نرخ موفقیت: {performance_data.get('success_rate', 0):.2f}%
• میانگین زمان پاسخ: {performance_data.get('avg_response_time', 0):.2f} ثانیه

👥 آمار کاربران:
• کل کاربران: {performance_data.get('total_users', 0):,}
• کاربران فعال: {performance_data.get('active_users', 0):,}
• کاربران جدید: {performance_data.get('new_users', 0):,}

💰 آمار مالی:
• کل درآمد: ${performance_data.get('total_revenue', 0):,.2f}
• درآمد این ماه: ${performance_data.get('monthly_revenue', 0):,.2f}
• میانگین درآمد روزانه: ${performance_data.get('daily_avg_revenue', 0):,.2f}

📈 محبوب‌ترین استراتژی‌ها:
"""
        
        top_strategies = performance_data.get('top_strategies', [])
        for i, strategy_data in enumerate(top_strategies[:5], 1):
            strategy = strategy_data.get('name', 'N/A')
            usage = strategy_data.get('usage_count', 0)
            success_rate = strategy_data.get('success_rate', 0)
            report += f"{i}. {strategy}: {usage:,} استفاده ({success_rate:.1f}% موفقیت)\n"
        
        report += f"""
🔧 سلامت سیستم:
• آپتایم: {performance_data.get('uptime', '99.9%')}
• استفاده از CPU: {performance_data.get('cpu_usage', 'N/A')}
• استفاده از حافظه: {performance_data.get('memory_usage', 'N/A')}
• فضای دیسک: {performance_data.get('disk_usage', 'N/A')}

⚠️ خطاهای رایج:
"""
        
        common_errors = performance_data.get('common_errors', [])
        for error_data in common_errors[:5]:
            error_type = error_data.get('type', 'N/A')
            count = error_data.get('count', 0)
            report += f"• {error_type}: {count:,} مورد\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 روند رشد:
• رشد کاربران: {performance_data.get('user_growth', 0):+.1f}%
• رشد درآمد: {performance_data.get('revenue_growth', 0):+.1f}%
• رشد استفاده: {performance_data.get('usage_growth', 0):+.1f}%

🏢 تولید شده توسط: MrTrader Bot
"""
        return report

class AdminReports:
    """گزارش‌های مخصوص ادمین"""
    
    @staticmethod
    def admin_dashboard_report(admin_data: Dict[str, Any]) -> str:
        """گزارش داشبورد مدیریتی"""
        report = f"""🔧 داشبورد مدیریتی MrTrader Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 تاریخ: {TimeManager.to_shamsi(datetime.now())}
🕒 آخرین به‌روزرسانی: {admin_data.get('last_update', 'نامشخص')}

📊 آمار امروز:
• کاربران آنلاین: {admin_data.get('online_users', 0):,}
• درخواست‌های امروز: {admin_data.get('today_requests', 0):,}
• درآمد امروز: ${admin_data.get('today_revenue', 0):,.2f}
• خطاهای امروز: {admin_data.get('today_errors', 0):,}

🚨 هشدارها:
"""
        
        alerts = admin_data.get('alerts', [])
        if alerts:
            for alert in alerts:
                level = alert.get('level', 'info')
                message = alert.get('message', 'N/A')
                emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "ℹ️")
                report += f"{emoji} {message}\n"
        else:
            report += "✅ بدون هشدار\n"
        
        report += f"""
💾 وضعیت سیستم:
• سرور: {admin_data.get('server_status', 'نامشخص')}
• دیتابیس: {admin_data.get('database_status', 'نامشخص')}
• API خارجی: {admin_data.get('external_api_status', 'نامشخص')}
• آخرین بکاپ: {admin_data.get('last_backup', 'نامشخص')}

🔧 اقدامات اخیر:
"""
        
        recent_actions = admin_data.get('recent_actions', [])
        for action in recent_actions[:5]:
            timestamp = action.get('timestamp', 'نامشخص')
            description = action.get('description', 'N/A')
            admin_user = action.get('admin_user', 'سیستم')
            report += f"• {timestamp}: {description} (توسط {admin_user})\n"
        
        return report
    
    @staticmethod
    def financial_report(financial_data: Dict[str, Any]) -> str:
        """گزارش مالی"""
        period = financial_data.get('period', 'ماه جاری')
        
        report = f"""💰 گزارش مالی
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 دوره: {period}
🕒 تاریخ گزارش: {TimeManager.to_shamsi(datetime.now())}

💵 درآمد:
• کل درآمد: ${financial_data.get('total_revenue', 0):,.2f}
• درآمد از پکیج‌ها: ${financial_data.get('package_revenue', 0):,.2f}
• درآمد از ارتقاء: ${financial_data.get('upgrade_revenue', 0):,.2f}
• درآمد از رفرال: ${financial_data.get('referral_revenue', 0):,.2f}

📊 فروش پکیج‌ها:
"""
        
        package_sales = financial_data.get('package_sales', [])
        for package_data in package_sales:
            package_name = package_data.get('name', 'N/A')
            sales_count = package_data.get('sales_count', 0)
            revenue = package_data.get('revenue', 0)
            report += f"• {package_name}: {sales_count:,} فروش (${revenue:,.2f})\n"
        
        report += f"""
📈 روند فروش:
• رشد ماهانه: {financial_data.get('monthly_growth', 0):+.1f}%
• بهترین روز فروش: {financial_data.get('best_sales_day', 'نامشخص')}
• میانگین فروش روزانه: ${financial_data.get('daily_avg_sales', 0):,.2f}

💳 روش‌های پرداخت:
"""
        
        payment_methods = financial_data.get('payment_methods', [])
        for method_data in payment_methods:
            method = method_data.get('method', 'N/A')
            percentage = method_data.get('percentage', 0)
            report += f"• {method}: {percentage:.1f}%\n"
        
        return report

class ExportFormats:
    """فرمت‌های صادرات گزارش"""
    
    @staticmethod
    def to_csv_format(data: List[Dict[str, Any]], headers: List[str]) -> str:
        """تبدیل به فرمت CSV"""
        csv_content = ",".join(headers) + "\n"
        
        for row in data:
            csv_row = []
            for header in headers:
                value = str(row.get(header, ''))
                # Escape commas and quotes
                if ',' in value or '"' in value:
                    value = f'"{value.replace('"', '""')}"'
                csv_row.append(value)
            csv_content += ",".join(csv_row) + "\n"
        
        return csv_content
    
    @staticmethod
    def to_json_format(data: Dict[str, Any]) -> str:
        """تبدیل به فرمت JSON"""
        import json
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    @staticmethod
    def to_excel_summary(data: Dict[str, Any]) -> str:
        """خلاصه برای Excel"""
        return f"""خلاصه داده‌ها برای Excel:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 تعداد رکوردها: {len(data.get('records', []))}
📅 تاریخ تولید: {TimeManager.to_shamsi(datetime.now())}
📋 فیلدهای موجود: {', '.join(data.get('fields', []))}

💡 نکته: این فایل قابل باز کردن در Excel، Google Sheets و سایر نرم‌افزارهای صفحه‌گسترده می‌باشد.

🔗 برای دریافت فایل کامل، از گزینه "دانلود گزارش" استفاده کنید.
"""

class ReportUtils:
    """ابزارهای کمکی گزارش‌گیری"""
    
    @staticmethod
    def add_watermark(content: str, user_info: Dict[str, Any]) -> str:
        """اضافه کردن واترمارک"""
        watermark = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ این گزارش برای {user_info.get('username', 'کاربر')} تولید شده است
🆔 شناسه کاربر: {user_info.get('user_id', 'نامشخص')}
🕒 زمان تولید: {TimeManager.to_shamsi(datetime.now())}
🔐 این گزارش محرمانه و غیرقابل انتقال است
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return content + watermark
    
    @staticmethod
    def calculate_report_stats(report_data: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه آمار گزارش"""
        return {
            'total_words': len(str(report_data).split()),
            'total_characters': len(str(report_data)),
            'generation_time': datetime.now().isoformat(),
            'report_type': report_data.get('type', 'unknown'),
            'data_points': len(report_data.get('data', [])),
            'complexity_score': min(100, len(str(report_data)) / 100)
        }
