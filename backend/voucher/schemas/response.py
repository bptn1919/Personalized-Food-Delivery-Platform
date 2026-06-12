from datetime import datetime
from decimal import Decimal
from typing import Optional
from ninja import ModelSchema, Schema
from uuid import UUID
from voucher.models import Voucher
from utils.enums import VoucherReservationStatus

class VoucherDetailSchema(Schema):
    """Schema response chi tiết voucher"""
    uid: UUID
    code: str
    name: str
    description: Optional[str]
    voucher_type: str
    discount_value: Decimal
    max_discount_amount: Optional[Decimal]
    min_order_amount: Decimal
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int]
    usage_count: int
    usage_limit_per_user: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def resolve_uid(obj):
        return str(obj.uid)

    @staticmethod
    def resolve_usage_count(obj):
        # Keep compatibility with old annotated/queryset values when present.
        if hasattr(obj, "usage_count") and obj.usage_count is not None:
            return obj.usage_count

        return obj.applied_vouchers.filter(
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).count()


class VoucherListSchema(ModelSchema):
    """Schema response danh sách voucher"""
    class Meta:
        model = Voucher
        exclude = [
            "created_at",
            "chef",
            "updated_at",
            "description",
        ]
    @staticmethod
    def resolve_uid(obj):
        return str(obj.uid)


class ValidateVoucherResponseSchema(Schema):
    """Schema response khi validate voucher"""
    is_valid: bool
    message: str
    discount_amount: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None
