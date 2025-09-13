"""
قالب‌های کیبورد - مدیریت کیبوردهای inline
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional, Union
from managers.symbol_manager import symbol_manager

class KeyboardTemplates:
    """کلاس قالب‌های کیبورد"""
    
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """کیبورد منوی اصلی یکپارچه و نهایی"""
        keyboard = [
            [
                InlineKeyboardButton("🇮🇷 تحلیل طلا", callback_data="gold_menu"),
                InlineKeyboardButton("💵 تحلیل ارز", callback_data="currency_menu")
            ],
            [
                InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="analysis_menu"),
                InlineKeyboardButton("🔬 بک‌تست", callback_data="backtest_menu")
            ],
            [
                InlineKeyboardButton("💎 قیمت لایو", callback_data="coins_list"),
                InlineKeyboardButton("📈 نمودار قیمت", callback_data="price_chart")
            ],
            [
                InlineKeyboardButton("🔔 هشدار قیمت", callback_data="price_alert"),
                InlineKeyboardButton("🎯 سیگنال‌ها", callback_data="signals_menu")
            ],
            [
                InlineKeyboardButton("📰 اخبار بازار", callback_data="market_news"),
                InlineKeyboardButton("👤 حساب کاربری", callback_data="user_profile")
            ],
            [
                InlineKeyboardButton("💰 کیف پول", callback_data="wallet_menu"),
                InlineKeyboardButton("🛒 خرید پکیج", callback_data="packages_menu")
            ],
            [
                InlineKeyboardButton("🎁 دعوت دوستان", callback_data="referral_menu"),
                InlineKeyboardButton("ℹ️ راهنما", callback_data="help_menu")
            ],
            [
                InlineKeyboardButton("📞 پشتیبانی", callback_data="support_menu")
            ]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔧 پنل مدیریت", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def generate_gold_menu_keyboard():
        """کیبورد کامل منوی تحلیل طلا و سکه را ایجاد می‌کند."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 طلای 18 عیار", callback_data="analyze_gold:IR_GOLD_18K")],
            [
                InlineKeyboardButton("💰 سکه امامی", callback_data="analyze_gold:IR_COIN_EMAMI"),
                InlineKeyboardButton("🪙 سکه بهار آزادی", callback_data="analyze_gold:IR_COIN_BAHAR")
            ],
            [
                InlineKeyboardButton("💰 نیم سکه", callback_data="analyze_gold:IR_COIN_HALF"),
                InlineKeyboardButton("🪙 ربع سکه", callback_data="analyze_gold:IR_COIN_QUARTER")
            ],
            [InlineKeyboardButton("✨ طلای 24 عیار", callback_data="analyze_gold:IR_GOLD_24K")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
        ])

    @staticmethod
    def generate_currency_menu_keyboard():
        """کیبورد کامل منوی تحلیل ارز را ایجاد می‌کند."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🇺🇸 دلار آمریکا", callback_data="analyze_gold:USD")],
            [InlineKeyboardButton("🇪🇺 یورو", callback_data="analyze_gold:EUR")],
            [InlineKeyboardButton("🇬🇧 پوند انگلیس", callback_data="analyze_gold:GBP")],
            [InlineKeyboardButton("🌍 انس طلا جهانی", callback_data="analyze_gold:XAUUSD")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
        ])

    @staticmethod
    def generate_backtest_menu_keyboard():
        """کیبورد کامل منوی بک‌تست استراتژی را ایجاد می‌کند."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 دلار آمریکا (USD)", callback_data="backtest:USD")],
            [InlineKeyboardButton("💰 سکه امامی (IR_COIN_EMAMI)", callback_data="backtest:IR_COIN_EMAMI")],
            [InlineKeyboardButton("🪙 طلای 18 عیار (IR_GOLD_18K)", callback_data="backtest:IR_GOLD_18K")],
            [InlineKeyboardButton("₿ بیت‌کوین (BTC)", callback_data="backtest:BTC")],
            [InlineKeyboardButton("✨ همه نمادها", callback_data="backtest:ALL")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
        ])

    @staticmethod
    def strategy_menu(user_package: str = "free") -> InlineKeyboardMarkup:
        """کیبورد منوی استراتژی‌ها - کامل با callback_data استاندارد شده"""
        keyboard = []
        
        # پیشوند استاندارد برای همه استراتژی‌ها جهت پردازش ساده‌تر
        prefix = "select_strategy:"

        # استراتژی‌های دمو برای کاربران رایگان
        if user_package == "free":
            keyboard.extend([
                [InlineKeyboardButton("🆓 === استراتژی‌های دمو ===", callback_data="info_demo")],
                [
                    InlineKeyboardButton("🎯 دمو پرایس اکشن", callback_data=f"{prefix}demo_price_action"),
                    InlineKeyboardButton("📈 دمو RSI", callback_data=f"{prefix}demo_rsi")
                ]
            ])
        
        # استراتژی‌های BASIC (9 استراتژی)
        if user_package in ["basic", "premium", "vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("🥉 === پکیج بیسیک (9 استراتژی) ===", callback_data="info_basic")],
                [
                    InlineKeyboardButton("📊 تحلیل CCI", callback_data=f"{prefix}cci_analysis"),
                    InlineKeyboardButton("📈 تحلیل EMA", callback_data=f"{prefix}ema_analysis")
                ],
                [
                    InlineKeyboardButton("☁️ ابر ایچیموکو", callback_data=f"{prefix}ichimoku"),
                    InlineKeyboardButton("📉 ایچیموکو سیگنال پایین", callback_data=f"{prefix}ichimoku_low_signal")
                ],
                [
                    InlineKeyboardButton("🌊 تحلیل MACD", callback_data=f"{prefix}macd"),
                    InlineKeyboardButton("🎯 پرایس اکشن TA", callback_data=f"{prefix}price_action_pandas_ta")
                ],
                [
                    InlineKeyboardButton("🔴 قیمت زنده بایننس", callback_data=f"{prefix}project_price_live_binance"),
                    InlineKeyboardButton("📊 تحلیل RSI", callback_data=f"{prefix}rsi")
                ],
                [
                    InlineKeyboardButton("📉 تحلیل Williams R", callback_data=f"{prefix}williams_r_analysis")
                ]
            ])
        
        # استراتژی‌های PREMIUM (17 استراتژی اضافی)
        if user_package in ["premium", "vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("🥈 === پکیج پریمیوم (+17 استراتژی) ===", callback_data="info_premium")],
                [
                    InlineKeyboardButton("🕯️ تحلیل کندل استیک", callback_data=f"{prefix}a_candlestick"),
                    InlineKeyboardButton("🕯️ کندل هایکن آشی", callback_data=f"{prefix}heikin_ashi")
                ],
                [
                    InlineKeyboardButton("📊 باندهای بولینگر", callback_data=f"{prefix}bollinger_bands"),
                    InlineKeyboardButton("📈 تحلیل استوکاستیک", callback_data=f"{prefix}stochastic")
                ],
                [
                    InlineKeyboardButton("🌊 واگرایی MACD", callback_data=f"{prefix}macd_divergence"),
                    InlineKeyboardButton("🚀 تحلیل مومنتوم", callback_data=f"{prefix}momentum")
                ],
                [
                    InlineKeyboardButton("🎯 نقاط محوری", callback_data=f"{prefix}b_pivot"),
                    InlineKeyboardButton("📐 خطوط روند", callback_data=f"{prefix}c_trend_lines")
                ],
                [
                    InlineKeyboardButton("🌀 استراتژی فیبوناچی", callback_data=f"{prefix}fibonacci_strategy"),
                    InlineKeyboardButton("🛡️ حمایت و مقاومت", callback_data=f"{prefix}support_resistance")
                ],
                [
                    InlineKeyboardButton("⛰️ الگوی دو قله", callback_data=f"{prefix}double_top_pattern"),
                    InlineKeyboardButton("📐 الگوی مثلث", callback_data=f"{prefix}triangle_pattern")
                ],
                [
                    InlineKeyboardButton("📊 الگوی گوه", callback_data=f"{prefix}wedge_pattern"),
                    InlineKeyboardButton("🏁 الگوی پرچم", callback_data=f"{prefix}flag_pattern")
                ],
                [
                    InlineKeyboardButton("👤 الگوی سر و شانه", callback_data=f"{prefix}head_shoulders_analysis"),
                    InlineKeyboardButton("🐊 تمساح ویلیامز", callback_data=f"{prefix}williams_alligator")
                ],
                [
                    InlineKeyboardButton("🎰 مارتینگل پایین", callback_data=f"{prefix}martingale_low"),
                    InlineKeyboardButton("📈 سار پارابولیک", callback_data=f"{prefix}parabolic_sar")
                ]
            ])
        
        # استراتژی‌های VIP (9 استراتژی اضافی)
        if user_package in ["vip", "ghost"]:
            keyboard.extend([
                [InlineKeyboardButton("👑 === پکیج وی‌آی‌پی (+9 استراتژی) ===", callback_data="info_vip")],
                [
                    InlineKeyboardButton("📊 تحلیل ATR", callback_data=f"{prefix}atr"),
                    InlineKeyboardButton("📈 SMA پیشرفته", callback_data=f"{prefix}sma_advanced")
                ],
                [
                    InlineKeyboardButton("📊 پروفایل حجم", callback_data=f"{prefix}volume_profile"),
                    InlineKeyboardButton("💎 تحلیل VWAP", callback_data=f"{prefix}vwap")
                ],
                [
                    InlineKeyboardButton("💎 الگوی الماس", callback_data=f"{prefix}diamond_pattern"),
                    InlineKeyboardButton("🎯 تحلیل CRT", callback_data=f"{prefix}crt")
                ],
                [
                    InlineKeyboardButton("🎯 سیستم P3", callback_data=f"{prefix}p3"),
                    InlineKeyboardButton("🔄 تحلیل RTM", callback_data=f"{prefix}rtm")
                ],
                [
                    InlineKeyboardButton("🛡️ مقاومت چندگانه", callback_data=f"{prefix}multi_resistance")
                ]
            ])
        
        # دکمه‌های عمومی
        keyboard.extend([
            [InlineKeyboardButton("💎 ارتقا پکیج", callback_data="packages_menu")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
        
    @staticmethod
    def symbol_selection(strategy: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب نماد ارز - بهبود یافته و استاندارد شده"""
        prefix = "select_symbol:"
        keyboard = [
            # ارزهای اصلی
            [
                InlineKeyboardButton("₿ BTC", callback_data=f"{prefix}{strategy}|BTC"),
                InlineKeyboardButton("♦️ ETH", callback_data=f"{prefix}{strategy}|ETH"),
                InlineKeyboardButton("🔶 BNB", callback_data=f"{prefix}{strategy}|BNB")
            ],
            # ارزهای محبوب
            [
                InlineKeyboardButton("🔷 ADA", callback_data=f"{prefix}{strategy}|ADA"),
                InlineKeyboardButton("☀️ SOL", callback_data=f"{prefix}{strategy}|SOL"),
                InlineKeyboardButton("💧 XRP", callback_data=f"{prefix}{strategy}|XRP")
            ],
            # ارزهای مم و محبوب
            [
                InlineKeyboardButton("🐕 DOGE", callback_data=f"{prefix}{strategy}|DOGE"),
                InlineKeyboardButton("🔥 SHIB", callback_data=f"{prefix}{strategy}|SHIB"),
                InlineKeyboardButton("⚪ DOT", callback_data=f"{prefix}{strategy}|DOT")
            ],
            # DeFi و Web3
            [
                InlineKeyboardButton("🔗 LINK", callback_data=f"{prefix}{strategy}|LINK"),
                InlineKeyboardButton("🔄 UNI", callback_data=f"{prefix}{strategy}|UNI"),
                InlineKeyboardButton("🚀 AVAX", callback_data=f"{prefix}{strategy}|AVAX")
            ],
            # Layer 1 و 2
            [
                InlineKeyboardButton("🔷 MATIC", callback_data=f"{prefix}{strategy}|MATIC"),
                InlineKeyboardButton("🌙 LUNA", callback_data=f"{prefix}{strategy}|LUNA"),
                InlineKeyboardButton("⚫ ATOM", callback_data=f"{prefix}{strategy}|ATOM")
            ],
            # سایر ارزهای محبوب
            [
                InlineKeyboardButton("🔴 ALGO", callback_data=f"{prefix}{strategy}|ALGO"),
                InlineKeyboardButton("🟦 FTM", callback_data=f"{prefix}{strategy}|FTM"),
                InlineKeyboardButton("🔵 NEAR", callback_data=f"{prefix}{strategy}|NEAR")
            ],
            # مجموعه دوم
            [
                InlineKeyboardButton("💎 ICP", callback_data=f"{prefix}{strategy}|ICP"),
                InlineKeyboardButton("🟢 VET", callback_data=f"{prefix}{strategy}|VET"),
                InlineKeyboardButton("🎭 THETA", callback_data=f"{prefix}{strategy}|THETA")
            ],
            # کیبورد ورود دستی و بازگشت
            [InlineKeyboardButton("🔤 ورود دستی نماد", callback_data=f"manual_symbol:{strategy}")],
            [InlineKeyboardButton("⬅️ بازگشت به استراتژی‌ها", callback_data="analysis_menu")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def currency_selection(strategy: str, symbol: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب ارز مرجع - استاندارد شده"""
        prefix = "select_currency:"
        keyboard = [
            # ارزهای اصلی
            [
                InlineKeyboardButton("💵 USDT", callback_data=f"{prefix}{strategy}|{symbol}|USDT"),
                InlineKeyboardButton("💵 BUSD", callback_data=f"{prefix}{strategy}|{symbol}|BUSD")
            ],
            [
                InlineKeyboardButton("💰 USDC", callback_data=f"{prefix}{strategy}|{symbol}|USDC")
            ],
            # ارزهای کریپتو
            [
                InlineKeyboardButton("₿ BTC", callback_data=f"{prefix}{strategy}|{symbol}|BTC"),
                InlineKeyboardButton("♦️ ETH", callback_data=f"{prefix}{strategy}|{symbol}|ETH")
            ],
            [
                InlineKeyboardButton("🔶 BNB", callback_data=f"{prefix}{strategy}|{symbol}|BNB")
            ],
            # ورود دستی و بازگشت
            [InlineKeyboardButton("🔤 ورود دستی ارز مرجع", callback_data=f"manual_currency:{strategy}|{symbol}")],
            [InlineKeyboardButton("⬅️ بازگشت به انتخاب نماد", callback_data=f"select_strategy:{strategy}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def timeframe_selection(strategy: str, symbol: str, currency: str) -> InlineKeyboardMarkup:
        """کیبورد انتخاب تایم‌فریم - کامل و استاندارد شده"""
        prefix = "select_timeframe:"
        keyboard = [
            # تایم‌فریم‌های کوتاه‌مدت
            [
                InlineKeyboardButton("1️⃣ دقیقه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|1m"),
                InlineKeyboardButton("3️⃣ دقیقه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|3m"),
                InlineKeyboardButton("5️⃣ دقیقه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|5m")
            ],
            [
                InlineKeyboardButton("1️⃣5️⃣ دقیقه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|15m"),
                InlineKeyboardButton("3️⃣0️⃣ دقیقه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|30m")
            ],
            # تایم‌فریم‌های ساعتی
            [
                InlineKeyboardButton("1️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|1h"),
                InlineKeyboardButton("2️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|2h"),
                InlineKeyboardButton("4️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|4h")
            ],
            [
                InlineKeyboardButton("6️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|6h"),
                InlineKeyboardButton("8️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|8h"),
                InlineKeyboardButton("1️⃣2️⃣ ساعت", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|12h")
            ],
            # تایم‌فریم‌های بلندمدت
            [
                InlineKeyboardButton("1️⃣ روز", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|1d"),
                InlineKeyboardButton("3️⃣ روز", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|3d"),
                InlineKeyboardButton("1️⃣ هفته", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|1w")
            ],
            [
                InlineKeyboardButton("1️⃣ ماه", callback_data=f"{prefix}{strategy}|{symbol}|{currency}|1M")
            ],
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به انتخاب ارز مرجع", callback_data=f"select_symbol:{strategy}|{symbol}")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def analysis_result_actions(strategy: str, symbol: str, currency: str, timeframe: str) -> InlineKeyboardMarkup:
        """کیبورد اقدامات پس از تحلیل - استاندارد شده"""
        keyboard = [
            # اقدامات اصلی
            [InlineKeyboardButton("🔄 به‌روزرسانی تحلیل", callback_data=f"select_timeframe:{strategy}|{symbol}|{currency}|{timeframe}")],
            # تغییرات
            [
                InlineKeyboardButton("⏱ تغییر تایم‌فریم", callback_data=f"select_currency:{strategy}|{symbol}|{currency}"),
                InlineKeyboardButton("💱 تغییر ارز مرجع", callback_data=f"select_symbol:{strategy}|{symbol}")
            ],
            [
                InlineKeyboardButton("🪙 تغییر نماد", callback_data=f"select_strategy:{strategy}"),
                InlineKeyboardButton("📊 استراتژی دیگر", callback_data="analysis_menu")
            ],
            # ابزارهای اضافی (در صورت پیاده‌سازی)
            # [
            #     InlineKeyboardButton("💾 ذخیره گزارش", callback_data=f"save_report:{strategy}|{symbol}|{currency}|{timeframe}"),
            #     InlineKeyboardButton("📤 اشتراک‌گذاری", callback_data=f"share_analysis:{strategy}|{symbol}|{currency}|{timeframe}")
            # ],
            # بازگشت
            [InlineKeyboardButton("⬅️ بازگشت به استراتژی‌ها", callback_data="analysis_menu")],
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
    def generate_live_price_menu_keyboard():
        """منوی اصلی انتخاب بازار برای قیمت لحظه‌ای را ایجاد می‌کند."""
        keyboard = [
            [InlineKeyboardButton("🇮🇷 طلا و سکه", callback_data="show_market:gold")],
            [InlineKeyboardButton("💵 ارزها", callback_data="show_market:currency")],
            [InlineKeyboardButton("📈 ارزهای دیجیتال", callback_data="show_market:crypto")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def generate_symbols_keyboard(market_type: str) -> InlineKeyboardMarkup:
        """کیبورد نمادها را به صورت پویا برای یک بازار خاص ایجاد می‌کند."""
        
        # تعیین اینکه آیا لیست کامل کریپتو درخواست شده است
        is_full_list = (market_type == 'crypto_full')
        
        # اگر لیست کامل درخواست شده، از آن استفاده کن، در غیر این صورت لیست عادی
        symbols_market_type = 'crypto_full' if is_full_list else market_type.replace('_full', '')
        symbols = symbol_manager.get_symbols_by_market(symbols_market_type)
        
        keyboard = []
        prefix = "live_price:"

        # ساخت دکمه‌ها به صورت دو ستونی (یا سه ستونی برای لیست کامل)
        columns = 3 if is_full_list else 2
        for i in range(0, len(symbols), columns):
            row = []
            for j in range(columns):
                if i + j < len(symbols):
                    # برای کریپتو نام انگلیسی و برای بقیه نام فارسی را نمایش بده
                    display_name = symbols[i+j][1] if market_type.startswith('crypto') else symbols[i+j][0]
                    row.append(InlineKeyboardButton(display_name, callback_data=f"{prefix}{symbols[i+j][1]}"))
            keyboard.append(row)
        
        # اضافه کردن دکمه‌های مخصوص کریپتو
        if market_type == 'crypto':
            keyboard.extend([
                [InlineKeyboardButton("✏️ ورود دستی نماد", callback_data="live_manual_input")],
                [InlineKeyboardButton("📋 لیست کامل بایننس", callback_data="show_market:crypto_full")]
            ])

        # دکمه بازگشت
        if is_full_list:
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به قیمت لایوی دیجیتال", callback_data="show_market:crypto")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به انتخاب بازار", callback_data="coins_list")])
            
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