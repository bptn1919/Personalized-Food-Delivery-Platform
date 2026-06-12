from django.db import models
from utils.enums import DeliveryTypeEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatus
from utils.models import BaseModel
from utils.types import User

class Checkout(BaseModel):
  owner = models.ForeignKey(
      to=User,
      on_delete=models.SET_NULL,
      to_field="id",
      db_column="owner_id",
      related_name="checkout_fk_owner",
      db_constraint=True,
      null=True,
      blank=True,
  )
  full_name = models.CharField(max_length=255)
  phone_number = models.CharField(max_length=20)
  sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
  tax_and_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
  delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
  total_price = models.DecimalField(max_digits=30, decimal_places=2, default=0)
  total_discount = models.DecimalField(max_digits=32, decimal_places=2, default=0)
  delivery_address = models.ForeignKey(
      to="profile.CustomerAddress",          # app_name.ModelName
      on_delete=models.SET_NULL,              # Không xóa Order nếu Address bị xóa
      to_field="id",                         # Trỏ theo khóa chính kiểu UUID
      db_column="delivery_address_id",       # Tên cột rõ ràng trong DB
      related_name="checkout_fk_delivery_address", 
      db_constraint=True,                     # Tạo ràng buộc FK trong DB
      null=True,                              # Cho phép NULL nếu user xóa địa chỉ
      blank=True,
  )
  payment_method = models.CharField(
      max_length=16,
      choices=PaymentMethodEnum.choices,
      default="COD",
  )
  delivery_date = models.DateField()
  delivery_time = models.TimeField()


    
class Order(BaseModel):
    checkout = models.ForeignKey(
        to=Checkout,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="checkout_uid",
        related_name="order_fk_checkout",
        db_constraint=True,
        null=False,
        blank=False,
    )
    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="order_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )
    chef = models.ForeignKey(
        to=User,       
        on_delete=models.CASCADE,
        to_field="id",
        db_column="chef_id",
        related_name="order_fk_chef",
        null=True,
        blank=True
    )
    
    delivery_name = models.CharField(max_length=255, null=True, blank=True, help_text="Tên người nhận lúc đặt đơn")
    delivery_phone = models.CharField(max_length=20, null=True, blank=True, help_text="SĐT người nhận lúc đặt đơn")
    delivery_address_text = models.CharField(max_length=500, null=True, blank=True, help_text="Chuỗi địa chỉ đầy đủ")
    delivery_latitude = models.FloatField(null=True, blank=True, help_text="Vĩ độ giao hàng")
    delivery_longitude = models.FloatField(null=True, blank=True, help_text="Kinh độ giao hàng")
    
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryTypeEnum.choices,
        default=DeliveryTypeEnum.THIRD_PARTY, # Set mặc định là gọi ship cho an toàn
        help_text="Phương thức giao hàng của đơn này"
    )
    
    
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_and_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Discount fields - stored separately for clarity
    platform_subtotal_discount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Giảm giá từ platform subtotal voucher (allocated proportionally)"
    )
    platform_shipping_discount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Giảm giá từ platform shipping voucher (allocated proportionally)"
    )
    shop_discount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Giảm giá từ shop voucher (chef's voucher)"
    )
    total_discount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Tổng giảm giá (platform + shop)"
    )
    total_price = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    status = models.CharField(
        max_length=16,
        choices=OrderStatusEnum.choices,
        default=OrderStatusEnum.PENDING,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,  # ← Set default
    )
    def __str__(self):
        return f"Order {self.uid} - {self.owner}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        to=Order,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="order_uid",
        related_name="orderitem_fk_order",
        db_constraint=True,
        null=False,
        blank=False,
    )
    
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="dish_uid",
        related_name="orderitem_fk_dish",
        db_constraint=True,
        null=True,
        blank=True,
    )
    dish_name = models.CharField(max_length=255)
    dish_image_url = models.URLField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # giá tại thời điểm đặt hàng

    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.dish.name} ({self.quantity})"
