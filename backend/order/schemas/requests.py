from typing import List, Optional, Literal

from django.db.models import Q
from ninja import FilterSchema

# from order.models import Order
# from utils.functions.remove_accents import remove_accents
from utils.schemas.fields import FilterField, OrderBySchema
# from uuid import UUID
from ninja import Schema
from uuid import UUID
from utils.functions.remove_accents import remove_accents
from utils.enums import OrderStatusEnum, DeliveryTypeEnum

class PersonalInfoSchema(Schema):
    full_name: str
    phone_number: str

class FilterOrderSchema(FilterSchema):
    search: Optional[str] = FilterField(
        default=None,
        description="Tìm kiếm theo tên món ăn",
    )
    
    status: Optional[str] = FilterField(
        default=None,
        description="Lọc theo trạng thái đơn hàng (PENDING, CONFIRMED_SYSTEM, CONFIRMED_SHOP, PROCESSING, DELIVERING, COMPLETED, CANCELLED)",
    )
      
    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(orderitem_fk_order__dish__name_no_accent__icontains=remove_accents(value))
    
    def filter_status(self, value: Optional[str]):
        if value is None:
            return Q()
        # Validate status value
        valid_statuses = [choice[0] for choice in OrderStatusEnum.choices]
        if value not in valid_statuses:
            return Q()
        return Q(status=value)


class OrderByOrderSchema(OrderBySchema):
    order_by: Literal["created_at"] = "created_at"


class ApplyVoucherSchema(Schema):
    """Schema để apply voucher vào order"""
    voucher_code: str


class ApplyPlatformVoucherSchema(Schema):
    """Schema để apply platform voucher vào checkout"""
    voucher_code: str
    voucher_type: str  # "PLATFORM_SUBTOTAL" or "PLATFORM_SHIPPING"

# class OrderIngredientSchema(Schema):
#     ingredient_uid: UUID
#     weight: Optional[float] = None
class SubOrderDeliverySchema(Schema):
    chef_id: int # ID của đơn hàng phụ (của 1 Chef cụ thể)
    delivery_type: DeliveryTypeEnum # 'SELF_PICKUP' hoặc 'THIRD_PARTY'

class UpdateDeliveryTypesPayload(Schema):
    sub_orders: List[SubOrderDeliverySchema]