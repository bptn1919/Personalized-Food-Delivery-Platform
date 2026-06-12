from typing import Optional, List
from uuid import UUID
from datetime import date
from ninja import Schema
        
class CartItemResponse(Schema):
    uid: UUID
    dish_uid: UUID
    dish_name: str
    image_url: Optional[str] = None
    price: float
    quantity: int
    delivery_date: date
    is_selected: bool
    subtotal: float


class ChefGroupResponse(Schema):
    chef_name: str
    items: List[CartItemResponse]


class DateGroupResponse(Schema):
    delivery_date: date
    chefs: List[ChefGroupResponse]


class CartResponse(Schema):
    items: List[DateGroupResponse]
    total_amount: float
    message: Optional[str] = None