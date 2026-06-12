from uuid import UUID
from menu.models import Menu
from menu.schemas.requests import (
    MenuSchema,
    MenuDishSchema
)
from utils.types import TUser
from utils.enums import MenuStatusEnum
from menu.models import MenuDish
from dish.models import Dish

class MenuORM:
    @staticmethod
    def create_new_menu(user: TUser, payload: MenuSchema):
        return Menu.objects.create(**payload.dict(), chef=user, updater=user)
    
    @staticmethod
    def get_all_menus_of_chef(id: str): #TODO:thêm phần đánh giá, rồi sắp xếp theo đánh giá cao nhất
        """
        - Loại bỏ menu bị đánh dấu deleted, chỉ lấy menu đang ACTIVE
        - Sắp xếp theo tên (name) tăng dần
        """
        menus = Menu.objects.filter(
            chef=id,
            deleted=False,
            status=MenuStatusEnum.ACTIVE,
        ).order_by("name")
        return list(menus)
    
        
    @staticmethod
    def get_dish_menu_elements(menu: Menu):
        """
        Lấy tất cả MenuDish thuộc menu, kèm thông tin dish.
        Chỉ lấy những món active.
        Gán vào menu.dishes để tiện sử dụng.
        """
        # Queryset lấy tất cả MenuDish active kèm dish
        menudishes_qs = MenuDish.objects.filter(menu=menu, active=True).select_related("dish")

        # Gán vào menu.dishes
        setattr(menu, "dishes", list(menudishes_qs))
        return menu
    
    @staticmethod
    def get_all_dishes_in_menu(menu: Menu):
        """
        Lấy tất cả MenuDish thuộc menu, kèm thông tin dish.
        Chỉ lấy những món active.
        Trả về list món (dish) thay vì list MenuDish
        """
        # Queryset lấy tất cả MenuDish active kèm dish
        menudishes_qs = MenuDish.objects.filter(menu=menu, active=True).select_related("dish")

        # Trả về list món (dish)
        return [menudish.dish for menudish in menudishes_qs]
    
    def exists_menu_dish(self, *, menu, dish) -> bool:
        """
        Trả về True nếu đã có MenuDish liên kết menu và dish.
        Nhận cả instances hoặc values phù hợp với filter().
        """
        return MenuDish.objects.filter(menu=menu, dish=dish).exists()

    
    @staticmethod
    def create_menu_dish(menu: Menu, dish: Dish, position: int = 0, active: bool = True):
        return MenuDish.objects.create(menu=menu, dish=dish, position=position, active=active)

    @staticmethod
    def get_menu_by_uid(uid: UUID):
        try:
            return Menu.objects.get(uid=uid)
        except Menu.DoesNotExist:
            return None


    @staticmethod
    def get_menu_by_uid_include_deleted(uid: UUID):
        try:
            return Menu.objects.get(uid=uid)
        except Menu.DoesNotExist:
            return None

    @staticmethod
    def update_menu(user: TUser, menu: Menu, payload: MenuSchema):
        for key, value in payload.dict().items():
            if hasattr(menu, key):
                setattr(menu, key, value)
        menu.updater = user

        menu.save()
        return menu

    @staticmethod
    def soft_delete_menu(user: TUser, menu: Menu):
        menu.deleted = True
        menu.updater = user
        menu.save()
        return True

    @staticmethod
    def restore_menu(user: TUser, menu: Menu):
        menu.deleted = False
        menu.updater = user
        menu.save()
        return True

    @staticmethod
    def delete_menu(menu: Menu) -> bool:
        menu.delete()
        return True

    # dành cho chef, xem cả menu đang active lẫn unactive, nhưng không xem menu đã bị xóa (deleted=True)
    @staticmethod
    def get_all_my_menus(id: str):
        """
        - Lấy tất cả menu của chef, bao gồm cả menu đang active lẫn unactive, nhưng không lấy menu đã bị xóa (deleted=True)
        - Sắp xếp theo tên (name) tăng dần
        """
        try:
            return Menu.objects.filter(
                chef=id,
                deleted=False,
            ).order_by("name")
        except Menu.DoesNotExist:
            return None
        
    @staticmethod
    def get_all_dishes_in_menu_for_chef(menu: Menu, active: bool | None = None):
        """
        Lấy tất cả MenuDish thuộc menu, kèm thông tin dish.
        Dành cho chef, nên không phân biệt active hay không.
        Không lấy những món đã bị xóa (deleted=True).
        Trả về payload Dish + metadata trong MenuDish (active, position).
        """
        #Nếu active=None thì lấy tất cả, còn nếu active=True/False thì filter theo active
        if active is None:
            menudishes_qs = (
                MenuDish.objects.filter(menu=menu)
                .select_related("dish", "dish__attachment")
                .exclude(dish__deleted=True)
            )
        else:
            menudishes_qs = (
                MenuDish.objects.filter(menu=menu, active=active)
                .select_related("dish", "dish__attachment")
                .exclude(dish__deleted=True)
            )
        return [
            {
                "uid": md.dish.uid,
                "name": md.dish.name,
                "category": md.dish.category,
                "description": md.dish.description,
                "price": md.dish.price,
                "status": md.dish.status,
                "avg_rating": md.dish.avg_rating,
                "active": md.active,
                "position": md.position,
                "public_url": md.dish.attachment.public_url if md.dish.attachment else None,
            }
            for md in menudishes_qs
        ]

    @staticmethod
    def activate_menu(user: TUser, menu: Menu):
        menu.status = MenuStatusEnum.ACTIVE
        menu.updater = user
        menu.save()
        return menu
    
    @staticmethod
    def deactivate_menu(user: TUser, menu: Menu):
        menu.status = MenuStatusEnum.INACTIVE
        menu.updater = user
        menu.save()
        return menu
    
    @staticmethod
    def activate_dish_in_menu(menu: Menu, dish: Dish):
        menudish = MenuDish.objects.get(menu=menu, dish=dish)
        menudish.active = True
        menudish.save()
        return menudish 
    
    @staticmethod
    def deactivate_dish_in_menu(menu: Menu, dish: Dish):
        menudish = MenuDish.objects.get(menu=menu, dish=dish)
        menudish.active = False
        menudish.save()
        return menudish 
    
    