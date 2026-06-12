from django.db import models

from utils.models import BaseModel
from utils.types import User

class Cart(BaseModel):
    owner = models.OneToOneField(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="cart_fk_owner",  
        db_constraint=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Cart of {self.owner}"

class CartItem(BaseModel):
    cart = models.ForeignKey(
        to=Cart,
        on_delete=models.CASCADE,
        related_name="cartitem_fk_cart",
        db_constraint=True,
        null=True,
        blank=True,
    )
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.CASCADE,
        related_name="cart_items",
        db_constraint=True,
        null=True,
        blank=True,
    )
    delivery_date = models.DateField()  
    quantity = models.PositiveIntegerField(default=1)
    is_selected = models.BooleanField(default=False)  # tick chọn hay không

    class Meta:
        unique_together = ("cart", "dish", "delivery_date")

    def subtotal(self):
        return self.quantity * self.dish.price

    def __str__(self):
        return f"{self.dish.name} x {self.quantity} on {self.delivery_date}"
