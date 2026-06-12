from exceptions.carts import CartNotFoundException, InvalidDeliveryDateException
from cart.orm.cart import CartORM
from dish.orm.dish import DishORM
from cart.schemas.requests import CartAddRequest
from utils.types import TUser
from datetime import date
from dish.models import DishAvailability
from django.utils import timezone

class CartService:
    def __init__(self):
        self.orm = CartORM()
        self.dish_orm = DishORM()
        
    def get_cart_by_user(self, user: TUser):
        cart = self.orm.get_cart_by_user(user=user)
        if not cart:
            raise CartNotFoundException

        # Gọi hàm helper để build response
        return self.orm.get_cart_detail(cart)
    def get_cart_item_count(self, user:TUser):
        return self.orm.get_cart_item_count(user=user)
        
    def remove_item(self, user, dish_uid, delivery_date):
        cart = self.orm.get_cart_by_user(user)
        self.orm.delete_cart_item(cart=cart, dish=dish_uid, delivery_date=delivery_date)
        return self.orm.get_cart_detail(cart)

    def toggle_select(self, cart_item_uid):
        cart_item = self.orm.get_cart_item_by_uid(cart_item_uid=cart_item_uid)
        
        # Nếu đang toggle từ False -> True (chọn món)
        if not cart_item.is_selected:
            # Kiểm tra xem đã có món nào được chọn chưa
            selected_items = self.orm.get_selected_cart_items_by_user(user=cart_item.cart.owner)
            
            if selected_items.exists():
                # Lấy delivery_date của món đầu tiên đã được chọn
                first_selected_date = selected_items.first().delivery_date
                
                # Kiểm tra xem món đang chọn có cùng delivery_date không
                if cart_item.delivery_date != first_selected_date:
                    raise Exception(
                        f"Không thể chọn món có ngày giao khác nhau. "
                        f"Các món đã chọn có ngày giao: {first_selected_date}, "
                        f"món này có ngày giao: {cart_item.delivery_date}"
                    )
        
        self.orm.toggle_select(cart_item=cart_item)
        return self.orm.get_cart_detail(cart=cart_item.cart)
    def clear_selected_items(self, user):
        """
        Gọi ORM để xóa hoặc reset các CartItem đã chọn của user.
        """
        deleted_count, _ = self.orm.clear_selected_items(user)
        return {"message": f"Đã xóa {deleted_count} sản phẩm được chọn trong giỏ hàng."}

    def add_item(self, user, payload: CartAddRequest):
        cart = self.orm.get_cart_by_user(user)
        dish = self.dish_orm.get_dish_by_uid(payload.dish_uid)
        delivery_date = payload.delivery_date
        quantity_to_add = payload.quantity_to_add or 1

        # ✅ 1. Không cho phép chọn ngày trong quá khứ
        today = timezone.now().date()
        if delivery_date < today:
            raise InvalidDeliveryDateException

        # Kiểm tra tồn kho theo ngày
        availability = DishAvailability.objects.filter(
            dish=dish, available_date=delivery_date, is_available=True
        ).first()

        if not availability:
            raise Exception(f"Món {dish.name} không có sẵn vào ngày {delivery_date}")

        available_qty = availability.available_quantity

        item = self.orm.get_cart_item(cart, dish, delivery_date)
        message = None

        if item:
            new_quantity = min(item.quantity + quantity_to_add, available_qty)
            if new_quantity < item.quantity + quantity_to_add:
                message = f"Chỉ còn {available_qty} món {dish.name} cho ngày {delivery_date}"
            item.quantity = new_quantity
            item.save()
        else:
            add_qty = min(quantity_to_add, available_qty)
            if add_qty < quantity_to_add:
                message = f"Chỉ còn {available_qty} món {dish.name} cho ngày {delivery_date}"
            self.orm.create_cart_item(cart, dish, delivery_date, add_qty)

        return self.orm.get_cart_detail(cart, message)

    def set_quantity(self, user, dish_uid, delivery_date, target_quantity):
        cart = self.orm.get_cart_by_user(user)
        dish = self.dish_orm.get_dish_by_uid(uid=dish_uid)
        item = self.orm.get_cart_item(cart, dish, delivery_date)

        if target_quantity <= 0:
            if item:
                self.orm.delete_cart_item(cart, dish, delivery_date)
            return self.orm.get_cart_detail(cart)

        availability = DishAvailability.objects.filter(
            dish=dish, available_date=delivery_date, is_available=True
        ).first()

        if not availability:
            raise Exception(f"Món {dish.name} không có sẵn vào ngày {delivery_date}")

        available_qty = availability.available_quantity
        message = None

        if target_quantity > available_qty:
            target_quantity = available_qty
            message = f"Đã giới hạn lại {available_qty} món {dish.name} cho ngày {delivery_date}"

        if item:
            item.quantity = target_quantity
            item.save()
        else:
            self.orm.create_cart_item(cart, dish, delivery_date, target_quantity)

        return self.orm.get_cart_detail(cart, message)

