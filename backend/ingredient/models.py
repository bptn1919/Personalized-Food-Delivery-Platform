from django.db import models

from utils.enums import IngredientCategoryEnum, IngredientImportStatusEnum, IngredientSourceEnum
from utils.functions.remove_accents import remove_accents
from utils.models import BaseModel
from utils.types import User


class Ingredient(BaseModel):
    name = models.TextField()
    name_no_accent = models.TextField(blank=True, editable=False)
    category = models.CharField(
        max_length=16,
        choices=IngredientCategoryEnum.choices,
    )

    weight = models.FloatField(null=True, blank=True) #g

    energy = models.FloatField(null=True, blank=True) #kcal

    protein = models.FloatField(null=True, blank=True) #g
    lipid = models.FloatField(null=True, blank=True) #g
    carbohydrate = models.FloatField(null=True, blank=True) #g
    fiber = models.FloatField(null=True, blank=True) #g
    natri = models.FloatField(null=True, blank=True) #no comment = mg
    kali = models.FloatField(null=True, blank=True)
    cholesterol = models.FloatField(null=True, blank=True)
    retinol = models.FloatField(null=True, blank=True) #µg
    caroten = models.FloatField(null=True, blank=True) #µg
    vitamin_b_1 = models.FloatField(null=True, blank=True)
    vitamin_b_2 = models.FloatField(null=True, blank=True)
    vitamin_pp = models.FloatField(null=True, blank=True)
    vitamin_c = models.FloatField(null=True, blank=True)
    calcium = models.FloatField(null=True, blank=True)
    phosphorus = models.FloatField(null=True, blank=True)
    fe = models.FloatField(null=True, blank=True)
    mg = models.FloatField(null=True, blank=True)
    zn = models.FloatField(null=True, blank=True)

    source = models.CharField(
        max_length=15,
        choices=IngredientSourceEnum.choices,
        default=IngredientSourceEnum.USDA)

    deleted = models.BooleanField(default=False, null=False, blank=False)

    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="ingredient_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )

    updater = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updater_id",
        related_name="ingredient_fk_updater",
        db_constraint=True,
        null=True,
        blank=True,
    )

    attachment = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="ingredient_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.name:
            self.name_no_accent = remove_accents(self.name)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ("name",)


class IngredientAlias(BaseModel):
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="ingredient_uid",
        related_name="aliases",
        db_constraint=True,
    )
    alias = models.TextField()
    alias_no_accent = models.TextField(blank=True, editable=False)
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="created_by_id",
        related_name="ingredient_alias_fk_creator",
        db_constraint=True,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.alias:
            self.alias_no_accent = remove_accents(self.alias)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.alias} -> {self.ingredient.name}"

    class Meta:
        ordering = ("alias",)
        constraints = [
            models.UniqueConstraint(fields=["alias_no_accent"], name="unique_ingredient_alias_no_accent"),
        ]

class IngredientSuggestion(BaseModel):
    suggested_name = models.TextField()
    suggested_name_no_accent = models.TextField(blank=True, editable=False)
    suggested_category = models.CharField(
        max_length=16,
        choices=IngredientCategoryEnum.choices,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingredient_suggestion_fk_creator",
    )

    status = models.CharField(
        max_length=10,
        choices=IngredientImportStatusEnum.choices,
        default=IngredientImportStatusEnum.PENDING)
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingredient_suggestion_fk_verified_by",
    )   
    verified_at = models.DateTimeField(null=True, blank=True)
    # tại sao xác thực / từ chối
    rejection_reason = models.TextField(null=True, blank=True)
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="ingredient_uid",
        related_name="ingredient_suggestion_fk_resolved_ingredient",
        db_constraint=True,
        null=True,
        blank=True,
    )

    resolved_alias = models.ForeignKey(
        to=IngredientAlias,
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="resolved_alias_uid",
        related_name="ingredient_suggestion_fk_resolved_alias",
        db_constraint=True,
        null=True,
        blank=True,
    )

    resolution_note = models.TextField(null=True, blank=True)
    attachment = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="ingredient_suggestion_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    def save(self, *args, **kwargs):
        if self.suggested_name:
            self.suggested_name_no_accent = remove_accents(self.suggested_name)
        return super().save(*args, **kwargs)
    

    def __str__(self) -> str:
        return self.suggested_name

    class Meta:
        ordering = ("-created_at",)


class FavouriteIngredient(BaseModel):
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="ingredient_uid",
        related_name="favourite_ingredient_fk_ingredient",
        db_constraint=True,
    )

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        to_field="id",
        db_column="user_id",
        related_name="favourite_ingredient_fk_user",
        db_constraint=True,
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        unique_together = ("ingredient", "user")


class AllergicIngredient(BaseModel):
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="ingredient_uid",
        related_name="allergic_ingredient_fk_ingredient",
        db_constraint=True,
    )

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        to_field="id",
        db_column="user_id",
        related_name="allergic_ingredient_fk_user",
        db_constraint=True,
    )
    deleted = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        unique_together = ("ingredient", "user")