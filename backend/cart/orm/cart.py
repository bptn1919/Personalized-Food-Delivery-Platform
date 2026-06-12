from cart.models import Cart, CartItem
from utils.types import TUser
from dish.models import Dish
from django.db import transaction
from collections import defaultdict
from django.db.models import Sum

class CartORM:
    @staticmethod
    def get_cart_by_user(user: TUser):
        cart, _ = Cart.objects.get_or_create(owner=user)
        return cart
      
    @staticmethod
    def get_cart_item_count(user: TUser):
        result = (
            CartItem.objects
            .filter(cart__owner=user)
            .aggregate(total_quantity=Sum("quantity"))
        )
        return result["total_quantity"] or 0
    @staticmethod
    def get_cart_item(cart, dish, delivery_date):
        return CartItem.objects.filter(cart=cart, dish=dish, delivery_date=delivery_date).first()

    @staticmethod
    def get_cart_item_by_uid(cart_item_uid):
        return CartItem.objects.filter(uid=cart_item_uid).first()
    @staticmethod
    def create_cart_item(cart, dish, delivery_date, quantity_to_add=1):
        return CartItem.objects.create(cart=cart, dish=dish, delivery_date=delivery_date, quantity=quantity_to_add)
    
    @staticmethod
    def create_cart_item_with_target_quantity(cart, dish, delivery_date, target_quantity):
        return CartItem.objects.create(cart=cart, dish=dish, delivery_date=delivery_date, quantity=target_quantity)

    @staticmethod
    def delete_cart_item(cart, dish, delivery_date):
        CartItem.objects.filter(cart=cart, dish=dish, delivery_date=delivery_date).delete()
        
    @staticmethod
    def toggle_select(cart_item):
        cart_item.is_selected = not cart_item.is_selected
        cart_item.save()
        
    @staticmethod
    def get_selected_cart_items_by_user(user: TUser):
        """Get selected cart items của một user"""
        return CartItem.objects.filter(
            cart__owner=user,
            is_selected=True
        ).select_related('dish')
        
    @staticmethod
    @transaction.atomic
    def clear_selected_items(user):
        """
        Xóa tất cả các CartItem đã được tick chọn (is_selected=True) của user.
        """
        return CartItem.objects.filter(
            cart__owner=user,
            is_selected=True
        ).delete()  # hoặc .update(is_selected=False) nếu bạn chỉ muốn reset
        
    # Mỗi lần bấm Checkout chỉ được chọn 1 ngày giao hàng"
    @staticmethod
    def get_delivery_dates_of_selected_items(cart):
        return (
            cart.cartitem_fk_cart
            .filter(is_selected=True)
            .values_list('delivery_date', flat=True)
            .distinct()
            .first()   # lấy ngày đầu tiên (hoặc None nếu không có)
        )
    @staticmethod
    def increase_item(cart, dish_uid, quantity_to_add=1):
        item, created = CartItem.objects.get_or_create(cart=cart, dish_id=dish_uid)
        if not created:
            item.quantity += quantity_to_add
        item.save()
        return CartORM.get_cart_detail(cart)
    
    @staticmethod
    def decrease_item(cart, dish_uid):
        item = CartItem.objects.get(cart=cart, dish_id=dish_uid)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
        return CartORM.get_cart_detail(cart)
    
    @staticmethod
    def set_quantity(cart, dish_uid, target_quantity):
        item = CartItem.objects.get(cart=cart, dish_id=dish_uid)
        item.quantity = target_quantity
        item.save()
        return CartORM.get_cart_detail(cart)
        
    @staticmethod
    def get_cart_detail(cart, message=None):
        # Lấy tất cả cart items
        cart_items = cart.cartitem_fk_cart.all().order_by("delivery_date")

        # Lấy list dish_ids từ cart items 
        dish_ids = [item.dish_id for item in cart_items]

        # Fetch tất cả dishes một lần bằng in_bulk
        dishes = Dish.objects.select_related("owner").in_bulk(dish_ids)

        # Nhóm theo ngày -> theo chef
        grouped_by_date = defaultdict(lambda: defaultdict(list))
        total = 0

        for item in cart_items:
            dish = dishes[item.dish_id]
            chef_name = dish.owner.get_full_name() if dish.owner else "Unknown Chef"

            item_info = {
                "uid": item.uid,
                "dish_uid": dish.uid,
                "dish_name": dish.name,
                "image_url": dish.attachment.public_url if dish.attachment else None,
                "price": float(dish.price),
                "quantity": item.quantity,
                "delivery_date": item.delivery_date,
                "is_selected": item.is_selected,
                "subtotal": float(item.quantity * dish.price)
            }

            grouped_by_date[item.delivery_date][chef_name].append(item_info)

            if item.is_selected:
                total += item_info["subtotal"]

        # Chuẩn hóa output thành dạng list có cấu trúc
        structured_items = []
        for delivery_date, chefs in grouped_by_date.items():
            structured_items.append({
                "delivery_date": delivery_date,
                "chefs": [
                    {
                        "chef_name": chef_name,
                        "items": items
                    }
                    for chef_name, items in chefs.items()
                ]
            })

        return {
            "items": structured_items,
            "total_amount": float(total),
            "message": message
        }
        
    @staticmethod
    def get_selected_items(cart, delivery_date):
        # Get selected cart items
        items = cart.cartitem_fk_cart.filter(
            is_selected=True, 
            delivery_date=delivery_date
        )
        
        # Get dish IDs and fetch all dishes at once
        dish_ids = [item.dish_id for item in items]
        dishes = Dish.objects.in_bulk(dish_ids)
        
        return [
            {
                "dish_uid": dishes[item.dish_id].uid,
                "dish_name": dishes[item.dish_id].name,
                "quantity": item.quantity,
                "price": float(dishes[item.dish_id].price),
                "subtotal": float(dishes[item.dish_id].price * item.quantity),
            }
            for item in items
        ]