import hashlib
import hmac

from django.conf import settings
from django.db import models
from utils.enums import PaymentMethodEnum, PaymentStatus, WalletTransactionStatusEnum, WalletTransactionTypeEnum
from order.models import Checkout, Order
from utils.types import User
import uuid


def _wallet_hmac(msg: str) -> str:
    secret = getattr(settings, "WALLET_CHAIN_SECRET", settings.SECRET_KEY).encode()
    return hmac.new(secret, msg.encode(), hashlib.sha256).hexdigest()


def _payment_event_hmac(msg: str) -> str:
    secret = getattr(settings, "PAYMENT_EVENT_SECRET", settings.SECRET_KEY).encode()
    return hmac.new(secret, msg.encode(), hashlib.sha256).hexdigest()


_WALLET_TX_IMMUTABLE = frozenset({"amount", "balance_before", "balance_after", "chain_hash", "transaction_type", "user_id"})




class PaymentTransaction(models.Model):
    """Model lưu trữ thông tin giao dịch thanh toán"""
    
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # checkout = models.OneToOneField(
    #     Checkout, 
    #     on_delete=models.CASCADE, 
    #     related_name='payment_transaction'
    # )

    checkout = models.OneToOneField(
        Checkout,
        on_delete=models.CASCADE,
        related_name="payment_transaction",
    )
    
    # Payment gateway info
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodEnum.choices,
        default=PaymentMethodEnum.COD
    )
    
    # VNPay specific fields
    vnp_txn_ref = models.CharField(max_length=100, null=True, blank=True)  # Mã đơn hàng
    vnp_transaction_no = models.CharField(max_length=100, null=True, blank=True)  # Mã giao dịch VNPay
    vnp_bank_code = models.CharField(max_length=50, null=True, blank=True)
    vnp_card_type = models.CharField(max_length=50, null=True, blank=True)
    
    # PayOS specific fields
    payos_order_code = models.BigIntegerField(null=True, blank=True, db_index=True)  # Mã đơn hàng PayOS
    
    # Amount and status
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vnp_txn_ref']),
            models.Index(fields=['payos_order_code']),
        ]
    
    def __str__(self):
        return f"Payment {self.uid} - {self.payment_method}"


class PaymentTransactionState(models.Model):
    """Mutable processing state for payment transactions."""

    # payment_transaction = models.OneToOneField(
    #     PaymentTransaction,
    #     on_delete=models.CASCADE,
    #     related_name="state",
    # )
    payment_transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="state",
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_url = models.TextField(null=True, blank=True)
    payos_payment_link_id = models.CharField(max_length=100, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_transaction_states"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="payment_tx_state_status_idx"),
            models.Index(fields=["paid_at"], name="payment_tx_state_paid_at_idx"),
        ]

    def __str__(self):
        return f"PaymentTxState {self.payment_transaction_id} - {self.status}"


class PaymentTransactionEvent(models.Model):
    """Append-only audit log for payment transaction changes."""
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=40)
    status_from = models.CharField(max_length=20, blank=True, null=True)
    status_to = models.CharField(max_length=20, blank=True, null=True)
    payload = models.JSONField(null=True, blank=True)
    signature_valid = models.BooleanField(null=True, blank=True)
    source = models.CharField(max_length=40, blank=True, default="")
    previous_hash = models.CharField(max_length=64, default="0" * 64)
    chain_hash = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_transaction_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_transaction", "created_at"], name="payment_tx_event_tx_idx"),
            models.Index(fields=["event_type"], name="payment_tx_event_type_idx"),
        ]

    def __str__(self):
        return f"PaymentTxEvent {self.payment_transaction_id} - {self.event_type}"

    @staticmethod
    def compute_chain_hash(payment_id, event_type, status_from, status_to, previous_hash) -> str:
        msg = f"{payment_id}:{event_type}:{status_from}:{status_to}:{previous_hash}"
        return _payment_event_hmac(msg)

    @classmethod
    def get_last_chain_hash(cls, payment_id: int) -> str:
        last = (
            cls.objects.filter(payment_transaction_id=payment_id)
            .order_by("-created_at")
            .values("chain_hash")
            .first()
        )
        return last["chain_hash"] if last and last["chain_hash"] else "0" * 64

    @classmethod
    def verify_event_chain(cls, payment_id: int) -> dict:
        """
        Recompute every chain_hash in the event log and compare against stored values.
        Returns {"valid": True, ...} if intact, or {"valid": False, "tampered_at": event_id, ...} on mismatch.
        Does NOT prevent a DB-level attacker who also recomputes hashes with the correct secret;
        that threat is covered by gateway reconciliation.
        """
        events = list(
            cls.objects.filter(payment_transaction_id=payment_id)
            .order_by("created_at", "id")
            .values("id", "event_type", "status_from", "status_to", "previous_hash", "chain_hash")
        )
        if not events:
            return {"valid": True, "events_checked": 0, "tampered_at": None}

        expected_prev = "0" * 64
        for idx, ev in enumerate(events):
            if ev["previous_hash"] != expected_prev:
                return {
                    "valid": False,
                    "events_checked": idx,
                    "tampered_at": ev["id"],
                    "reason": "previous_hash_mismatch",
                }
            computed = cls.compute_chain_hash(
                payment_id=payment_id,
                event_type=ev["event_type"],
                status_from=ev["status_from"],
                status_to=ev["status_to"],
                previous_hash=ev["previous_hash"],
            )
            if ev["chain_hash"] != computed:
                return {
                    "valid": False,
                    "events_checked": idx,
                    "tampered_at": ev["id"],
                    "reason": "chain_hash_mismatch",
                }
            expected_prev = ev["chain_hash"]

        return {"valid": True, "events_checked": len(events), "tampered_at": None}


class CustomerPaymentInfo(models.Model):
    """Bank information for customer wallet withdrawals."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_payment_info",
    )
    bank_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=20)
    bank_account_number = models.CharField(max_length=50)
    bank_account_name = models.CharField(max_length=255)
    bank_branch = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_payment_info'
        verbose_name = 'Customer Payment Information'
        verbose_name_plural = 'Customer Payment Information'

    def __str__(self):
        return f"{self.user.email} - {self.bank_name} ({self.bank_account_number})"


class InternalWallet(models.Model):
    """Internal wallet used for customer refunds and chef settlements."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="internal_wallet",
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pending_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="VND")
    # HMAC-SHA256(secret, "{user_id}:{balance}:{pending_balance}") — detects direct DB edits
    signature = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'internal_wallets'

    def __str__(self):
        return f"Wallet - {self.user.email} - {self.balance} {self.currency}"

    def compute_signature(self) -> str:
        return _wallet_hmac(f"{self.user_id}:{self.balance}:{self.pending_balance}")

    def verify_signature(self) -> bool:
        if not self.signature:
            return False
        expected = self.compute_signature()
        return hmac.compare_digest(expected, self.signature)

    def compute_expected_balance(self) -> "Decimal":
        from django.db.models import Sum
        from decimal import Decimal
        from utils.enums import WalletTransactionTypeEnum, WalletTransactionStatusEnum
        credits = (
            WalletTransaction.objects.filter(
                user_id=self.user_id,
                transaction_type__in=[
                    WalletTransactionTypeEnum.REFUND,
                    WalletTransactionTypeEnum.RELEASE,
                ],
                state__status=WalletTransactionStatusEnum.SUCCESS,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )
        debits = (
            WalletTransaction.objects.filter(
                user_id=self.user_id,
                transaction_type=WalletTransactionTypeEnum.PAYOUT,
                state__status=WalletTransactionStatusEnum.SUCCESS,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )
        return credits - debits

    def _verify_wallet_tx_chain(self) -> dict:
        """
        Walk toàn bộ WalletTransaction của user theo thứ tự tạo (ASC) và kiểm tra:

          1. chain_hash integrity — mỗi record tự xác nhận tính toàn vẹn của chính nó:
               chain_hash == HMAC(uid:user_id:tx_type:amount:balance_before:balance_after:previous_hash)
             → Phát hiện bất kỳ ai sửa amount, balance_before, balance_after, hoặc tx_type.

          2. chain linkage — record[n].previous_hash phải khớp với record[n-1].chain_hash:
             → Phát hiện INSERT hoặc DELETE bất kỳ record nào ở giữa chuỗi.

          3. balance continuity — balance_after[n] phải bằng balance_before[n+1]:
             → Phát hiện INSERT giả ở cuối chuỗi có chain_hash hợp lệ nhưng số dư không liên tục.

        Trả về dict với:
          chain_intact  : bool
          chain_length  : int  — số record đã kiểm tra
          break_at_uid  : str | None — uid của record đầu tiên bị phá vỡ (để audit)
          break_reason  : str | None — loại vi phạm phát hiện được
        """
        txs = list(
            WalletTransaction.objects.filter(user_id=self.user_id)
            .order_by("created_at")
            .values(
                "uid", "user_id", "transaction_type", "amount",
                "balance_before", "balance_after",
                "previous_hash", "chain_hash",
            )
        )

        if not txs:
            return {"chain_intact": True, "chain_length": 0, "break_at_uid": None, "break_reason": None}

        expected_previous = "0" * 64

        for i, tx in enumerate(txs):
            uid        = str(tx["uid"])
            user_id    = tx["user_id"]
            tx_type    = tx["transaction_type"]
            amount     = tx["amount"]
            bal_before = tx["balance_before"]
            bal_after  = tx["balance_after"]
            stored_prev  = tx["previous_hash"]
            stored_chain = tx["chain_hash"]

            # Check 2: linkage — previous_hash phải bằng chain_hash của record trước
            if not hmac.compare_digest(stored_prev, expected_previous):
                return {
                    "chain_intact": False,
                    "chain_length": i,
                    "break_at_uid": uid,
                    "break_reason": "chain_link_broken",
                }

            # Check 1: hash integrity — chain_hash phải khớp với nội dung record
            expected_hash = WalletTransaction.compute_chain_hash(
                uid, user_id, tx_type, amount, bal_before, bal_after, stored_prev,
            )
            if not hmac.compare_digest(expected_hash, stored_chain):
                return {
                    "chain_intact": False,
                    "chain_length": i,
                    "break_at_uid": uid,
                    "break_reason": "hash_mismatch",
                }

            # Check 3: balance continuity — balance_after[n] == balance_before[n+1]
            if i > 0:
                prev_bal_after = txs[i - 1]["balance_after"]
                if bal_before != prev_bal_after:
                    return {
                        "chain_intact": False,
                        "chain_length": i,
                        "break_at_uid": uid,
                        "break_reason": "balance_discontinuity",
                    }

            expected_previous = stored_chain

        return {"chain_intact": True, "chain_length": len(txs), "break_at_uid": None, "break_reason": None}

    def verify_integrity(self) -> dict:
        """
        Kiểm tra toàn vẹn của ví theo 3 lớp độc lập:

          1. signature_valid       — HMAC(balance, pending_balance) khớp với stored signature
          2. balance_matches_ledger — balance == tổng WalletTransaction từ ledger
          3. chain_intact          — toàn bộ chuỗi WalletTransaction chưa bị sửa/thêm/xóa

        Cả 3 phải True thì mới cho phép rút tiền.
        """
        sig_ok   = self.verify_signature()
        expected = self.compute_expected_balance()
        balance_ok = self.balance == expected
        chain_result = self._verify_wallet_tx_chain()

        return {
            "signature_valid":        sig_ok,
            "balance_matches_ledger": balance_ok,
            "chain_intact":           chain_result["chain_intact"],
            "stored_balance":         str(self.balance),
            "expected_balance":       str(expected),
            "chain_length":           chain_result["chain_length"],
            "chain_break_at":         chain_result["break_at_uid"],
            "chain_break_reason":     chain_result["break_reason"],
        }


class WalletTransaction(models.Model):
    """Audit trail for all internal wallet movements."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
    )
    transaction_type = models.CharField(max_length=20, choices=WalletTransactionTypeEnum.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference_id = models.CharField(max_length=120, null=True, blank=True)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Transaction chaining: each record commits to the previous hash, forming a tamper-evident chain.
    previous_hash = models.CharField(max_length=64, default="0" * 64)
    chain_hash = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type'], name='wallet_tx_type_idx'),
        ]

    def __str__(self):
        return f"WalletTx {self.uid} - {self.transaction_type} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.pk:
            update_fields = kwargs.get("update_fields")
            blocked = _WALLET_TX_IMMUTABLE.intersection(set(update_fields)) if update_fields else set()
            if blocked:
                raise ValueError(f"Cannot modify immutable WalletTransaction fields: {blocked}")
        super().save(*args, **kwargs)

    @staticmethod
    def compute_chain_hash(uid, user_id, tx_type, amount, balance_before, balance_after, previous_hash) -> str:
        msg = f"{uid}:{user_id}:{tx_type}:{amount}:{balance_before}:{balance_after}:{previous_hash}"
        return _wallet_hmac(msg)

    @classmethod
    def get_last_chain_hash(cls, user_id: int) -> str:
        last = cls.objects.filter(user_id=user_id).order_by("-created_at").values("chain_hash").first()
        return last["chain_hash"] if last and last["chain_hash"] else "0" * 64


class WalletTransactionState(models.Model):
    """Mutable processing state for wallet transactions."""

    wallet_transaction = models.OneToOneField(
        WalletTransaction,
        on_delete=models.CASCADE,
        related_name="state",
    )
    status = models.CharField(
        max_length=20,
        choices=WalletTransactionStatusEnum.choices,
        default=WalletTransactionStatusEnum.PENDING,
    )
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(null=True, blank=True)
    payout_id = models.CharField(max_length=120, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallet_transaction_states"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="wallet_tx_state_status_idx"),
            models.Index(fields=["processed_at"], name="wallet_tx_state_processed_idx"),
        ]

    def __str__(self):
        return f"WalletTxState {self.wallet_transaction_id} - {self.status}"


class WithdrawalFailureLog(models.Model):
    """Audit log for failed wallet withdrawal attempts."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawal_failures")
    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="failure_logs",
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    stage = models.CharField(max_length=40)
    error_type = models.CharField(max_length=120, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wallet_withdrawal_failures"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["stage"]),
        ]

    def __str__(self):
        return f"WithdrawalFailure {self.uid} - {self.user_id} - {self.stage}"


class SettlementRecord(models.Model):
    """
    Tracks settlement for each order after completion.
    Used for both PayOS (escrow release) and COD (cash collected).
    """
    SETTLEMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),  # Order completed, settlement not yet processed
        ('LEDGER_RECORDED', 'Ledger Recorded'),  # Amount recorded in ledger
        ('PAYOUT_SCHEDULED', 'Payout Scheduled'),  # Scheduled for payout
        ('PAYOUT_PROCESSED', 'Payout Processed'),  # Payout initiated to chef
        ('PAYOUT_COMPLETED', 'Payout Completed'),  # Payout confirmed complete
        ('PAYOUT_FAILED', 'Payout Failed'),  # Payout failed
    ]
    
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='settlement_record'
    )
    chef = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settlement_records'
    )
    
    # Amount breakdown
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    chef_payout_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Settlement status
    status = models.CharField(
        max_length=20,
        choices=SETTLEMENT_STATUS_CHOICES,
        default='PENDING'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodEnum.choices,
        default=PaymentMethodEnum.COD
    )
    
    # Payout info
    payout_id = models.CharField(max_length=100, null=True, blank=True)  # PayOS payout ID or internal reference
    payout_reference = models.CharField(max_length=100, null=True, blank=True)
    
    # Settlement metadata
    settlement_data = models.JSONField(null=True, blank=True)  # Store payout details like bank info, approval state
    error_reason = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settled_at = models.DateTimeField(null=True, blank=True)  # When payout was completed
    
    class Meta:
        db_table = 'settlement_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chef', 'status']),
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Settlement {self.uid} - Order {self.order.uid} - {self.status}"


class PayoutLedger(models.Model):
    """
    Accounting ledger for platform revenue and chef payouts.
    Tracks all financial transactions for auditing and reporting.
    """
    LEDGER_TYPE_CHOICES = [
        ('CHEF_PAYOUT', 'Chef Payout'),  # Money going out to chef
        ('PLATFORM_REVENUE', 'Platform Revenue'),  # Platform commission earned
        ('PAYOUT_REVERSAL', 'Payout Reversal'),  # Reversal/refund
    ]
    
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    settlement_record = models.ForeignKey(
        SettlementRecord,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    
    # Ledger details
    ledger_type = models.CharField(
        max_length=20,
        choices=LEDGER_TYPE_CHOICES
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    
    # Reference info
    order_uid = models.CharField(max_length=100)
    chef_id = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payout_ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ledger_type', 'created_at']),
            models.Index(fields=['chef_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"Ledger {self.uid} - {self.ledger_type} - {self.amount}"


class ChefCODBalance(models.Model):
    """
    Tracks unsettled COD balance for each chef.
    COD money is collected directly from customer, then settled to chef.
    """
    chef = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cod_balance'
    )
    
    # COD balance tracking
    unsettled_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total COD money collected but not yet settled"
    )
    unsettled_orders_count = models.IntegerField(
        default=0,
        help_text="Number of COD orders awaiting settlement"
    )
    total_settled = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total COD money settled to chef"
    )
    
    # Last settlement
    last_settlement_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chef_cod_balance'
    
    def __str__(self):
        return f"COD Balance - Chef {self.chef.email} - {self.unsettled_balance} VND"
