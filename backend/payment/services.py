from __future__ import annotations

"""
Payment Service
Handles payment transaction logic for PayOS integration
"""
from uuid import UUID
from decimal import Decimal
from decimal import ROUND_HALF_UP
from django.utils import timezone
from django.conf import settings
import threading
import time
import hashlib
from django.db import models
import logging

from payment.models import (
    CustomerPaymentInfo,
    InternalWallet,
    PaymentTransaction,
    PaymentTransactionEvent,
    PaymentTransactionState,
    PaymentStatus,
    SettlementRecord,
    WalletTransaction,
    WalletTransactionState,
    WithdrawalFailureLog,
)
from payment.providers.payos import PayOSPaymentProvider
from order.models import Checkout, Order
from utils.enums import PaymentMethodEnum, OrderStatusEnum
from utils.enums import WalletTransactionStatusEnum, WalletTransactionTypeEnum
from order.models import Order
from profile.orm.chef_payment import ChefPaymentInfoORM
import uuid
from voucher.models import AppliedVoucher
from utils.enums import VoucherReservationStatus
from typing import Optional

class PaymentService:
    """Service for handling payment transactions"""

    PLATFORM_FEE_PERCENT = Decimal("0.10")

    def __init__(self):
        self.payos_provider = PayOSPaymentProvider()
        from utils.services.email.client import EmailClient
        from utils.services.email.template import EmailTemplate
        self.email_client = EmailClient()
        self.email_template = EmailTemplate()
        self.logger = logging.getLogger(__name__)

        self._allowed_transitions = {
            PaymentStatus.PENDING: {
                PaymentStatus.HOLDING,
                PaymentStatus.SUCCESS,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED,
            },
            PaymentStatus.HOLDING: {
                PaymentStatus.RELEASED,
                PaymentStatus.REFUND_PENDING,
                PaymentStatus.REFUNDED,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED,
            },
            PaymentStatus.SUCCESS: {
                PaymentStatus.REFUND_PENDING,
                PaymentStatus.REFUNDED,
                PaymentStatus.CANCELLED,
            },
            PaymentStatus.REFUND_PENDING: {
                PaymentStatus.REFUNDED,
                PaymentStatus.CANCELLED,
            },
            PaymentStatus.RELEASED: {
                PaymentStatus.REFUND_PENDING,
                PaymentStatus.REFUNDED,
            },
            PaymentStatus.FAILED: set(),
            PaymentStatus.CANCELLED: set(),
            PaymentStatus.REFUNDED: set(),
        }

    def _ensure_payment_state(
        self,
        payment: PaymentTransaction,
        status: str = PaymentStatus.PENDING,
        paid_at=None,
        gateway_response: dict | None = None,
    ) -> PaymentTransactionState:
        state, created = PaymentTransactionState.objects.get_or_create(
            payment_transaction=payment,
            defaults={
                "status": status,
                "paid_at": paid_at,
                "gateway_response": gateway_response,
            },
        )
        if created:
            self._record_payment_event(
                payment=payment,
                event_type="STATE_INIT",
                status_from=None,
                status_to=state.status,
                payload=gateway_response,
                signature_valid=None,
                source="system",
            )
        return state

    def _record_payment_event(
        self,
        payment: PaymentTransaction,
        event_type: str,
        status_from: str | None,
        status_to: str | None,
        payload: dict | None,
        signature_valid: bool | None,
        source: str,
    ) -> PaymentTransactionEvent:
        previous_hash = PaymentTransactionEvent.get_last_chain_hash(payment.id)
        chain_hash = PaymentTransactionEvent.compute_chain_hash(
            payment_id=payment.id,
            event_type=event_type,
            status_from=status_from,
            status_to=status_to,
            previous_hash=previous_hash,
        )
        return PaymentTransactionEvent.objects.create(
            payment_transaction=payment,
            event_type=event_type,
            status_from=status_from,
            status_to=status_to,
            payload=payload,
            signature_valid=signature_valid,
            source=source,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
        )

    def _transition_payment_state(
        self,
        payment: PaymentTransaction,
        new_status: str,
        reason: str | None = None,
        gateway_payload: dict | None = None,
        source: str = "system",
        signature_valid: bool | None = None,
        paid_at=None,
        allow_same: bool = True,
    ) -> PaymentTransactionState:
        state = self._ensure_payment_state(payment)
        old_status = state.status

        if new_status == old_status and allow_same:
            self._record_payment_event(
                payment=payment,
                event_type="STATE_NOOP",
                status_from=old_status,
                status_to=new_status,
                payload={
                    "reason": reason,
                    "gateway_payload": gateway_payload,
                },
                signature_valid=signature_valid,
                source=source,
            )
            return state

        allowed = self._allowed_transitions.get(old_status, set())
        if new_status not in allowed:
            self._record_payment_event(
                payment=payment,
                event_type="STATE_REJECTED",
                status_from=old_status,
                status_to=new_status,
                payload={
                    "reason": reason,
                    "gateway_payload": gateway_payload,
                },
                signature_valid=signature_valid,
                source=source,
            )
            raise ValueError(f"Invalid payment status transition: {old_status} -> {new_status}")

        state.status = new_status
        if paid_at is not None:
            state.paid_at = paid_at
        if gateway_payload is not None:
            state.gateway_response = gateway_payload
        state.save(update_fields=["status", "paid_at", "gateway_response", "updated_at"])

        self._record_payment_event(
            payment=payment,
            event_type="STATE_CHANGED",
            status_from=old_status,
            status_to=new_status,
            payload={
                "reason": reason,
                "gateway_payload": gateway_payload,
            },
            signature_valid=signature_valid,
            source=source,
        )

        return state

    def set_payment_state(
        self,
        payment: PaymentTransaction,
        new_status: str,
        reason: str | None = None,
        gateway_payload: dict | None = None,
        source: str = "system",
        paid_at=None,
    ) -> PaymentTransactionState:
        return self._transition_payment_state(
            payment=payment,
            new_status=new_status,
            reason=reason,
            gateway_payload=gateway_payload,
            source=source,
            paid_at=paid_at,
        )

    def assert_payment_confirmed(
        self,
        payment: PaymentTransaction,
        reconcile_with_gateway: bool = False,
    ) -> None:
        """
        Enforce 3-layer payment validity before any payout or refund.

        Layer 1 — operational state: status must be a confirmed terminal.
        Layer 2 — audit evidence: at least one signature-verified event must exist.
        Layer 3 — chain integrity: recompute every HMAC in the event chain.
        Layer 4 (opt) — gateway reconciliation: cross-check live with PayOS API.

        Raises ValueError describing which layer failed.
        """
        state = self._ensure_payment_state(payment)

        confirmed = {
            PaymentStatus.HOLDING,
            PaymentStatus.SUCCESS,
            PaymentStatus.REFUND_PENDING,
            PaymentStatus.REFUNDED,
        }
        if state.status not in confirmed:
            raise ValueError(
                f"Payment {payment.uid} not confirmed: status={state.status}"
            )

        has_webhook_verified = payment.events.filter(signature_valid=True).exists()
        has_reconciled = payment.events.filter(event_type="RECONCILIATION_CONFIRMED").exists()
        is_cod = payment.payment_method == PaymentMethodEnum.COD
        if not (has_webhook_verified or has_reconciled or is_cod):
            raise ValueError(
                f"Payment {payment.uid} has no audit evidence of confirmation "
                f"(no webhook signature nor reconciliation event)"
            )

        chain = PaymentTransactionEvent.verify_event_chain(payment.id)
        if not chain["valid"]:
            raise ValueError(
                f"Payment {payment.uid} audit chain tampered at event_id={chain['tampered_at']} "
                f"({chain.get('reason')})"
            )

        if reconcile_with_gateway and payment.payos_order_code:
            info = self.payos_provider.get_payment_info(payment.payos_order_code)
            if not info.get("success") or info.get("status") not in {"PAID"}:
                raise ValueError(
                    f"Payment {payment.uid} gateway reconciliation failed: "
                    f"gateway_status={info.get('status')}"
                )

    def _record_withdrawal_failure(
        self,
        user,
        amount: Decimal,
        stage: str,
        error: Exception | str,
        wallet_tx: WalletTransaction | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            error_message = str(error)
            error_type = type(error).__name__ if isinstance(error, Exception) else "Error"
            WithdrawalFailureLog.objects.create(
                user=user,
                wallet_transaction=wallet_tx,
                amount=self._quantize_amount(amount),
                stage=stage,
                error_type=error_type,
                error_message=error_message,
                metadata=metadata or {},
            )
        except Exception as exc:
            self.logger.error("Failed to record withdrawal failure: %s", exc, exc_info=True)

    def _send_withdraw_failure_email(
        self,
        user,
        amount: Decimal,
        reference_id: str,
        reason: str,
    ) -> None:
        try:
            template = self.email_template.send_withdraw_failed_email(
                user=user,
                amount=f"{int(self._quantize_amount(amount)):,}",
                reference_id=reference_id,
                reason=reason,
            )
            self.email_client.send(messages=[template])
        except Exception as exc:
            self.logger.error("Failed to send withdrawal failure email: %s", exc, exc_info=True)

    def _should_retry_payout(self, payout_result: dict, attempt: int, max_attempts: int) -> bool:
        if attempt >= max_attempts:
            return False
        status_code = payout_result.get("status_code")
        error = str(payout_result.get("error", "")).lower()
        if status_code in {408, 429, 500, 502, 503, 504}:
            return True
        if any(token in error for token in ["timeout", "temporarily", "connection", "rate limit"]):
            return True
        return False

    def _create_payout_with_retry(self, **kwargs) -> dict:
        max_attempts = 3
        backoff_seconds = 0.6
        last_result: dict | None = None

        for attempt in range(1, max_attempts + 1):
            result = self.payos_provider.create_payout(**kwargs)
            last_result = result
            if result.get("success"):
                return result
            if not self._should_retry_payout(result, attempt, max_attempts):
                return result
            time.sleep(backoff_seconds)
            backoff_seconds *= 2

        return last_result or {"success": False, "error": "Payout failed"}

    def _get_user_bank_info(self, user):
        customer_info = getattr(user, 'customer_payment_info', None)
        if customer_info:
            return customer_info
        chef_info = getattr(user, 'chef_payment_info', None)
        if chef_info:
            return chef_info
        return None

    def _mask_account_number(self, account_number: str) -> str:
        if not account_number:
            return ""
        if len(account_number) <= 4:
            return account_number
        return "*" * (len(account_number) - 4) + account_number[-4:]

    def get_or_create_internal_wallet(self, user):
        wallet, _ = InternalWallet.objects.get_or_create(user=user)
        return wallet

    def get_internal_wallet_summary(self, user) -> dict:
        wallet = self.get_or_create_internal_wallet(user)
        recent_transactions = list(
            WalletTransaction.objects.filter(user=user)
            .select_related('order', 'state')
            .order_by('-created_at')[:10]
        )
        return {
            'wallet_uid': wallet.uid if hasattr(wallet, 'uid') else None,
            'user_id': user.id,
            'balance': wallet.balance,
            'pending_balance': wallet.pending_balance,
            'total_balance': wallet.balance + wallet.pending_balance,
            'currency': wallet.currency,
            'recent_transactions': [
                {
                    'uid': tx.uid,
                    'transaction_type': tx.transaction_type,
                    'status': tx.state.status if getattr(tx, 'state', None) else WalletTransactionStatusEnum.PENDING,
                    'amount': tx.amount,
                    'reference_id': tx.reference_id,
                    'description': tx.state.description if getattr(tx, 'state', None) else None,
                    'balance_before': tx.balance_before,
                    'balance_after': tx.balance_after,
                    'payout_id': tx.state.payout_id if getattr(tx, 'state', None) else None,
                    'order_uid': tx.order.uid if tx.order else None,
                    'created_at': tx.created_at,
                    'processed_at': tx.state.processed_at if getattr(tx, 'state', None) else None,
                }
                for tx in recent_transactions
            ],
        }

    def credit_internal_wallet(
        self,
        user,
        amount: Decimal,
        transaction_type: str,
        order: Order | None = None,
        reference_id: str | None = None,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> WalletTransaction:
        amount = self._quantize_amount(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            wallet = InternalWallet.objects.select_for_update().get_or_create(user=user)[0]
            balance_before = wallet.balance
            wallet.balance = self._quantize_amount(wallet.balance + amount)

            tx_uid = uuid.uuid4()
            previous_hash = WalletTransaction.get_last_chain_hash(user.id)
            chain_hash = WalletTransaction.compute_chain_hash(
                uid=tx_uid,
                user_id=user.id,
                tx_type=transaction_type,
                amount=str(amount),
                balance_before=str(balance_before),
                balance_after=str(wallet.balance),
                previous_hash=previous_hash,
            )

            wallet.signature = wallet.compute_signature()
            wallet.save(update_fields=['balance', 'signature', 'updated_at'])

            tx = WalletTransaction.objects.create(
                uid=tx_uid,
                user=user,
                order=order,
                transaction_type=transaction_type,
                amount=amount,
                reference_id=reference_id,
                balance_before=balance_before,
                balance_after=wallet.balance,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
            )
            WalletTransactionState.objects.create(
                wallet_transaction=tx,
                status=WalletTransactionStatusEnum.SUCCESS,
                description=description or '',
                metadata=metadata,
                processed_at=timezone.now(),
            )

        return tx

    def create_or_update_customer_payment_info(self, user, payload):
        info, _ = CustomerPaymentInfo.objects.get_or_create(user=user)
        info.bank_name = payload.bank_name
        info.bank_code = payload.bank_code
        info.bank_account_number = payload.bank_account_number
        info.bank_account_name = payload.bank_account_name
        info.bank_branch = payload.bank_branch
        info.is_verified = True
        info.verified_at = timezone.now()
        info.save()
        return info

    def get_customer_payment_info(self, user):
        return CustomerPaymentInfo.objects.filter(user=user).first()

    # ========== Bank info OTP methods ==========

    def request_bank_verify_otp(self, user, payload) -> dict:
        """Save/update bank info (is_verified=False) then send OTP to email."""
        from users.queries import Query as UserQuery

        info, _ = CustomerPaymentInfo.objects.get_or_create(user=user)
        info.bank_name = payload.bank_name
        info.bank_code = payload.bank_code
        info.bank_account_number = payload.bank_account_number
        info.bank_account_name = payload.bank_account_name
        info.bank_branch = payload.bank_branch
        info.is_verified = False
        info.verified_at = None
        info.save()

        UserQuery.inactive_otp_token(user)
        otp_record, plain_otp = UserQuery.create_otp(user=user, purpose="BANK_VERIFY")

        template = self.email_template.send_verification_email(
            user=user, otp=plain_otp, purpose="BANK_VERIFY"
        )
        self.email_client.send(messages=[template])

        return {"reset_session_token": otp_record.reset_session_token}

    def verify_bank_info_otp(self, user, reset_session_token: str, otp: str):
        """Verify OTP then mark bank info as verified."""
        from users.queries import Query as UserQuery
        from exceptions.auth import InvalidOrExpiredToken, InvalidOtp

        record = UserQuery.get_otp_record(reset_session_token)

        if not record:
            raise InvalidOrExpiredToken
        if record.otp_verified:
            raise InvalidOtp("OTP already used")
        if record.purpose != "BANK_VERIFY":
            raise InvalidOrExpiredToken
        if record.user_id != user.id:
            raise InvalidOrExpiredToken
        if record.is_expired():
            record.active = False
            record.save(update_fields=["active"])
            raise InvalidOrExpiredToken
        if not record.verify(otp):
            raise InvalidOtp

        record.otp_verified = True
        record.active = False
        record.save(update_fields=["otp_verified", "active"])

        try:
            info = CustomerPaymentInfo.objects.get(user=user)
        except CustomerPaymentInfo.DoesNotExist:
            from ninja.errors import HttpError
            raise HttpError(400, "Bank info not found. Please submit bank info first.")

        info.is_verified = True
        info.verified_at = timezone.now()
        info.save(update_fields=["is_verified", "verified_at", "updated_at"])
        return info

    # ========== Withdraw OTP methods ==========

    def _get_daily_withdrawal_sum(self, user) -> Decimal:
        """Get total withdrawal amount for today (successful payouts only)."""
        from django.utils import timezone
        today = timezone.now().date()
        from datetime import datetime
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        daily_total = WalletTransaction.objects.filter(
            user=user,
            transaction_type=WalletTransactionTypeEnum.PAYOUT,
            state__status=WalletTransactionStatusEnum.SUCCESS,
            state__processed_at__gte=today_start,
            state__processed_at__lte=today_end,
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return self._quantize_amount(daily_total)

    def request_withdraw_otp(self, user, amount: Decimal) -> dict:
        """Validate withdrawal eligibility then send OTP to email."""
        from users.queries import Query as UserQuery
        from ninja.errors import HttpError

        amount = self._quantize_amount(amount)
        MIN_WITHDRAWAL = Decimal('10000')
        MAX_DAILY_WITHDRAWAL = Decimal('20000000')
        
        if amount <= 0:
            raise HttpError(400, "Withdrawal amount must be greater than zero")
        if amount < MIN_WITHDRAWAL:
            raise HttpError(400, f"Minimum withdrawal amount is {int(MIN_WITHDRAWAL):,} VND")
        
        # Check daily limit
        daily_withdrawn = self._get_daily_withdrawal_sum(user)
        remaining_daily = MAX_DAILY_WITHDRAWAL - daily_withdrawn
        if amount > remaining_daily:
            raise HttpError(400, f"Daily withdrawal limit exceeded. Remaining today: {int(remaining_daily):,} VND")

        bank_info = self._get_user_bank_info(user)
        if not bank_info:
            raise HttpError(400, "Bank information not found. Please add bank information first.")
        if hasattr(bank_info, "is_verified") and not bank_info.is_verified:
            raise HttpError(400, "Bank information is not verified")

        wallet = self.get_or_create_internal_wallet(user)
        integrity = wallet.verify_integrity()
        if (
            not integrity.get("signature_valid")
            or not integrity.get("balance_matches_ledger")
            or not integrity.get("chain_intact")
        ):
            import logging
            logging.getLogger("django").error(
                "Wallet integrity violation user=%s sig=%s ledger=%s chain=%s break_at=%s reason=%s",
                user.id,
                integrity.get("signature_valid"),
                integrity.get("balance_matches_ledger"),
                integrity.get("chain_intact"),
                integrity.get("chain_break_at"),
                integrity.get("chain_break_reason"),
            )
            raise HttpError(400, "Wallet integrity check failed")
        if wallet.balance < amount:
            raise HttpError(400, "Insufficient internal wallet balance")

        UserQuery.inactive_otp_token(user)
        otp_record, plain_otp = UserQuery.create_otp(user=user, purpose="WITHDRAW_VERIFY", target_email=str(amount))

        template = self.email_template.send_verification_email(
            user=user, otp=plain_otp, purpose="WITHDRAW_VERIFY"
        )
        self.email_client.send(messages=[template])

        return {"reset_session_token": otp_record.reset_session_token}

    def confirm_withdraw_with_otp(self, user, reset_session_token: str, otp: str) -> dict:
        """Verify OTP then execute the withdrawal."""
        from users.queries import Query as UserQuery
        from exceptions.auth import InvalidOrExpiredToken, InvalidOtp
        from decimal import Decimal as D
        from decimal import InvalidOperation

        record = UserQuery.get_otp_record(reset_session_token)

        if not record:
            raise InvalidOrExpiredToken
        if record.otp_verified:
            raise InvalidOtp("OTP already used")
        if record.purpose != "WITHDRAW_VERIFY":
            raise InvalidOrExpiredToken
        if record.user_id != user.id:
            raise InvalidOrExpiredToken
        if record.is_expired():
            record.active = False
            record.save(update_fields=["active"])
            raise InvalidOrExpiredToken
        if not record.verify(otp):
            raise InvalidOtp

        # Amount was saved when OTP was requested; confirm step should not require client to resend it.
        try:
            stored_amount = self._quantize_amount(D(record.target_email))
        except (TypeError, InvalidOperation):
            raise InvalidOrExpiredToken

        record.otp_verified = True
        record.active = False
        record.save(update_fields=["otp_verified", "active"])

        result = self.withdraw_internal_wallet(user, stored_amount)
        if "amount" not in result:
            result["amount"] = float(stored_amount)
        return result

    def withdraw_internal_wallet(self, user, amount: Decimal) -> dict:
        amount = self._quantize_amount(amount)
        if amount <= 0:
            return {'success': False, 'error': 'Withdrawal amount must be greater than zero'}

        bank_info = self._get_user_bank_info(user)
        if not bank_info:
            return {'success': False, 'error': 'Bank information not found. Please add bank information first.'}
        if hasattr(bank_info, 'is_verified') and not bank_info.is_verified:
            return {'success': False, 'error': 'Bank information is not verified'}

        from django.db import transaction as db_transaction

        reference_id = f"wallet_withdraw_{user.id}_{int(timezone.now().timestamp())}"
        idempotency_key = str(uuid.uuid4())
        wallet_tx: WalletTransaction | None = None
        wallet_tx_state: WalletTransactionState | None = None

        bank_metadata = {
            'bank_name': getattr(bank_info, 'bank_name', None),
            'bank_code': getattr(bank_info, 'bank_code', None),
            'bank_account_number': getattr(bank_info, 'bank_account_number', None),
            'bank_account_name': getattr(bank_info, 'bank_account_name', None),
            'bank_branch': getattr(bank_info, 'bank_branch', None),
        }

        try:
            with db_transaction.atomic():
                wallet = InternalWallet.objects.select_for_update().get_or_create(user=user)[0]
                integrity = wallet.verify_integrity()
                if not integrity.get("signature_valid") or not integrity.get("balance_matches_ledger"):
                    return {
                        'success': False,
                        'error': 'Wallet integrity check failed',
                        'status': 'FAILED',
                    }
                if wallet.balance < amount:
                    return {'success': False, 'error': 'Insufficient internal wallet balance'}

                balance_before = wallet.balance
                wallet.balance = self._quantize_amount(wallet.balance - amount)
                wallet.pending_balance = self._quantize_amount(wallet.pending_balance + amount)

                tx_uid = uuid.uuid4()
                previous_hash = WalletTransaction.get_last_chain_hash(user.id)
                chain_hash = WalletTransaction.compute_chain_hash(
                    uid=tx_uid,
                    user_id=user.id,
                    tx_type=WalletTransactionTypeEnum.PAYOUT,
                    amount=str(amount),
                    balance_before=str(balance_before),
                    balance_after=str(wallet.balance),
                    previous_hash=previous_hash,
                )

                wallet.signature = wallet.compute_signature()
                wallet.save(update_fields=['balance', 'pending_balance', 'signature', 'updated_at'])

                wallet_tx = WalletTransaction.objects.create(
                    uid=tx_uid,
                    user=user,
                    transaction_type=WalletTransactionTypeEnum.PAYOUT,
                    amount=amount,
                    reference_id=reference_id,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    previous_hash=previous_hash,
                    chain_hash=chain_hash,
                )
                wallet_tx_state = WalletTransactionState.objects.create(
                    wallet_transaction=wallet_tx,
                    status=WalletTransactionStatusEnum.PENDING,
                    description='Wallet withdrawal request',
                    metadata=bank_metadata,
                )

                payout_result = self._create_payout_with_retry(
                    reference_id=reference_id,
                    amount=int(amount),
                    description='Wallet withdrawal',
                    to_bin=getattr(bank_info, 'bank_code', None),
                    to_account_number=getattr(bank_info, 'bank_account_number', None),
                    idempotency_key=idempotency_key,
                    category=['wallet_withdrawal'],
                )

                if not payout_result.get('success'):
                    wallet.balance = self._quantize_amount(wallet.balance + amount)
                    wallet.pending_balance = self._quantize_amount(wallet.pending_balance - amount)
                    wallet.signature = wallet.compute_signature()
                    wallet.save(update_fields=['balance', 'pending_balance', 'signature', 'updated_at'])
                    if wallet_tx_state:
                        wallet_tx_state.status = WalletTransactionStatusEnum.FAILED
                        wallet_tx_state.description = payout_result.get('error', 'Payout failed')
                        wallet_tx_state.metadata = {**(wallet_tx_state.metadata or {}), 'payout_result': payout_result}
                        wallet_tx_state.save(update_fields=['status', 'description', 'metadata', 'updated_at'])

                    self._record_withdrawal_failure(
                        user=user,
                        amount=amount,
                        stage='PAYOUT_FAILED',
                        error=payout_result.get('error', 'Payout failed'),
                        wallet_tx=wallet_tx,
                        metadata={
                            'reference_id': reference_id,
                            'payout_result': payout_result,
                            'bank_account': self._mask_account_number(getattr(bank_info, 'bank_account_number', '')),
                        },
                    )
                    self._send_withdraw_failure_email(
                        user=user,
                        amount=amount,
                        reference_id=reference_id,
                        reason=payout_result.get('error', 'Payout failed'),
                    )

                    return {
                        'success': False,
                        'error': payout_result.get('error', 'Failed to create payout'),
                        'status': 'FAILED',
                        'reference_id': reference_id,
                    }

                wallet.pending_balance = self._quantize_amount(wallet.pending_balance - amount)
                wallet.save(update_fields=['pending_balance', 'updated_at'])
                if wallet_tx_state:
                    wallet_tx_state.status = WalletTransactionStatusEnum.SUCCESS
                    wallet_tx_state.payout_id = payout_result.get('payout_id')
                    wallet_tx_state.metadata = {**(wallet_tx_state.metadata or {}), 'payout_result': payout_result}
                    wallet_tx_state.processed_at = timezone.now()
                    wallet_tx_state.save(update_fields=['status', 'payout_id', 'metadata', 'processed_at', 'updated_at'])

                return {
                    'success': True,
                    'message': 'Withdrawal processed successfully',
                    'status': 'SUCCESS',
                    'payout_id': payout_result.get('payout_id'),
                    'reference_id': reference_id,
                    'amount': float(amount),
                    'bank_account': f"{getattr(bank_info, 'bank_name', '')} - {self._mask_account_number(getattr(bank_info, 'bank_account_number', ''))}",
                }
        except Exception as exc:
            self._record_withdrawal_failure(
                user=user,
                amount=amount,
                stage='EXCEPTION',
                error=exc,
                wallet_tx=wallet_tx,
                metadata={
                    'reference_id': reference_id,
                    'bank_account': self._mask_account_number(getattr(bank_info, 'bank_account_number', '')),
                },
            )
            self._send_withdraw_failure_email(
                user=user,
                amount=amount,
                reference_id=reference_id,
                reason='Unexpected error while processing withdrawal',
            )
            self.logger.error("Withdrawal failed: %s", exc, exc_info=True)
            return {
                'success': False,
                'error': 'Withdrawal failed. Please try again later.',
                'status': 'FAILED',
                'reference_id': reference_id,
            }

    def _quantize_amount(self, amount: Decimal | int | float) -> Decimal:
        """Normalize VND amounts to whole units."""
        return Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def _cancel_orders_for_payment(self, payment: PaymentTransaction, reason: str, gateway_payload: dict | None = None) -> None:
        from django.db import transaction as db_transaction
        from dish.orm.dish import DishORM
        from order.models import Order

        dish_orm = DishORM()
        orders = list(
            Order.objects.select_related("checkout")
            .prefetch_related("orderitem_fk_order__dish")
            .filter(checkout=payment.checkout)
        )

        if not orders:
            return

        with db_transaction.atomic():
            AppliedVoucher.objects.filter(
                models.Q(checkout=payment.checkout) | models.Q(order__in=orders),
                status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED],
            ).update(status=VoucherReservationStatus.CANCELLED)

            for order in orders:
                if order.status == OrderStatusEnum.CANCELLED:
                    continue

                for item in order.orderitem_fk_order.all():
                    dish_orm.increase_quantity(
                        dish=item.dish,
                        available_date=order.checkout.delivery_date,
                        quantity=item.quantity,
                    )

                state = self._ensure_payment_state(payment)
                order.status = OrderStatusEnum.CANCELLED
                order.payment_status = state.status
                order.save(update_fields=["status", "payment_status", "updated_at"])

            self.logger.info(
                "[Payment] Cancelled orders for payment %s. Reason: %s", payment.uid, reason
            )

    def _get_checkout_orders(self, checkout: Checkout):
        return Order.objects.filter(checkout=checkout).select_related(
            "chef",
            "checkout",
            "checkout__delivery_address",
        ).prefetch_related("orderitem_fk_order__dish").order_by("created_at")

    def _build_checkout_split_summary(self, checkout: Checkout) -> dict:
        """Build payout split plan for every chef in a checkout."""
        orders = list(self._get_checkout_orders(checkout))
        split_items: list[dict] = []
        total_gross = Decimal("0")
        total_platform_fee = Decimal("0")
        total_chef_payout = Decimal("0")

        for order in orders:
            order_gross = self._quantize_amount(order.total_price or Decimal("0"))
            platform_fee = self._quantize_amount(order_gross * self.PLATFORM_FEE_PERCENT)
            chef_payout = self._quantize_amount(order_gross - platform_fee)

            total_gross += order_gross
            total_platform_fee += platform_fee
            total_chef_payout += chef_payout

            split_items.append(
                {
                    "order_uid": str(order.uid),
                    "chef_id": order.chef.id if order.chef else None,
                    "chef_name": order.chef.get_full_name() if order.chef else None,
                    "chef_email": order.chef.email if order.chef else None,
                    "gross_amount": float(order_gross),
                    "platform_fee_percent": float(self.PLATFORM_FEE_PERCENT),
                    "platform_fee_amount": float(platform_fee),
                    "chef_payout_amount": float(chef_payout),
                    "status": "PLANNED",
                }
            )

        return {
            "checkout_uid": str(checkout.uid),
            "order_count": len(orders),
            "chef_count": len({item["chef_id"] for item in split_items if item["chef_id"] is not None}),
            "gross_amount": float(total_gross),
            "platform_fee_amount": float(total_platform_fee),
            "chef_payout_amount": float(total_chef_payout),
            "split_items": split_items,
            "created_at": timezone.now().isoformat(),
        }

    def _sync_successful_payment(self, payment: PaymentTransaction, gateway_payload: dict | None, source: str) -> dict:
        """Persist payment success, confirm orders, and store settlement split plan."""
        # import time
        # from datetime import datetime
        
        # sync_start = time.time()
        
        state = self._ensure_payment_state(payment)
        if state.status != PaymentStatus.HOLDING:
            self._transition_payment_state(
                payment,
                PaymentStatus.HOLDING,
                reason="payos_confirmed",
                gateway_payload=gateway_payload,
                source=source,
                paid_at=timezone.now(),
            )
        elif gateway_payload is not None:
            state.gateway_response = gateway_payload
            state.save(update_fields=["gateway_response", "updated_at"])

        orders = self._get_checkout_orders(payment.checkout)
        
        # 📊 [PERFORMANCE MEASUREMENT] T2 Update happens here
        # t2_update_start = time.time()
        orders.update(status=OrderStatusEnum.CONFIRMED_SYSTEM, payment_status=PaymentStatus.HOLDING)
        # t2_update_end = time.time()

        updated_count = AppliedVoucher.objects.filter(
            checkout=payment.checkout,
            status=VoucherReservationStatus.RESERVED,
        ).update(
            status=VoucherReservationStatus.USED,
            reservation_expires_at=None,
        )

        split_summary = self._build_checkout_split_summary(payment.checkout)
        state = self._ensure_payment_state(payment)
        gateway_response = state.gateway_response or {}
        settlement = gateway_response.get("settlement", {}) if isinstance(gateway_response, dict) else {}
        settlement.update(
            {
                "status": "HOLDING",
                "source": source,
                "split_summary": split_summary,
                "updated_at": timezone.now().isoformat(),
            }
        )
        gateway_response["settlement"] = settlement
        state.gateway_response = gateway_response
        state.save(update_fields=["gateway_response", "updated_at"])

        # 📊 [PERFORMANCE MEASUREMENT] Calculate total time
        # t2_process_end = time.time()
        
        # if t2_webhook_received is not None:
        #     total_confirmation_time = t2_process_end - t2_webhook_received
        # else:
        #     total_confirmation_time = 0
        
        # order_update_time = t2_update_end - t2_update_start
        # print("\n" + "="*80)
        # print("🕐 [PAYOS WEBHOOK] ===== PERFORMANCE MEASUREMENT COMPLETE =====")
        # print(f"T2 (Backend receives webhook): {datetime.utcnow().isoformat()}")
        # print(f"T2 + Order Update: {datetime.utcnow().isoformat()}")
        # print(f"⏱️  Order Update Duration: {order_update_time*1000:.2f} ms")
        # print(f"⏱️  Total Backend Processing Time: {total_confirmation_time*1000:.2f} ms (from T2 to Order CONFIRMED_SYSTEM)")
        # print(f"✅ Payment {payment.uid} confirmed and held in escrow")
        # print(f"✅ {orders.count()} order(s) moved to CONFIRMED_SYSTEM")
        # print(f"✅ {updated_count} voucher(s) marked as USED")
        # print(f"✅ Split planned for {split_summary['chef_count']} chef(s)")
        # print("="*80 + "\n")

        # print(
        #     f"[Payment] Payment {payment.uid} confirmed and held in escrow, orders moved to CONFIRMED_SYSTEM, "
        #     f"vouchers USED={updated_count}, split planned for {split_summary['chef_count']} chef(s)"
        # )

        return {
            "orders_count": orders.count(),
            "vouchers_used": updated_count,
            "split_summary": split_summary,
        }
    
    def create_payment(
        self,
        checkout_uid: UUID,
        payment_method: str,
        bank_code: str | None = None,
        language: str | None = None
    ) -> PaymentTransaction:
        """
        Create payment transaction and get payment URL
        
        Args:
            checkout_uid: UUID of checkout
            payment_method: PAYOS or COD
            bank_code: Not used (kept for backward compatibility)
            language: vn or en
            
        Returns:
            PaymentTransaction instance with payment_url
        """
        # Get checkout
        try:
            checkout = Checkout.objects.get(uid=checkout_uid)
        except Checkout.DoesNotExist:
            raise ValueError(f"Checkout {checkout_uid} not found")
        
        # Check if payment already exists
        if hasattr(checkout, 'payment_transaction'):
            payment = checkout.payment_transaction
            state = self._ensure_payment_state(payment)
            if state.status == PaymentStatus.SUCCESS:
                raise ValueError("Payment already completed")
            if state.status in [PaymentStatus.FAILED, PaymentStatus.PENDING]:
                payment.delete()
        
        # Generate payment URL based on method
        if payment_method == PaymentMethodEnum.PAYOS:
            payment_uid = uuid.uuid4()
            order_code = self._generate_order_code(payment_uid)

            try:
                payment_data = self.payos_provider.create_payment(
                    order_code=order_code,
                    amount=int(checkout.total_price),
                    description=f"DH {order_code}",
                    buyer_name=None,
                    buyer_email=None,
                    buyer_phone=None,
                )

                print(f"[PayOS] Payment data: {payment_data}")

                payment = PaymentTransaction.objects.create(
                    uid=payment_uid,
                    checkout=checkout,
                    payment_method=payment_method,
                    amount=checkout.total_price,
                    payos_order_code=order_code,
                )
                state = self._ensure_payment_state(
                    payment,
                    status=PaymentStatus.PENDING,
                    gateway_response=payment_data,
                )
                if payment_data.get("success"):
                    payment_link_id = payment_data.get("payment_link_id")
                    checkout_url = payment_data.get("checkout_url", "")
                    # Fallback: extract from URL if provider didn't return payment_link_id directly
                    if not payment_link_id and "/web/" in checkout_url:
                        payment_link_id = checkout_url.split("/web/")[-1]
                    state.payment_url = checkout_url
                    state.payos_payment_link_id = payment_link_id
                    state.transaction_id = payment_link_id
                    state.save(update_fields=["payment_url", "payos_payment_link_id", "transaction_id", "updated_at"])
                self._record_payment_event(
                    payment=payment,
                    event_type="PAYOS_CREATE",
                    status_from=state.status,
                    status_to=state.status,
                    payload=payment_data,
                    signature_valid=None,
                    source="payos_create",
                )

                if not payment_data.get("success"):
                    self._transition_payment_state(
                        payment,
                        PaymentStatus.FAILED,
                        reason=payment_data.get("error"),
                        gateway_payload=payment_data,
                        source="payos_create",
                    )
                    raise ValueError(f"Failed to create PayOS payment: {payment_data.get('error')}")
            except Exception as e:
                print(f"[PayOS] Exception: {str(e)}")
                if "payment" not in locals():
                    payment = PaymentTransaction.objects.create(
                        uid=payment_uid,
                        checkout=checkout,
                        payment_method=payment_method,
                        amount=checkout.total_price,
                        payos_order_code=order_code,
                    )
                    self._ensure_payment_state(payment, status=PaymentStatus.FAILED)
                raise
        
        elif payment_method == PaymentMethodEnum.COD:
            payment = PaymentTransaction.objects.create(
                uid=uuid.uuid4(),
                checkout=checkout,
                payment_method=payment_method,
                amount=checkout.total_price,
            )
            cod_state = self._ensure_payment_state(
                payment,
                status=PaymentStatus.SUCCESS,
                paid_at=timezone.now(),
            )
            cod_state.transaction_id = f"COD-{checkout.uid}"
            cod_state.save(update_fields=["transaction_id", "updated_at"])
        
        return payment
    
    def create_cod_payment(self, checkout_uid: UUID) -> PaymentTransaction:
        """
        Create payment transaction for COD orders
        
        COD payment starts as PENDING and becomes SUCCESS when order is COMPLETED
        (after delivery and cash received)
        
        Args:
            checkout_uid: UUID of checkout
            
        Returns:
            PaymentTransaction instance with PENDING status
        """
        try:
            checkout = Checkout.objects.get(uid=checkout_uid)
        except Checkout.DoesNotExist:
            raise ValueError(f"Checkout {checkout_uid} not found")
        
        # Check if payment already exists
        if hasattr(checkout, 'payment_transaction'):
            payment = checkout.payment_transaction
            return payment
        
        # Create COD payment transaction with PENDING status
        payment = PaymentTransaction.objects.create(
            uid=uuid.uuid4(),
            checkout=checkout,
            payment_method=PaymentMethodEnum.COD,
            amount=checkout.total_price,
        )
        cod_state = self._ensure_payment_state(payment, status=PaymentStatus.PENDING)
        cod_state.transaction_id = f"COD-{checkout.uid}"
        cod_state.save(update_fields=["transaction_id", "updated_at"])
        
        print(f"[COD Payment] Created payment transaction {payment.uid} for checkout {checkout_uid}")
        return payment
    
    def get_payment_status(self, payment_uid: UUID, sync_with_gateway: bool = True):
        """
        Get payment transaction status
        
        Args:
            payment_uid: Payment UUID
            sync_with_gateway: If True, sync with PayOS before returning (default: True)
        """
        try:
            payment = PaymentTransaction.objects.get(uid=payment_uid)
            state = self._ensure_payment_state(payment)
            
            # Sync with PayOS if payment is pending and method is PayOS
            if (
                sync_with_gateway
                and payment.payment_method == PaymentMethodEnum.PAYOS
                and state.status == PaymentStatus.PENDING
                and payment.payos_order_code
            ):
                sync_result = self.sync_payment_by_order_code(payment.payos_order_code)
                if sync_result.get("success") and sync_result.get("status") == PaymentStatus.HOLDING:
                    print(
                        f"[PayOS Sync] Payment {payment_uid} updated to HOLDING, "
                        f"orders to CONFIRMED_SYSTEM, vouchers USED={sync_result['vouchers_used']}, "
                        f"split planned for {sync_result['split_summary']['chef_count']} chef(s)"
                    )
                elif sync_result.get("success") and sync_result.get("status") == PaymentStatus.FAILED:
                    print(f"[PayOS Sync] Payment {payment_uid} updated to FAILED")
            
            return payment
        except PaymentTransaction.DoesNotExist:
            raise ValueError(f"Payment {payment_uid} not found")
    
    def get_payment_info_by_order_code(self, order_code: int) -> dict:
        """
        Get payment information from PayOS by order code
        
        Args:
            order_code: PayOS order code
            
        Returns:
            Dict with payment information
        """
        return self.payos_provider.get_payment_info(order_code)

    def sync_payment_by_order_code(self, order_code: int) -> dict:
        """
        Sync a PayOS payment with the latest gateway state using order code.

        This is used as a fallback for redirect/return flows when the webhook
        is delayed or has not been delivered yet.
        """
        try:
            payment = PaymentTransaction.objects.get(payos_order_code=order_code)
        except PaymentTransaction.DoesNotExist:
            return {
                "success": False,
                "error": f"Payment with order code {order_code} not found"
            }

        if payment.payment_method != PaymentMethodEnum.PAYOS:
            return {
                "success": False,
                "error": "Only PayOS payments can be synced by order code"
            }

        payos_info = self.payos_provider.get_payment_info(order_code)
        if not payos_info.get("success"):
            return payos_info

        payos_status = payos_info.get("status")
        if payos_status == "PAID":
            _pre_sync_state = self._ensure_payment_state(payment)
            # Ghi event riêng biệt để phân biệt reconciliation vs webhook trong audit log.
            # signature_valid=None vì path này xác thực bằng API key PayOS, không phải webhook HMAC.
            self._record_payment_event(
                payment=payment,
                event_type="RECONCILIATION_CONFIRMED",
                status_from=_pre_sync_state.status,
                status_to=PaymentStatus.HOLDING,
                payload={"gateway_status": payos_status, "order_code": order_code},
                signature_valid=None,
                source="payos_return",
            )
            sync_result = self._sync_successful_payment(
                payment=payment,
                gateway_payload=payos_info,
                source="payos_return",
            )
            return {
                "success": True,
                "status": PaymentStatus.HOLDING,
                "payment_uid": str(payment.uid),
                "order_code": order_code,
                "orders_count": sync_result["orders_count"],
                "vouchers_used": sync_result["vouchers_used"],
                "split_summary": sync_result["split_summary"],
            }

        if payos_status in ["CANCELLED", "EXPIRED"]:
            new_status = PaymentStatus.CANCELLED if payos_status == "CANCELLED" else PaymentStatus.FAILED
            self._transition_payment_state(
                payment,
                new_status,
                reason=f"payos_{payos_status.lower()}",
                gateway_payload=payos_info,
                source="payos_return",
            )
            self._cancel_orders_for_payment(
                payment=payment,
                reason=f"PayOS payment {payos_status.lower()}",
                gateway_payload=payos_info,
            )
            return {
                "success": True,
                "status": new_status,
                "payment_uid": str(payment.uid),
                "order_code": order_code,
            }

        state = self._ensure_payment_state(payment)
        return {
            "success": True,
            "status": state.status,
            "payment_uid": str(payment.uid),
            "order_code": order_code,
            "gateway_status": payos_status,
        }
    
    def cancel_payment(self, payment_uid: UUID, reason: str | None = None) -> dict:
        """
        Cancel payment transaction
        
        Args:
            payment_uid: UUID of payment transaction
            reason: Cancellation reason
            
        Returns:
            Dict with cancellation result
        """
        try:
            payment = PaymentTransaction.objects.get(uid=payment_uid)
        except PaymentTransaction.DoesNotExist:
            return {
                "success": False,
                "error": f"Payment {payment_uid} not found"
            }

        state = self._ensure_payment_state(payment)

        state = self._ensure_payment_state(payment)
        
        # Check if payment can be cancelled
        if state.status not in [PaymentStatus.SUCCESS, PaymentStatus.HOLDING, PaymentStatus.REFUND_PENDING]:
            return {
                "success": False,
                "error": "Cannot cancel successful payment"
            }

        if state.status == PaymentStatus.HOLDING:
            self._transition_payment_state(
                payment,
                PaymentStatus.REFUND_PENDING,
                reason="cancel_requested",
                source="cancel_payment",
            )
            return {
                "success": True,
                "status": "REFUND_PENDING",
                "message": "Refund requested while payment is holding"
            }
        
        if state.status == PaymentStatus.CANCELLED:
            return {
                "success": False,
                "error": "Payment already cancelled"
            }
        
        # Cancel via PayOS if it's a PayOS payment
        if payment.payment_method == PaymentMethodEnum.PAYOS and payment.payos_order_code:
            result = self.payos_provider.cancel_payment(
                order_code=payment.payos_order_code,
                reason=reason
            )
            
            if result.get("success"):
                self._transition_payment_state(
                    payment,
                    PaymentStatus.CANCELLED,
                    reason=reason,
                    gateway_payload=result,
                    source="cancel_payment",
                )
                return result
            else:
                return result
        else:
            # For non-PayOS payments, just update status
            self._transition_payment_state(
                payment,
                PaymentStatus.CANCELLED,
                reason=reason,
                source="cancel_payment",
            )
            return {
                "success": True,
                "status": "CANCELLED"
            }
    
    def cancel_payment_with_refund(self, payment_uid: UUID, reason: str | None = None) -> dict:
        """
        Cancel payment and process refund (for successful PayOS payments)
            payment_uid: UUID of payment transaction
            reason: Reason for cancellation/refund
            
        Returns:
            Dict with refund result
        """
        try:
            payment = PaymentTransaction.objects.get(uid=payment_uid)
        except PaymentTransaction.DoesNotExist:
            return {
                "success": False,
                "error": f"Payment {payment_uid} not found"
            }

        state = self._ensure_payment_state(payment)
        # Idempotency guard: skip if already refunded
        if state.status == PaymentStatus.REFUNDED:
            return {"success": True, "skipped": True, "payment_uid": str(payment.uid), "message": "Payment already refunded"}

        # Validate payment can be refunded
        if payment.payment_method != PaymentMethodEnum.PAYOS:
            return {
                "success": False,
                "error": "Only PayOS payments can be refunded"
            }

        if state.status not in [PaymentStatus.SUCCESS, PaymentStatus.HOLDING, PaymentStatus.REFUND_PENDING]:
            return {
                "success": False,
                "error": f"Cannot refund payment with status: {state.status}"
            }
        
        if not payment.payos_order_code:
            return {
                "success": False,
                "error": "Missing PayOS order code"
            }
        
        # Call PayOS cancel API (acts as refund request)
        result = self.payos_provider.cancel_payment(
            order_code=payment.payos_order_code,
            reason=reason or "Order cancelled, refund requested"
        )
        if result.get("success"):
            gateway_response = {
                **(state.gateway_response or {}),
                "refund_info": result,
                "refund_reason": reason,
                "refunded_at": timezone.now().isoformat(),
            }
            self._transition_payment_state(
                payment,
                PaymentStatus.REFUND_PENDING,
                reason=reason,
                gateway_payload=gateway_response,
                source="cancel_payment_with_refund",
            )

            print(f"[Payment] Refund initiated for payment {payment_uid}")

            return {
                "success": True,
                "message": "Refund initiated successfully",
                "payment_uid": str(payment.uid),
                "order_code": payment.payos_order_code,
                "amount": float(payment.amount),
                "refund_status": result.get("status")
            }

        return {
            "success": False,
            "error": result.get("error", "Failed to process refund"),
            "payment_uid": str(payment.uid)
        }

    def handle_order_cancellation_refund(self, order_uid: UUID, reason=None) -> dict:
        """
        Handle refund for cancelled orders.
        - For PayOS: Call API to refund from escrow
        - For COD: Create refund record in ledger (no API call)

        Args:
            order_uid: Order UUID
            reason: Cancellation reason

        Returns:
            Dict with refund info
        """
        from payment.models import PayoutLedger, SettlementRecord

        try:
            order = Order.objects.select_related("checkout", "chef").get(uid=order_uid)

            if order.checkout.payment_method == PaymentMethodEnum.PAYOS:
                from django.db import transaction as db_transaction
                from payment.models import PaymentTransaction as PaymentTransactionModel

                # Acquire row-level lock before status check to prevent double-refund race.
                with db_transaction.atomic():
                    try:
                        payment = PaymentTransactionModel.objects.select_for_update().get(
                            checkout=order.checkout
                        )
                    except PaymentTransactionModel.DoesNotExist:
                        return {"success": False, "error": "Payment transaction not found"}

                    state = self._ensure_payment_state(payment)

                    # Idempotency guard — checked under lock so only one request proceeds
                    if state.status == PaymentStatus.REFUNDED:
                        return {"success": True, "skipped": True, "refund_status": "ALREADY_REFUNDED"}

                    # Case 1: Tiền đã về merchant account (HOLDING/SUCCESS)
                    # PayOS cancel API không thể hoàn tiền cho link đã PAID.
                    # → Credit ví nội bộ khách hàng từ escrow, không gọi PayOS.
                    if state.status in [PaymentStatus.HOLDING, PaymentStatus.SUCCESS]:
                        self.assert_payment_confirmed(payment)
                        refund_amount = order.total_price or Decimal("0")
                        customer_wallet_credit = self.credit_internal_wallet(
                            user=order.owner,
                            amount=refund_amount,
                            transaction_type=WalletTransactionTypeEnum.REFUND,
                            order=order,
                            reference_id=f"refund_{order.uid}",
                            description=f"Refund for cancelled order {order.uid}",
                            metadata={"payment_method": "PAYOS", "cancellation_reason": reason},
                        ) if order.owner else None

                        gateway_response = {
                            **(state.gateway_response or {}),
                            "refund_info": {
                                "type": "INTERNAL_WALLET_CREDIT",
                                "amount": float(refund_amount),
                                "reason": reason,
                            },
                            "refund_reason": reason,
                            "refunded_at": timezone.now().isoformat(),
                            "wallet_credit_tx": str(customer_wallet_credit.uid) if customer_wallet_credit else None,
                        }
                        self._transition_payment_state(
                            payment,
                            PaymentStatus.REFUNDED,
                            reason=reason,
                            gateway_payload=gateway_response,
                            source="order_cancel_refund",
                        )

                        print(f"[Refund] Credited {refund_amount} VND to customer wallet for order {order_uid}")
                        return {
                            "success": True,
                            "payment_method": "PAYOS",
                            "refund_status": "REFUNDED",
                            "message": "Refund processed to customer internal wallet",
                            "amount": float(refund_amount),
                            "wallet_credit_tx": str(customer_wallet_credit.uid) if customer_wallet_credit else None,
                        }

                    # Case 2: Link chưa thanh toán (PENDING) → cancel PayOS link
                    if state.status == PaymentStatus.PENDING:
                        if payment.payos_order_code:
                            result = self.payos_provider.cancel_payment(
                                order_code=payment.payos_order_code,
                                reason=reason or "Order cancelled"
                            )
                            if result.get("success"):
                                gateway_response = {
                                    **(state.gateway_response or {}),
                                    "cancel_info": result,
                                    "cancel_reason": reason,
                                    "cancelled_at": timezone.now().isoformat(),
                                }
                                self._transition_payment_state(
                                    payment,
                                    PaymentStatus.CANCELLED,
                                    reason=reason,
                                    gateway_payload=gateway_response,
                                    source="order_cancel_refund",
                                )
                                return {
                                    "success": True,
                                    "payment_method": "PAYOS",
                                    "refund_status": "CANCELLED",
                                    "message": "Payment link cancelled successfully",
                                }
                            return {"success": False, "payment_method": "PAYOS", "error": result.get("error")}
                        else:
                            self._transition_payment_state(
                                payment,
                                PaymentStatus.CANCELLED,
                                reason=reason,
                                source="order_cancel_refund",
                            )
                            return {"success": True, "payment_method": "PAYOS", "refund_status": "CANCELLED"}

                    return {
                        "success": False,
                        "error": f"Payment status is {state.status}, cannot process refund/cancellation"
                    }

            if order.checkout.payment_method == PaymentMethodEnum.COD:
                settlement = SettlementRecord.objects.filter(order=order).first()
                if settlement:
                    settlement.status = "CANCELLED"
                    settlement.error_reason = reason or "Order cancelled"
                    settlement.save()

                    PayoutLedger.objects.create(
                        ledger_type="PAYOUT_REVERSAL",
                        amount=settlement.chef_payout_amount,
                        description=f"COD order cancelled: {reason}",
                        order_uid=str(order_uid),
                        chef_id=order.chef.id if order.chef else None,
                    )

                # Transition payment state → CANCELLED (COD is created as SUCCESS at place_order)
                try:
                    payment = PaymentTransaction.objects.get(checkout=order.checkout)
                    state = self._ensure_payment_state(payment)
                    if state.status not in {PaymentStatus.CANCELLED, PaymentStatus.REFUNDED}:
                        self._transition_payment_state(
                            payment,
                            PaymentStatus.CANCELLED,
                            reason=reason or "COD order cancelled",
                            source="order_cancel_cod",
                        )
                except PaymentTransaction.DoesNotExist:
                    pass

                return {
                    "success": True,
                    "payment_method": "COD",
                    "refund_status": "CANCELLED",
                    "message": "COD order cancelled (no payment made yet)"
                }

            return {
                "success": False,
                "error": f"Unknown payment method: {order.checkout.payment_method}"
            }

        except Exception as e:
            print(f"[Refund] Error processing refund: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def payout_to_chef(self, order_uid: UUID, chef_user) -> dict:
        """
        Process payout to chef when order is completed (Escrow release)
        
        This transfers the chef share for a single order from escrow to the chef.
        
        Args:
            order_uid: Order UUID
            chef_user: Chef user object
            
        Returns:
            Dict with payout result
        """
        
        try:
            order = Order.objects.select_related("checkout", "chef").get(uid=order_uid)
            payment = order.checkout.payment_transaction

            if not order.chef or order.chef.id != chef_user.id:
                return {
                    "success": False,
                    "error": "Order does not belong to the provided chef"
                }
            
            # Check if payment method is PayOS
            if order.checkout.payment_method != PaymentMethodEnum.PAYOS:
                return {
                    "success": True,
                    "message": "COD order - no payout needed",
                    "payment_method": "COD"
                }
            
            # Check if payment was successful
            state = self._ensure_payment_state(payment)
            if state.status != PaymentStatus.SUCCESS:
                return {
                    "success": False,
                    "error": "Payment not successful. Cannot process payout."
                }
            
            # Get chef's payment info via ORM
            chef_payment_info = ChefPaymentInfoORM.get_by_user(chef_user)
            
            if not chef_payment_info:
                return {
                    "success": False,
                    "error": "Chef has not set up payment information. Please add bank account details first."
                }
            
            if not chef_payment_info.is_verified:
                return {
                    "success": False,
                    "error": "Chef payment information not verified. Please verify bank account first."
                }
            
            # Calculate payout amount for this specific order, not the whole checkout.
            order_amount = self._quantize_amount(order.total_price or Decimal("0"))
            platform_fee_percent = self.PLATFORM_FEE_PERCENT
            platform_fee = self._quantize_amount(order_amount * platform_fee_percent)
            payout_amount = self._quantize_amount(order_amount - platform_fee)

            state = self._ensure_payment_state(payment)
            gateway_response = state.gateway_response or {}
            settlement = gateway_response.get("settlement", {}) if isinstance(gateway_response, dict) else {}
            payout_entries = settlement.get("payouts", []) if isinstance(settlement, dict) else []

            settlement_entry = {
                "order_uid": str(order.uid),
                "chef_email": chef_user.email,
                "order_amount": float(order_amount),
                "platform_fee": float(platform_fee),
                "payout_amount": float(payout_amount),
                "processed_at": timezone.now().isoformat(),
                "mode": "planned",
            }

            bank_code = getattr(chef_payment_info, "bank_code", None)
            if not bank_code:
                payout_entries.append(
                    {
                        **settlement_entry,
                        "status": "RECORDED_ONLY",
                        "reason": "Chef bank BIN is not configured on ChefPaymentInfo",
                    }
                )
                settlement.update(
                    {
                        "status": "PARTIALLY_SETTLED",
                        "payouts": payout_entries,
                        "updated_at": timezone.now().isoformat(),
                    }
                )
                gateway_response["settlement"] = settlement
                state.gateway_response = gateway_response
                state.save(update_fields=["gateway_response", "updated_at"])

                return {
                    "success": True,
                    "message": "Chef payout split recorded. External transfer skipped because bank BIN is unavailable.",
                    "mode": "ledger_only",
                    "order_uid": str(order_uid),
                    "chef_email": chef_user.email,
                    "payout_amount": float(payout_amount),
                    "platform_fee": float(platform_fee),
                    "bank_account": f"{chef_payment_info.bank_name} - {chef_payment_info.bank_account_number[-4:]}",
                    "transactions": []
                }
            
            # ✅ Call PayOS Payout API to transfer money
            reference_id = f"payout_{order_uid}_{int(timezone.now().timestamp())}"
            idempotency_key = str(uuid.uuid4())
            
            payout_result = self._create_payout_with_retry(
                reference_id=reference_id,
                amount=int(payout_amount),  # PayOS requires integer
                description=f"Chi {order.uid}",  # Short description for PayOS
                to_bin=bank_code,  # Bank BIN code
                to_account_number=chef_payment_info.bank_account_number,
                idempotency_key=idempotency_key,
                category=["order_payout"]
            )
            
            if not payout_result.get("success"):
                payout_error = str(payout_result.get("error", ""))
                payout_status_code = payout_result.get("status_code")
                # Nếu PayOS trả lỗi xác thực / thiếu API key, vẫn ghi nhận settlement nội bộ để đơn hàng không bị kẹt.
                if (
                    payout_status_code == 403
                    or any(token in payout_error.lower() for token in ["api key", "unauthorized", "401", "missing", "forbidden", "permission"])
                ):
                    payout_entries.append(
                        {
                            **settlement_entry,
                            "status": "RECORDED_ONLY",
                            "reason": payout_error,
                        }
                    )
                    settlement.update(
                        {
                            "status": "PAYOUT_NEEDS_CONFIGURATION",
                            "payouts": payout_entries,
                            "updated_at": timezone.now().isoformat(),
                        }
                    )
                    gateway_response["settlement"] = settlement
                    state.gateway_response = gateway_response
                    state.save(update_fields=["gateway_response", "updated_at"])

                    print(f"[Payout] Auth/config issue detected, recorded ledger only: {payout_error}")
                    return {
                        "success": True,
                        "message": "Chef payout recorded internally. External transfer skipped because PayOS payout credentials are not valid.",
                        "mode": "ledger_only",
                        "order_uid": str(order_uid),
                        "chef_email": chef_user.email,
                        "payout_amount": float(payout_amount),
                        "platform_fee": float(platform_fee),
                        "bank_account": f"{chef_payment_info.bank_name} - {chef_payment_info.bank_account_number[-4:]}",
                        "transactions": [],
                        "details": payout_result,
                    }

                # Payout failed
                settlement_rec = SettlementRecord.objects.filter(order=order).first()
                if settlement_rec:
                    settlement_rec.status = "PAYOUT_FAILED"
                    settlement_rec.error_reason = payout_error
                    settlement_rec.save(update_fields=["status", "error_reason", "updated_at"])
                print(f"[Payout] Failed to create payout: {payout_error}")
                return {
                    "success": False,
                    "error": f"Failed to process payout: {payout_error}",
                    "details": payout_result
                }
            
            # Update payment record with payout info
            payout_info = {
                "payout_processed": True,
                "payout_date": timezone.now().isoformat(),
                "payout_id": payout_result.get("payout_id"),
                "reference_id": reference_id,
                "chef_email": chef_user.email,
                "total_amount": float(order_amount),
                "platform_fee": platform_fee,
                "payout_amount": payout_amount,
                "order_uid": str(order_uid),
                "approval_state": payout_result.get("approval_state"),
                "transactions": payout_result.get("transactions", []),
                "bank_info": {
                    "bank_name": chef_payment_info.bank_name,
                    "bank_code": bank_code,
                    "account_number": chef_payment_info.bank_account_number[-4:],  # Last 4 digits only
                    "account_name": chef_payment_info.bank_account_name
                }
            }
            
            payout_entries.append(payout_info)
            settlement.update(
                {
                    "status": "SETTLED",
                    "payouts": payout_entries,
                    "updated_at": timezone.now().isoformat(),
                }
            )
            gateway_response["settlement"] = settlement
            state.gateway_response = gateway_response
            state.save(update_fields=["gateway_response", "updated_at"])

            # Update SettlementRecord with payout result
            settlement_rec = SettlementRecord.objects.filter(order=order).first()
            if settlement_rec:
                settlement_rec.payout_id = payout_result.get("payout_id")
                settlement_rec.payout_reference = reference_id
                settlement_rec.status = "PAYOUT_PROCESSED"
                settlement_rec.settled_at = timezone.now()
                settlement_rec.save(update_fields=["payout_id", "payout_reference", "status", "settled_at", "updated_at"])

            print(f"[Payout] ✅ Processed payout of {payout_amount} VND to {chef_payment_info.bank_name} "
                  f"({chef_payment_info.bank_account_number}) for order {order_uid}")
            print(f"[Payout] PayOS Payout ID: {payout_result.get('payout_id')}")
            print(f"[Payout] Approval State: {payout_result.get('approval_state')}")
            
            return {
                "success": True,
                "message": "Payout processed successfully via PayOS",
                "payout_id": payout_result.get("payout_id"),
                "reference_id": reference_id,
                "chef_email": chef_user.email,
                "payout_amount": payout_amount,
                "platform_fee": platform_fee,
                "approval_state": payout_result.get("approval_state"),
                "bank_account": f"{chef_payment_info.bank_name} - {chef_payment_info.bank_account_number[-4:]}",
                "order_uid": str(order_uid),
                "transactions": payout_result.get("transactions", [])
            }
            
        except Exception as e:
            print(f"[Payout] ❌ Error processing payout: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    
    def get_payment_invoices(self, payment_uid: UUID) -> dict:
        """
        Get payment invoices
        
        Args:
            payment_uid: UUID of payment transaction
            
        Returns:
            Dict with invoices information
        """
        try:
            payment = PaymentTransaction.objects.get(uid=payment_uid)
        except PaymentTransaction.DoesNotExist:
            return {
                "success": False,
                "error": f"Payment {payment_uid} not found"
            }
        
        if payment.payment_method == PaymentMethodEnum.PAYOS and payment.payos_order_code:
            return self.payos_provider.get_payment_invoices(payment.payos_order_code)
        else:
            return {
                "success": False,
                "error": "Invoices only available for PayOS payments"
            }
    
    def handle_payos_webhook(self, webhook_data: dict) -> dict:
    # def handle_payos_webhook(self, webhook_data: dict, t2_webhook_received: float = None) 
        """
        Handle PayOS payment webhook
        
        Args:
            webhook_data: Dict containing PayOS webhook data
            (use for testing) t2_webhook_received: Timestamp when webhook was received by backend (T2)
            
        Returns:
            Dict with processing result
        """
        import logging
        # import time
        # from datetime import datetime
        
        logger = logging.getLogger(__name__)
        # t2_process_start = time.time()
        
        try:
            # Verify webhook signature
            verification = self.payos_provider.verify_webhook_data(webhook_data)
            logger.info(f"Webhook verification result: {verification}")
            
            if not verification['is_valid']:
                logger.warning(f"Invalid webhook signature for data: {webhook_data}")
                # Forensic: ghi lại attempt webhook giả mạo để audit
                _tamper_order_code = verification.get('order_code')
                if _tamper_order_code:
                    try:
                        _tamper_payment = PaymentTransaction.objects.get(
                            payos_order_code=_tamper_order_code
                        )
                        self._record_payment_event(
                            payment=_tamper_payment,
                            event_type="WEBHOOK_SIG_INVALID",
                            status_from=None,
                            status_to=None,
                            payload={"truncated_raw": str(webhook_data)[:500]},
                            signature_valid=False,
                            source="payos_webhook",
                        )
                    except PaymentTransaction.DoesNotExist:
                        pass
                return {
                    'success': False,
                    'message': 'Invalid signature',
                    'code': '97'
                }
            
            # Get payment transaction by order_code
            order_code = verification.get('order_code')
            
            if not order_code:
                logger.error(f"Missing order_code in webhook data: {webhook_data}")
                return {
                    'success': False,
                    'message': 'Missing order_code',
                    'code': '02'
                }
            
            try:
                payment = PaymentTransaction.objects.get(payos_order_code=order_code)
                state = self._ensure_payment_state(payment)
                logger.info(f"Found payment: {payment.uid}, status: {state.status}")
            except PaymentTransaction.DoesNotExist:
                logger.error(f"Transaction not found for order_code: {order_code}")
                return {
                    'success': False,
                    'message': f'Transaction not found for order_code: {order_code}',
                    'code': '01'
                }
            
            # Idempotency guard: skip if already in a terminal state
            if state.status == PaymentStatus.HOLDING:
                logger.info(f"Duplicate webhook ignored: payment {payment.uid} already HOLDING")
                return {'success': True, 'message': 'Already processed', 'code': '00'}
            if state.status in [PaymentStatus.CANCELLED, PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
                logger.info(f"Late webhook ignored: payment {payment.uid} already in terminal state {state.status}")
                return {'success': True, 'message': 'Already in terminal state', 'code': '00'}

            # Update payment status
            if verification['is_success']:
                reference_id = verification.get('reference')
                if reference_id and state.transaction_id != reference_id:
                    state.transaction_id = reference_id
                if not state.payos_payment_link_id and verification.get('payment_link_id'):
                    state.payos_payment_link_id = verification.get('payment_link_id')
                if reference_id or verification.get('payment_link_id'):
                    state.save(update_fields=["transaction_id", "payos_payment_link_id", "updated_at"])
                self._record_payment_event(
                    payment=payment,
                    event_type="PAYOS_WEBHOOK",
                    status_from=state.status,
                    status_to=PaymentStatus.HOLDING,
                    payload=webhook_data,
                    signature_valid=True,
                    source="payos_webhook",
                )

                sync_result = self._sync_successful_payment(
                    payment=payment,
                    gateway_payload=webhook_data,
                    source="payos_webhook",
                    # t2_webhook_received=t2_webhook_received,
                )
                logger.info(
                    f"Payment {payment.uid} marked as HOLDING, orders CONFIRMED_SYSTEM, "
                    f"vouchers USED={sync_result['vouchers_used']}, split planned for {sync_result['split_summary']['chef_count']} chef(s)"
                )
                
                return {
                    'success': True,
                    'message': 'Payment held in escrow',
                    'code': '00'
                }
            else:
                gateway_status = webhook_data.get("data", {}).get("status") if isinstance(webhook_data, dict) else None
                if gateway_status == "CANCELLED":
                    new_status = PaymentStatus.CANCELLED
                elif gateway_status == "EXPIRED":
                    new_status = PaymentStatus.FAILED
                else:
                    new_status = PaymentStatus.FAILED

                self._transition_payment_state(
                    payment,
                    new_status,
                    reason=f"payos_{gateway_status or 'failed'}",
                    gateway_payload=webhook_data,
                    source="payos_webhook",
                    signature_valid=True,
                )

                self._cancel_orders_for_payment(
                    payment=payment,
                    reason=f"PayOS payment {gateway_status or 'failed'}",
                    gateway_payload=webhook_data,
                )

                logger.info(f"Payment {payment.uid} marked as {new_status} and orders cancelled")

                return {
                    'success': False,
                    'message': 'Payment failed',
                    'code': '99'
                }
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e),
                'code': '98'
            }
    
    # ========== Settlement Methods ==========
    
    def create_settlement_record(self, order_uid: UUID, chef_user):
        """
        Create a settlement record for an order when it's completed.
        
        Args:
            order_uid: Order UUID
            chef_user: Chef user object
            
        Returns:
            SettlementRecord instance
        """
        from payment.models import SettlementRecord, PayoutLedger
        from django.db import transaction as db_transaction
        
        order = Order.objects.select_related("checkout", "chef").get(uid=order_uid)
        
        # Calculate settlement amounts
        gross_amount = self._quantize_amount(order.total_price or Decimal("0"))
        platform_fee = self._quantize_amount(gross_amount * self.PLATFORM_FEE_PERCENT)
        chef_payout_amount = self._quantize_amount(gross_amount - platform_fee)
        
        # Create settlement record
        with db_transaction.atomic():
            settlement = SettlementRecord.objects.create(
                order=order,
                chef=chef_user,
                gross_amount=gross_amount,
                platform_fee=platform_fee,
                chef_payout_amount=chef_payout_amount,
                payment_method=order.checkout.payment_method,
                status='LEDGER_RECORDED',
                settlement_data={
                    'order_total': float(gross_amount),
                    'payment_method': order.checkout.payment_method,
                    'settled_at': timezone.now().isoformat()
                }
            )
            
            # Create ledger entries
            PayoutLedger.objects.create(
                settlement_record=settlement,
                ledger_type='PLATFORM_REVENUE',
                amount=platform_fee,
                description=f"Platform commission for order {order_uid}",
                order_uid=str(order_uid),
                chef_id=chef_user.id
            )
            
            PayoutLedger.objects.create(
                settlement_record=settlement,
                ledger_type='CHEF_PAYOUT',
                amount=chef_payout_amount,
                description=f"Payout for order {order_uid}",
                order_uid=str(order_uid),
                chef_id=chef_user.id
            )
            
            print(f"[Settlement] Created settlement record {settlement.uid} for order {order_uid}")
            print(f"  Gross: {gross_amount}, Platform Fee: {platform_fee}, Chef Payout: {chef_payout_amount}")
        
        return settlement
    
    def update_chef_cod_balance(self, chef_user, amount: Decimal) -> None:
        """
        Update COD balance for a chef when COD order is completed.
        
        Args:
            chef_user: Chef user object
            amount: Payout amount
        """
        from payment.models import ChefCODBalance
        
        balance, created = ChefCODBalance.objects.get_or_create(chef=chef_user)
        balance.unsettled_balance = self._quantize_amount(balance.unsettled_balance + amount)
        balance.unsettled_orders_count += 1
        balance.save()
        
        print(f"[COD Balance] Updated balance for chef {chef_user.email}: {balance.unsettled_balance} VND")
    
    def settle_cod_balance_for_chef(self, chef_user, batch_id=None) -> dict:
        """
        Settle COD balance for a chef by creating a batch payout.
        
        Args:
            chef_user: Chef user object
            batch_id: Optional batch ID for grouping payouts
            
        Returns:
            Dict with settlement result
        """
        from payment.models import ChefCODBalance, InternalWallet, SettlementRecord
        from django.db import transaction as db_transaction
        
        try:
            with db_transaction.atomic():
                balance = ChefCODBalance.objects.select_for_update().get(chef=chef_user)
                
                if balance.unsettled_balance <= 0:
                    return {
                        "success": False,
                        "error": "No unsettled COD balance available"
                    }
                
                # Get unsettled orders
                unsettled_orders = SettlementRecord.objects.filter(
                    chef=chef_user,
                    payment_method=PaymentMethodEnum.COD,
                    status__in=['LEDGER_RECORDED', 'PAYOUT_SCHEDULED']
                )
                
                total_amount = sum(order.chef_payout_amount for order in unsettled_orders)
                
                # Update settlement records
                unsettled_orders.update(status='PAYOUT_SCHEDULED')
                
                # Reset COD balance
                balance.total_settled = self._quantize_amount(balance.total_settled + balance.unsettled_balance)
                balance.unsettled_balance = Decimal("0")
                balance.unsettled_orders_count = 0
                balance.last_settlement_at = timezone.now()
                balance.save()
                
                print(f"[COD Settlement] Settled {balance.unsettled_orders_count} orders, "
                      f"total: {total_amount} VND for chef {chef_user.email}")
                
                return {
                    "success": True,
                    "chef_id": chef_user.id,
                    "chef_email": chef_user.email,
                    "settled_amount": float(total_amount),
                    "order_count": len(unsettled_orders),
                    "settled_at": timezone.now().isoformat()
                }
        
        except ChefCODBalance.DoesNotExist:
            return {
                "success": False,
                "error": "COD balance not found for chef"
            }
        except Exception as e:
            print(f"[COD Settlement] Error settling balance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_chef_balance_summary(self, chef_user) -> dict:
        """
        Get complete balance summary for a chef (COD + PayOS).
        
        Args:
            chef_user: Chef user object
            
        Returns:
            Dict with balance summary
        """
        from payment.models import ChefCODBalance, SettlementRecord
        
        # Get COD balance
        cod_balance_obj = ChefCODBalance.objects.filter(chef=chef_user).first()
        cod_balance = cod_balance_obj.unsettled_balance if cod_balance_obj else Decimal("0")
        unsettled_orders = cod_balance_obj.unsettled_orders_count if cod_balance_obj else 0
        
        wallet = InternalWallet.objects.filter(user=chef_user).first()
        wallet_balance = wallet.balance if wallet else Decimal("0")
        wallet_pending = wallet.pending_balance if wallet else Decimal("0")
        
        # Get completed settlements
        completed_settlements = SettlementRecord.objects.filter(
            chef=chef_user,
            status='LEDGER_RECORDED'
        ).aggregate(total=models.Sum('chef_payout_amount'))
        
        completed_total = completed_settlements['total'] or Decimal("0")
        
        return {
            "chef_id": chef_user.id,
            "chef_email": chef_user.email,
            "cod_balance": {
                "unsettled_balance": cod_balance,
                "unsettled_orders": unsettled_orders,
                "note": "COD money collected from customers"
            },
            "payos_balance": {
                "pending_payout": wallet_balance,
                "note": "Internal wallet available balance"
            },
            "total_available_payout": cod_balance + wallet_balance,
            "total_settled": completed_total + wallet_balance,
            "currency": "VND"
        }
                
        #         return {
        #             'success': False,
        #             'message': verification.get('desc', 'Payment failed'),
        #             'code': verification.get('code', '99')
        #         }
        # except Exception as e:
        #     logger.error(f"Unexpected error in handle_payos_webhook: {str(e)}", exc_info=True)
        #     return {
        #         'success': False,
        #         'message': f'Internal error: {str(e)}',
        #         'code': '99'
        #     }
    
    def _generate_order_code(self, payment_uid: UUID) -> int:
        """
        Generate unique order code from payment UID for PayOS
        PayOS requires integer order_code
        
        Returns:
            Integer order code (max 9223372036854775807)
        """
        # Use hash of UUID to generate integer
        uuid_str = str(payment_uid)
        hash_object = hashlib.md5(uuid_str.encode())
        hash_int = int(hash_object.hexdigest(), 16)
        
        # Keep it within reasonable range (13 digits)
        order_code = hash_int % 10000000000000
        
        return order_code
