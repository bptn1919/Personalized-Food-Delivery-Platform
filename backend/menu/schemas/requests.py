from ninja import ModelSchema

from menu.models import Menu
from utils.enums import MenuStatusEnum
from uuid import UUID
from ninja import Schema

class MenuSchema(ModelSchema):
    status: MenuStatusEnum

    class Meta:
        model = Menu
        exclude = [
            "created_at",
            "deleted",
            "chef",
            "uid",
            "updated_at",
            "updater",
        ]
        

class MenuDishSchema(Schema):
    menu_uid: UUID
    dish_uid: UUID
    position: int | None = 0
    active: bool | None = True


class AddDishToMenuSchema(Schema):
    """Schema for POST /chef/menus/{uid}/add-dish/ - menu_uid is in path, not body"""
    dish_uid: UUID
    position: int = 0
    active: bool = True



