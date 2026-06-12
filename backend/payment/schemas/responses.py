from typing import Optional, List, Any
from uuid import UUID
from ninja import Schema
from decimal import Decimal
from datetime import datetime


class PaymentData(Schema):
    """Payment data nested in response"""
    payment_uid: UUID
    checkout_uid: UUID
    payment_method: str
    amount: Decimal
    status: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    payment_link_id: Optional[str] = None
    order_code: Optional[int] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    transaction_id: Optional[str] = None
    settlement: Optional[dict[str, Any]] = None


class CreatePaymentResponse(Schema):
    """Response for create payment endpoint"""
    success: bool
    message: str
    data: Any = None


class PaymentTransactionInfo(Schema):
    """Transaction info in payment details"""
    reference: str
    amount: int
    accountNumber: str
    description: str
    transactionDateTime: str
    virtualAccountName: Optional[str] = None
    virtualAccountNumber: Optional[str] = None
    counterAccountBankId: Optional[str] = None
    counterAccountBankName: Optional[str] = None
    counterAccountName: Optional[str] = None
    counterAccountNumber: Optional[str] = None


class PaymentInfoResponse(Schema):
    """Payment information response"""
    success: bool
    payment_link_id: Optional[str] = None
    order_code: Optional[int] = None
    amount: Optional[int] = None
    amount_paid: Optional[int] = 0
    amount_remaining: Optional[int] = None
    status: Optional[str] = None


    # ========== Settlement Schemas ==========

class SettlementItemResponse(Schema):
    """Single settlement record"""
    settlement_uid: UUID
    order_uid: UUID
    chef_name: str
    gross_amount: Decimal
    platform_fee: Decimal
    chef_payout_amount: Decimal
    status: str
    payment_method: str
    settled_at: Optional[datetime] = None


class ChefCODBalanceResponse(Schema):
    """Chef's COD balance information"""
    unsettled_balance: Decimal
    unsettled_orders: int
    note: str


class ChefPayOSBalanceResponse(Schema):
    """Chef's PayOS balance information"""
    pending_payout: Decimal
    note: str


class ChefBalanceSummaryResponse(Schema):
    """Complete balance summary for a chef"""
    chef_id: int
    chef_email: str
    cod_balance: ChefCODBalanceResponse
    payos_balance: ChefPayOSBalanceResponse
    total_available_payout: Decimal
    total_settled: Decimal
    currency: str


class SettlementReportResponse(Schema):
    """Admin settlement report"""
    total_cod: Decimal
    total_commission: Decimal
    total_payout_to_chefs: Decimal
    cod_orders_count: int
    payos_orders_count: int
    pending_settlement_count: int
    settled_count: int
    settlements: List[SettlementItemResponse]


class CODSettlementResponse(Schema):
    """Response for COD settlement"""
    success: bool
    chef_id: int
    chef_email: str
    settled_amount: Decimal
    order_count: int
    settled_at: str
    message: Optional[str] = None
    created_at: Optional[str] = None
    transactions: Optional[List[PaymentTransactionInfo]] = []
    error: Optional[str] = None


class CancelPaymentResponse(Schema):
    """Cancel payment response"""
    success: bool
    status: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    error: Optional[str] = None


class PaymentStatusResponse(Schema):
    payment_uid: UUID
    transaction_id: str
    status: str
    amount: Decimal
    payment_method: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    settlement: Optional[dict[str, Any]] = None


class CustomerPaymentInfoResponse(Schema):
    bank_name: str
    bank_code: str
    bank_account_number: str
    bank_account_name: str
    bank_branch: Optional[str] = None
    is_verified: bool
    verified_at: Optional[str] = None
    created_at: str
    updated_at: str


class WalletTransactionResponse(Schema):
    uid: UUID
    transaction_type: str
    status: str
    amount: Decimal
    reference_id: Optional[str] = None
    description: Optional[str] = None
    balance_before: Decimal
    balance_after: Decimal
    payout_id: Optional[str] = None
    order_uid: Optional[UUID] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class InternalWalletSummaryResponse(Schema):
    wallet_uid: Optional[UUID] = None
    user_id: int
    balance: Decimal
    pending_balance: Decimal
    total_balance: Decimal
    currency: str
    recent_transactions: List[WalletTransactionResponse] = []


class WalletWithdrawResponse(Schema):
    success: bool
    message: str
    amount: Decimal
    status: str
    payout_id: Optional[str] = None
    reference_id: Optional[str] = None
    bank_account: Optional[str] = None
    error: Optional[str] = None


class PaymentOtpSessionResponse(Schema):
    reset_session_token: str
    message: str


class PaymentCallbackResponse(Schema):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    status: Optional[str] = None


class PaymentInvoiceInfo(Schema):
    """Invoice information"""
    invoiceId: str
    invoiceNumber: str
    issuedTimestamp: int
    issuedDatetime: str
    transactionId: str
    reservationCode: str
    codeOfTax: str


class PaymentInvoicesResponse(Schema):
    """Payment invoices response"""
    success: bool
    invoices: Optional[List[PaymentInvoiceInfo]] = []
    error: Optional[str] = None
