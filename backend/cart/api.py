from uuid import UUID

from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, post, put
from utils.types import AuthenticatedRequest

from .schemas.requests import  CartAddRequest, CartSetQuantityRequest, CartRemoveRequest
from .schemas.responses import CartResponse
from .services import CartService


@api(prefix_or_class="carts", tags=["Cart"], auth=AuthBear())
class CartController(Controller):
    def __init__(self, service: CartService) -> None:
        self.service = service
        
    @get("/", response=CartResponse)
    def get_cart_by_user(self,request: AuthenticatedRequest):
        return self.service.get_cart_by_user(user=request.user)
      
    @get("/count", response=int)
    def get_cart_item_count(self, request: AuthenticatedRequest):
        return self.service.get_cart_item_count(user=request.user)

    
    @post("/add", response=CartResponse)
    def add_item(self, request: AuthenticatedRequest, payload: CartAddRequest):
        return self.service.add_item(user=request.user, payload=payload)
    
    # 1. Toggle chọn món trong giỏ
    @put("/cart-items/{cart_item_uid}/toggle", response = CartResponse)
    def toggle_select(self, request: AuthenticatedRequest, cart_item_uid: UUID):
        return self.service.toggle_select(cart_item_uid=cart_item_uid)

    @put("/items/{dish_uid}", response=CartResponse)
    def set_quantity(
        self,
        request: AuthenticatedRequest,
        dish_uid: UUID,
        payload: CartSetQuantityRequest,
    ):
        return self.service.set_quantity(
            user=request.user,
            dish_uid=dish_uid,
            delivery_date=payload.delivery_date,
            target_quantity=payload.target_quantity,
        )

    @delete("/items/{dish_uid}", response=CartResponse)
    def remove_item(self, request: AuthenticatedRequest, dish_uid: UUID, payload: CartRemoveRequest):
        return self.service.remove_item(user=request.user, dish_uid=dish_uid, delivery_date=payload.delivery_date)
    
