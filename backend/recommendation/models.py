from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from utils.models import BaseModel
from utils.enums import AllergyModeEnum, DietLevelEnum, DietModeEnum, GenderEnum, ActivityLevelEnum, GoalEnum, MealTimeEnum, MealSourceEnum
from utils.types import User

class UserFoodPreferenceFeature(BaseModel):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="user_food_preference_feature_fk_user",
        db_index=True,
    )

    # =========================
    # HARD CONSTRAINTS
    # =========================
    allergic_ingredient_ids = models.JSONField(default=list, blank=True)

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

    # =========================
    # SOFT PREFERENCES
    # =========================
    favorite_ingredient_ids = models.JSONField(default=list, blank=True)

    favorite_dish_ids = models.JSONField(default=list, blank=True)

    # =========================
    # OPTIONAL (AI / ML)
    # =========================
    embedding = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
    )
    
    class Meta:
        db_table = "user_food_preference_feature"

    def __str__(self):
        return f"UserFoodPreferenceFeature(user_id={self.user_id})"


class UserDailyNutrition(BaseModel):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="user_daily_nutrition_fk_user",
        db_index=True,
    )
    date = models.DateField(db_index=True)
    is_active = models.BooleanField(default=True)

    age = models.PositiveIntegerField(default=25)
    gender = models.CharField(
        max_length=16,
        choices=GenderEnum.choices,
        default=GenderEnum.OTHER,
    )
    height_cm = models.FloatField(default=170.0)
    weight_kg = models.FloatField(default=65.0)
    activity_level = models.CharField(max_length=16, choices=ActivityLevelEnum.choices, default=ActivityLevelEnum.LIGHT)
    goal = models.CharField(max_length=16, choices=GoalEnum.choices, default=GoalEnum.MAINTAIN)

    bmr_kcal = models.FloatField(default=0.0)
    tdee_kcal = models.FloatField(default=0.0)

    target_protein_g = models.FloatField(default=0.0)
    target_lipid_g = models.FloatField(default=0.0)
    target_carb_g = models.FloatField(default=0.0)
    target_sodium_mg = models.FloatField(default=0.0)
    target_fiber_g = models.FloatField(default=0.0)

    consumed_protein_g = models.FloatField(default=0.0)
    consumed_lipid_g = models.FloatField(default=0.0)
    consumed_carb_g = models.FloatField(default=0.0)
    consumed_sodium_mg = models.FloatField(default=0.0)
    consumed_fiber_g = models.FloatField(default=0.0)

    class Meta:
        db_table = "user_daily_nutrition"
        unique_together = ("user", "date")

    def __str__(self):
        return f"UserDailyNutrition(user_id={self.user_id}, date={self.date})"


class DailyMealLog(BaseModel):
    daily_nutrition = models.ForeignKey(
        to="recommendation.UserDailyNutrition",
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="daily_nutrition_uid",
        related_name="daily_meal_logs",
        db_constraint=True,
    )
    source = models.CharField(max_length=16, choices=MealSourceEnum.choices, default=MealSourceEnum.PARSED)
    meal_time = models.CharField(max_length=16, choices=MealTimeEnum.choices, default=MealTimeEnum.UNKNOWN)

    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="dish_uid",
        related_name="daily_meal_log_fk_dish",
        db_constraint=True,
        null=True,
        blank=True,
    )
    meal_name = models.TextField()
    quantity_multiplier = models.FloatField(default=1.0)

    nutrition_protein_g = models.FloatField(default=0.0)
    nutrition_lipid_g = models.FloatField(default=0.0)
    nutrition_carb_g = models.FloatField(default=0.0)
    nutrition_sodium_mg = models.FloatField(default=0.0)
    nutrition_fiber_g = models.FloatField(default=0.0)

    confidence_parse = models.FloatField(default=1.0)
    confidence_source = models.FloatField(default=1.0)
    raw_payload = JSONField(default=dict, blank=True)
    source_ref = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "daily_meal_log"


class DishTranslationMapping(BaseModel):
    vietnamese_name = models.TextField(unique=True)
    normalized_vietnamese_name = models.TextField(db_index=True)
    english_name = models.TextField(null=True, blank=True)
    ingredients = JSONField(default=list, blank=True)
    nutrition_per_serving = JSONField(default=dict, blank=True)
    serving_grams = models.FloatField(default=100.0)
    usda_confidence = models.FloatField(default=0.8)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "dish_translation_mapping"

    def save(self, *args, **kwargs):
        from utils.functions.remove_accents import remove_accents

        self.normalized_vietnamese_name = remove_accents((self.vietnamese_name or "").strip())
        return super().save(*args, **kwargs)


class DishRecipeSnapshot(BaseModel):
    """
    Snapshot of a generated or imported recipe for an outside meal.
    Stored so nutrition computations are deterministic and auditable.
    """
    dish_name = models.TextField()
    normalized_name = models.TextField(db_index=True)
    # ingredients: list of {"name": str, "ingredient_uid": str|None, "weight_g": float}
    ingredients = JSONField(default=list, blank=True)
    source = models.CharField(max_length=32, default="GEMINI")
    confidence_score = models.FloatField(default=0.0)

    class Meta:
        db_table = "dish_recipe_snapshot"

    def __str__(self) -> str:
        return f"DishRecipeSnapshot({self.dish_name} @ {self.created_at})"