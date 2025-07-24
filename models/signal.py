"""
مدل‌های سیگنال و تعاریف Enum برای MrTrader Bot
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.logger import logger


class SignalType(Enum):
    """انواع سیگنال معاملاتی"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class TimeFrame(Enum):
    """بازه‌های زمانی تحلیل"""
    M1 = "1m"       # 1 دقیقه
    M5 = "5m"       # 5 دقیقه
    M15 = "15m"     # 15 دقیقه
    M30 = "30m"     # 30 دقیقه
    H1 = "1h"       # 1 ساعت
    H4 = "4h"       # 4 ساعت
    D1 = "1d"       # روزانه
    W1 = "1w"       # هفتگی
    MN1 = "1M"      # ماهانه


class SignalStrength(Enum):
    """قدرت سیگنال"""
    VERY_WEAK = 1
    WEAK = 2
    NEUTRAL = 3
    STRONG = 4
    VERY_STRONG = 5


class AnalysisType(Enum):
    """نوع تحلیل"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    PRICE_ACTION = "price_action"
    VOLUME = "volume"
    SENTIMENT = "sentiment"


class TrendDirection(Enum):
    """جهت ترند"""
    BULLISH = "bullish"      # صعودی
    BEARISH = "bearish"      # نزولی
    SIDEWAYS = "sideways"    # خنثی/کناری


class OrderType(Enum):
    """نوع سفارش"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class RiskLevel(Enum):
    """سطح ریسک"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class TechnicalIndicator:
    """شاخص فنی"""
    name: str
    value: float
    signal: SignalType
    confidence: float = 0.0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'name': self.name,
            'value': self.value,
            'signal': self.signal.value,
            'confidence': self.confidence,
            'description': self.description
        }


@dataclass
class PriceLevel:
    """سطوح قیمتی"""
    level: float
    type: str  # support, resistance, pivot
    strength: SignalStrength
    tested_count: int = 0
    last_test_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'level': self.level,
            'type': self.type,
            'strength': self.strength.value,
            'tested_count': self.tested_count,
            'last_test_date': self.last_test_date.isoformat() if self.last_test_date else None
        }


@dataclass
class VolumeAnalysis:
    """تحلیل حجم معاملات"""
    current_volume: float
    average_volume: float
    volume_ratio: float
    volume_trend: TrendDirection
    is_unusual: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'current_volume': self.current_volume,
            'average_volume': self.average_volume,
            'volume_ratio': self.volume_ratio,
            'volume_trend': self.volume_trend.value,
            'is_unusual': self.is_unusual
        }


@dataclass
class MarketSentiment:
    """احساسات بازار"""
    fear_greed_index: float  # 0-100
    social_sentiment: float  # -1 to 1
    news_sentiment: float    # -1 to 1
    overall_sentiment: SignalType
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'fear_greed_index': self.fear_greed_index,
            'social_sentiment': self.social_sentiment,
            'news_sentiment': self.news_sentiment,
            'overall_sentiment': self.overall_sentiment.value,
            'confidence': self.confidence
        }


@dataclass
class RiskManagement:
    """مدیریت ریسک"""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    position_size: float = 0.0
    max_loss_percent: float = 2.0
    
    def calculate_position_size(self, account_balance: float, 
                              entry_price: float, stop_loss: float) -> float:
        """محاسبه اندازه پوزیشن"""
        try:
            if stop_loss == 0 or entry_price == 0:
                return 0.0
            
            risk_amount = account_balance * (self.max_loss_percent / 100)
            price_difference = abs(entry_price - stop_loss)
            position_size = risk_amount / price_difference
            
            return round(position_size, 6)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward_ratio': self.risk_reward_ratio,
            'position_size': self.position_size,
            'max_loss_percent': self.max_loss_percent
        }


@dataclass
class Signal:
    """کلاس اصلی سیگنال معاملاتی"""
    
    # اطلاعات پایه
    symbol: str
    currency: str = "USDT"
    signal_type: SignalType = SignalType.HOLD
    timeframe: TimeFrame = TimeFrame.H1
    analysis_type: AnalysisType = AnalysisType.TECHNICAL
    
    # قیمت‌ها
    current_price: float = 0.0
    entry_price: Optional[float] = None
    target_prices: List[float] = field(default_factory=list)
    
    # قدرت و اعتماد
    strength: SignalStrength = SignalStrength.NEUTRAL
    confidence: float = 0.0
    
    # ترند و حجم
    trend_direction: TrendDirection = TrendDirection.SIDEWAYS
    volume_analysis: Optional[VolumeAnalysis] = None
    
    # شاخص‌های فنی
    indicators: List[TechnicalIndicator] = field(default_factory=list)
    price_levels: List[PriceLevel] = field(default_factory=list)
    
    # مدیریت ریسک
    risk_management: Optional[RiskManagement] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # احساسات بازار
    market_sentiment: Optional[MarketSentiment] = None
    
    # اطلاعات زمانی
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # متا دیتا
    source: str = "MrTrader"
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """اعتبارسنجی و تنظیمات پس از ایجاد"""
        try:
            # اعتبارسنجی قیمت‌ها
            if self.current_price <= 0:
                logger.warning(f"Invalid current price for {self.symbol}: {self.current_price}")
            
            # تنظیم قیمت ورود اگر تعریف نشده
            if self.entry_price is None:
                self.entry_price = self.current_price
            
            # ایجاد مدیریت ریسک پیش‌فرض
            if self.risk_management is None:
                self.risk_management = RiskManagement()
            
            # محاسبه سطح ریسک بر اساس قدرت سیگنال
            self._calculate_risk_level()
            
        except Exception as e:
            logger.error(f"Error in Signal post-init: {e}")
    
    def _calculate_risk_level(self):
        """محاسبه سطح ریسک بر اساس پارامترهای مختلف"""
        try:
            risk_score = 0
            
            # بر اساس قدرت سیگنال
            strength_mapping = {
                SignalStrength.VERY_WEAK: 5,
                SignalStrength.WEAK: 4,
                SignalStrength.NEUTRAL: 3,
                SignalStrength.STRONG: 2,
                SignalStrength.VERY_STRONG: 1
            }
            risk_score += strength_mapping.get(self.strength, 3)
            
            # بر اساس اعتماد
            if self.confidence < 0.3:
                risk_score += 2
            elif self.confidence < 0.6:
                risk_score += 1
            
            # بر اساس تایم فریم
            timeframe_risk = {
                TimeFrame.M1: 3, TimeFrame.M5: 3, TimeFrame.M15: 2,
                TimeFrame.M30: 2, TimeFrame.H1: 1, TimeFrame.H4: 1,
                TimeFrame.D1: 0, TimeFrame.W1: 0, TimeFrame.MN1: 0
            }
            risk_score += timeframe_risk.get(self.timeframe, 1)
            
            # تعیین سطح ریسک نهایی
            if risk_score <= 3:
                self.risk_level = RiskLevel.LOW
            elif risk_score <= 5:
                self.risk_level = RiskLevel.MEDIUM
            elif risk_score <= 7:
                self.risk_level = RiskLevel.HIGH
            else:
                self.risk_level = RiskLevel.VERY_HIGH
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            self.risk_level = RiskLevel.MEDIUM
    
    def add_indicator(self, name: str, value: float, signal: SignalType, 
                      confidence: float = 0.0, description: str = ""):
        """افزودن شاخص فنی"""
        try:
            indicator = TechnicalIndicator(
                name=name,
                value=value,
                signal=signal,
                confidence=confidence,
                description=description
            )
            self.indicators.append(indicator)
            logger.debug(f"Added indicator {name} to signal for {self.symbol}")
            
        except Exception as e:
            logger.error(f"Error adding indicator {name}: {e}")
    
    def add_price_level(self, level: float, level_type: str, 
                        strength: SignalStrength, tested_count: int = 0):
        """افزودن سطح قیمتی"""
        try:
            price_level = PriceLevel(
                level=level,
                type=level_type,
                strength=strength,
                tested_count=tested_count,
                last_test_date=datetime.now() if tested_count > 0 else None
            )
            self.price_levels.append(price_level)
            logger.debug(f"Added price level {level} ({level_type}) to signal for {self.symbol}")
            
        except Exception as e:
            logger.error(f"Error adding price level: {e}")
    
    def get_signal_score(self) -> float:
        """محاسبه امتیاز کلی سیگنال"""
        try:
            base_score = 0
            
            # امتیاز بر اساس نوع سیگنال
            signal_scores = {
                SignalType.STRONG_BUY: 2.0,
                SignalType.BUY: 1.0,
                SignalType.HOLD: 0.0,
                SignalType.SELL: -1.0,
                SignalType.STRONG_SELL: -2.0
            }
            base_score = signal_scores.get(self.signal_type, 0)
            
            # ضریب قدرت
            strength_multiplier = {
                SignalStrength.VERY_STRONG: 1.5,
                SignalStrength.STRONG: 1.2,
                SignalStrength.NEUTRAL: 1.0,
                SignalStrength.WEAK: 0.8,
                SignalStrength.VERY_WEAK: 0.5
            }
            multiplier = strength_multiplier.get(self.strength, 1.0)
            
            # امتیاز شاخص‌ها
            if self.indicators:
                indicator_score = sum([
                    signal_scores.get(ind.signal, 0) * ind.confidence 
                    for ind in self.indicators
                ]) / len(self.indicators)
                base_score = (base_score + indicator_score) / 2
            
            # اعمال ضریب و اعتماد
            final_score = base_score * multiplier * self.confidence
            
            return round(final_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating signal score: {e}")
            return 0.0
    
    def is_valid(self) -> bool:
        """بررسی معتبر بودن سیگنال"""
        try:
            # بررسی زمان انقضا
            if self.expires_at and datetime.now() > self.expires_at:
                return False
            
            # بررسی داده‌های ضروری
            if not self.symbol or self.current_price <= 0:
                return False
            
            # بررسی حداقل اعتماد
            if self.confidence < 0.1:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
    
    def get_signal_summary(self) -> str:
        """خلاصه سیگنال برای نمایش"""
        try:
            signal_emoji = {
                SignalType.STRONG_BUY: "🟢⬆️",
                SignalType.BUY: "🟢",
                SignalType.HOLD: "🟡",
                SignalType.SELL: "🔴",
                SignalType.STRONG_SELL: "🔴⬇️"
            }
            
            emoji = signal_emoji.get(self.signal_type, "⚪")
            risk_emoji = {
                RiskLevel.LOW: "🟢",
                RiskLevel.MEDIUM: "🟡", 
                RiskLevel.HIGH: "🟠",
                RiskLevel.VERY_HIGH: "🔴"
            }
            
            summary = f"{emoji} {self.symbol}/{self.currency}\n"
            summary += f"📊 سیگنال: {self.signal_type.value.upper()}\n"
            summary += f"💪 قدرت: {self.strength.value}/5\n"
            summary += f"🎯 اعتماد: {self.confidence:.1%}\n"
            summary += f"💰 قیمت: ${self.current_price:,.4f}\n"
            summary += f"⚠️ ریسک: {risk_emoji.get(self.risk_level, '⚪')} {self.risk_level.value}\n"
            summary += f"📈 ترند: {self.trend_direction.value}\n"
            summary += f"⏰ زمان: {self.timeframe.value}"
            
            if self.risk_management and self.risk_management.stop_loss:
                summary += f"\n🛑 حد ضرر: ${self.risk_management.stop_loss:,.4f}"
            
            if self.risk_management and self.risk_management.take_profit:
                summary += f"\n🎯 هدف: ${self.risk_management.take_profit:,.4f}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating signal summary: {e}")
            return f"خطا در نمایش سیگنال {self.symbol}"
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل سیگنال به دیکشنری"""
        try:
            return {
                'symbol': self.symbol,
                'currency': self.currency,
                'signal_type': self.signal_type.value,
                'timeframe': self.timeframe.value,
                'analysis_type': self.analysis_type.value,
                'current_price': self.current_price,
                'entry_price': self.entry_price,
                'target_prices': self.target_prices,
                'strength': self.strength.value,
                'confidence': self.confidence,
                'trend_direction': self.trend_direction.value,
                'volume_analysis': self.volume_analysis.to_dict() if self.volume_analysis else None,
                'indicators': [ind.to_dict() for ind in self.indicators],
                'price_levels': [level.to_dict() for level in self.price_levels],
                'risk_management': self.risk_management.to_dict() if self.risk_management else None,
                'risk_level': self.risk_level.value,
                'market_sentiment': self.market_sentiment.to_dict() if self.market_sentiment else None,
                'created_at': self.created_at.isoformat(),
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'source': self.source,
                'notes': self.notes,
                'tags': self.tags,
                'signal_score': self.get_signal_score()
            }
            
        except Exception as e:
            logger.error(f"Error converting signal to dict: {e}")
            return {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """ایجاد سیگنال از دیکشنری"""
        try:
            # تبدیل enum ها
            signal_type = SignalType(data.get('signal_type', 'hold'))
            timeframe = TimeFrame(data.get('timeframe', '1h'))
            analysis_type = AnalysisType(data.get('analysis_type', 'technical'))
            strength = SignalStrength(data.get('strength', 3))
            trend_direction = TrendDirection(data.get('trend_direction', 'sideways'))
            risk_level = RiskLevel(data.get('risk_level', 'medium'))
            
            # تبدیل تاریخ‌ها
            created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
            expires_at = None
            if data.get('expires_at'):
                expires_at = datetime.fromisoformat(data['expires_at'])
            
            # ایجاد سیگنال
            signal = cls(
                symbol=data.get('symbol', ''),
                currency=data.get('currency', 'USDT'),
                signal_type=signal_type,
                timeframe=timeframe,
                analysis_type=analysis_type,
                current_price=data.get('current_price', 0.0),
                entry_price=data.get('entry_price'),
                target_prices=data.get('target_prices', []),
                strength=strength,
                confidence=data.get('confidence', 0.0),
                trend_direction=trend_direction,
                risk_level=risk_level,
                created_at=created_at,
                expires_at=expires_at,
                source=data.get('source', 'MrTrader'),
                notes=data.get('notes', ''),
                tags=data.get('tags', [])
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal from dict: {e}")
            return cls(symbol="ERROR", current_price=0.0)


# کلاس‌های کمکی برای مدیریت مجموعه سیگنال‌ها
class SignalCollection:
    """مجموعه‌ای از سیگنال‌ها"""
    
    def __init__(self):
        self.signals: List[Signal] = []
    
    def add_signal(self, signal: Signal):
        """افزودن سیگنال"""
        if signal.is_valid():
            self.signals.append(signal)
            logger.info(f"Added signal for {signal.symbol}: {signal.signal_type.value}")
        else:
            logger.warning(f"Invalid signal rejected for {signal.symbol}")
    
    def remove_expired(self):
        """حذف سیگنال‌های منقضی"""
        before_count = len(self.signals)
        self.signals = [s for s in self.signals if s.is_valid()]
        removed_count = before_count - len(self.signals)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} expired signals")
    
    def get_by_symbol(self, symbol: str) -> List[Signal]:
        """دریافت سیگنال‌های یک نماد"""
        return [s for s in self.signals if s.symbol.upper() == symbol.upper()]
    
    def get_top_signals(self, limit: int = 10) -> List[Signal]:
        """دریافت بهترین سیگنال‌ها"""
        valid_signals = [s for s in self.signals if s.is_valid()]
        sorted_signals = sorted(valid_signals, key=lambda x: x.get_signal_score(), reverse=True)
        return sorted_signals[:limit]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """آمار خلاصه سیگنال‌ها"""
        try:
            total = len(self.signals)
            valid = len([s for s in self.signals if s.is_valid()])
            
            signal_types = {}
            for signal in self.signals:
                signal_type = signal.signal_type.value
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            avg_confidence = sum([s.confidence for s in self.signals]) / total if total > 0 else 0
            
            return {
                'total_signals': total,
                'valid_signals': valid,
                'expired_signals': total - valid,
                'signal_types': signal_types,
                'average_confidence': round(avg_confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}


# Export کلاس‌ها و enum ها
__all__ = [
    'SignalType', 'TimeFrame', 'SignalStrength', 'AnalysisType', 
    'TrendDirection', 'OrderType', 'RiskLevel',
    'TechnicalIndicator', 'PriceLevel', 'VolumeAnalysis', 
    'MarketSentiment', 'RiskManagement', 'Signal', 'SignalCollection'
]