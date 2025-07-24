"""
قالب‌های کیبورد - مدیریت کیبوردهای inline
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional, Union

class KeyboardTemplates:
    """کلاس قالب‌های کیبورد"""
    
    @staticmethod
    def main_menu(user_package: str = "free", is_admin: bool = False) -> InlineKeyboardMarkup:
        """کیبورد منوی اصلی"""
        keyboard = [
            [
                InlineKeyboardButton("📊 استراتژی‌ها", callback_data="menu_strategy"),
                InlineKeyboardButton("💰 قیمت لایو", callback_data="menu_live_prices")
            ],
            [
                InlineKeyboardButton("💎 پکیج‌ها", callback_data="menu_packages"),
                InlineKeyboardButton("👤 پروفایل", callback_data="user_profile")
            ],
            [
                InlineKeyboardButton("📚 راهنما", callback_data="menu_help"),
                InlineKeyboardButton("🎧 پشتیبانی", callback_data="support_contact")
            ]
        ]
        
        # اضافه کردن دکمه ادمین
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("🔧 پنل مدیریت", callback_data="admin_panel")
            ])
        
        # اضافه کردن دکمه رفرال برای کاربران VIP
        if user_package in ["vip", "ghost"]:
            keyboard.append([
                InlineKeyboardButton("🎁 دعوت دوستان", callback_data="referral_system")
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def strategy_menu(user_package: str = "free") -> InlineKeyboardMarkup:
        """کیبورد منوی استراتژی‌ها - سازمان‌دهی کامل 35 استراتژی"""
        keyboard = []
        
        # استراتژی‌های دمو برای کاربران رایگان
        if user_package == "free":
            keyboard.extend([
                [InlineKeyboardButton("🆓 === استراتژی‌های دمو ===", callback_data="info_demo")],
                [
                    InlineKeyboardButton("🆓 دمو پرایس اکشن", callback_data="strategy_demo_price_action"),
                    InlineKeyboardButton("🆓 دمو RSI", callback_data="strategy_demo_rsi")
                ]
            ])
        
        # استراتژی‌های BASIC (9 استراتژی - برای پکیج basic و بالاتر)
        if user_package in ["basic", "premium", "vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("🥉 === پکیج بیسیک (9 استراتژی) ===", callback_data="info_basic")],
                [
                    InlineKeyboardButton("📊 CCI Analysis", callback_data="strategy_cci_analysis"),
                    InlineKeyboardButton("📈 EMA Analysis", callback_data="strategy_ema_analysis")
                ],
                [
                    InlineKeyboardButton("☁️ Ichimoku", callback_data="strategy_ichimoku"),
                    InlineKeyboardButton("📉 Ichimoku Low", callback_data="strategy_ichimoku_low_signal")
                ],
                [
                    InlineKeyboardButton("⚡ MACD", callback_data="strategy_macd"),
                    InlineKeyboardButton("📊 Price Action TA", callback_data="strategy_price_action_pandas_ta")
                ],
                [
                    InlineKeyboardButton("💰 Live Binance", callback_data="strategy_project_price_live_binance"),
                    InlineKeyboardButton("📈 RSI", callback_data="strategy_rsi")
                ],
                [
                    InlineKeyboardButton("📊 Williams R", callback_data="strategy_williams_r_analysis")
                ]
            ])
        
        # استراتژی‌های PREMIUM (17 استراتژی اضافی - برای پکیج premium و بالاتر)
        if user_package in ["premium", "vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("🥈 === پکیج پریمیوم (+17 استراتژی) ===", callback_data="info_premium")],
                
                # الگوهای کندلی و پرایس اکشن
                [
                    InlineKeyboardButton("🕯️ Candlestick", callback_data="strategy_a_candlestick"),
                    InlineKeyboardButton("🕯️ Heikin Ashi", callback_data="strategy_heikin_ashi")
                ],
                [
                    InlineKeyboardButton("📈 Price Action Hi", callback_data="strategy_price_action_hi")
                ],
                
                # اندیکاتورهای تکنیکال
                [
                    InlineKeyboardButton("📊 Bollinger Bands", callback_data="strategy_bollinger_bands"),
                    InlineKeyboardButton("📊 Stochastic", callback_data="strategy_stochastic")
                ],
                [
                    InlineKeyboardButton("📊 MACD Divergence", callback_data="strategy_macd_divergence")
                ],
                
                # تحلیل روند
                [
                    InlineKeyboardButton("📍 Pivot Points", callback_data="strategy_b_pivot"),
                    InlineKeyboardButton("📈 Trend Lines", callback_data="strategy_c_trend_lines")
                ],
                [
                    InlineKeyboardButton("☁️ Ichimoku Hi", callback_data="strategy_ichimoku_hi_signal"),
                    InlineKeyboardButton("🌊 Fibonacci", callback_data="strategy_fibonacci_strategy")
                ],
                
                # الگوهای قیمتی
                [
                    InlineKeyboardButton("🔺 Double Top", callback_data="strategy_double_top_pattern"),
                    InlineKeyboardButton("🔺 Triangle", callback_data="strategy_triangle_pattern")
                ],
                [
                    InlineKeyboardButton("📐 Wedge", callback_data="strategy_wedge_pattern"),
                    InlineKeyboardButton("🏁 Flag Pattern", callback_data="strategy_flag_pattern")
                ],
                [
                    InlineKeyboardButton("☕ Cup & Handle", callback_data="strategy_cup_handle"),
                    InlineKeyboardButton("👤 Head & Shoulders", callback_data="strategy_head_shoulders_analysis")
                ],
                
                # سیستم‌های پیشرفته
                [
                    InlineKeyboardButton("⚡ Momentum", callback_data="strategy_momentum"),
                    InlineKeyboardButton("🎯 Martingale Low", callback_data="strategy_martingale_low")
                ]
            ])
        
        # استراتژی‌های VIP (9 استراتژی اضافی - برای پکیج vip و ghost)
        if user_package in ["vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("👑 === پکیج وی‌آی‌پی (+9 استراتژی) ===", callback_data="info_vip")],
                
                # اندیکاتورهای پیشرفته
                [
                    InlineKeyboardButton("📊 ATR", callback_data="strategy_atr"),
                    InlineKeyboardButton("📊 SMA Advanced", callback_data="strategy_sma")
                ],
                
                # تحلیل حجم
                [
                    InlineKeyboardButton("📊 Volume Profile", callback_data="strategy_volume_profile"),
                    InlineKeyboardButton("📊 VWAP", callback_data="strategy_vwap")
                ],
                
                # الگوهای نادر
                [
                    InlineKeyboardButton("💎 Diamond Pattern", callback_data="strategy_diamond_pattern")
                ],
                
                # سیستم‌های تخصصی
                [
                    InlineKeyboardButton("📈 CRT Analysis", callback_data="strategy_crt"),
                    InlineKeyboardButton("📊 P3 Analysis", callback_data="strategy_p3")
                ],
                [
                    InlineKeyboardButton("📈 RTM Analysis", callback_data="strategy_rtm"),
                    InlineKeyboardButton("🔄 Multi Resistance", callback_data="strategy_multi_level_resistance")
                ]
            ])
        
        # دکمه‌های عمومی
        keyboard.extend([
            [InlineKeyboardButton("💎 ارتقا پکیج", callback_data="menu_packages")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def symbol_selection(strategy: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب نماد ارز - بهبود یافته"""
        keyboard = [
            # ارزهای اصلی
            [
                InlineKeyboardButton("₿ BTC", callback_data=f"symbol_{strategy}|BTC"),
                InlineKeyboardButton("♦️ ETH", callback_data=f"symbol_{strategy}|ETH"),
                InlineKeyboardButton("🔶 BNB", callback_data=f"symbol_{strategy}|BNB")
            ],
            
            # ارزهای محبوب
            [
                InlineKeyboardButton("🔷 ADA", callback_data=f"symbol_{strategy}|ADA"),
                InlineKeyboardButton("☀️ SOL", callback_data=f"symbol_{strategy}|SOL"),
                InlineKeyboardButton("💧 XRP", callback_data=f"symbol_{strategy}|XRP")
            ],
            
            # ارزهای مم و محبوب
            [
                InlineKeyboardButton("🐕 DOGE", callback_data=f"symbol_{strategy}|DOGE"),
                InlineKeyboardButton("🔥 SHIB", callback_data=f"symbol_{strategy}|SHIB"),
                InlineKeyboardButton("⚪ DOT", callback_data=f"symbol_{strategy}|DOT")
            ],
            
            # DeFi و Web3
            [
                InlineKeyboardButton("🔗 LINK", callback_data=f"symbol_{strategy}|LINK"),
                InlineKeyboardButton("🔄 UNI", callback_data=f"symbol_{strategy}|UNI"),
                InlineKeyboardButton("🚀 AVAX", callback_data=f"symbol_{strategy}|AVAX")
            ],
            
            # Layer 1 و 2
            [
                InlineKeyboardButton("🔷 MATIC", callback_data=f"symbol_{strategy}|MATIC"),
                InlineKeyboardButton("🌙 LUNA", callback_data=f"symbol_{strategy}|LUNA"),
                InlineKeyboardButton("⚫ ATOM", callback_data=f"symbol_{strategy}|ATOM")
            ],
            
            # سایر ارزهای محبوب
            [
                InlineKeyboardButton("🔴 ALGO", callback_data=f"symbol_{strategy}|ALGO"),
                InlineKeyboardButton("🟦 FTM", callback_data=f"symbol_{strategy}|FTM"),
                InlineKeyboardButton("🔵 NEAR", callback_data=f"symbol_{strategy}|NEAR")
            ],
            
            # مجموعه دوم
            [
                InlineKeyboardButton("💎 ICP", callback_data=f"symbol_{strategy}|ICP"),
                InlineKeyboardButton("🟢 VET", callback_data=f"symbol_{strategy}|VET"),
                InlineKeyboardButton("🎭 THETA", callback_data=f"symbol_{strategy}|THETA")
            ],
            
            # کیبورد ورود دستی و بازگشت
            [InlineKeyboardButton("🔤 ورود دستی نماد", callback_data=f"manual_symbol_{strategy}")],
            [InlineKeyboardButton("⬅️ بازگشت به استراتژی‌ها", callback_data="menu_strategy")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def currency_selection(strategy: str, symbol: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب ارز مرجع"""
        keyboard = [
            # ارزهای اصلی
            [
                InlineKeyboardButton("💵 USDT", callback_data=f"currency_{strategy}|{symbol}|USDT"),
                InlineKeyboardButton("💵 BUSD", callback_data=f"currency_{strategy}|{symbol}|BUSD")
            ],
            [
                InlineKeyboardButton("💰 USDC", callback_data=f"currency_{strategy}|{symbol}|USDC")
            ],
            
            # ارزهای کریپتو
            [
                InlineKeyboardButton("₿ BTC", callback_data=f"currency_{strategy}|{symbol}|BTC"),
                InlineKeyboardButton("♦️ ETH", callback_data=f"currency_{strategy}|{symbol}|ETH")
            ],
            [
                InlineKeyboardButton("🔶 BNB", callback_data=f"currency_{strategy}|{symbol}|BNB")
            ],
            
            # ورود دستی و بازگشت
            [InlineKeyboardButton("🔤 ورود دستی ارز مرجع", callback_data=f"manual_currency_{strategy}|{symbol}")],
            [InlineKeyboardButton("⬅️ بازگشت به انتخاب نماد", callback_data=f"strategy_{strategy}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def timeframe_selection(strategy: str, symbol: str, currency: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب تایم‌فریم - کامل و سازمان‌دهی شده"""
        keyboard = [
            # تایم‌فریم‌های کوتاه‌مدت
            [
                InlineKeyboardButton("1️⃣ دقیقه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|1m"),
                InlineKeyboardButton("3️⃣ دقیقه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|3m"),
                InlineKeyboardButton("5️⃣ دقیقه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|5m")
            ],
            [
                InlineKeyboardButton("1️⃣5️⃣ دقیقه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|15m"),
                InlineKeyboardButton("3️⃣0️⃣ دقیقه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|30m")
            ],
            
            # تایم‌فریم‌های ساعتی
            [
                InlineKeyboardButton("1️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|1h"),
                InlineKeyboardButton("2️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|2h"),
                InlineKeyboardButton("4️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|4h")
            ],
            [
                InlineKeyboardButton("6️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|6h"),
                InlineKeyboardButton("8️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|8h"),
                InlineKeyboardButton("1️⃣2️⃣ ساعت", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|12h")
            ],
            
            # تایم‌فریم‌های بلندمدت
            [
                InlineKeyboardButton("1️⃣ روز", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|1d"),
                InlineKeyboardButton("3️⃣ روز", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|3d"),
                InlineKeyboardButton("1️⃣ هفته", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|1w")
            ],
            [
                InlineKeyboardButton("1️⃣ ماه", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|1M")
            ],
            
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به انتخاب ارز مرجع", callback_data=f"currency_{strategy}|{symbol}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def analysis_result_actions(strategy: str, symbol: str, currency: str, timeframe: str) -> InlineKeyboardMarkup:
        """کیبورد اقدامات پس از تحلیل"""
        keyboard = [
            # اقدامات اصلی
            [InlineKeyboardButton("🔄 به‌روزرسانی تحلیل", callback_data=f"timeframe_{strategy}|{symbol}|{currency}|{timeframe}")],
            
            # تغییرات
            [
                InlineKeyboardButton("⏱ تغییر تایم‌فریم", callback_data=f"currency_{strategy}|{symbol}|{currency}"),
                InlineKeyboardButton("💱 تغییر ارز مرجع", callback_data=f"symbol_{strategy}|{symbol}")
            ],
            [
                InlineKeyboardButton("🪙 تغییر نماد", callback_data=f"strategy_{strategy}"),
                InlineKeyboardButton("📊 استراتژی دیگر", callback_data="menu_strategy")
            ],
            
            # ابزارهای اضافی
            [
                InlineKeyboardButton("💾 ذخیره گزارش", callback_data=f"save_report_{strategy}|{symbol}|{currency}|{timeframe}"),
                InlineKeyboardButton("📤 اشتراک‌گذاری", callback_data=f"share_analysis_{strategy}|{symbol}|{currency}|{timeframe}")
            ],
            [
                InlineKeyboardButton("🔔 تنظیم هشدار", callback_data=f"set_alert_{strategy}|{symbol}|{currency}|{timeframe}"),
                InlineKeyboardButton("📈 نمودار تکمیلی", callback_data=f"show_chart_{strategy}|{symbol}|{currency}|{timeframe}")
            ],
            
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به استراتژی‌ها", callback_data="menu_strategy")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def packages_menu() -> InlineKeyboardMarkup:
        """کیبورد منوی پکیج‌ها"""
        keyboard = [
            # پکیج‌های اصلی
            [
                InlineKeyboardButton("🥉 BASIC (9 استراتژی)", callback_data="pkg_select_basic"),
                InlineKeyboardButton("🥈 PREMIUM (26 استراتژی)", callback_data="pkg_select_premium")
            ],
            [
                InlineKeyboardButton("👑 VIP (35 استراتژی)", callback_data="pkg_select_vip"),
                InlineKeyboardButton("👻 GHOST (ویژه)", callback_data="pkg_select_ghost")
            ],
            
            # ابزارها و اطلاعات
            [
                InlineKeyboardButton("📊 مقایسه پکیج‌ها", callback_data="packages_compare"),
                InlineKeyboardButton("💰 تاریخچه خریدها", callback_data="payment_history")
            ],
            [
                InlineKeyboardButton("🎁 کد تخفیف", callback_data="discount_code"),
                InlineKeyboardButton("❓ سوالات متداول", callback_data="packages_faq")
            ],
            [
                InlineKeyboardButton("📞 مشاوره خرید", callback_data="purchase_consultation"),
                InlineKeyboardButton("🔄 تمدید پکیج", callback_data="renew_package")
            ],
            
            # بازگشت
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def package_details(package_name: str) -> InlineKeyboardMarkup:
        """کیبورد جزئیات پکیج"""
        keyboard = [
            # خرید با مدت‌های مختلف
            [
                InlineKeyboardButton("💳 خرید 1 ماهه", callback_data=f"buy_{package_name}_monthly"),
                InlineKeyboardButton("💳 خرید 3 ماهه (-10%)", callback_data=f"buy_{package_name}_quarterly")
            ],
            [
                InlineKeyboardButton("💳 خرید 6 ماهه (-15%)", callback_data=f"buy_{package_name}_semi_annual"),
                InlineKeyboardButton("💳 خرید سالانه (-25%)", callback_data=f"buy_{package_name}_yearly")
            ],
            
            # خدمات ویژه
            [
                InlineKeyboardButton("🎁 خرید هدیه", callback_data=f"gift_{package_name}"),
                InlineKeyboardButton("👥 خرید گروهی", callback_data=f"bulk_{package_name}")
            ],
            
            # اطلاعات
            [
                InlineKeyboardButton("📊 مقایسه با سایر پکیج‌ها", callback_data="packages_compare"),
                InlineKeyboardButton("🎯 مشاهده دمو", callback_data=f"demo_{package_name}")
            ],
            [
                InlineKeyboardButton("❓ سوالات متداول", callback_data=f"faq_{package_name}"),
                InlineKeyboardButton("📞 مشاوره", callback_data="purchase_consultation")
            ],
            
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به پکیج‌ها", callback_data="menu_packages")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def payment_methods(package_name: str, duration: str) -> InlineKeyboardMarkup:
        """کیبورد روش‌های پرداخت"""
        keyboard = [
            # روش‌های پرداخت ایرانی
            [
                InlineKeyboardButton("💳 کارت بانکی", callback_data=f"pay_{package_name}_{duration}_card"),
                InlineKeyboardButton("🏪 درگاه بانک", callback_data=f"pay_{package_name}_{duration}_bank")
            ],
            [
                InlineKeyboardButton("📱 زرین‌پال", callback_data=f"pay_{package_name}_{duration}_zarinpal"),
                InlineKeyboardButton("🔷 آیدی‌پی", callback_data=f"pay_{package_name}_{duration}_idpay")
            ],
            
            # روش‌های پرداخت کریپتو
            [
                InlineKeyboardButton("₿ بیت‌کوین", callback_data=f"pay_{package_name}_{duration}_btc"),
                InlineKeyboardButton("💰 تتر (USDT)", callback_data=f"pay_{package_name}_{duration}_usdt")
            ],
            [
                InlineKeyboardButton("♦️ اتریوم", callback_data=f"pay_{package_name}_{duration}_eth"),
                InlineKeyboardButton("🔶 BNB", callback_data=f"pay_{package_name}_{duration}_bnb")
            ],
            
            # گزینه‌های ویژه
            [
                InlineKeyboardButton("🎁 استفاده از کد تخفیف", callback_data=f"discount_{package_name}_{duration}"),
                InlineKeyboardButton("⭐ استفاده از امتیاز", callback_data=f"points_{package_name}_{duration}")
            ],
            [
                InlineKeyboardButton("🔄 پرداخت اقساطی", callback_data=f"installment_{package_name}_{duration}"),
                InlineKeyboardButton("💸 کیف پول ربات", callback_data=f"wallet_{package_name}_{duration}")
            ],
            
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به پکیج", callback_data=f"pkg_select_{package_name}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def live_prices_menu() -> InlineKeyboardMarkup:
        """کیبورد منوی قیمت‌های زنده"""
        keyboard = [
            # صرافی‌های بین‌المللی
            [
                InlineKeyboardButton("🟡 بایننس", callback_data="live_binance"),
                InlineKeyboardButton("🔵 کوین‌بیس", callback_data="live_coinbase")
            ],
            [
                InlineKeyboardButton("🟢 کوکوین", callback_data="live_kucoin"),
                InlineKeyboardButton("🟠 Bybit", callback_data="live_bybit")
            ],
            
            # صرافی‌های ایرانی
            [
                InlineKeyboardButton("🔴 نوبیتکس", callback_data="live_nobitex"),
                InlineKeyboardButton("🟣 تبدیل", callback_data="live_tabdeal")
            ],
            [
                InlineKeyboardButton("🔵 والکس", callback_data="live_wallex"),
                InlineKeyboardButton("🟢 آسان‌کوین", callback_data="live_asancoin")
            ],
            
            # ابزارهای تحلیلی
            [
                InlineKeyboardButton("📊 مقایسه قیمت‌ها", callback_data="price_compare"),
                InlineKeyboardButton("⚪ همه صرافی‌ها", callback_data="live_all_exchanges")
            ],
            [
                InlineKeyboardButton("🔔 تنظیم هشدار قیمت", callback_data="set_price_alert"),
                InlineKeyboardButton("📈 نمودارهای زنده", callback_data="live_charts")
            ],
            [
                InlineKeyboardButton("📊 تحلیل تکنیکال", callback_data="technical_analysis"),
                InlineKeyboardButton("📰 اخبار بازار", callback_data="market_news")
            ],
            
            # بازگشت
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """کیبورد پنل مدیریت"""
        keyboard = [
            # مدیریت کاربران
            [
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
                InlineKeyboardButton("📊 گزارش‌ها", callback_data="admin_reports")
            ],
            [
                InlineKeyboardButton("💰 مدیریت پکیج‌ها", callback_data="admin_packages"),
                InlineKeyboardButton("💳 مدیریت پرداخت‌ها", callback_data="admin_payments")
            ],
            
            # مدیریت محتوا
            [
                InlineKeyboardButton("📊 مدیریت استراتژی‌ها", callback_data="admin_strategies"),
                InlineKeyboardButton("🔒 امنیت و دسترسی", callback_data="admin_security")
            ],
            [
                InlineKeyboardButton("📤 ارسال پیام گروهی", callback_data="admin_broadcast"),
                InlineKeyboardButton("📢 مدیریت اطلاعیه‌ها", callback_data="admin_announcements")
            ],
            
            # مدیریت سیستم
            [
                InlineKeyboardButton("🔧 تنظیمات سیستم", callback_data="admin_settings"),
                InlineKeyboardButton("⚡ مانیتورینگ عملکرد", callback_data="admin_performance")
            ],
            [
                InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup"),
                InlineKeyboardButton("📋 مشاهده لاگ‌ها", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton("🔄 بروزرسانی سیستم", callback_data="admin_update"),
                InlineKeyboardButton("🛠️ ابزارهای توسعه", callback_data="admin_dev_tools")
            ],
            
            # بازگشت
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_profile_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """کیبورد منوی پروفایل کاربر"""
        keyboard = [
            # اطلاعات کاربری
            [
                InlineKeyboardButton("📊 آمار استفاده", callback_data="user_stats"),
                InlineKeyboardButton("📋 تاریخچه تحلیل‌ها", callback_data="user_history")
            ],
            [
                InlineKeyboardButton("📄 گزارش‌های ذخیره شده", callback_data="user_reports"),
                InlineKeyboardButton("💰 تاریخچه تراکنش‌ها", callback_data="payment_history")
            ],
            
            # تنظیمات
            [
                InlineKeyboardButton("⚙️ تنظیمات کلی", callback_data="user_settings"),
                InlineKeyboardButton("🔔 تنظیمات اطلاع‌رسانی", callback_data="notification_settings")
            ],
            [
                InlineKeyboardButton("🔒 حریم خصوصی", callback_data="privacy_settings"),
                InlineKeyboardButton("🔐 امنیت حساب", callback_data="security_settings")
            ],
            
            # ابزارها
            [
                InlineKeyboardButton("🎁 سیستم رفرال", callback_data="referral_system"),
                InlineKeyboardButton("⭐ مدیریت امتیازها", callback_data="points_management")
            ],
            [
                InlineKeyboardButton("📊 داشبورد شخصی", callback_data="personal_dashboard"),
                InlineKeyboardButton("💾 صادرات داده‌ها", callback_data="export_data")
            ]
        ]
        
        # اضافه کردن دسترسی ادمین
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("🔧 پنل ادمین", callback_data="admin_panel"),
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")
            ])
        
        # بازگشت
        keyboard.append([
            InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def help_menu() -> InlineKeyboardMarkup:
        """کیبورد منوی راهنما"""
        keyboard = [
            # راهنماهای اصلی
            [
                InlineKeyboardButton("🚀 شروع کار", callback_data="help_getting_started"),
                InlineKeyboardButton("📊 نحوه استفاده", callback_data="help_how_to_use")
            ],
            [
                InlineKeyboardButton("📈 راهنمای استراتژی‌ها", callback_data="help_strategies"),
                InlineKeyboardButton("💰 راهنمای پکیج‌ها", callback_data="help_packages")
            ],
            
            # اطلاعات تکمیلی
            [
                InlineKeyboardButton("💡 سوالات متداول", callback_data="help_faq"),
                InlineKeyboardButton("📚 راهنمای کامل", callback_data="help_manual")
            ],
            [
                InlineKeyboardButton("🎥 ویدیوهای آموزشی", callback_data="help_videos"),
                InlineKeyboardButton("📖 مقالات آموزشی", callback_data="help_articles")
            ],
            
            # مشکلات و پشتیبانی
            [
                InlineKeyboardButton("🔧 عیب‌یابی", callback_data="help_troubleshooting"),
                InlineKeyboardButton("🆘 حل مشکلات رایج", callback_data="help_common_issues")
            ],
            [
                InlineKeyboardButton("🎧 تماس با پشتیبانی", callback_data="support_contact"),
                InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")
            ],
            
            # اطلاعات سیستم
            [
                InlineKeyboardButton("📋 شرایط استفاده", callback_data="terms_of_service"),
                InlineKeyboardButton("🔒 حریم خصوصی", callback_data="privacy_policy")
            ],
            [
                InlineKeyboardButton("📄 درباره ربات", callback_data="about_bot"),
                InlineKeyboardButton("🔄 آپدیت‌ها", callback_data="updates_changelog")
            ],
            
            # بازگشت
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    # =====================================================
    # کیبوردهای کمکی و ابزاری
    # =====================================================
    
    @staticmethod
    def confirm_action(action_data: str, confirm_text: str = "تأیید", cancel_text: str = "لغو") -> InlineKeyboardMarkup:
        """کیبورد تأیید عملیات"""
        keyboard = [
            [
                InlineKeyboardButton(f"✅ {confirm_text}", callback_data=f"confirm_{action_data}"),
                InlineKeyboardButton(f"❌ {cancel_text}", callback_data=f"cancel_{action_data}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu(menu_callback: str = "main_menu", text: str = "🏠 منوی اصلی") -> InlineKeyboardMarkup:
        """کیبورد بازگشت به منو"""
        keyboard = [
            [InlineKeyboardButton(text, callback_data=menu_callback)]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pagination(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
        """کیبورد صفحه‌بندی"""
        keyboard = []
        
        if total_pages > 1:
            nav_buttons = []
            
            # دکمه صفحه قبل
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"{callback_prefix}_page_{current_page - 1}"))
            
            # نمایش شماره صفحه
            nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
            
            # دکمه صفحه بعد
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"{callback_prefix}_page_{current_page + 1}"))
            
            keyboard.append(nav_buttons)
            
            # اگر صفحات زیاد باشد، دکمه‌های پرش سریع اضافه کن
            if total_pages > 5:
                jump_buttons = []
                if current_page > 3:
                    jump_buttons.append(InlineKeyboardButton("1️⃣", callback_data=f"{callback_prefix}_page_1"))
                if current_page < total_pages - 2:
                    jump_buttons.append(InlineKeyboardButton(f"{total_pages}️⃣", callback_data=f"{callback_prefix}_page_{total_pages}"))
                
                if jump_buttons:
                    keyboard.append(jump_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def notification_settings() -> InlineKeyboardMarkup:
        """کیبورد تنظیمات اطلاع‌رسانی"""
        keyboard = [
            [
                InlineKeyboardButton("🔔 هشدار قیمت", callback_data="toggle_price_alerts"),
                InlineKeyboardButton("📊 هشدار سیگنال", callback_data="toggle_signal_alerts")
            ],
            [
                InlineKeyboardButton("📰 اخبار بازار", callback_data="toggle_news_alerts"),
                InlineKeyboardButton("💰 هشدار پکیج", callback_data="toggle_package_alerts")
            ],
            [
                InlineKeyboardButton("🎯 هشدار اهداف", callback_data="toggle_target_alerts"),
                InlineKeyboardButton("⚠️ هشدار ریسک", callback_data="toggle_risk_alerts")
            ],
            [
                InlineKeyboardButton("🕐 تنظیم زمان فعال", callback_data="set_notification_time"),
                InlineKeyboardButton("📱 تنظیم دستگاه", callback_data="device_settings")
            ],
            [
                InlineKeyboardButton("🔕 خاموش کردن همه", callback_data="disable_all_notifications"),
                InlineKeyboardButton("🔔 روشن کردن همه", callback_data="enable_all_notifications")
            ],
            [InlineKeyboardButton("⬅️ بازگشت به پروفایل", callback_data="user_profile")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)

class DynamicKeyboards:
    """کلاس کیبوردهای پویا"""
    
    @staticmethod
    def create_custom_keyboard(buttons: List[List[Dict[str, str]]], 
                             back_button: Optional[Dict[str, str]] = None) -> InlineKeyboardMarkup:
        """ایجاد کیبورد سفارشی"""
        keyboard = []
        
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append(InlineKeyboardButton(button['text'], callback_data=button['callback_data']))
            keyboard.append(keyboard_row)
        
        if back_button:
            keyboard.append([InlineKeyboardButton(back_button['text'], callback_data=back_button['callback_data'])])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_strategy_list_keyboard(strategies: List[str], callback_prefix: str = "strategy") -> InlineKeyboardMarkup:
        """ایجاد کیبورد لیست استراتژی‌ها"""
        keyboard = []
        
        # تقسیم استراتژی‌ها به ردیف‌های 2 تایی
        for i in range(0, len(strategies), 2):
            row = []
            for j in range(2):
                if i + j < len(strategies):
                    strategy = strategies[i + j]
                    # نام نمایشی استراتژی
                    display_name = strategy.replace('_', ' ').title()
                    row.append(InlineKeyboardButton(display_name, callback_data=f"{callback_prefix}_{strategy}"))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_symbol_keyboard(symbols: List[str], strategy: str) -> InlineKeyboardMarkup:
        """ایجاد کیبورد انتخاب نماد پویا"""
        keyboard = []
        
        # تقسیم نمادها به ردیف‌های 3 تایی
        for i in range(0, len(symbols), 3):
            row = []
            for j in range(3):
                if i + j < len(symbols):
                    symbol = symbols[i + j]
                    row.append(InlineKeyboardButton(symbol, callback_data=f"symbol_{strategy}|{symbol}"))
            keyboard.append(row)
        
        # اضافه کردن دکمه‌های عمومی
        keyboard.append([InlineKeyboardButton("🔤 ورود دستی", callback_data=f"manual_symbol_{strategy}")])
        keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="menu_strategy")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_list_keyboard(items: List[Dict[str, Any]], 
                           callback_prefix: str,
                           items_per_page: int = 10,
                           current_page: int = 1) -> InlineKeyboardMarkup:
        """ایجاد کیبورد لیستی با صفحه‌بندی"""
        keyboard = []
        
        # محاسبه شروع و پایان آیتم‌ها برای صفحه فعلی
        start_index = (current_page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = items[start_index:end_index]
        
        # اضافه کردن آیتم‌ها
        for item in page_items:
            text = item.get('text', str(item.get('id', 'Item')))
            callback_data = f"{callback_prefix}_{item.get('id', '')}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
        # اضافه کردن دکمه‌های صفحه‌بندی
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            nav_buttons = []
            
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_page_{current_page - 1}"))
            
            nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
            
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_page_{current_page + 1}"))
            
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)