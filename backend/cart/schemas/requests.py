from typing import Optional
from datetime import date
from ninja import Schema
from uuid import UUID

class CartAddRequest(Schema):
    dish_uid: UUID
    delivery_date: date
    quantity_to_add: int
    
class CartSetQuantityRequest(Schema):
    delivery_date: date
    target_quantity: int
    
class CartRemoveRequest(Schema):
    delivery_date: date

