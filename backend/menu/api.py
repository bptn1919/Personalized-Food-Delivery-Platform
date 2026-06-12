from uuid import UUID

from utils.enums import UserTypeEnum
from exceptions.dishes import DishNotFoundException
from exceptions.menus import MenuDoesNotExist, MenuIsNotDeleted, PermissionDenied
from menu.schemas.requests import (
    MenuSchema,
    MenuDishSchema,
    AddDishToMenuSchema,
)
from menu.schemas.responses import MenuResponse, MenuDishResponse
from dish.schemas.responses import DishResponse, AllDishesInMenuResponse
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, patch, post, put
from utils.types import AuthenticatedRequest
from utils.permissions.decorators import require_group, require_permission, require_object_permission
from menu.models import Menu

from .services import MenuService
from typing import List
    
@api(prefix_or_class="menus", tags=["Menu"], auth=AuthBear())
class MenuController(Controller):
    def __init__(self, service: MenuService) -> None:
        self.service = service

# chef api
    @get("/mine",response=List[MenuResponse])
    @require_group(UserTypeEnum.CHEF)
    def get_all_my_menus(self, request: AuthenticatedRequest):
        """
        Lấy toàn bộ menu, dành cho chef
        """
        return self.service.get_all_my_menus(id=request.user.id)
    # customer api
    @get("/chef/{chef_id}", response=List[MenuResponse])
    def get_all_menus_of_chef(self, chef_id: int):
        """
        Lấy toàn bộ menu, dành cho customer, chỉ lấy những menu đang ACTIVE
        """
        return self.service.get_all_menus_of_chef(id=chef_id)
    
    @get("/{uid}", response=MenuResponse, exceptions=(MenuDoesNotExist,))
    def get_menu(self, uid: UUID):
        """
        Lấy chi tiết menu theo uid, giao diện customer, chỉ lấy những menu đang ACTIVE
        """
        return self.service.get_menu(uid=uid)
    
    @get("/{uid}/dishes", response=List[DishResponse], exceptions=(MenuDoesNotExist,))
    def get_all_dishes_in_menu(self, uid: UUID):
        """
        Lấy toàn bộ món trong menu theo uid, giao diện customer, chỉ lấy những món đang ACTIVE
        """
        return self.service.get_all_dishes_in_menu(uid=uid)
    

    # API dành cho chef để lấy toàn bộ dish trong menu, kèm thông tin dish, không cần phân biệt active hay không, để hiển thị ở giao diện quản lý menu của chef
    @get("/{uid}/all-dishes", response=List[AllDishesInMenuResponse], exceptions=(MenuDoesNotExist,))
    @require_group(UserTypeEnum.CHEF)
    def get_all_dishes_in_menu_for_chef(self, request: AuthenticatedRequest, uid: UUID, active: bool | None = None):
        """
        Lấy toàn bộ món trong menu theo uid, dành cho chef, không phân biệt active hay không
        """
        return self.service.get_all_dishes_in_menu_for_chef(uid=uid, user=request.user, active=active)

    # Chef ACTIVE MENU
    @patch("/{uid}/activate", response=MenuResponse, exceptions=(MenuDoesNotExist, PermissionDenied))
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def activate_menu(self, request: AuthenticatedRequest, uid: UUID):
        """
        Kích hoạt menu, chỉ dành cho chef
        """
        return self.service.active_menu(user=request.user, uid=uid)
    
    #Chef UNACTIVE MENU
    @patch("/{uid}/deactivate", response=MenuResponse, exceptions=(MenuDoesNotExist, PermissionDenied))
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def deactivate_menu(self, request: AuthenticatedRequest, uid: UUID):
        """
        Hủy kích hoạt menu, chỉ dành cho chef
        """
        return self.service.deactivate_menu(user=request.user, uid=uid)
    
    #Chef ACTIVE Dish in Menu
    @patch("/{uid}/dishes/{dish_uid}/activate", response=MenuDishResponse, exceptions=(MenuDoesNotExist, DishNotFoundException, PermissionDenied))
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def activate_dish_in_menu(self, request: AuthenticatedRequest, uid: UUID, dish_uid: UUID):
        """
        Kích hoạt món trong menu, chỉ dành cho chef
        """
        return self.service.activate_dish_in_menu(user=request.user, menu_uid=uid, dish_uid=dish_uid)
    
    #Chef UNACTIVE Dish in Menu
    @patch("/{uid}/dishes/{dish_uid}/deactivate", response=MenuDishResponse, exceptions=(MenuDoesNotExist, DishNotFoundException, PermissionDenied))
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def deactivate_dish_in_menu(self, request: AuthenticatedRequest, uid: UUID , dish_uid: UUID):
        """
        Hủy kích hoạt món trong menu, chỉ dành cho chef
        """
        return self.service.deactivate_dish_in_menu(user=request.user, menu_uid=uid, dish_uid=dish_uid)
    
    @post("", response=MenuResponse)
    @require_group(UserTypeEnum.CHEF)
    def create_new_menu(self, request: AuthenticatedRequest, payload: MenuSchema):
        return self.service.create_new_menu(user=request.user, payload=payload)
    
    @put("/{uid}", response=MenuResponse, exceptions=(PermissionDenied,))
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def update_menu(
        self, request: AuthenticatedRequest, uid: UUID, payload: MenuSchema
    ):
        return self.service.update_menu(user=request.user, uid=uid, payload=payload)

    @put("/{uid}/deleted", response=bool, exceptions=(PermissionDenied,))
    @require_object_permission('menu.delete_menu', Menu, owner_field='chef')
    def soft_delete_menu(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.soft_delete_menu(user=request.user, uid=uid)

    @delete("/{uid}", response=bool)
    @require_permission('menu.delete_menu')
    @require_group(UserTypeEnum.ADMIN)
    def hard_delete_menu(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.hard_delete_menu(uid=uid)

    @put(
        "/{uid}/restore",
        response=bool,
        exceptions=(MenuIsNotDeleted, MenuDoesNotExist, PermissionDenied),
    )
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def restore_menu(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.restore_menu(user=request.user, uid=uid)
    
    @post("/{uid}/add-dish/", response=MenuDishResponse)
    @require_object_permission('menu.change_menu', Menu, owner_field='chef')
    def add_dish_to_menu(self, request: AuthenticatedRequest, uid: UUID, payload: AddDishToMenuSchema):
        """
        Thêm món ăn vào menu, dành cho chef
        """
        return self.service.add_dish_to_menu(uid=uid, payload=payload)
