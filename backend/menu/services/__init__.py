from uuid import UUID

from exceptions.menus import MenuDoesNotExist, MenuIsNotDeleted, PermissionDenied
from menu.orm.menu import MenuORM
from dish.orm.dish import DishORM
from menu.schemas.requests import (
    MenuSchema,
    MenuDishSchema,
    AddDishToMenuSchema
)
from menu.models import Menu
from dish.models import Dish
from utils.enums import MenuStatusEnum
from utils.types import TUser
from exceptions.dishes import DishNotFoundException
from exceptions.menus import MenuDoesNotExist, MenuDishAlreadyExists


class MenuService:
    def __init__(self):  
        self.orm = MenuORM()
        self.dish_orm = DishORM()
    #TODO: dependencies.py, Dependency Injection (DI) theo chuẩn FastAPI/NinjaAPI.
    def create_new_menu(self, user: TUser, payload: MenuSchema):
        return self.orm.create_new_menu(user=user, payload=payload)
    
    def get_all_menus_of_chef(self, id: str):
        """
        Gọi ORM để lấy danh sách menu đang active của chef
        """

        return self.orm.get_all_menus_of_chef(id=id)
 
    
    def add_dish_to_menu(self, uid: UUID, payload: AddDishToMenuSchema):
        menu = Menu.objects.filter(uid=uid).first()
        if not menu:
            raise MenuDoesNotExist
        dish = Dish.objects.filter(uid=payload.dish_uid).first()
        if not dish:
            raise DishNotFoundException
        if self.orm.exists_menu_dish(menu=menu, dish=dish):
            raise MenuDishAlreadyExists

        return self.orm.create_menu_dish(menu=menu, dish=dish, position=payload.position, active=payload.active)

    def get_menu(self, uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu or menu.status != MenuStatusEnum.ACTIVE:
            raise MenuDoesNotExist
        return self.orm.get_dish_menu_elements(menu=menu)
    
    def get_all_dishes_in_menu(self, uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu or menu.status != MenuStatusEnum.ACTIVE:
            raise MenuDoesNotExist
        return self.orm.get_all_dishes_in_menu(menu=menu)

    def update_menu(self, user: TUser, uid: UUID, payload: MenuSchema):
        #Kiểm tra nguoi dùng có quyền sửa menu này không (chỉ có chef sở hữu menu mới được sửa)
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        return self.orm.update_menu(
            user=user, menu=menu, payload=payload
        )

    def soft_delete_menu(self, user: TUser, uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        return self.orm.soft_delete_menu(
            user=user, menu=menu
        )

    def hard_delete_menu(self, uid: UUID) -> bool:
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        return self.orm.delete_menu(menu=menu)

    def restore_menu(self, user: TUser, uid: UUID):
        menu = self.orm.get_menu_by_uid_include_deleted(uid=uid)
        if menu is None:
            raise MenuDoesNotExist
        if not menu.deleted:
            raise MenuIsNotDeleted
        if user.id != self.orm.get_menu_by_uid_include_deleted(uid=uid).chef.id:
            raise PermissionDenied
        return self.orm.restore_menu(user=user, menu=menu)
    
    def get_all_my_menus(self, id: str):
        """
        Gọi ORM để lấy danh sách menu đang active của chef
        """

        menus = self.orm.get_all_my_menus(id=id)
        if not menus:
            raise MenuDoesNotExist
        return menus
    
    def get_all_dishes_in_menu_for_chef(self, user: TUser, uid: UUID, active: bool | None = None):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        return self.orm.get_all_dishes_in_menu_for_chef(menu=menu, active=active)
    
    def active_menu(self, user: TUser, uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        return self.orm.activate_menu(user=user, menu=menu)
    
    def deactivate_menu(self, user: TUser, uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        return self.orm.deactivate_menu(user=user, menu=menu)
    
    def activate_dish_in_menu(self, user: TUser, menu_uid: UUID, dish_uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=menu_uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        dish = Dish.objects.filter(uid=dish_uid).first()
        if not dish:
            raise DishNotFoundException
        return self.orm.activate_dish_in_menu(menu=menu, dish=dish)

    def deactivate_dish_in_menu(self, user: TUser, menu_uid: UUID, dish_uid: UUID):
        menu = self.orm.get_menu_by_uid(uid=menu_uid)
        if not menu:
            raise MenuDoesNotExist
        if user.id != menu.chef.id:
            raise PermissionDenied
        dish = Dish.objects.filter(uid=dish_uid).first()
        if not dish:
            raise DishNotFoundException
        return self.orm.deactivate_dish_in_menu(menu=menu, dish=dish)


