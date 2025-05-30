"""
قالب‌های کیبورد inline برای MrTrader Bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional
from models.package import PackageModel, DefaultPackages


class MainKeyboard:
    """کیبوردهای منوی اصلی"""
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """منوی اصلی"""
        keyboard = [
            [
                InlineKeyboardButton("📊 تحلیل سریع", callback_data="quick_analysis"),
                InlineKeyboardButton("📈 سیگنال‌ها", callback_data="show_signals")
            ],
            [
                InlineKeyboardButton("💼 پورتفولیو", callback_data="show_portfolio"),
                InlineKeyboardButton("💰 قیمت‌ها", callback_data="price_check")
            ],
            [
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="show_settings"),
                InlineKeyboardButton("📊 گزارش‌ها", callback_data="show_reports")
            ],
            [
                InlineKeyboardButton("🎁 رفرال", callback_data="show_referral"),
                InlineKeyboardButton("💎 ارتقاء پکیج", callback_data="show_packages")
            ],
            [
                InlineKeyboardButton("🆘 پشتیبانی", callback_data="contact_support"),
                InlineKeyboardButton("❓ راهنما", callback_data="show_help")
            ]
        ]
        
        # افزودن پنل ادمین
        if is_admin:
            keyboard.append([InlineKeyboardButton("🛠️ پنل ادمین", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def quick_menu() -> InlineKeyboardMarkup:
        """منوی سریع"""
        keyboard = [
            [
                InlineKeyboardButton("⚡ تحلیل فوری", callback_data="instant_analysis"),
                InlineKeyboardButton("📊 نمادهای محبوب", callback_data="popular_symbols")
            ],
            [
                InlineKeyboardButton("🔥 سیگنال‌های داغ", callback_data="hot_signals"),
                InlineKeyboardButton("📈 بازار کل", callback_data="market_overview")
            ],
            [
                InlineKeyboardButton("💰 قیمت‌ها", callback_data="price_check"),
                InlineKeyboardButton("🔔 هشدارها", callback_data="price_alerts")
            ],
            [
                InlineKeyboardButton("👤 پروفایل من", callback_data="my_profile")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """دکمه بازگشت به منوی اصلی"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
        ]])


class AnalysisKeyboard:
    """کیبوردهای تحلیل"""
    
    @staticmethod
    def symbol_selection() -> InlineKeyboardMarkup:
        """انتخاب نماد برای تحلیل"""
        keyboard = [
            [
                InlineKeyboardButton("BTC", callback_data="analyze_symbol:BTC"),
                InlineKeyboardButton("ETH", callback_data="analyze_symbol:ETH"),
                InlineKeyboardButton("BNB", callback_data="analyze_symbol:BNB")
            ],
            [
                InlineKeyboardButton("ADA", callback_data="analyze_symbol:ADA"),
                InlineKeyboardButton("XRP", callback_data="analyze_symbol:XRP"),
                InlineKeyboardButton("SOL", callback_data="analyze_symbol:SOL")
            ],
            [
                InlineKeyboardButton("DOT", callback_data="analyze_symbol:DOT"),
                InlineKeyboardButton("MATIC", callback_data="analyze_symbol:MATIC"),
                InlineKeyboardButton("LINK", callback_data="analyze_symbol:LINK")
            ],
            [
                InlineKeyboardButton("🔍 جستجوی نماد", callback_data="search_symbol"),
                InlineKeyboardButton("📊 همه نمادها", callback_data="all_symbols")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def timeframe_selection(symbol: str) -> InlineKeyboardMarkup:
        """انتخاب تایم فریم"""
        keyboard = [
            [
                InlineKeyboardButton("1M", callback_data=f"timeframe:{symbol}:1m"),
                InlineKeyboardButton("5M", callback_data=f"timeframe:{symbol}:5m"),
                InlineKeyboardButton("15M", callback_data=f"timeframe:{symbol}:15m")
            ],
            [
                InlineKeyboardButton("30M", callback_data=f"timeframe:{symbol}:30m"),
                InlineKeyboardButton("1H", callback_data=f"timeframe:{symbol}:1h"),
                InlineKeyboardButton("4H", callback_data=f"timeframe:{symbol}:4h")
            ],
            [
                InlineKeyboardButton("1D", callback_data=f"timeframe:{symbol}:1d"),
                InlineKeyboardButton("1W", callback_data=f"timeframe:{symbol}:1w")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="quick_analysis")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def strategy_selection(symbol: str, timeframe: str) -> InlineKeyboardMarkup:
        """انتخاب استراتژی"""
        keyboard = [
            [
                InlineKeyboardButton("📊 RSI", callback_data=f"strategy:{symbol}:{timeframe}:rsi"),
                InlineKeyboardButton("📈 MA", callback_data=f"strategy:{symbol}:{timeframe}:ma")
            ],
            [
                InlineKeyboardButton("🎯 MACD", callback_data=f"strategy:{symbol}:{timeframe}:macd"),
                InlineKeyboardButton("📉 Bollinger", callback_data=f"strategy:{symbol}:{timeframe}:bollinger")
            ],
            [
                InlineKeyboardButton("⚡ همه استراتژی‌ها", callback_data=f"strategy:{symbol}:{timeframe}:all")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"analyze_symbol:{symbol}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def analysis_actions(symbol: str) -> InlineKeyboardMarkup:
        """عملیات روی نتایج تحلیل"""
        keyboard = [
            [
                InlineKeyboardButton("📈 تحلیل تفصیلی", callback_data=f"detailed_analysis:{symbol}"),
                InlineKeyboardButton("🔔 تنظیم هشدار", callback_data=f"set_alert:{symbol}")
            ],
            [
                InlineKeyboardButton("📊 نمودار", callback_data=f"show_chart:{symbol}"),
                InlineKeyboardButton("➕ افزودن به لیست", callback_data=f"add_watchlist:{symbol}")
            ],
            [
                InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_symbol:{symbol}"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="quick_analysis")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


class PackageKeyboard:
    """کیبوردهای پکیج"""
    
    @staticmethod
    def packages_list() -> InlineKeyboardMarkup:
        """لیست پکیج‌ها"""
        packages = DefaultPackages.get_all_packages()
        keyboard = []
        
        for package in packages:
            if package.package_id == 'free':
                continue
            
            emoji = "🌟 " if package.is_popular else ""
            price_text = f"${package.price_monthly}/ماه" if package.price_monthly > 0 else "رایگان"
            
            button_text = f"{emoji}{package.name_persian} - {price_text}"
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"select_package:{package.package_id}"
            )])
        
        keyboard.extend([
            [InlineKeyboardButton("🎁 کد تخفیف", callback_data="enter_discount_code")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def package_durations(package_id: str, monthly_price: float, 
                         quarterly_price: float = 0, yearly_price: float = 0) -> InlineKeyboardMarkup:
        """انتخاب مدت پکیج"""
        keyboard = [
            [InlineKeyboardButton(f"1 ماه - ${monthly_price}", 
                               callback_data=f"buy_package:{package_id}:1")]
        ]
        
        if quarterly_price > 0:
            monthly_equivalent = quarterly_price / 3
            savings = monthly_price - monthly_equivalent
            keyboard.append([
                InlineKeyboardButton(f"3 ماه - ${quarterly_price} (صرفه‌جویی ${savings:.2f})", 
                                   callback_data=f"buy_package:{package_id}:3")
            ])
        
        if yearly_price > 0:
            monthly_equivalent = yearly_price / 12
            savings = monthly_price - monthly_equivalent
            keyboard.append([
                InlineKeyboardButton(f"12 ماه - ${yearly_price} (صرفه‌جویی ${savings:.2f})", 
                                   callback_data=f"buy_package:{package_id}:12")
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="show_packages")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        """روش‌های پرداخت"""
        keyboard = [
            [
                InlineKeyboardButton("💳 کارت اعتباری", callback_data="payment_method:credit_card"),
                InlineKeyboardButton("🏦 انتقال بانکی", callback_data="payment_method:bank_transfer")
            ],
            [
                InlineKeyboardButton("₿ بیت‌کوین", callback_data="payment_method:bitcoin"),
                InlineKeyboardButton("💰 تتر (USDT)", callback_data="payment_method:tether")
            ],
            [
                InlineKeyboardButton("💎 اتریوم", callback_data="payment_method:ethereum"),
                InlineKeyboardButton("🔄 Perfect Money", callback_data="payment_method:perfect_money")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="show_packages")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def payment_confirmation(transaction_id: str) -> InlineKeyboardMarkup:
        """تأیید پرداخت"""
        keyboard = [
            [
                InlineKeyboardButton("✅ پرداخت کردم", 
                                   callback_data=f"payment_done:{transaction_id}"),
                InlineKeyboardButton("❌ لغو پرداخت", 
                                   callback_data=f"payment_cancel:{transaction_id}")
            ],
            [
                InlineKeyboardButton("🔄 روش پرداخت دیگر", callback_data="show_payment_methods")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


class SettingsKeyboard:
    """کیبوردهای تنظیمات"""
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """منوی تنظیمات"""
        keyboard = [
            [
                InlineKeyboardButton("🔔 اعلان‌ها", callback_data="notification_settings"),
                InlineKeyboardButton("📊 تحلیل", callback_data="analysis_settings")
            ],
            [
                InlineKeyboardButton("👤 حساب کاربری", callback_data="account_settings"),
                InlineKeyboardButton("🌐 زبان", callback_data="language_settings")
            ],
            [
                InlineKeyboardButton("🔒 امنیت", callback_data="security_settings"),
                InlineKeyboardButton("💬 پشتیبانی", callback_data="support_settings")
            ],
            [
                InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def notification_settings(current_settings: Dict[str, bool]) -> InlineKeyboardMarkup:
        """تنظیمات اعلان"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"📊 سیگنال‌ها {'✅' if current_settings.get('signals', True) else '❌'}", 
                    callback_data="toggle_notification:signals"
                ),
                InlineKeyboardButton(
                    f"💰 قیمت‌ها {'✅' if current_settings.get('prices', True) else '❌'}", 
                    callback_data="toggle_notification:prices"
                )
            ],
            [
                InlineKeyboardButton(
                    f"📰 اخبار {'✅' if current_settings.get('news', True) else '❌'}", 
                    callback_data="toggle_notification:news"
                ),
                InlineKeyboardButton(
                    f"⚙️ سیستم {'✅' if current_settings.get('system', True) else '❌'}", 
                    callback_data="toggle_notification:system"
                )
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="show_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def analysis_settings(current_risk: str, current_strategies: List[str]) -> InlineKeyboardMarkup:
        """تنظیمات تحلیل"""
        risk_levels = {"low": "کم", "medium": "متوسط", "high": "زیاد"}
        
        keyboard = [
            [InlineKeyboardButton("🎯 انتخاب ریسک", callback_data="select_risk_level")],
            [InlineKeyboardButton("📊 انتخاب استراتژی‌ها", callback_data="select_strategies")],
            [InlineKeyboardButton(f"⚠️ ریسک فعلی: {risk_levels.get(current_risk, 'متوسط')}", 
                               callback_data="show_risk_info")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="show_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)


class AdminKeyboard:
    """کیبوردهای ادمین"""
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """پنل ادمین اصلی"""
        keyboard = [
            [
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("💰 مدیریت پرداخت", callback_data="admin_payments"),
                InlineKeyboardButton("🎁 مدیریت رفرال", callback_data="admin_referrals")
            ],
            [
                InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
                InlineKeyboardButton("📋 گزارش‌ها", callback_data="admin_reports")
            ],
            [
                InlineKeyboardButton("🔒 امنیت", callback_data="admin_security"),
                InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup")
            ],
            [
                InlineKeyboardButton("⚙️ تنظیمات سیستم", callback_data="admin_settings"),
                InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_refresh")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_management() -> InlineKeyboardMarkup:
        """مدیریت کاربران"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
                InlineKeyboardButton("📋 لیست کاربران", callback_data="admin_list_users")
            ],
            [
                InlineKeyboardButton("🚫 کاربران مسدود", callback_data="admin_blocked_users"),
                InlineKeyboardButton("⭐ کاربران VIP", callback_data="admin_vip_users")
            ],
            [
                InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_user_stats"),
                InlineKeyboardButton("🆕 کاربران جدید", callback_data="admin_new_users")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_actions(user_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
        """عملیات روی کاربر"""
        keyboard = [
            [
                InlineKeyboardButton("🚫 مسدود کردن" if not is_blocked else "✅ رفع مسدودی", 
                                   callback_data=f"admin_toggle_block:{user_id}"),
                InlineKeyboardButton("⭐ تغییر پکیج", callback_data=f"admin_change_package:{user_id}")
            ],
            [
                InlineKeyboardButton("💰 اضافه کردن امتیاز", callback_data=f"admin_add_points:{user_id}"),
                InlineKeyboardButton("📊 آمار تفصیلی", callback_data=f"admin_user_details:{user_id}")
            ],
            [
                InlineKeyboardButton("💬 ارسال پیام", callback_data=f"admin_message_user:{user_id}"),
                InlineKeyboardButton("🗑️ حذف کاربر", callback_data=f"admin_delete_user:{user_id}")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_reports() -> InlineKeyboardMarkup:
        """گزارش‌های ادمین"""
        keyboard = [
            [
                InlineKeyboardButton("📊 گزارش روزانه", callback_data="admin_daily_report"),
                InlineKeyboardButton("📈 گزارش هفتگی", callback_data="admin_weekly_report")
            ],
            [
                InlineKeyboardButton("💰 گزارش مالی", callback_data="admin_financial_report"),
                InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_detailed_user_stats")
            ],
            [
                InlineKeyboardButton("📊 آمار سیگنال‌ها", callback_data="admin_signal_stats"),
                InlineKeyboardButton("🎁 آمار رفرال", callback_data="admin_referral_stats")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


class NavigationKeyboard:
    """کیبوردهای ناوبری"""
    
    @staticmethod
    def pagination(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
        """صفحه‌بندی"""
        keyboard = []
        
        if total_pages > 1:
            nav_buttons = []
            
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}:{current_page-1}"))
            
            nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="current_page"))
            
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}:{current_page+1}"))
            
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_cancel(confirm_callback: str, cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
        """تأیید/لغو"""
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data=confirm_callback),
                InlineKeyboardButton("❌ لغو", callback_data=cancel_callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def yes_no(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
        """بله/خیر"""
        keyboard = [
            [
                InlineKeyboardButton("✅ بله", callback_data=yes_callback),
                InlineKeyboardButton("❌ خیر", callback_data=no_callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
        """دکمه بازگشت"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)
        ]])
    
    @staticmethod
    def close_button() -> InlineKeyboardMarkup:
        """دکمه بستن"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ بستن", callback_data="close_message")
        ]])


# Export
__all__ = [
    'MainKeyboard',
    'AnalysisKeyboard',
    'PackageKeyboard', 
    'SettingsKeyboard',
    'AdminKeyboard',
    'NavigationKeyboard'
]