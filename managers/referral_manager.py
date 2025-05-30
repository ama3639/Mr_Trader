"""
مدیریت سیستم رفرال و پاداش‌ها MrTrader Bot
"""
import secrets
import string
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from core.config import Config
from utils.logger import logger
from database.database_manager import DatabaseManager
from core.cache import cache


@dataclass
class ReferralReward:
    """مدل پاداش رفرال"""
    user_id: int
    referrer_id: int
    reward_type: str  # 'signup', 'purchase', 'milestone'
    amount: float
    currency: str = 'points'
    description: str = ''
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ReferralManager:
    """مدیریت سیستم رفرال"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.referral_settings = self._load_referral_settings()
        self._initialize_referral_system()
    
    def _initialize_referral_system(self):
        """مقداردهی اولیه سیستم رفرال"""
        try:
            # ایجاد جدول کدهای رفرال
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS referral_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    referral_code TEXT UNIQUE NOT NULL,
                    total_referrals INTEGER DEFAULT 0,
                    total_earnings REAL DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)
            
            # ایجاد جدول رفرال‌ها
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_user_id INTEGER NOT NULL,
                    referral_code TEXT NOT NULL,
                    signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_purchase_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    UNIQUE(referred_user_id)
                )
            """)
            
            # ایجاد جدول پاداش‌ها
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS referral_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    referrer_id INTEGER,
                    referred_user_id INTEGER,
                    reward_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'points',
                    description TEXT,
                    is_claimed BOOLEAN DEFAULT 0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    claimed_date TIMESTAMP
                )
            """)
            
            # ایجاد جدول رتبه‌بندی رفرال
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS referral_leaderboard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    total_referrals INTEGER DEFAULT 0,
                    total_earnings REAL DEFAULT 0.0,
                    current_rank INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Referral system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing referral system: {e}")
    
    def _load_referral_settings(self) -> Dict[str, Any]:
        """بارگذاری تنظیمات رفرال"""
        return {
            'signup_reward': {
                'referrer': 100,    # پاداش معرف
                'referee': 50       # پاداش معرفی‌شده
            },
            'purchase_reward': {
                'percentage': 10,   # درصد از خرید
                'max_amount': 1000  # حداکثر پاداش
            },
            'milestone_rewards': [
                {'referrals': 5, 'reward': 500},
                {'referrals': 10, 'reward': 1200},
                {'referrals': 25, 'reward': 3000},
                {'referrals': 50, 'reward': 7500},
                {'referrals': 100, 'reward': 20000}
            ],
            'code_length': 8,
            'code_expiry_days': 365,
            'max_referrals_per_user': 1000
        }
    
    def generate_referral_code(self, user_id: int) -> Optional[str]:
        """تولید کد رفرال برای کاربر"""
        try:
            # بررسی وجود کد قبلی
            existing_code = self.db.fetch_one("""
                SELECT referral_code FROM referral_codes 
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            if existing_code:
                return existing_code['referral_code']
            
            # تولید کد جدید
            attempts = 0
            max_attempts = 10
            
            while attempts < max_attempts:
                # ایجاد کد تصادفی
                code = self._generate_random_code()
                
                # بررسی یکتا بودن
                existing = self.db.fetch_one("""
                    SELECT id FROM referral_codes WHERE referral_code = ?
                """, (code,))
                
                if not existing:
                    # ذخیره کد جدید
                    self.db.execute_query("""
                        INSERT INTO referral_codes 
                        (user_id, referral_code, created_date, is_active)
                        VALUES (?, ?, ?, 1)
                    """, (user_id, code, datetime.now().isoformat()))
                    
                    logger.info(f"Generated referral code {code} for user {user_id}")
                    return code
                
                attempts += 1
            
            logger.error(f"Failed to generate unique referral code for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating referral code for user {user_id}: {e}")
            return None
    
    def _generate_random_code(self) -> str:
        """تولید کد تصادفی"""
        length = self.referral_settings['code_length']
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    async def process_referral(self, referred_user_id: int, referral_code: str) -> Dict[str, Any]:
        """پردازش رفرال کاربر جدید"""
        try:
            # بررسی معتبر بودن کد رفرال
            referrer_info = self.db.fetch_one("""
                SELECT user_id, referral_code, total_referrals 
                FROM referral_codes 
                WHERE referral_code = ? AND is_active = 1
            """, (referral_code.upper(),))
            
            if not referrer_info:
                return {
                    'success': False,
                    'message': 'کد رفرال نامعتبر است'
                }
            
            referrer_id = referrer_info['user_id']
            
            # بررسی عدم خود-رفرالی
            if referrer_id == referred_user_id:
                return {
                    'success': False,
                    'message': 'امکان استفاده از کد رفرال خودتان وجود ندارد'
                }
            
            # بررسی عدم رفرال قبلی
            existing_referral = self.db.fetch_one("""
                SELECT id FROM referrals WHERE referred_user_id = ?
            """, (referred_user_id,))
            
            if existing_referral:
                return {
                    'success': False,
                    'message': 'شما قبلاً با کد رفرال ثبت‌نام کرده‌اید'
                }
            
            # بررسی حداکثر تعداد رفرال
            max_referrals = self.referral_settings['max_referrals_per_user']
            if referrer_info['total_referrals'] >= max_referrals:
                return {
                    'success': False,
                    'message': 'حداکثر تعداد رفرال برای این کاربر به پایان رسیده'
                }
            
            # ثبت رفرال
            self.db.execute_query("""
                INSERT INTO referrals 
                (referrer_id, referred_user_id, referral_code, signup_date, status)
                VALUES (?, ?, ?, ?, 'active')
            """, (referrer_id, referred_user_id, referral_code, datetime.now().isoformat()))
            
            # بروزرسانی آمار معرف
            self.db.execute_query("""
                UPDATE referral_codes 
                SET total_referrals = total_referrals + 1,
                    last_used = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), referrer_id))
            
            # اعطای پاداش ثبت‌نام
            await self._grant_signup_rewards(referrer_id, referred_user_id)
            
            # بررسی دستیابی به نقاط عطف
            await self._check_milestone_rewards(referrer_id)
            
            # بروزرسانی رتبه‌بندی
            await self._update_leaderboard(referrer_id)
            
            logger.info(f"Processed referral: user {referred_user_id} referred by {referrer_id}")
            
            return {
                'success': True,
                'message': 'رفرال با موفقیت ثبت شد',
                'referrer_id': referrer_id,
                'rewards': {
                    'referrer_reward': self.referral_settings['signup_reward']['referrer'],
                    'referee_reward': self.referral_settings['signup_reward']['referee']
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing referral for user {referred_user_id}: {e}")
            return {
                'success': False,
                'message': 'خطا در پردازش رفرال'
            }
    
    async def _grant_signup_rewards(self, referrer_id: int, referred_user_id: int):
        """اعطای پاداش‌های ثبت‌نام"""
        try:
            signup_rewards = self.referral_settings['signup_reward']
            
            # پاداش معرف
            referrer_reward = ReferralReward(
                user_id=referrer_id,
                referrer_id=referrer_id,
                reward_type='signup_referrer',
                amount=signup_rewards['referrer'],
                description=f'پاداش معرفی کاربر جدید'
            )
            
            # پاداش معرفی‌شده
            referee_reward = ReferralReward(
                user_id=referred_user_id,
                referrer_id=referrer_id,
                reward_type='signup_referee',
                amount=signup_rewards['referee'],
                description='پاداش خوش‌آمدگویی'
            )
            
            # ذخیره پاداش‌ها
            await self._save_reward(referrer_reward)
            await self._save_reward(referee_reward)
            
            logger.info(f"Granted signup rewards: {signup_rewards['referrer']} to referrer {referrer_id}, "
                       f"{signup_rewards['referee']} to referee {referred_user_id}")
            
        except Exception as e:
            logger.error(f"Error granting signup rewards: {e}")
    
    async def _save_reward(self, reward: ReferralReward):
        """ذخیره پاداش در دیتابیس"""
        try:
            self.db.execute_query("""
                INSERT INTO referral_rewards 
                (user_id, referrer_id, referred_user_id, reward_type, amount, 
                 currency, description, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reward.user_id,
                reward.referrer_id,
                getattr(reward, 'referred_user_id', None),
                reward.reward_type,
                reward.amount,
                reward.currency,
                reward.description,
                reward.created_at.isoformat()
            ))
            
        except Exception as e:
            logger.error(f"Error saving reward: {e}")
    
    async def _check_milestone_rewards(self, referrer_id: int):
        """بررسی و اعطای پاداش‌های نقاط عطف"""
        try:
            # دریافت تعداد کل رفرال‌ها
            total_referrals = self.db.fetch_one("""
                SELECT total_referrals FROM referral_codes 
                WHERE user_id = ?
            """, (referrer_id,))
            
            if not total_referrals:
                return
            
            current_referrals = total_referrals['total_referrals']
            
            # بررسی نقاط عطف
            for milestone in self.referral_settings['milestone_rewards']:
                required_referrals = milestone['referrals']
                reward_amount = milestone['reward']
                
                if current_referrals >= required_referrals:
                    # بررسی عدم اعطای قبلی این پاداش
                    existing_reward = self.db.fetch_one("""
                        SELECT id FROM referral_rewards 
                        WHERE user_id = ? AND reward_type = ? AND amount = ?
                    """, (referrer_id, 'milestone', reward_amount))
                    
                    if not existing_reward:
                        # اعطای پاداش نقطه عطف
                        milestone_reward = ReferralReward(
                            user_id=referrer_id,
                            referrer_id=referrer_id,
                            reward_type='milestone',
                            amount=reward_amount,
                            description=f'دستیابی به {required_referrals} رفرال'
                        )
                        
                        await self._save_reward(milestone_reward)
                        logger.info(f"Granted milestone reward {reward_amount} to user {referrer_id} "
                                   f"for {required_referrals} referrals")
            
        except Exception as e:
            logger.error(f"Error checking milestone rewards for user {referrer_id}: {e}")
    
    async def process_purchase_reward(self, user_id: int, purchase_amount: float) -> Dict[str, Any]:
        """پردازش پاداش خرید"""
        try:
            # بررسی آیا کاربر معرفی‌شده است
            referral_info = self.db.fetch_one("""
                SELECT referrer_id, first_purchase_date 
                FROM referrals 
                WHERE referred_user_id = ? AND status = 'active'
            """, (user_id,))
            
            if not referral_info:
                return {'success': False, 'message': 'کاربر معرفی‌شده نیست'}
            
            referrer_id = referral_info['referrer_id']
            
            # محاسبه پاداش
            purchase_settings = self.referral_settings['purchase_reward']
            reward_amount = min(
                purchase_amount * (purchase_settings['percentage'] / 100),
                purchase_settings['max_amount']
            )
            
            if reward_amount <= 0:
                return {'success': False, 'message': 'مبلغ خرید کافی نیست'}
            
            # ثبت اولین خرید اگر وجود نداشته باشد
            if not referral_info['first_purchase_date']:
                self.db.execute_query("""
                    UPDATE referrals 
                    SET first_purchase_date = ?
                    WHERE referred_user_id = ?
                """, (datetime.now().isoformat(), user_id))
            
            # اعطای پاداش خرید
            purchase_reward = ReferralReward(
                user_id=referrer_id,
                referrer_id=referrer_id,
                reward_type='purchase',
                amount=reward_amount,
                description=f'پاداش خرید {purchase_amount} واحد'
            )
            
            await self._save_reward(purchase_reward)
            
            # بروزرسانی کل درآمد
            self.db.execute_query("""
                UPDATE referral_codes 
                SET total_earnings = total_earnings + ?
                WHERE user_id = ?
            """, (reward_amount, referrer_id))
            
            # بروزرسانی رتبه‌بندی
            await self._update_leaderboard(referrer_id)
            
            logger.info(f"Granted purchase reward {reward_amount} to referrer {referrer_id} "
                       f"for purchase by user {user_id}")
            
            return {
                'success': True,
                'reward_amount': reward_amount,
                'referrer_id': referrer_id
            }
            
        except Exception as e:
            logger.error(f"Error processing purchase reward for user {user_id}: {e}")
            return {'success': False, 'message': 'خطا در پردازش پاداش'}
    
    async def _update_leaderboard(self, user_id: int):
        """بروزرسانی رتبه‌بندی"""
        try:
            # دریافت آمار کاربر
            user_stats = self.db.fetch_one("""
                SELECT total_referrals, total_earnings 
                FROM referral_codes 
                WHERE user_id = ?
            """, (user_id,))
            
            if not user_stats:
                return
            
            # بروزرسانی یا درج در leaderboard
            self.db.execute_query("""
                INSERT OR REPLACE INTO referral_leaderboard 
                (user_id, total_referrals, total_earnings, last_updated)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                user_stats['total_referrals'],
                user_stats['total_earnings'],
                datetime.now().isoformat()
            ))
            
            # محاسبه رتبه‌ها
            await self._calculate_ranks()
            
        except Exception as e:
            logger.error(f"Error updating leaderboard for user {user_id}: {e}")
    
    async def _calculate_ranks(self):
        """محاسبه رتبه‌های جدید"""
        try:
            # مرتب‌سازی بر اساس تعداد رفرال و سپس درآمد
            self.db.execute_query("""
                UPDATE referral_leaderboard 
                SET current_rank = (
                    SELECT COUNT(*) + 1 
                    FROM referral_leaderboard as rl2 
                    WHERE (rl2.total_referrals > referral_leaderboard.total_referrals) 
                    OR (rl2.total_referrals = referral_leaderboard.total_referrals 
                        AND rl2.total_earnings > referral_leaderboard.total_earnings)
                )
            """)
            
        except Exception as e:
            logger.error(f"Error calculating ranks: {e}")
    
    def get_user_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """دریافت آمار رفرال کاربر"""
        try:
            # اطلاعات کد رفرال
            referral_info = self.db.fetch_one("""
                SELECT referral_code, total_referrals, total_earnings, created_date
                FROM referral_codes 
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            if not referral_info:
                # ایجاد کد رفرال اگر وجود نداشته باشد
                referral_code = self.generate_referral_code(user_id)
                if referral_code:
                    referral_info = {
                        'referral_code': referral_code,
                        'total_referrals': 0,
                        'total_earnings': 0.0,
                        'created_date': datetime.now().isoformat()
                    }
                else:
                    return {}
            
            # دریافت رتبه
            rank_info = self.db.fetch_one("""
                SELECT current_rank 
                FROM referral_leaderboard 
                WHERE user_id = ?
            """, (user_id,))
            
            # پاداش‌های کسب‌نشده
            unclaimed_rewards = self.db.fetch_all("""
                SELECT amount, reward_type, description, created_date
                FROM referral_rewards 
                WHERE user_id = ? AND is_claimed = 0
                ORDER BY created_date DESC
            """, (user_id,))
            
            # رفرال‌های اخیر
            recent_referrals = self.db.fetch_all("""
                SELECT referred_user_id, signup_date, first_purchase_date
                FROM referrals 
                WHERE referrer_id = ? 
                ORDER BY signup_date DESC 
                LIMIT 10
            """, (user_id,))
            
            # محاسبه پیش‌بینی پاداش بعدی
            next_milestone = self._get_next_milestone(referral_info['total_referrals'])
            
            stats = {
                'referral_code': referral_info['referral_code'],
                'total_referrals': referral_info['total_referrals'],
                'total_earnings': referral_info['total_earnings'],
                'current_rank': rank_info['current_rank'] if rank_info else None,
                'unclaimed_rewards': [dict(row) for row in unclaimed_rewards] if unclaimed_rewards else [],
                'recent_referrals': [dict(row) for row in recent_referrals] if recent_referrals else [],
                'next_milestone': next_milestone,
                'referral_link': f"{Config.BOT_LINK}?start={referral_info['referral_code']}",
                'member_since': referral_info['created_date']
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            return {}
    
    def _get_next_milestone(self, current_referrals: int) -> Optional[Dict[str, Any]]:
        """دریافت نقطه عطف بعدی"""
        try:
            for milestone in self.referral_settings['milestone_rewards']:
                if milestone['referrals'] > current_referrals:
                    return {
                        'required_referrals': milestone['referrals'],
                        'reward': milestone['reward'],
                        'remaining': milestone['referrals'] - current_referrals
                    }
            return None
            
        except Exception as e:
            logger.error(f"Error getting next milestone: {e}")
            return None
    
    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        """دریافت رتبه‌بندی برتر"""
        try:
            leaderboard = self.db.fetch_all("""
                SELECT rl.user_id, rl.total_referrals, rl.total_earnings, 
                       rl.current_rank, rc.referral_code
                FROM referral_leaderboard rl
                JOIN referral_codes rc ON rl.user_id = rc.user_id
                WHERE rc.is_active = 1
                ORDER BY rl.current_rank ASC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in leaderboard] if leaderboard else []
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def claim_rewards(self, user_id: int) -> Dict[str, Any]:
        """دریافت پاداش‌های کسب‌نشده"""
        try:
            # دریافت پاداش‌های کسب‌نشده
            unclaimed_rewards = self.db.fetch_all("""
                SELECT id, amount, reward_type, description
                FROM referral_rewards 
                WHERE user_id = ? AND is_claimed = 0
            """, (user_id,))
            
            if not unclaimed_rewards:
                return {
                    'success': False,
                    'message': 'پاداش کسب‌نشده‌ای وجود ندارد'
                }
            
            total_amount = sum(float(row['amount']) for row in unclaimed_rewards)
            reward_ids = [row['id'] for row in unclaimed_rewards]
            
            # علامت‌گذاری به‌عنوان دریافت‌شده
            placeholders = ','.join(['?' for _ in reward_ids])
            self.db.execute_query(f"""
                UPDATE referral_rewards 
                SET is_claimed = 1, claimed_date = ?
                WHERE id IN ({placeholders})
            """, [datetime.now().isoformat()] + reward_ids)
            
            logger.info(f"User {user_id} claimed {len(unclaimed_rewards)} rewards totaling {total_amount}")
            
            return {
                'success': True,
                'total_amount': total_amount,
                'rewards_count': len(unclaimed_rewards),
                'rewards': [dict(row) for row in unclaimed_rewards]
            }
            
        except Exception as e:
            logger.error(f"Error claiming rewards for user {user_id}: {e}")
            return {
                'success': False,
                'message': 'خطا در دریافت پاداش‌ها'
            }
    
    def validate_referral_code(self, code: str) -> Dict[str, Any]:
        """اعتبارسنجی کد رفرال"""
        try:
            code = code.upper().strip()
            
            referrer_info = self.db.fetch_one("""
                SELECT user_id, total_referrals, is_active 
                FROM referral_codes 
                WHERE referral_code = ?
            """, (code,))
            
            if not referrer_info:
                return {'valid': False, 'message': 'کد رفرال یافت نشد'}
            
            if not referrer_info['is_active']:
                return {'valid': False, 'message': 'کد رفرال غیرفعال است'}
            
            max_referrals = self.referral_settings['max_referrals_per_user']
            if referrer_info['total_referrals'] >= max_referrals:
                return {'valid': False, 'message': 'حداکثر تعداد رفرال به پایان رسیده'}
            
            return {
                'valid': True,
                'referrer_id': referrer_info['user_id'],
                'message': 'کد رفرال معتبر است'
            }
            
        except Exception as e:
            logger.error(f"Error validating referral code {code}: {e}")
            return {'valid': False, 'message': 'خطا در اعتبارسنجی'}
    
    def get_referral_analytics(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """تحلیل‌های رفرال"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            base_query = """
                SELECT COUNT(*) as count, 
                       DATE(signup_date) as date
                FROM referrals 
                WHERE signup_date >= ? 
            """
            params = [start_date.isoformat()]
            
            if user_id:
                base_query += " AND referrer_id = ?"
                params.append(user_id)
            
            base_query += " GROUP BY DATE(signup_date) ORDER BY date"
            
            daily_referrals = self.db.fetch_all(base_query, params)
            
            # آمار کلی
            total_query = "SELECT COUNT(*) as total FROM referrals WHERE signup_date >= ?"
            if user_id:
                total_query += " AND referrer_id = ?"
            
            total_result = self.db.fetch_one(total_query, params[:1] if not user_id else params)
            
            analytics = {
                'period_days': days,
                'total_referrals': total_result['total'] if total_result else 0,
                'daily_breakdown': [dict(row) for row in daily_referrals] if daily_referrals else [],
                'average_per_day': round(total_result['total'] / days, 2) if total_result else 0
            }
            
            if user_id:
                # آمار شخصی
                user_rewards = self.db.fetch_one("""
                    SELECT SUM(amount) as total_earned 
                    FROM referral_rewards 
                    WHERE user_id = ? AND created_date >= ?
                """, (user_id, start_date.isoformat()))
                
                analytics['total_earned'] = user_rewards['total_earned'] if user_rewards else 0
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting referral analytics: {e}")
            return {}


# Export
__all__ = ['ReferralManager', 'ReferralReward']