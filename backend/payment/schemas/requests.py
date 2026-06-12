from typing import Optional, List
from uuid import UUID
from ninja import Schema
from decimal import Decimal
import re
from pydantic import field_validator
from utils.enums import VietnamBankEnum


class PaymentItemRequest(Schema):
    """Item in payment request"""
    name: str
    quantity: int
    price: int
    unit: Optional[str] = None
    taxPercentage: Optional[int] = 0


class PaymentInvoiceRequest(Schema):
    """Invoice configuration for payment"""
    buyerNotGetInvoice: Optional[bool] = True
    taxPercentage: Optional[int] = 0


class CreatePaymentRequest(Schema):
    checkout_uid: UUID
    payment_method: str
    bank_code: Optional[str] = None  # For VNPay: NCB, VIETCOMBANK, etc.
    language: Optional[str] = "vn"  # vn or en
    
    # PayOS specific fields (optional)
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_company_name: Optional[str] = None
    buyer_tax_code: Optional[str] = None
    items: Optional[List[PaymentItemRequest]] = None
    invoice: Optional[PaymentInvoiceRequest] = None
    expired_at: Optional[int] = None  # Unix timestamp


class CancelPaymentRequest(Schema):
    """Request to cancel payment"""
    cancellation_reason: Optional[str] = None


class CustomerPaymentInfoRequest(Schema):
    """Request schema for customer bank information."""
    bank_name: VietnamBankEnum
    bank_code: str
    bank_account_number: str
    bank_account_name: str
    bank_branch: Optional[str] = None

    @field_validator('bank_code')
    def validate_bank_code(cls, v):
        v = v.strip().replace(' ', '')
        if not re.match(r'^\d{6,8}$', v):
            raise ValueError("Bank code must be 6-8 digits")
        return v

    @field_validator('bank_account_number')
    def validate_account_number(cls, v):
        v = v.replace(' ', '').replace('-', '')
        if not re.match(r'^\d{6,19}$', v):
            raise ValueError("Account number must be 6-19 digits only (no letters or special characters)")
        return v

    @field_validator('bank_account_name')
    def validate_account_name(cls, v):
        v = v.strip()
        v = re.sub(r'\s+', ' ', v)
        if not re.match(r'^[A-Z\s]+$', v):
            raise ValueError("Account name must be UPPERCASE letters without accents (A-Z and spaces only)")
        return v


class WalletWithdrawRequest(Schema):
    amount: Decimal


class PaymentOtpVerifyRequest(Schema):
    reset_session_token: str
    otp: str


class WithdrawConfirmRequest(Schema):
    reset_session_token: str
    otp: str


class PaymentCallbackRequest(Schema):
    """VNPay callback parameters"""
    vnp_TmnCode: str
    vnp_Amount: str
    vnp_BankCode: Optional[str]
    vnp_BankTranNo: Optional[str]
    vnp_CardType: Optional[str]
    vnp_PayDate: str
    vnp_OrderInfo: str
    vnp_TransactionNo: str
    vnp_ResponseCode: str
    vnp_TransactionStatus: str
    vnp_TxnRef: str
    vnp_SecureHash: str
