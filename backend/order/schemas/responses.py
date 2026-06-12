from typing import List, Optional
from decimal import Decimal
from uuid import UUID
from datetime import date, time
from ninja import Schema
from utils.enums import PaymentMethodEnum, OrderStatusEnum
        
class OrderItemResponse(Schema):
    dish_uid: UUID  
    dish_name: str
    chef_name: Optional[str] = None
    image_url: Optional[str]
    quantity: int
    price: Decimal
    subtotal: Decimal  
    
class OrderResponse(Schema):
    uid: UUID
    chef_id: int
    chef_name: str
    sub_total: Decimal
    tax_and_fees: Decimal
    delivery_fee: Decimal
    platform_subtotal_discount: Decimal = Decimal(0)  # Allocated from checkout platform subtotal voucher
    platform_shipping_discount: Decimal = Decimal(0)  # Allocated from checkout platform shipping voucher
    shop_discount: Decimal = Decimal(0)  # Shop voucher discount (chef's voucher)
    total_discount: Decimal = Decimal(0)  # Sum of all discounts for this order
    total_price: Decimal
    voucher_code: Optional[str] = None
    items: List[OrderItemResponse]
    
class OrderResponeWithInfo(Schema):
    uid: UUID
    full_name: str
    phone_number: str
    delivery_date: date
    delivery_time: time
    delivery_address: Optional[str]
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    
    delivery_type: str 
    chef_name: Optional[str] = None
    chef_address: Optional[str] = None     
    chef_latitude: Optional[float] = None  
    chef_longitude: Optional[float] = None
    
    payment_method: PaymentMethodEnum
    sub_total: Decimal
    tax_and_fees: Decimal
    delivery_fee: Decimal
    platform_subtotal_discount: Decimal = Decimal(0)
    platform_shipping_discount: Decimal = Decimal(0)
    shop_discount: Decimal = Decimal(0)
    total_discount: Decimal = Decimal(0)
    total_price: Decimal
    items: List[OrderItemResponse]
    status: OrderStatusEnum
    refund_status: Optional[str] = None  # PENDING, PROCESSING, SUCCESS, FAILED
    voucher_code: Optional[str] = None
     
class CheckoutResponse(Schema):
    uid: UUID
    full_name: str
    phone_number: str
    delivery_date: date
    delivery_time: time
    delivery_address: Optional[str]
    payment_method: PaymentMethodEnum
    sub_total: Decimal
    tax_and_fees: Decimal
    delivery_fee: Decimal
    platform_subtotal_discount: Decimal = Decimal(0)  # Discount from PLATFORM_SUBTOTAL voucher
    platform_shipping_discount: Decimal = Decimal(0)  # Discount from PLATFORM_SHIPPING voucher
    total_discount: Decimal = Decimal(0)  # Total discount at checkout level
    total_price: Decimal
    orders: List[OrderResponse]
    
    # Payment fields (for PayOS and similar gateways)
    payment_url: Optional[str] = None
    payment_uid: Optional[UUID] = None
    transaction_id: Optional[str] = None
    qr_code: Optional[str] = None        # VietQR string — FE dùng thư viện render thành ảnh QR


class ChefInfoSchema(Schema):
    """Thông tin chef"""
    chef_id: int
    chef_name: str
    

class ChefOrderGroupResponse(Schema):
    """Response group orders theo chef"""
    chef_info: ChefInfoSchema
    orders: List[OrderResponeWithInfo]

class OrderListResponse(Schema):
    chef_info: Optional[ChefInfoSchema] = None
    orders: List[OrderResponeWithInfo]