from django.db import models
from pydantic import ValidationError
from utils.models import BaseModel
from utils.enums import AllergyModeEnum, DietLevelEnum, DietModeEnum, ChefSuspensionLevelEnum
from utils.types import User
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator

class CustomerProfile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )
    bio = models.TextField(blank=True, null=True)
    
    avatar = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="customer_profile_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
    )
    
    points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_onboarded = models.BooleanField(default=False)

    diet_mode = models.CharField(
        max_length=17,
        choices=DietModeEnum.choices,
        default=DietModeEnum.NONE,
    )

    diet_level = models.CharField(
        max_length=16,
        choices=DietLevelEnum.choices,
        default=DietLevelEnum.NONE,
    )
    allergy_mode = models.CharField(
        max_length=16,
        choices=AllergyModeEnum.choices,
        default=AllergyModeEnum.WARN,
    )
    class Meta:
        constraints = [
            CheckConstraint(
                check=(
                    Q(diet_mode=DietModeEnum.NONE, diet_level=DietLevelEnum.NONE)
                    |
                    (
                        ~Q(diet_mode=DietModeEnum.NONE)
                        & ~Q(diet_level=DietLevelEnum.NONE)
                    )
                ),
                name="diet_mode_level_consistency",
            )
        ]
     
    def clean(self):
        if self.diet_mode == DietModeEnum.NONE and self.diet_level != DietLevelEnum.NONE:
            raise ValidationError("Diet level must be NONE when diet mode is NONE")
    def __str__(self):
        return self.user.username
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
class CustomerFavoriteDish(BaseModel):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="customer_favorite_dish_user_fk_user",
        to_field="id",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="dish_uid",
        related_name="customer_favorite_dish_fk_dish",
        db_constraint=True,
        null=False,
        blank=False,
    )
    deleted=models.BooleanField(default=False)
    
    class Meta:
        unique_together = ("user", "dish")

class ChefProfile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="chef_profile"
    )
    bio = models.TextField(blank=True, null=True)
    specialty = models.TextField(blank=True, null=True)
    
    avatar = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="chef_profile_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
    )
    
    kitchen_address = models.CharField(max_length=255, null=True, blank=True, help_text="Số nhà, Tên tòa nhà")
    kitchen_street = models.CharField(max_length=255, null=True, blank=True)
    kitchen_ward = models.CharField(max_length=100, null=True, blank=True)
    kitchen_district = models.CharField(max_length=100, null=True, blank=True)
    kitchen_city = models.CharField(max_length=100, null=True, blank=True)
    
    kitchen_latitude = models.FloatField(null=True, blank=True)
    kitchen_longitude = models.FloatField(null=True, blank=True)
    
    rating = models.FloatField(default=0.0)
    number_of_orders = models.IntegerField(default=0)

    is_accepting_orders = models.BooleanField(default=True)
    suspension_level = models.CharField(
        max_length=16,
        choices=ChefSuspensionLevelEnum.choices,
        default=ChefSuspensionLevelEnum.NONE,
    )

    def __str__(self):
        return self.user.username


class ChefPaymentInfo(models.Model):
    """
    Thông tin thanh toán của chef để nhận tiền payout
    """
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="chef_payment_info"
    )
    
    # Thông tin ngân hàng
    bank_name = models.CharField(max_length=255, help_text="Tên ngân hàng (VD: Vietcombank, VPBank)")
    bank_code = models.CharField(max_length=20, help_text="Mã BIN/Bank code dùng cho payout")
    bank_account_number = models.CharField(max_length=50, help_text="Số tài khoản ngân hàng")
    bank_account_name = models.CharField(max_length=255, help_text="Tên chủ tài khoản")
    bank_branch = models.CharField(max_length=255, blank=True, null=True, help_text="Chi nhánh (optional)")
    
    # Thông tin định danh
    citizen_id = models.CharField(max_length=20, blank=True, null=True, help_text="CCCD/CMND")
    tax_code = models.CharField(max_length=20, blank=True, null=True, help_text="Mã số thuế (nếu có)")
    
    # Trạng thái xác thực
    is_verified = models.BooleanField(default=False, help_text="Đã xác thực thông tin chưa")
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'chef_payment_info'
        verbose_name = 'Chef Payment Information'
        verbose_name_plural = 'Chef Payment Information'
    
    def __str__(self):
        return f"{self.user.email} - {self.bank_name} ({self.bank_account_number})"
    
class CustomerAddress(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="customer_address_user_fk_user",
        to_field="id",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )
    #Địa chỉ 4 cấp như cũ
    address= models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    ward = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    selected = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    
    def full_address(self):
        return f"{self.address}, {self.street}, {self.ward}, {self.district}, {self.city}"
    
