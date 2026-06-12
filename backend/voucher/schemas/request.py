from datetime import datetime
from decimal import Decimal
from typing import Optional
from ninja import Schema
from utils.enums import VoucherDiscountTypeEnum, VoucherTypeEnum

class CreateVoucherSchema(Schema):
    """Schema để Chef tạo voucher mới"""
    code: str
    name: str
    description: Optional[str] = None
    discount_type: VoucherDiscountTypeEnum  # "PERCENTAGE" or "FIXED_AMOUNT"
    discount_value: Decimal
    max_discount_amount: Optional[Decimal] = None
    min_order_amount: Decimal = Decimal("0")
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = None
    usage_limit_per_user: int = 1
    is_active: bool = True

class AdminCreateVoucherSchema(Schema):
    """Schema để tạo Admin voucher mới"""
    code: str
    name: str
    description: Optional[str] = None
    voucher_type: VoucherTypeEnum
    discount_type: VoucherDiscountTypeEnum  # "PERCENTAGE" or "FIXED_AMOUNT"
    discount_value: Decimal
    max_discount_amount: Optional[Decimal] = None
    min_order_amount: Decimal = Decimal("0")
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = None
    usage_limit_per_user: int = 1
    is_active: bool = True


class UpdateVoucherSchema(Schema):
    """Schema để cập nhật voucher"""
    name: Optional[str] = None
    description: Optional[str] = None
    discount_value: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    min_order_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    usage_limit: Optional[int] = None
    usage_limit_per_user: Optional[int] = None
    is_active: Optional[bool] = None


class ValidateVoucherSchema(Schema):
    """Schema để validate voucher"""
    code: str
    chef_id: int
    order_amount: Decimal
