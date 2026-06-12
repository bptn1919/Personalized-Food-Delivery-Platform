from django.db import models
from utils.functions.remove_accents import remove_accents
from utils.enums import DishCategoryEnum, DishStatusEnum, DishLocationTypeEnum, IngredientSourceEnum, IngredientImportStatusEnum
from utils.models import BaseModel
from utils.types import User
from django.db.models import Q, CheckConstraint
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class DishLocation(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    type = models.CharField(max_length=20, choices=DishLocationTypeEnum.choices)

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children"
    )

    class Meta:
        unique_together = ("name", "parent")
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["parent"]),
        ]
        constraints = [
            CheckConstraint(
                condition=(
                    Q(type=DishLocationTypeEnum.REGION, parent_id__isnull=True) |
                    Q(type=DishLocationTypeEnum.SUBREGION, parent_id__isnull=False) |
                    Q(type=DishLocationTypeEnum.COUNTRY, parent_id__isnull=False)
                ),
                name="valid_location_parent_null"
            )
        ]

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):
        # ❌ self-parent
        if self.parent_id and self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Cannot be its own parent."})

        # ROOT
        if not self.parent:
            if self.type != DishLocationTypeEnum.REGION:
                raise ValidationError("Only REGION can be root.")
            return

        # hierarchy rule
        allowed_parent = {
            DishLocationTypeEnum.REGION: None,
            DishLocationTypeEnum.SUBREGION: DishLocationTypeEnum.REGION,
            DishLocationTypeEnum.COUNTRY: DishLocationTypeEnum.SUBREGION,
        }

        expected = allowed_parent[self.type]
        if self.parent.type != expected:
            raise ValidationError(
                f"{self.type} must have parent type {expected}"
            )

        # cycle check
        ancestor = self.parent
        while ancestor:
            if self.pk and ancestor.pk == self.pk:
                raise ValidationError("Cycle detected")
            ancestor = ancestor.parent

    # -------------------------
    # SAVE (slug auto-gen)
    # -------------------------
    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(remove_accents(self.name)) or "location"

            slug = base_slug
            i = 2
            while DishLocation.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1

            self.slug = slug

        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Dish(BaseModel): 
    name = models.TextField()
    name_no_accent = models.TextField(blank=True, editable=False)

    # Enum để phân loại: FOOD / BEVERAGES / DESSERT
    category = models.CharField(
        max_length=16,
        choices=DishCategoryEnum.choices,
    )

    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    # available_quantity = models.IntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=DishStatusEnum.choices,
        default="AVAILABLE",
    )

    location = models.ForeignKey(
        to=DishLocation,
        on_delete=models.SET_NULL,
        db_column="location_id",
        related_name="dish_fk_location",
        null=True,
        blank=True,
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="dish_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )

    updater = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updater_id",
        related_name="dish_fk_updater",
        db_constraint=True,
        null=True,
        blank=True,
    )

    attachment = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="dish_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
    )

    avg_rating = models.FloatField(default=0)
    final_score = models.FloatField(default=0)
    is_suspended = models.BooleanField(default=False)
    serving_size = models.PositiveSmallIntegerField(
        default=1,
        help_text="Số người ăn cho 1 phần (1=cá nhân, 4=gia đình/lẩu). Dùng để chuẩn hóa dinh dưỡng per-serving.",
    )
    def clean(self):
        if self.location and self.location.type != DishLocationTypeEnum.COUNTRY:
            raise ValidationError("Dish must belong to a COUNTRY.")

    def save(self, *args, **kwargs):
        if self.name:
            self.name_no_accent = remove_accents(self.name)
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ("name",)
        
class DishIngredient(BaseModel):
    dish = models.ForeignKey(
        to=Dish,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="dish_uid",
        related_name="dish_ingredient_fk_dish",
        db_constraint=True,
        null=False,
        blank=False,
    )

    ingredient = models.ForeignKey(
        to="ingredient.Ingredient",
        on_delete=models.RESTRICT,
        to_field="uid",
        db_column="ingredient_uid",
        related_name="dish_ingredient_fk_ingredient",
        db_constraint=True,
        null=True,
        blank=True,
    )

    custom_name = models.TextField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=IngredientSourceEnum.choices,
        default=IngredientSourceEnum.USDA,
    )
    approval_status = models.CharField(
        max_length=16,
        choices=IngredientImportStatusEnum.choices,
        default=IngredientImportStatusEnum.PENDING,
    )
    suggestion = models.ForeignKey(
        to="ingredient.IngredientSuggestion",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="suggestion_uid",
        related_name="dish_ingredient_fk_suggestion",
        db_constraint=True,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="created_by_id",
        related_name="dish_ingredient_fk_creator",
        db_constraint=True,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updated_by_id",
        related_name="dish_ingredient_fk_updater",
        db_constraint=True,
        null=True,
        blank=True,
    )   



    weight = models.FloatField(null=True, blank=True)
    energy = models.FloatField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True)
    lipid = models.FloatField(null=True, blank=True)
    carbohydrate = models.FloatField(null=True, blank=True)
    fiber = models.FloatField(null=True, blank=True)
    natri = models.FloatField(null=True, blank=True)
    kali = models.FloatField(null=True, blank=True)
    cholesterol = models.FloatField(null=True, blank=True)
    retinol = models.FloatField(null=True, blank=True)
    caroten = models.FloatField(null=True, blank=True)
    vitamin_b_1 = models.FloatField(null=True, blank=True)
    vitamin_b_2 = models.FloatField(null=True, blank=True)
    vitamin_pp = models.FloatField(null=True, blank=True)
    vitamin_c = models.FloatField(null=True, blank=True)
    calcium = models.FloatField(null=True, blank=True)
    phosphorus = models.FloatField(null=True, blank=True)
    fe = models.FloatField(null=True, blank=True)
    mg = models.FloatField(null=True, blank=True)
    zn = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(
        default=1.0,
        null=True,
        blank=True,
        help_text="Confidence score (0-1) based on ingredient validation flags, source, and status"
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    @property
    def computed_ingredient_name(self):
        if self.custom_name:
            return self.custom_name
        return self.ingredient.name if self.ingredient else "Unknown"

    @property
    def computed_ingredient_uid(self):
        return self.ingredient.uid if self.ingredient else None

    class Meta:
        unique_together = ("dish", "ingredient")

class DishAvailability(models.Model):
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="dish_uid",
        related_name="availability_fk_dish",
        db_constraint=True,
        null=False,
        blank=False,
    )

    # Ngày món ăn này được bày bán
    available_date = models.DateField()

    # Trạng thái trong ngày (có thể có hoặc tạm ngừng)
    is_available = models.BooleanField(default=True)

    # Số lượng còn trong ngày (tuỳ chọn)
    available_quantity = models.PositiveIntegerField(default=0)

    # Chef có thể ghi chú thêm nếu muốn
    note = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("dish", "available_date")  # 1 dish chỉ có 1 record mỗi ngày
        ordering = ("available_date",)

    def __str__(self):
        return f"{self.dish.name} on {self.available_date} ({'Available' if self.is_available else 'Unavailable'})"


class DishAlias(models.Model):
    """Mapping từ tên gọi khác (alias) -> chính thức Dish
    Dùng để fuzzy search và semantic matching"""
    
    dish = models.ForeignKey(
        to=Dish,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="dish_uid",
        related_name="aliases",
        db_constraint=True,
        null=False,
        blank=False,
    )
    
    # Tên gọi khác (ví dụ: "Phở bò" -> aliases: "phở", "phở hà nội", "phở bò lò")
    alias_name = models.TextField()
    alias_name_no_accent = models.TextField(blank=True, editable=False)
    
    # Độ tương đồng với tên chính (0-1), dùng cho ranking
    similarity_score = models.FloatField(default=0.9)
    
    # Loại alias: REGIONAL (phương ngữ), ABBREVIATION (viết tắt), TRANSLATION (dịch)
    alias_type = models.CharField(
        max_length=20,
        choices=[
            ('REGIONAL', 'Regional Name'),
            ('ABBREVIATION', 'Abbreviation'),
            ('TRANSLATION', 'Translation'),
            ('SYNONYM', 'Synonym'),
        ],
        default='SYNONYM',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("dish", "alias_name_no_accent")
        indexes = [
            models.Index(fields=["dish"]),
            models.Index(fields=["alias_name_no_accent"]),
            models.Index(fields=["alias_type"]),
        ]
    
    def save(self, *args, **kwargs):
        if self.alias_name:
            self.alias_name_no_accent = remove_accents(self.alias_name)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.alias_name} -> {self.dish.name}"
