from django.contrib.auth import get_user_model
from django.db import models

from utils.enums import MenuStatusEnum
from utils.models import BaseModel


User = get_user_model()

class Menu(BaseModel):
    name = models.CharField()
    description = models.TextField(blank=True, null=True)

    # trạng thái menu: ACTIVE / INACTIVE / DRAFT
    status = models.CharField(
        max_length=16,
        choices=MenuStatusEnum.choices,
        default=MenuStatusEnum.ACTIVE,
    )

    # Chef sở hữu menu này
    chef = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        to_field="id",
        db_column="chef_id",
        related_name="menu_fk_chef",
        db_constraint=True,
        null=True,
        blank=True,
    )

    updater = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updater_id",
        related_name="menu_fk_updater",
        db_constraint=True,
        null=True,
        blank=True,
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
        
class MenuDish(models.Model):
    menu = models.ForeignKey(
        to=Menu,
        on_delete=models.CASCADE,           # Xóa menu → xóa luôn mối liên kết
        to_field="uid",
        db_column="menu_id",
        related_name="menudish_fk_menu",
        db_constraint=True,
        null=False,     
        blank=False,
    )

    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.CASCADE,    # Xóa dish → xóa liên kết
        to_field="uid",
        db_column="dish_id",
        related_name="menudish_fk_dish",
        db_constraint=True,
        null=True,
        blank=True,
    )
    
    # Tùy chọn thêm: có thể thêm thứ tự
    position = models.PositiveIntegerField(default=0)
    
    # Trạng thái món trong menu (có bày bán hay không)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("menu", "dish")  # Tránh trùng món trong 1 menu
        ordering = ("position",)
        
    def __str__(self):
        status = "Active" if self.active else "Inactive"
        return f"{self.menu.name} - {self.dish.name} ({status})"