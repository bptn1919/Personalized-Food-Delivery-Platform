

from ninja import ModelSchema
from menu.models import Menu, MenuDish

class MenuResponse(ModelSchema):
    class Meta:
        model = Menu
        exclude = [
            "created_at",
            "deleted",
            "updated_at",
            "updater",
        ]
        
class MenuDishResponse(ModelSchema):
    class Meta:
        model = MenuDish
        fields = "__all__"
        