"""
مدل تراکنش - مدیریت تراکنش‌های مالی و خرید پکیج‌ها
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
import json
import uuid

class TransactionType(Enum):
    """نوع تراکنش"""
    PACKAGE_PURCHASE = "package_purchase"
    PACKAGE_UPGRADE = "package_upgrade"
    PACKAGE_RENEWAL = "package_renewal"
    REFUND = "refund"
    BONUS = "bonus"
    REFERRAL_REWARD = "referral_reward"

class TransactionStatus(Enum):
    """وضعیت تراکنش"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    """روش پرداخت"""
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CRYPTO = "crypto"
    ZARINPAL = "zarinpal"
    MELLAT = "mellat"
    PASARGAD = "pasargad"
    ADMIN_CREDIT = "admin_credit"

@dataclass
class PaymentDetails:
    """جزئیات پرداخت"""
    payment_method: PaymentMethod
    gateway_transaction_id: Optional[str] = None
    gateway_reference: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    bank_name: Optional[str] = None
    card_number_masked: Optional[str] = None
    crypto_address: Optional[str] = None
    crypto_tx_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "payment_method": self.payment_method.value,
            "gateway_transaction_id": self.gateway_transaction_id,
            "gateway_reference": self.gateway_reference,
            "gateway_response": self.gateway_response,
            "bank_name": self.bank_name,
            "card_number_masked": self.card_number_masked,
            "crypto_address": self.crypto_address,
            "crypto_tx_hash": self.crypto_tx_hash
        }

@dataclass
class Transaction:
    """مدل کامل تراکنش"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    transaction_type: TransactionType = TransactionType.PACKAGE_PURCHASE
    status: TransactionStatus = TransactionStatus.PENDING
    amount: float = 0.0
    currency: str = "USD"
    package_id: Optional[str] = None
    package_name: Optional[str] = None
    subscription_duration: Optional[str] = None
    payment_details: Optional[PaymentDetails] = None
    description: str = ""
    notes: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None
    refunded_date: Optional[datetime] = None
    
    # فیلدهای اضافی برای ارتقا
    from_package_id: Optional[str] = None
    to_package_id: Optional[str] = None
    upgrade_days_remaining: Optional[int] = None
    
    # فیلدهای رفرال
    referrer_user_id: Optional[int] = None
    referral_reward_amount: float = 0.0
    
    def __post_init__(self):
        """پردازش پس از ایجاد"""
        if not self.description and self.package_name:
            self.description = f"خرید پکیج {self.package_name}"
    
    def is_completed(self) -> bool:
        """بررسی تکمیل تراکنش"""
        return self.status == TransactionStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """بررسی شکست تراکنش"""
        return self.status in [TransactionStatus.FAILED, TransactionStatus.CANCELLED]
    
    def is_pending(self) -> bool:
        """بررسی وضعیت انتظار"""
        return self.status in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]
    
    def can_be_refunded(self) -> bool:
        """بررسی امکان بازگشت وجه"""
        if self.status != TransactionStatus.COMPLETED:
            return False
        
        # حداکثر 7 روز برای بازگشت وجه
        if self.completed_date:
            refund_deadline = self.completed_date + timedelta(days=7)
            return datetime.now() <= refund_deadline
        
        return False
    
    def mark_completed(self, gateway_response: Optional[Dict[str, Any]] = None):
        """علامت‌گذاری به عنوان تکمیل شده"""
        self.status = TransactionStatus.COMPLETED
        self.completed_date = datetime.now()
        self.updated_date = datetime.now()
        
        if gateway_response and self.payment_details:
            self.payment_details.gateway_response = gateway_response
    
    def mark_failed(self, reason: str = ""):
        """علامت‌گذاری به عنوان شکست خورده"""
        self.status = TransactionStatus.FAILED
        self.updated_date = datetime.now()
        if reason:
            self.notes += f"\nFailed: {reason}"
    
    def mark_refunded(self, refund_amount: Optional[float] = None):
        """علامت‌گذاری به عنوان بازگشت داده شده"""
        self.status = TransactionStatus.REFUNDED
        self.refunded_date = datetime.now()
        self.updated_date = datetime.now()
        
        if refund_amount is not None:
            self.notes += f"\nRefunded: {refund_amount} {self.currency}"
    
    def get_duration_in_days(self) -> int:
        """دریافت مدت زمان در روز"""
        if not self.completed_date:
            return 0
        
        duration_map = {
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
            "lifetime": 365 * 100
        }
        
        return duration_map.get(self.subscription_duration, 30)
    
    def calculate_expiry_date(self, start_date: Optional[datetime] = None) -> datetime:
        """محاسبه تاریخ انقضا"""
        if not start_date:
            start_date = self.completed_date or datetime.now()
        
        duration_days = self.get_duration_in_days()
        return start_date + timedelta(days=duration_days)
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "amount": self.amount,
            "currency": self.currency,
            "package_id": self.package_id,
            "package_name": self.package_name,
            "subscription_duration": self.subscription_duration,
            "payment_details": self.payment_details.to_dict() if self.payment_details else None,
            "description": self.description,
            "notes": self.notes,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "refunded_date": self.refunded_date.isoformat() if self.refunded_date else None,
            "from_package_id": self.from_package_id,
            "to_package_id": self.to_package_id,
            "upgrade_days_remaining": self.upgrade_days_remaining,
            "referrer_user_id": self.referrer_user_id,
            "referral_reward_amount": self.referral_reward_amount,
            "duration_days": self.get_duration_in_days(),
            "can_refund": self.can_be_refunded()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """ایجاد از دیکشنری"""
        # پردازش payment_details
        payment_details = None
        if data.get("payment_details"):
            pd_data = data["payment_details"]
            payment_details = PaymentDetails(
                payment_method=PaymentMethod(pd_data["payment_method"]),
                gateway_transaction_id=pd_data.get("gateway_transaction_id"),
                gateway_reference=pd_data.get("gateway_reference"),
                gateway_response=pd_data.get("gateway_response"),
                bank_name=pd_data.get("bank_name"),
                card_number_masked=pd_data.get("card_number_masked"),
                crypto_address=pd_data.get("crypto_address"),
                crypto_tx_hash=pd_data.get("crypto_tx_hash")
            )
        
        return cls(
            transaction_id=data["transaction_id"],
            user_id=data["user_id"],
            transaction_type=TransactionType(data["transaction_type"]),
            status=TransactionStatus(data["status"]),
            amount=data["amount"],
            currency=data["currency"],
            package_id=data.get("package_id"),
            package_name=data.get("package_name"),
            subscription_duration=data.get("subscription_duration"),
            payment_details=payment_details,
            description=data.get("description", ""),
            notes=data.get("notes", ""),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"]),
            completed_date=datetime.fromisoformat(data["completed_date"]) if data.get("completed_date") else None,
            refunded_date=datetime.fromisoformat(data["refunded_date"]) if data.get("refunded_date") else None,
            from_package_id=data.get("from_package_id"),
            to_package_id=data.get("to_package_id"),
            upgrade_days_remaining=data.get("upgrade_days_remaining"),
            referrer_user_id=data.get("referrer_user_id"),
            referral_reward_amount=data.get("referral_reward_amount", 0.0)
        )

@dataclass
class PaymentInvoice:
    """فاکتور پرداخت"""
    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str = ""
    user_id: int = 0
    amount: float = 0.0
    currency: str = "USD"
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    final_amount: float = 0.0
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    gateway_url: Optional[str] = None
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    created_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """محاسبه مبلغ نهایی"""
        if self.final_amount == 0.0:
            self.final_amount = self.amount + self.tax_amount - self.discount_amount
    
    def is_expired(self) -> bool:
        """بررسی انقضا"""
        return datetime.now() > self.expires_at
    
    def time_remaining(self) -> timedelta:
        """زمان باقی‌مانده"""
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "invoice_id": self.invoice_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "tax_amount": self.tax_amount,
            "discount_amount": self.discount_amount,
            "final_amount": self.final_amount,
            "payment_method": self.payment_method.value,
            "gateway_url": self.gateway_url,
            "expires_at": self.expires_at.isoformat(),
            "created_date": self.created_date.isoformat(),
            "is_expired": self.is_expired(),
            "time_remaining_minutes": int(self.time_remaining().total_seconds() / 60)
        }

class TransactionManager:
    """مدیریت تراکنش‌ها"""
    
    @staticmethod
    def create_purchase_transaction(user_id: int, 
                                  package_id: str, 
                                  package_name: str,
                                  amount: float,
                                  subscription_duration: str,
                                  payment_method: PaymentMethod) -> Transaction:
        """ایجاد تراکنش خرید"""
        payment_details = PaymentDetails(payment_method=payment_method)
        
        return Transaction(
            user_id=user_id,
            transaction_type=TransactionType.PACKAGE_PURCHASE,
            amount=amount,
            package_id=package_id,
            package_name=package_name,
            subscription_duration=subscription_duration,
            payment_details=payment_details,
            description=f"خرید پکیج {package_name} - {subscription_duration}"
        )
    
    @staticmethod
    def create_upgrade_transaction(user_id: int,
                                 from_package_id: str,
                                 to_package_id: str,
                                 to_package_name: str,
                                 amount: float,
                                 remaining_days: int,
                                 payment_method: PaymentMethod) -> Transaction:
        """ایجاد تراکنش ارتقا"""
        payment_details = PaymentDetails(payment_method=payment_method)
        
        return Transaction(
            user_id=user_id,
            transaction_type=TransactionType.PACKAGE_UPGRADE,
            amount=amount,
            package_id=to_package_id,
            package_name=to_package_name,
            from_package_id=from_package_id,
            to_package_id=to_package_id,
            upgrade_days_remaining=remaining_days,
            payment_details=payment_details,
            description=f"ارتقا به پکیج {to_package_name}"
        )
    
    @staticmethod
    def create_referral_reward(user_id: int, 
                             referrer_id: int,
                             reward_amount: float,
                             source_transaction_id: str) -> Transaction:
        """ایجاد پاداش رفرال"""
        return Transaction(
            user_id=referrer_id,
            transaction_type=TransactionType.REFERRAL_REWARD,
            status=TransactionStatus.COMPLETED,
            amount=reward_amount,
            currency="USD",
            referrer_user_id=user_id,
            referral_reward_amount=reward_amount,
            description=f"پاداش رفرال از کاربر {user_id}",
            notes=f"Source transaction: {source_transaction_id}",
            completed_date=datetime.now()
        )
    
    @staticmethod
    def create_invoice(transaction: Transaction, 
                      tax_rate: float = 0.0,
                      discount_amount: float = 0.0) -> PaymentInvoice:
        """ایجاد فاکتور پرداخت"""
        tax_amount = transaction.amount * tax_rate
        
        return PaymentInvoice(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            currency=transaction.currency,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            payment_method=transaction.payment_details.payment_method if transaction.payment_details else PaymentMethod.BANK_TRANSFER
        )

class TransactionRepository:
    """مخزن تراکنش‌ها - برای استفاده در DatabaseManager"""
    
    @staticmethod
    def create_transaction_schema() -> str:
        """ایجاد جدول تراکنش‌ها"""
        return """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            status TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            package_id TEXT,
            package_name TEXT,
            subscription_duration TEXT,
            payment_details TEXT,
            description TEXT,
            notes TEXT DEFAULT '',
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL,
            completed_date TEXT,
            refunded_date TEXT,
            from_package_id TEXT,
            to_package_id TEXT,
            upgrade_days_remaining INTEGER,
            referrer_user_id INTEGER,
            referral_reward_amount REAL DEFAULT 0.0
        );
        
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            tax_amount REAL DEFAULT 0.0,
            discount_amount REAL DEFAULT 0.0,
            final_amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            gateway_url TEXT,
            expires_at TEXT NOT NULL,
            created_date TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
        CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_date);
        CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_expires ON invoices(expires_at);
        """
    
    @staticmethod
    def transaction_to_db_row(transaction: Transaction) -> Dict[str, Any]:
        """تبدیل Transaction به سطر دیتابیس"""
        return {
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "transaction_type": transaction.transaction_type.value,
            "status": transaction.status.value,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "package_id": transaction.package_id,
            "package_name": transaction.package_name,
            "subscription_duration": transaction.subscription_duration,
            "payment_details": json.dumps(transaction.payment_details.to_dict()) if transaction.payment_details else None,
            "description": transaction.description,
            "notes": transaction.notes,
            "created_date": transaction.created_date.isoformat(),
            "updated_date": transaction.updated_date.isoformat(),
            "completed_date": transaction.completed_date.isoformat() if transaction.completed_date else None,
            "refunded_date": transaction.refunded_date.isoformat() if transaction.refunded_date else None,
            "from_package_id": transaction.from_package_id,
            "to_package_id": transaction.to_package_id,
            "upgrade_days_remaining": transaction.upgrade_days_remaining,
            "referrer_user_id": transaction.referrer_user_id,
            "referral_reward_amount": transaction.referral_reward_amount
        }
    
    @staticmethod
    def invoice_to_db_row(invoice: PaymentInvoice) -> Dict[str, Any]:
        """تبدیل Invoice به سطر دیتابیس"""
        return {
            "invoice_id": invoice.invoice_id,
            "transaction_id": invoice.transaction_id,
            "user_id": invoice.user_id,
            "amount": invoice.amount,
            "currency": invoice.currency,
            "tax_amount": invoice.tax_amount,
            "discount_amount": invoice.discount_amount,
            "final_amount": invoice.final_amount,
            "payment_method": invoice.payment_method.value,
            "gateway_url": invoice.gateway_url,
            "expires_at": invoice.expires_at.isoformat(),
            "created_date": invoice.created_date.isoformat()
        }
    
    @staticmethod
    def db_row_to_transaction(row: Dict[str, Any]) -> Transaction:
        """تبدیل سطر دیتابیس به Transaction"""
        payment_details = None
        if row.get("payment_details"):
            pd_data = json.loads(row["payment_details"])
            payment_details = PaymentDetails(
                payment_method=PaymentMethod(pd_data["payment_method"]),
                gateway_transaction_id=pd_data.get("gateway_transaction_id"),
                gateway_reference=pd_data.get("gateway_reference"),
                gateway_response=pd_data.get("gateway_response"),
                bank_name=pd_data.get("bank_name"),
                card_number_masked=pd_data.get("card_number_masked"),
                crypto_address=pd_data.get("crypto_address"),
                crypto_tx_hash=pd_data.get("crypto_tx_hash")
            )
        
        return Transaction(
            transaction_id=row["transaction_id"],
            user_id=row["user_id"],
            transaction_type=TransactionType(row["transaction_type"]),
            status=TransactionStatus(row["status"]),
            amount=row["amount"],
            currency=row["currency"],
            package_id=row.get("package_id"),
            package_name=row.get("package_name"),
            subscription_duration=row.get("subscription_duration"),
            payment_details=payment_details,
            description=row.get("description", ""),
            notes=row.get("notes", ""),
            created_date=datetime.fromisoformat(row["created_date"]),
            updated_date=datetime.fromisoformat(row["updated_date"]),
            completed_date=datetime.fromisoformat(row["completed_date"]) if row.get("completed_date") else None,
            refunded_date=datetime.fromisoformat(row["refunded_date"]) if row.get("refunded_date") else None,
            from_package_id=row.get("from_package_id"),
            to_package_id=row.get("to_package_id"),
            upgrade_days_remaining=row.get("upgrade_days_remaining"),
            referrer_user_id=row.get("referrer_user_id"),
            referral_reward_amount=row.get("referral_reward_amount", 0.0)
        )
