import re
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from dish.models import Dish, DishIngredient
from ingredient.models import Ingredient
from order.models import OrderItem
from recommendation.models import DailyMealLog, DishTranslationMapping, UserDailyNutrition
from exceptions.recommendation import DailyNutritionProfileNotFoundException
from utils.enums import OrderStatusEnum, MealSourceEnum, MealTimeEnum
from utils.functions.remove_accents import remove_accents
from google import genai
from dish.services.search import DishSearchService
import re

@dataclass
class ParsedMeal:
    name: str
    quantity_multiplier: float
    confidence_parse: float


class DailyNutritionService:
    ACTIVITY_FACTOR = {
        "SEDENTARY": 1.2,
        "LIGHT": 1.375,
        "MODERATE": 1.55,
        "ACTIVE": 1.725,
        "VERY_ACTIVE": 1.9,
    }

    PORTION_MULTIPLIER_HINTS = {
        "to cha ba": 1.8,
        "to lon": 1.5,
        "lon": 1.3,
        "nhieu": 1.3,
        "it": 0.8,
        "nho": 0.8,
    }

    # Max meal ratio: No single meal should exceed 60% of daily target (safer than 70%)
    MAX_MEAL_RATIO = 0.60

    SOURCE_BASE_QUALITY = {
        MealSourceEnum.APP: 0.98,
        MealSourceEnum.PARSED: 0.86,
        MealSourceEnum.USDA: 0.90,
        MealSourceEnum.MANUAL: 0.75,
    }

    def initialize_daily_profile(
        self,
        *,
        user_id: int,
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float,
        activity_level: str,
        goal: str = "MAINTAIN",
    ) -> dict[str, Any]:
        today = timezone.localdate()
        daily, _ = UserDailyNutrition.objects.get_or_create(
            user_id=user_id,
            date=today,
            defaults={
                "age": max(int(age), 1),
                "gender": self._normalize_gender(gender),
                "height_cm": max(float(height_cm), 1.0),
                "weight_kg": max(float(weight_kg), 1.0),
                "activity_level": self._normalize_activity(activity_level),
                "goal": self._normalize_goal(goal),
                "is_active": True,
            },
        )

        daily.age = max(int(age), 1)
        daily.gender = self._normalize_gender(gender)
        daily.height_cm = max(float(height_cm), 1.0)
        daily.weight_kg = max(float(weight_kg), 1.0)
        daily.activity_level = self._normalize_activity(activity_level)
        daily.goal = self._normalize_goal(goal)
        daily.is_active = True

        self._compute_daily_targets(daily)
        daily.save()

        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)

        return self._build_summary(daily)

    def update_daily_nutrition_profile(
        self,
        *,
        user_id: int,
        age: int | None = None,
        gender: str | None = None,
        height_cm: float | None = None,
        weight_kg: float | None = None,
        activity_level: str | None = None,
        goal: str | None = None,
    ) -> dict[str, Any]:
        """
        Update nutrition profile for today.
        Only provided fields are updated (others remain unchanged).
        TDEE and targets are recalculated based on new profile.
        Returns full profile with personal info and nutrition data.
        """
        today = timezone.localdate()
        daily = UserDailyNutrition.objects.filter(
            user_id=user_id,
            date=today,
        ).first()
        
        if daily is None:
            raise DailyNutritionProfileNotFoundException
        
        # Update only provided fields
        if age is not None:
            daily.age = max(int(age), 1)
        if gender is not None:
            daily.gender = self._normalize_gender(gender)
        if height_cm is not None:
            daily.height_cm = max(float(height_cm), 1.0)
        if weight_kg is not None:
            daily.weight_kg = max(float(weight_kg), 1.0)
        if activity_level is not None:
            daily.activity_level = self._normalize_activity(activity_level)
        if goal is not None:
            daily.goal = self._normalize_goal(goal)
        
        # Recalculate TDEE and targets
        self._compute_daily_targets(daily)
        daily.save()
        
        # Re-sync order logs and recalculate consumed totals
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)
        
        return self._build_profile(daily)

    def get_daily_nutrition_profile(
        self,
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """
        Get user's current daily nutrition profile with personal info and nutrition data.
        Returns: age, gender, height_cm, weight_kg, activity_level, goal, BMR, TDEE, targets, consumed, remaining
        """
        today = timezone.localdate()
        daily = UserDailyNutrition.objects.filter(
            user_id=user_id,
            date=today,
        ).first()
        
        if daily is None:
            raise DailyNutritionProfileNotFoundException
        
        return self._build_profile(daily)

    @transaction.atomic
    def parse_outside_meals(self, *, user_id: int, text: str, meal_time: str = MealTimeEnum.UNKNOWN) -> dict[str, Any]:
        daily = self._get_today_daily(user_id=user_id)
        parsed_meals = self._parse_meal_text(text)
        dish_nutrition_cache: dict[str, dict[str, float]] = {}
        dish_quality_cache: dict[str, float] = {}

        unresolved: list[str] = []
        created_count = 0

        for meal in parsed_meals:
            dish = self._match_dish(meal.name)
            if dish is not None:
                dish_uid = str(dish.uid)
                if dish_uid not in dish_nutrition_cache:
                    dish_nutrition_cache[dish_uid] = self._get_dish_nutrition_map([dish_uid]).get(
                        dish_uid,
                        self._empty_nutrition(),
                    )
                if dish_uid not in dish_quality_cache:
                    dish_quality_cache[dish_uid] = self._get_dish_quality_map([dish_uid]).get(dish_uid, 0.9)

                nutrition = dish_nutrition_cache[dish_uid]
                confidence_source = self._compute_source_confidence(
                    parsed_name=meal.name,
                    resolved_name=dish.name,
                    nutrition=nutrition,
                    base_quality=dish_quality_cache[dish_uid],
                )
                self._create_meal_log(
                    daily=daily,
                    source=MealSourceEnum.PARSED,
                    meal_time=meal_time,
                    meal_name=meal.name,
                    dish=dish,
                    quantity_multiplier=meal.quantity_multiplier,
                    nutrition=nutrition,
                    confidence_parse=meal.confidence_parse,
                    confidence_source=confidence_source,
                    raw_payload={"resolver": "dish_db"},
                )
                created_count += 1
                continue

            mapping = self._match_translation_mapping(meal.name)
            if mapping is not None:
                nutrition = self._extract_mapping_nutrition(mapping)
                confidence_source = self._compute_source_confidence(
                    parsed_name=meal.name,
                    resolved_name=mapping.vietnamese_name,
                    nutrition=nutrition,
                    base_quality=float(mapping.usda_confidence or 0.8),
                )
                self._create_meal_log(
                    daily=daily,
                    source=MealSourceEnum.USDA,
                    meal_time=meal_time,
                    meal_name=meal.name,
                    dish=None,
                    quantity_multiplier=meal.quantity_multiplier,
                    nutrition=nutrition,
                    confidence_parse=meal.confidence_parse,
                    confidence_source=confidence_source,
                    raw_payload={"resolver": "usda_mapping", "mapping_uid": str(mapping.uid)},
                )
                created_count += 1
                continue

            # If no mapping found, try to find USDA ingredient entries directly
            usda_ing = self._match_usda_ingredient(meal.name)
            if usda_ing is not None:
                nutrition = self._extract_ingredient_nutrition(usda_ing)
                base_quality = float(getattr(usda_ing, "usda_confidence", 0.9) or 0.9)
                confidence_source = self._compute_source_confidence(
                    parsed_name=meal.name,
                    resolved_name=getattr(usda_ing, "name", ""),
                    nutrition=nutrition,
                    base_quality=base_quality,
                )
                self._create_meal_log(
                    daily=daily,
                    source=MealSourceEnum.USDA,
                    meal_time=meal_time,
                    meal_name=meal.name,
                    dish=None,
                    quantity_multiplier=meal.quantity_multiplier,
                    nutrition=nutrition,
                    confidence_parse=meal.confidence_parse,
                    confidence_source=confidence_source,
                    raw_payload={"resolver": "usda_ingredient", "ingredient_uid": str(usda_ing.uid)},
                )
                created_count += 1
                continue

            # If no local dish/mapping/ingredient found, try generating a recipe via Gemini
            generated = self._call_gemini_recipe_generator(meal.name)
            if generated:
                mapped_ings, conf = self._normalize_and_map_recipe(generated)
                if mapped_ings:
                    nutrition = self._compute_recipe_nutrition(mapped_ings)
                    confidence_source = max(0.0, min(1.0, conf))
                    # store snapshot for audit
                    try:
                        self._store_recipe_snapshot(meal.name, mapped_ings, confidence_source, source="GEMINI")
                    except Exception:
                        pass
                    self._create_meal_log(
                        daily=daily,
                        source=MealSourceEnum.PARSED,
                        meal_time=meal_time,
                        meal_name=meal.name,
                        dish=None,
                        quantity_multiplier=meal.quantity_multiplier,
                        nutrition=nutrition,
                        confidence_parse=meal.confidence_parse,
                        confidence_source=confidence_source,
                        raw_payload={"resolver": "gemini_generated"},
                    )
                    created_count += 1
                    continue

            unresolved.append(meal.name)

        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)

        return {
            "summary": self._build_summary(daily),
            "parsed_count": created_count,
            "unresolved_meals": unresolved,
        }

    def get_balanced_recommendations(self, *, user_id: int, limit: int = 10) -> dict[str, Any]:
        daily = self._get_today_daily(user_id=user_id)
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)

        summary = self._build_summary(daily)
        remaining = summary["remaining"]

        from recommendation.services.pipeline import RecommendationPipelineService

        pool_size = max(60, int(limit) * 5)
        base_feed = RecommendationPipelineService().recommend_for_user(
            user_id=user_id,
            limit=pool_size,
            offset=0,
            include_explain=True,
        )

        base_items = base_feed.get("items", [])
        if not base_items:
            # ⚠️ FALLBACK: No candidates from pipeline (could be cold start or no eligible dishes)
            # Return high-rated dishes to avoid empty feed (poor UX)
            from dish.models import Dish
            fallback_items = list(
                Dish.objects
                .filter(deleted=False, status="AVAILABLE")
                .select_related("attachment")
                .order_by("-avg_rating", "-final_score")
                [:limit * 2]
            )
            
            if not fallback_items:
                # Complete failure: no dishes at all
                return {"summary": summary, "items": []}
            
            # Build minimal response from fallback (skip complex nutritional calculations)
            fallback_response = []
            for dish in fallback_items:
                fallback_response.append({
                    "rank_position": len(fallback_response) + 1,
                    "dish_uid": str(dish.uid),
                    "dish_name": dish.name,
                    "public_url": dish.attachment.public_url if dish.attachment else None,
                    "price": float(dish.price),
                    "avg_rating": float(dish.avg_rating or 0),
                    "base_recommendation_score": 0.0,
                    "macro_match_score": 0.0,
                    "final_score": 0.5,
                    "suggested_servings": 1.0,
                    "nutrition_impact": {"protein_g": 0, "lipid_g": 0, "carb_g": 0, "sodium_mg": 0, "fiber_g": 0},
                    "reasons": ["No personalized recommendations available, showing popular dishes"],
                })
            
            return {"summary": summary, "items": fallback_response[: max(int(limit), 1)]}

        # Get dishes already logged today (filter them out from recommendations)
        # ⚠️ CRITICAL: Convert UUID objects to strings to match item["dish_uid"] type
        # Bug: if not converted, type mismatch (UUID vs string) causes filter to fail silently
        already_logged_dish_ids = set(
            str(x) for x in DailyMealLog.objects.filter(
                daily_nutrition=daily,
                is_deleted=False,
                dish_id__isnull=False,
            ).values_list("dish_id", flat=True)
        )
        
        # Filter out already-logged dishes from recommendations
        # Now both sides are strings, so comparison works correctly
        filtered_items = [
            item for item in base_items
            if str(item["dish_uid"]) not in already_logged_dish_ids
        ]
        
        # If we filtered out too many, fall back to unfiltered items to ensure we have enough
        if len(filtered_items) < max(5, int(limit)):
            filtered_items = base_items

        dish_ids = [item["dish_uid"] for item in filtered_items]
        dish_nutrition_map = self._get_dish_nutrition_map(dish_ids)
        dish_quality_map = self._get_dish_quality_map(dish_ids)

        max_base_score = max(float(item.get("score", 0.0)) for item in filtered_items) or 1.0

        ranked: list[dict[str, Any]] = []
        
        # IMPORTANT: Preserve MMR order from Pipeline (diversity-aware ranking)
        # DO NOT re-sort by final_score as it would break diversity guarantees from MMR
        for idx, item in enumerate(filtered_items):
            dish_uid = item["dish_uid"]
            dish_nutrition = dish_nutrition_map.get(dish_uid, self._empty_nutrition())

            macro_match = self._macro_match_score(remaining=remaining, dish_nutrition=dish_nutrition)
            sodium_penalty = self._sodium_penalty(remaining=remaining, dish_nutrition=dish_nutrition)
            base_norm = max(0.0, min(1.0, float(item.get("score", 0.0)) / max_base_score))
            
            # Compute nutrition-aware score (for explanation, not for re-ranking)
            # DESIGN NOTE: We preserve MMR order from Pipeline for diversity guarantees.
            # This score is for explainability (why this dish matches nutrition needs),
            # NOT for resort (which would break diversity).
            # 
            # Weight: nutrition fit (55%) + base recommendation (30%) - sodium risk (15%)
            # If you want nutrition to drive ranking instead, remove MMR preservation
            # and uncomment the sort below (but lose diversity guarantee)
            final_score = (
                0.55 * macro_match +
                0.30 * base_norm -
                0.15 * sodium_penalty
            )
            final_score = max(0.0, min(1.0, final_score))

            servings = self._suggest_servings(remaining=remaining, dish_nutrition=dish_nutrition)
            dish_alpha = 1.0 - self._clamp(float(dish_quality_map.get(dish_uid, 0.98)))

            def _impact(srv: float) -> dict[str, float]:
                return {
                    "protein_g": round(dish_nutrition["protein_g"] * srv, 3),
                    "protein_g_uncertainty": round(dish_nutrition["protein_g"] * srv * dish_alpha, 3),
                    "lipid_g": round(dish_nutrition["lipid_g"] * srv, 3),
                    "lipid_g_uncertainty": round(dish_nutrition["lipid_g"] * srv * dish_alpha, 3),
                    "carb_g": round(dish_nutrition["carb_g"] * srv, 3),
                    "carb_g_uncertainty": round(dish_nutrition["carb_g"] * srv * dish_alpha, 3),
                    "sodium_mg": round(dish_nutrition["sodium_mg"] * srv, 3),
                    "sodium_mg_uncertainty": round(dish_nutrition["sodium_mg"] * srv * dish_alpha, 3),
                    "fiber_g": round(dish_nutrition["fiber_g"] * srv, 3),
                    "fiber_g_uncertainty": round(dish_nutrition["fiber_g"] * srv * dish_alpha, 3),
                }

            impact = _impact(servings)

            # ⭐ VALIDATION: Check if meal exceeds 60% of daily targets
            # If yes, scale down servings to fit within limit
            adjusted_servings = self._validate_meal_portion(
                servings=servings,
                dish_nutrition=dish_nutrition,
                daily_target=summary["target"]
            )
            reasons = list(item.get("reasons", []))[:2]
            if adjusted_servings != servings:
                impact = _impact(adjusted_servings)
                reasons.append(f"⚠️ Portion adjusted to fit daily targets (max {int(self.MAX_MEAL_RATIO * 100)}% per meal)")
                servings = adjusted_servings
            deficit_reasons = self._remaining_reasons(remaining=remaining)
            reasons.extend(deficit_reasons[: max(0, 3 - len(reasons))])

            ranked.append(
                {
                    "rank_position": idx + 1,  # Keep MMR position
                    "dish_uid": dish_uid,
                    "dish_name": item.get("dish_name", ""),
                    "public_url": item.get("public_url"),
                    "price": float(item.get("price", 0.0)),
                    "avg_rating": float(item.get("avg_rating", 0.0)),
                    "base_recommendation_score": round(float(item.get("score", 0.0)), 6),
                    "macro_match_score": round(macro_match, 6),
                    "final_score": round(final_score, 6),
                    "suggested_servings": round(servings, 2),
                    "nutrition_impact": impact,
                    "reasons": reasons[:3],
                }
            )

        # ⭐ CRITICAL: Do NOT re-sort. Return in MMR order (maintains diversity-aware ranking)
        # MMR already optimized for: relevance + dissimilarity (diversity)
        return {"summary": summary, "items": ranked[: max(int(limit), 1)]}

    def get_daily_summary(self, *, user_id: int) -> dict[str, Any]:
        daily = self._get_today_daily(user_id=user_id)
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)
        return self._build_summary(daily)

    @transaction.atomic
    def get_daily_meal_logs(self, *, user_id: int) -> dict[str, Any]:
        daily = self._get_today_daily(user_id=user_id)
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)
        logs = self._get_active_meal_logs(daily)
        return {
            "summary": self._build_summary(daily),
            "items": [self._serialize_meal_log(log) for log in logs],
        }

    @transaction.atomic
    def update_daily_meal_log(
        self,
        *,
        user_id: int,
        log_uid: str,
        meal_name: str | None = None,
        meal_time: str | None = None,
        quantity_multiplier: float | None = None,
        dish_uid: str | None = None,
    ) -> dict[str, Any]:
        log = DailyMealLog.objects.select_related("daily_nutrition", "dish").filter(
            uid=log_uid,
            daily_nutrition__user_id=user_id,
            is_deleted=False,
        ).first()
        if log is None:
            raise ValueError("Daily meal log not found")

        if meal_name is not None:
            log.meal_name = meal_name
        if meal_time is not None:
            log.meal_time = (meal_time or MealTimeEnum.UNKNOWN).upper()

        current_quantity = max(float(log.quantity_multiplier or 1.0), 0.1)
        updated_quantity = max(float(quantity_multiplier or current_quantity), 0.1)

        if dish_uid is not None:
            dish = Dish.objects.filter(uid=dish_uid, deleted=False).first()
            if dish is None:
                raise ValueError("Dish not found")

            dish_nutrition = self._get_dish_nutrition_map([str(dish.uid)]).get(str(dish.uid), self._empty_nutrition())
            log.dish = dish
            log.nutrition_protein_g = float(dish_nutrition["protein_g"]) * updated_quantity
            log.nutrition_lipid_g = float(dish_nutrition["lipid_g"]) * updated_quantity
            log.nutrition_carb_g = float(dish_nutrition["carb_g"]) * updated_quantity
            log.nutrition_sodium_mg = float(dish_nutrition["sodium_mg"]) * updated_quantity
            log.nutrition_fiber_g = float(dish_nutrition["fiber_g"]) * updated_quantity
        elif quantity_multiplier is not None:
            scale = updated_quantity / current_quantity
            log.nutrition_protein_g = float(log.nutrition_protein_g or 0.0) * scale
            log.nutrition_lipid_g = float(log.nutrition_lipid_g or 0.0) * scale
            log.nutrition_carb_g = float(log.nutrition_carb_g or 0.0) * scale
            log.nutrition_sodium_mg = float(log.nutrition_sodium_mg or 0.0) * scale
            log.nutrition_fiber_g = float(log.nutrition_fiber_g or 0.0) * scale

        log.quantity_multiplier = updated_quantity
        log.save()

        daily = log.daily_nutrition
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)
        return {
            "summary": self._build_summary(daily),
            "items": [self._serialize_meal_log(item) for item in self._get_active_meal_logs(daily)],
        }

    @transaction.atomic
    def delete_daily_meal_log(self, *, user_id: int, log_uid: str) -> dict[str, Any]:
        log = DailyMealLog.objects.select_related("daily_nutrition").filter(
            uid=log_uid,
            daily_nutrition__user_id=user_id,
            is_deleted=False,
        ).first()
        if log is None:
            raise ValueError("Daily meal log not found")

        log.is_deleted = True
        log.save(update_fields=["is_deleted", "updated_at"])

        daily = log.daily_nutrition
        self._sync_app_order_logs(daily)
        self._recalculate_consumed_totals(daily)
        return {
            "summary": self._build_summary(daily),
            "items": [self._serialize_meal_log(item) for item in self._get_active_meal_logs(daily)],
        }

    @transaction.atomic
    def sync_order_meal_logs(self, *, order_uid: str) -> dict[str, Any]:
        rows = list(
            OrderItem.objects.filter(
                order__uid=order_uid,
                order__status=OrderStatusEnum.COMPLETED,
                dish__isnull=False,
            ).select_related("dish", "order")
        )

        if not rows:
            return {"created_count": 0, "summary": None, "items": []}

        order = rows[0].order
        daily = self._get_daily_for_date(user_id=order.owner_id, target_date=timezone.localdate(order.created_at))
        created_count = self._sync_app_order_logs(daily, order_rows=rows)
        self._recalculate_consumed_totals(daily)

        return {
            "created_count": created_count,
            "summary": self._build_summary(daily),
            "items": [self._serialize_meal_log(item) for item in self._get_active_meal_logs(daily)],
        }

    def _get_daily_for_date(self, *, user_id: int, target_date) -> UserDailyNutrition:
        daily = UserDailyNutrition.objects.filter(user_id=user_id, date=target_date).first()
        if daily is None:
            daily = UserDailyNutrition.objects.create(
                user_id=user_id,
                date=target_date,
                is_active=True,
            )
            self._compute_daily_targets(daily)
            daily.save()
        return daily

    def _get_today_daily(self, *, user_id: int) -> UserDailyNutrition:
        return self._get_daily_for_date(user_id=user_id, target_date=timezone.localdate())

    def _normalize_gender(self, gender: str) -> str:
        value = ("" if gender is None else str(gender)).strip().upper()
        allowed = {
            "MALE",
            "FEMALE",
            "OTHER",
        }
        return value if value in allowed else "OTHER"

    def _normalize_activity(self, activity: str) -> str:
        value = ("" if activity is None else str(activity)).strip().upper()
        return value if value in self.ACTIVITY_FACTOR else "LIGHT"

    def _normalize_goal(self, goal: str) -> str:
        value = ("" if goal is None else str(goal)).strip().upper()
        allowed = {
            "MAINTAIN",
            "LOSE",
            "GAIN",
        }
        return value if value in allowed else "MAINTAIN"

    def _compute_daily_targets(self, daily: UserDailyNutrition) -> None:
        age = max(float(daily.age or 25), 1.0)
        weight = max(float(daily.weight_kg or 65), 1.0)
        height = max(float(daily.height_cm or 170), 1.0)

        if daily.gender == "MALE":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        elif daily.gender == "FEMALE":
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.33 * age)
        else:
            bmr_male = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            bmr_female = 447.593 + (9.247 * weight) + (3.098 * height) - (4.33 * age)
            bmr = (bmr_male + bmr_female) / 2.0

        tdee = bmr * self.ACTIVITY_FACTOR.get(daily.activity_level, 1.375)
        if daily.goal == "LOSE":
            tdee -= 300
        elif daily.goal == "GAIN":
            tdee += 300

        tdee = max(tdee, 900.0)

        protein_g = 1.2 * weight if daily.goal == "GAIN" else 1.0 * weight
        lipid_g = (0.27 * tdee) / 9.0
        carb_g = max((tdee - (protein_g * 4.0 + lipid_g * 9.0)) / 4.0, 0.0)
        sodium_mg = 2300.0
        fiber_g = (14.0 * tdee) / 1000.0

        daily.bmr_kcal = round(bmr, 3)
        daily.tdee_kcal = round(tdee, 3)
        daily.target_protein_g = round(protein_g, 3)
        daily.target_lipid_g = round(lipid_g, 3)
        daily.target_carb_g = round(carb_g, 3)
        daily.target_sodium_mg = round(sodium_mg, 3)
        daily.target_fiber_g = round(fiber_g, 3)

    @staticmethod
    def _infer_meal_time_from_delivery_time(delivery_time) -> str:
        """
        Infer meal time (BREAKFAST, LUNCH, DINNER, SNACK) from delivery time.
        
        Time ranges:
        - BREAKFAST: 6:00 - 10:59
        - LUNCH: 11:00 - 15:59
        - DINNER: 16:00 - 21:59
        - SNACK/OTHER: 22:00 - 5:59
        """
        from datetime import time
        
        if delivery_time is None:
            return MealTimeEnum.UNKNOWN
        
        # Convert to time object if needed
        if not isinstance(delivery_time, time):
            if hasattr(delivery_time, 'time'):  # datetime object
                delivery_time = delivery_time.time()
            else:
                return MealTimeEnum.UNKNOWN
        
        hour = delivery_time.hour
        
        if 6 <= hour < 11:
            return MealTimeEnum.BREAKFAST
        elif 11 <= hour < 16:
            return MealTimeEnum.LUNCH
        elif 16 <= hour < 22:
            return MealTimeEnum.DINNER
        elif 22 <= hour < 24 or 0 <= hour < 6:
            return MealTimeEnum.SNACK
        
        return MealTimeEnum.UNKNOWN

    def _sync_app_order_logs(self, daily: UserDailyNutrition, order_rows: list[OrderItem] | None = None) -> int:
        rows = order_rows or list(
            OrderItem.objects.filter(
                order__owner_id=daily.user_id,
                order__status=OrderStatusEnum.COMPLETED,
                order__created_at__date=daily.date,
                dish__isnull=False,
            ).select_related("dish", "order", "order__checkout")
        )

        if not rows:
            return 0

        dish_ids = [str(row.dish_id) for row in rows if row.dish_id]
        dish_nutrition_map = self._get_dish_nutrition_map(dish_ids)
        dish_quality_map = self._get_dish_quality_map(dish_ids)

        created_count = 0
        for row in rows:
            if not row.dish_id:
                continue

            source_ref = self._app_order_source_ref(row)
            existing = DailyMealLog.objects.filter(
                daily_nutrition=daily,
                source=MealSourceEnum.APP,
                source_ref=source_ref,
            ).first()
            if existing is None:
                existing = DailyMealLog.objects.filter(
                    daily_nutrition=daily,
                    source=MealSourceEnum.APP,
                    raw_payload__order_item_id=str(row.id),
                ).first()
            if existing is None:
                existing = DailyMealLog.objects.filter(
                    daily_nutrition=daily,
                    source=MealSourceEnum.APP,
                    raw_payload__order_uid=str(row.order_id),
                    dish_id=row.dish_id,
                    quantity_multiplier=max(float(row.quantity or 1), 1.0),
                ).first()
            if existing is not None:
                if not existing.source_ref:
                    existing.source_ref = source_ref
                    existing.raw_payload = {
                        **(existing.raw_payload or {}),
                        "order_uid": str(row.order_id),
                        "order_item_id": str(row.id),
                    }
                    existing.save(update_fields=["source_ref", "raw_payload", "updated_at"])
                continue

            nutrition = dish_nutrition_map.get(str(row.dish_id), self._empty_nutrition())
            quantity = max(float(row.quantity or 1), 1.0)
            
            # Infer meal_time from order's checkout delivery_time
            delivery_time = None
            if row.order and row.order.checkout:
                delivery_time = row.order.checkout.delivery_time
            meal_time = self._infer_meal_time_from_delivery_time(delivery_time)

            DailyMealLog.objects.create(
                daily_nutrition=daily,
                source=MealSourceEnum.APP,
                meal_time=meal_time,
                dish=row.dish,
                meal_name=row.dish_name or (row.dish.name if row.dish else "Unknown dish"),
                quantity_multiplier=quantity,
                nutrition_protein_g=nutrition["protein_g"] * quantity,
                nutrition_lipid_g=nutrition["lipid_g"] * quantity,
                nutrition_carb_g=nutrition["carb_g"] * quantity,
                nutrition_sodium_mg=nutrition["sodium_mg"] * quantity,
                nutrition_fiber_g=nutrition["fiber_g"] * quantity,
                confidence_parse=1.0,
                confidence_source=dish_quality_map.get(str(row.dish_id), 0.98),
                raw_payload={"order_uid": str(row.order_id), "order_item_id": str(row.id)},
                source_ref=source_ref,
            )
            created_count += 1

        return created_count

    def _recalculate_consumed_totals(self, daily: UserDailyNutrition) -> None:
        logs = DailyMealLog.objects.filter(daily_nutrition=daily, is_deleted=False)

        consumed = {
            "protein_g": 0.0,
            "lipid_g": 0.0,
            "carb_g": 0.0,
            "sodium_mg": 0.0,
            "fiber_g": 0.0,
        }

        for log in logs:
            consumed["protein_g"] += float(log.nutrition_protein_g or 0.0)
            consumed["lipid_g"] += float(log.nutrition_lipid_g or 0.0)
            consumed["carb_g"] += float(log.nutrition_carb_g or 0.0)
            consumed["sodium_mg"] += float(log.nutrition_sodium_mg or 0.0)
            consumed["fiber_g"] += float(log.nutrition_fiber_g or 0.0)

        daily.consumed_protein_g = round(consumed["protein_g"], 3)
        daily.consumed_lipid_g = round(consumed["lipid_g"], 3)
        daily.consumed_carb_g = round(consumed["carb_g"], 3)
        daily.consumed_sodium_mg = round(consumed["sodium_mg"], 3)
        daily.consumed_fiber_g = round(consumed["fiber_g"], 3)
        daily.save(
            update_fields=[
                "consumed_protein_g",
                "consumed_lipid_g",
                "consumed_carb_g",
                "consumed_sodium_mg",
                "consumed_fiber_g",
                "updated_at",
            ]
        )

    def _compute_consumed_uncertainty(self, daily: UserDailyNutrition) -> dict[str, float]:
        """On-the-fly: uncertainty_k = sum(nutrition_k × alpha), alpha = 1 - confidence_parse × confidence_source"""
        logs = DailyMealLog.objects.filter(daily_nutrition=daily, is_deleted=False)
        uncertainty: dict[str, float] = {
            "protein_g": 0.0,
            "lipid_g": 0.0,
            "carb_g": 0.0,
            "sodium_mg": 0.0,
            "fiber_g": 0.0,
        }
        for log in logs:
            alpha = 1.0 - self._clamp(float(log.confidence_parse or 1.0)) * self._clamp(
                float(log.confidence_source or 1.0)
            )
            uncertainty["protein_g"] += float(log.nutrition_protein_g or 0.0) * alpha
            uncertainty["lipid_g"] += float(log.nutrition_lipid_g or 0.0) * alpha
            uncertainty["carb_g"] += float(log.nutrition_carb_g or 0.0) * alpha
            uncertainty["sodium_mg"] += float(log.nutrition_sodium_mg or 0.0) * alpha
            uncertainty["fiber_g"] += float(log.nutrition_fiber_g or 0.0) * alpha
        return {k: round(v, 3) for k, v in uncertainty.items()}

    def _get_active_meal_logs(self, daily: UserDailyNutrition):
        return DailyMealLog.objects.filter(daily_nutrition=daily, is_deleted=False).select_related(
            "dish",
            "dish__attachment"
        ).order_by(
            "created_at",
            "updated_at",
        )

    def _serialize_meal_log(self, log: DailyMealLog) -> dict[str, Any]:
        dish = getattr(log, "dish", None)
        raw_payload = log.raw_payload if isinstance(log.raw_payload, dict) else {}

        image_url = None
        price = None
        if dish:
            attachment = getattr(dish, "attachment", None)
            if attachment:
                image_url = getattr(attachment, "public_url", None)
            price = float(dish.price) if dish.price is not None else None

        alpha = 1.0 - self._clamp(float(log.confidence_parse or 1.0)) * self._clamp(
            float(log.confidence_source or 1.0)
        )

        def _unc(val: float) -> float:
            return round(val * alpha, 3)

        p = float(log.nutrition_protein_g or 0.0)
        l = float(log.nutrition_lipid_g or 0.0)
        c = float(log.nutrition_carb_g or 0.0)
        s = float(log.nutrition_sodium_mg or 0.0)
        f = float(log.nutrition_fiber_g or 0.0)

        return {
            "uid": str(log.uid),
            "source": str(log.source or ""),
            "meal_time": str(log.meal_time or DailyMealLog.MEAL_UNKNOWN),
            "dish_uid": str(log.dish_id) if log.dish_id else None,
            "dish_name": getattr(dish, "name", None),
            "meal_name": str(log.meal_name or ""),
            "quantity_multiplier": float(log.quantity_multiplier or 0.0),
            "nutrition_protein_g": p,
            "nutrition_protein_g_uncertainty": _unc(p),
            "nutrition_lipid_g": l,
            "nutrition_lipid_g_uncertainty": _unc(l),
            "nutrition_carb_g": c,
            "nutrition_carb_g_uncertainty": _unc(c),
            "nutrition_sodium_mg": s,
            "nutrition_sodium_mg_uncertainty": _unc(s),
            "nutrition_fiber_g": f,
            "nutrition_fiber_g_uncertainty": _unc(f),
            "confidence_parse": float(log.confidence_parse or 0.0),
            "confidence_source": float(log.confidence_source or 0.0),
            "raw_payload": raw_payload,
            "image_url": image_url,
            "price": price,
            "created_at": log.created_at.isoformat(),
            "updated_at": log.updated_at.isoformat(),
        }

    @staticmethod
    def _app_order_source_ref(row: OrderItem) -> str:
        return f"order_item:{row.id}"

    def _get_dish_nutrition_map(self, dish_ids: list[str]) -> dict[str, dict[str, float]]:
        """
        Trả về nutrition PER SERVING (tổng / dish.serving_size).

        Dish cho nhiều người (lẩu, combo, serving_size > 1) sẽ được chia đều
        để recommendation tính đúng cho 1 người ăn.
        """
        if not dish_ids:
            return {}

        rows = (
            DishIngredient.objects.filter(dish_id__in=dish_ids, deleted=False, dish__deleted=False)
            .values("dish_id", "protein", "lipid", "carbohydrate", "natri", "fiber", "dish__serving_size")
            .order_by("dish_id")
        )

        nutrition_map: dict[str, dict[str, float]] = {}
        for row in rows:
            dish_id = str(row["dish_id"])
            if dish_id not in nutrition_map:
                nutrition_map[dish_id] = self._empty_nutrition()

            # Chia cho serving_size để ra per-serving (default 1 nếu null/0)
            serving = max(int(row.get("dish__serving_size") or 1), 1)

            nutrition_map[dish_id]["protein_g"] += float(row.get("protein") or 0.0) / serving
            nutrition_map[dish_id]["lipid_g"] += float(row.get("lipid") or 0.0) / serving
            nutrition_map[dish_id]["carb_g"] += float(row.get("carbohydrate") or 0.0) / serving
            nutrition_map[dish_id]["sodium_mg"] += float(row.get("natri") or 0.0) / serving
            nutrition_map[dish_id]["fiber_g"] += float(row.get("fiber") or 0.0) / serving

        return nutrition_map

    def _get_dish_quality_map(self, dish_ids: list[str]) -> dict[str, float]:
        if not dish_ids:
            return {}

        rows = (
            DishIngredient.objects.filter(dish_id__in=dish_ids, deleted=False, dish__deleted=False)
            .values("dish_id", "weight", "confidence")
            .order_by("dish_id")
        )

        weighted_sum: dict[str, float] = {}
        weight_total: dict[str, float] = {}
        for row in rows:
            dish_id = str(row["dish_id"])
            weight = max(float(row.get("weight") or 1.0), 0.0)
            confidence = self._clamp(float(row.get("confidence") or 1.0))
            weighted_sum[dish_id] = weighted_sum.get(dish_id, 0.0) + (weight * confidence)
            weight_total[dish_id] = weight_total.get(dish_id, 0.0) + weight

        result: dict[str, float] = {}
        for dish_id in dish_ids:
            total = weight_total.get(dish_id, 0.0)
            if total <= 0:
                result[dish_id] = 0.9
                continue
            result[dish_id] = self._clamp(weighted_sum.get(dish_id, 0.0) / total)
        return result

    def _parse_meal_text(self, text: str) -> list[ParsedMeal]:
        parsed = self._call_gemini_meal_parser(text)
        if parsed:
            print(f"Parsed meal text with Gemini parser: {parsed}")
            return parsed

        parsed = self._call_external_llm_parser(text)
        if parsed:
            return parsed
        print("Falling back to heuristic meal parser for text:", text)
        return self._heuristic_parse(text)

    def _call_openai_meal_parser(self, text: str) -> list[ParsedMeal]:
        # Deprecated: OpenAI is no longer used. Keep for compatibility but return empty.
        return []

    # def _call_gemini_meal_parser(self, text: str) -> list[ParsedMeal]:
    #     base_url = (getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434") or "").strip().rstrip("/")
    #     model = (getattr(settings, "OLLAMA_MODEL", "llama-3.1") or "llama-3.1").strip()
    #     timeout = int(getattr(settings, "AI_MODEL_TIMEOUT_SECONDS", 10) or 10)

    #     if not base_url or not model:
    #         return []

    #     # Ollama HTTP API: POST /api/models/{model}/chat or /api/generate depending on setup.
    #     # We call /api/generate with a short prompt instructing JSON-only output.
    #     prompt = (
    #         "Extract Vietnamese meal text into strict JSON only. "
    #         "Return an object with key 'meals' as a list. "
    #         "Each item includes: name (string), quantity_multiplier (float 0.2-3.0), confidence_parse (float 0-1). "
    #         f"Text: {text}"
    #     )

    #     url = f"{base_url}/api/generate"
    #     payload = {
    #         "model": model,
    #         "prompt": prompt,
    #         "max_tokens": 512,
    #         "temperature": 0.0,
    #     }

    #     try:
    #         resp = requests.post(url, json=payload, timeout=timeout)
    #         resp.raise_for_status()
    #         body = resp.json() if resp.content else {}
    #         # Ollama may return `response` or `results` depending on install; try several keys.
    #         content = ""
    #         if isinstance(body, dict):
    #             content = body.get("response") or body.get("results", [{}])[0].get("content", "") or ""
    #         if not content and isinstance(body, list) and body:
    #             content = str(body[0])

    #         parsed_json = self._parse_json_safely(content)
    #         if not isinstance(parsed_json, dict):
    #             return []
    #         rows = parsed_json.get("meals", [])
    #         return self._normalize_parsed_rows(rows)
    #     except Exception:
    #         return []

    def _extract_json(self, text: str) -> str:
        """
        Extract first JSON block from LLM output
        """
        if not text:
            return ""

        match = re.search(r"\{.*\}", text, re.S)
        return match.group() if match else text
    

    def _call_gemini_meal_parser(self, text: str) -> list[ParsedMeal]:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            return []
        print(f"Calling Gemini parser for meal text. Input: {text}, API key present: {bool(api_key)}")
        client = genai.Client(api_key=api_key)
        # for m in client.models.list():
        #     print(m.name)
        prompt = f"""
    You are a strict JSON generator.

    Task:
    Extract Vietnamese meal text into JSON ONLY.

    Rules:
    - Output ONLY valid JSON (no markdown, no explanation)
    - Schema:
    {{
    "meals": [
        {{
        "name": string,
        "quantity_multiplier": float,
        "confidence_parse": float
        }}
    ]
    }}

    Text:
    {text}
    """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )

            content = response.text or ""

            # 🔥 STEP 1: clean possible junk text
            json_text = self._extract_json(content)

            parsed_json = self._parse_json_safely(json_text)

            if not isinstance(parsed_json, dict):
                return []

            rows = parsed_json.get("meals", [])
            return self._normalize_parsed_rows(rows)

        except Exception as e:
            print("GEMINI ERROR:", str(e))
            return []

    def _match_usda_ingredient(self, meal_name: str):
        """Try to find a USDA-sourced ingredient that matches the meal name."""
        if not meal_name:
            return None
        normalized = remove_accents((meal_name or "").strip().lower())
        if not normalized:
            return None

        # Try exact match on normalized name fields if available
        ing = (
            Ingredient.objects.filter(deleted=False)
            .filter(name_no_accent__icontains=normalized)
            .filter(source__icontains="USDA")
            .first()
        )
        if ing:
            return ing

        # fallback: partial match
        return (
            Ingredient.objects.filter(deleted=False)
            .filter(name_no_accent__icontains=normalized)
            .first()
        )

    def _extract_ingredient_nutrition(self, ingredient: Ingredient) -> dict[str, float]:
        # Best-effort extraction from Ingredient model fields
        return {
            "protein_g": float(getattr(ingredient, "protein", 0.0) or 0.0),
            "lipid_g": float(getattr(ingredient, "lipid", 0.0) or 0.0),
            "carb_g": float(getattr(ingredient, "carbohydrate", 0.0) or 0.0),
            "sodium_mg": float(getattr(ingredient, "natri", 0.0) or 0.0),
            "fiber_g": float(getattr(ingredient, "fiber", 0.0) or 0.0),
        }

    def _call_gemini_recipe_generator(self, dish_name: str) -> dict | None:
        """Call Gemini to generate a recipe (ingredients + weights).

        Expected JSON schema:
        {
          "dish": "phở bò",
          "ingredients": [
            {"name": "bún phở", "weight_g": 200},
            {"name": "thịt bò", "weight_g": 100}
          ],
          "confidence": 0.78
        }
        
        ⚠️ IMPORTANT: This is a blocking call. Consider moving to Celery background task
        for production to avoid API timeouts.
        """
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key or not dish_name:
            return None
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
You are a JSON-only generator. Given a Vietnamese dish name, output a JSON object with keys: dish (string), ingredients (list of objects with name and weight_g as integer/float), confidence (0-1).

Dish: {dish_name}
"""
            # ⚠️ CRITICAL: Set timeout to prevent API from hanging indefinitely
            # Gemini should respond quickly for JSON generation (typically < 2s)
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                timeout=3.0,  # Timeout after 3 seconds
            )
            content = response.text or ""
            json_text = self._extract_json(content)
            parsed = self._parse_json_safely(json_text)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception:
            return None

    def _normalize_and_map_recipe(self, parsed: dict) -> tuple[list[dict], float]:
        """Normalize recipe JSON and map ingredient names to Ingredient records.

        Returns (mapped_ingredients, confidence_score)
        mapped_ingredients: [{"name": str, "ingredient_uid": str|None, "weight_g": float}]
        """
        results: list[dict] = []
        raw_ings = parsed.get("ingredients") if isinstance(parsed, dict) else []
        confidence = float(parsed.get("confidence") or 0.0)
        for item in (raw_ings or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            weight = float(item.get("weight_g") or item.get("weight") or 0.0)
            if not name or weight <= 0:
                continue
            # Try to map to Ingredient by normalized name
            ing = self._match_usda_ingredient(name)
            uid = str(ing.uid) if ing else None
            results.append({"name": name, "ingredient_uid": uid, "weight_g": round(float(weight), 3)})
        return results, self._clamp(confidence)

    def _compute_recipe_nutrition(self, mapped_ingredients: list[dict]) -> dict[str, float]:
        """Compute nutrition by summing mapped ingredient nutrition scaled by weight.

        For each mapped ingredient, use Ingredient fields (protein, lipid, carbohydrate, natri) as per-portion values assumed per 100g.
        """
        totals = {"protein_g": 0.0, "lipid_g": 0.0, "carb_g": 0.0, "sodium_mg": 0.0, "fiber_g": 0.0}
        ing_ids = [item["ingredient_uid"] for item in mapped_ingredients if item.get("ingredient_uid")]
        ing_map = {}
        if ing_ids:
            rows = Ingredient.objects.filter(uid__in=ing_ids, deleted=False)
            for r in rows:
                ing_map[str(r.uid)] = r

        for item in mapped_ingredients:
            uid = item.get("ingredient_uid")
            weight = float(item.get("weight_g") or 0.0)
            if uid and uid in ing_map:
                ing = ing_map[uid]
                # assume ingredient fields are per 100g
                factor = weight / 100.0
                totals["protein_g"] += float(getattr(ing, "protein", 0.0) or 0.0) * factor
                totals["lipid_g"] += float(getattr(ing, "lipid", 0.0) or 0.0) * factor
                totals["carb_g"] += float(getattr(ing, "carbohydrate", 0.0) or 0.0) * factor
                totals["sodium_mg"] += float(getattr(ing, "natri", 0.0) or 0.0) * factor
                totals["fiber_g"] += float(getattr(ing, "fiber", 0.0) or 0.0) * factor
            else:
                # Unknown ingredient: skip or apply heuristic (skip for now)
                continue

        return {k: round(v, 3) for k, v in totals.items()}

    def _store_recipe_snapshot(self, dish_name: str, mapped_ingredients: list[dict], confidence: float, source: str = "GEMINI"):
        from recommendation.models import DishRecipeSnapshot
        normalized_name = remove_accents((dish_name or "").strip().lower())
        snapshot = DishRecipeSnapshot.objects.create(
            dish_name=dish_name,
            normalized_name=normalized_name,
            ingredients=mapped_ingredients,
            source=source,
            confidence_score=confidence,
        )
        return snapshot

    def _call_external_llm_parser(self, text: str) -> list[ParsedMeal]:
        base_url = (getattr(settings, "AI_MODEL_BASE_URL", "") or "").strip().rstrip("/")
        if not base_url:
            return []

        timeout = int(getattr(settings, "AI_MODEL_TIMEOUT_SECONDS", 10) or 10)
        url = f"{base_url}/nutrition/parse-meals"
        try:
            response = requests.post(url, json={"text": text}, timeout=timeout)
            response.raise_for_status()
            payload = response.json() if response.content else {}
        except Exception:
            return []

        rows = payload.get("meals", []) if isinstance(payload, dict) else []
        return self._normalize_parsed_rows(rows)

    def _normalize_parsed_rows(self, rows: list[Any]) -> list[ParsedMeal]:
        results: list[ParsedMeal] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            quantity_multiplier = float(row.get("quantity_multiplier") or 1.0)
            confidence_parse = float(row.get("confidence_parse") or row.get("confidence") or 0.7)
            results.append(
                ParsedMeal(
                    name=name,
                    quantity_multiplier=max(0.2, min(3.0, quantity_multiplier)),
                    confidence_parse=self._clamp(confidence_parse),
                )
            )
        return results

    def _parse_json_safely(self, content: str) -> Any:
        text = (content or "").strip()
        if not text:
            return None

        try:
            return json.loads(text)
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return None

    def _heuristic_parse(self, text: str) -> list[ParsedMeal]:
        normalized = remove_accents((text or "").lower())
        parts = re.split(r",|\+|\bva\b|\bkem\b|\bvoi\b", normalized)

        stop_tokens = {
            "sang",
            "trua",
            "chieu",
            "toi",
            "hom nay",
            "toi moi",
            "toi da",
            "an",
            "uong",
            "vua",
            "moi",
        }

        results: list[ParsedMeal] = []
        for raw in parts:
            segment = re.sub(r"\s+", " ", raw).strip()
            if not segment:
                continue

            quantity_multiplier = 1.0
            for key, multiplier in self.PORTION_MULTIPLIER_HINTS.items():
                if key in segment:
                    quantity_multiplier = max(quantity_multiplier, multiplier)

            tokens = [token for token in segment.split(" ") if token and token not in stop_tokens]
            meal_name = " ".join(tokens).strip()
            if len(meal_name) < 2:
                continue

            results.append(
                ParsedMeal(
                    name=meal_name,
                    quantity_multiplier=max(0.2, min(3.0, quantity_multiplier)),
                    confidence_parse=0.65,
                )
            )

        return results

    def _match_dish(self, meal_name: str):
        """
        Match meal name to Dish using production-grade fuzzy search with aliases.
        
        Uses DishSearchService which implements:
        - Normalize: remove accents, lowercase
        - Retrieve: fuzzy matching on name + aliases (threshold 0.6)
        - Semantic rank: score based on fuzzy ratio + rating + popularity
        - Return: highest-scoring match or None
        """
        if not meal_name or not meal_name.strip():
            return None
        
        try:
            # Use production-grade search service (fuzzy + alias support)
            search_result = DishSearchService.search(
                query=meal_name,
                category=None,
                location_id=None,
                status=None,
                available_today=False,
                limit=1,  # Only need top 1 match
            )
            
            results = search_result.get("results", [])
            if not results:
                return None
            
            # Get the highest-scoring match
            top_match = results[0]
            dish_uid = top_match.get("uid")
            
            if not dish_uid:
                return None
            
            # Fetch the full Dish object from DB
            try:
                dish = Dish.objects.get(uid=dish_uid, deleted=False)
                return dish
            except Dish.DoesNotExist:
                return None
        
        except Exception:
            # Fallback to None if search service fails
            return None

    def _match_translation_mapping(self, meal_name: str):
        normalized = remove_accents((meal_name or "").strip().lower())
        if not normalized:
            return None

        mapping = DishTranslationMapping.objects.filter(active=True, normalized_vietnamese_name=normalized).first()
        if mapping is not None:
            return mapping

        return DishTranslationMapping.objects.filter(
            active=True, normalized_vietnamese_name__icontains=normalized
        ).first()

    def _extract_mapping_nutrition(self, mapping: DishTranslationMapping) -> dict[str, float]:
        payload = mapping.nutrition_per_serving if isinstance(mapping.nutrition_per_serving, dict) else {}
        return {
            "protein_g": float(payload.get("protein_g") or 0.0),
            "lipid_g": float(payload.get("lipid_g") or 0.0),
            "carb_g": float(payload.get("carb_g") or 0.0),
            "sodium_mg": float(payload.get("sodium_mg") or 0.0),
            "fiber_g": float(payload.get("fiber_g") or 0.0),
        }

    def _create_meal_log(
        self,
        *,
        daily: UserDailyNutrition,
        source: str,
        meal_time: str,
        meal_name: str,
        dish,
        quantity_multiplier: float,
        nutrition: dict[str, float],
        confidence_parse: float,
        confidence_source: float,
        raw_payload: dict[str, Any],
    ) -> DailyMealLog:
        multiplier = max(float(quantity_multiplier or 1.0), 0.1)
        return DailyMealLog.objects.create(
            daily_nutrition=daily,
            source=source,
            meal_time=(meal_time or DailyMealLog.MEAL_UNKNOWN).upper(),
            meal_name=meal_name,
            dish=dish,
            quantity_multiplier=multiplier,
            nutrition_protein_g=float(nutrition.get("protein_g", 0.0)) * multiplier,
            nutrition_lipid_g=float(nutrition.get("lipid_g", 0.0)) * multiplier,
            nutrition_carb_g=float(nutrition.get("carb_g", 0.0)) * multiplier,
            nutrition_sodium_mg=float(nutrition.get("sodium_mg", 0.0)) * multiplier,
            nutrition_fiber_g=float(nutrition.get("fiber_g", 0.0)) * multiplier,
            confidence_parse=self._clamp(confidence_parse),
            confidence_source=self._clamp(confidence_source),
            raw_payload=raw_payload or {},
        )

    @staticmethod
    def _empty_nutrition() -> dict[str, float]:
        return {
            "protein_g": 0.0,
            "lipid_g": 0.0,
            "carb_g": 0.0,
            "sodium_mg": 0.0,
            "fiber_g": 0.0,
        }

    def _build_summary(self, daily: UserDailyNutrition) -> dict[str, Any]:
        target = {
            "protein_g": float(daily.target_protein_g or 0.0),
            "lipid_g": float(daily.target_lipid_g or 0.0),
            "carb_g": float(daily.target_carb_g or 0.0),
            "sodium_mg": float(daily.target_sodium_mg or 0.0),
            "fiber_g": float(daily.target_fiber_g or 0.0),
        }
        consumed_raw = {
            "protein_g": float(daily.consumed_protein_g or 0.0),
            "lipid_g": float(daily.consumed_lipid_g or 0.0),
            "carb_g": float(daily.consumed_carb_g or 0.0),
            "sodium_mg": float(daily.consumed_sodium_mg or 0.0),
            "fiber_g": float(daily.consumed_fiber_g or 0.0),
        }
        uncertainty = self._compute_consumed_uncertainty(daily)

        macros = ("protein_g", "lipid_g", "carb_g", "sodium_mg", "fiber_g")
        consumed_out: dict[str, Any] = {}
        for k in macros:
            consumed_out[k] = round(consumed_raw[k], 3)
            consumed_out[f"{k}_uncertainty"] = uncertainty[k]

        remaining: dict[str, Any] = {}
        for k in macros:
            mid = round(target[k] - consumed_raw[k], 3)
            unc = uncertainty[k]
            remaining[k] = mid
            remaining[f"{k}_lower"] = round(mid - unc, 3)
            remaining[f"{k}_upper"] = round(mid + unc, 3)

        return {
            "date": str(daily.date),
            "bmr_kcal": round(float(daily.bmr_kcal or 0.0), 3),
            "tdee_kcal": round(float(daily.tdee_kcal or 0.0), 3),
            "target": {k: round(v, 3) for k, v in target.items()},
            "consumed": consumed_out,
            "remaining": remaining,
        }

    def _build_profile(self, daily: UserDailyNutrition) -> dict[str, Any]:
        """Build profile response with personal info + nutrition data"""
        summary = self._build_summary(daily)
        return {
            # Profile fields
            "age": int(daily.age),
            "gender": str(daily.gender),
            "height_cm": float(daily.height_cm),
            "weight_kg": float(daily.weight_kg),
            "activity_level": str(daily.activity_level),
            "goal": str(daily.goal),
            # Nutrition fields (from summary)
            **summary,
        }

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _compute_source_confidence(
        self,
        *,
        parsed_name: str,
        resolved_name: str,
        nutrition: dict[str, float],
        base_quality: float,
    ) -> float:
        similarity_to_resolved = self._name_similarity(parsed_name, resolved_name)
        completeness_score = self._nutrition_completeness(nutrition)
        data_quality_score = self._clamp(float(base_quality or 0.0))

        confidence = similarity_to_resolved * completeness_score * data_quality_score
        return max(0.2, round(self._clamp(confidence), 3))

    def _name_similarity(self, raw_name: str, resolved_name: str) -> float:
        a = remove_accents((raw_name or "").strip().lower())
        b = remove_accents((resolved_name or "").strip().lower())
        if not a or not b:
            return 0.0

        if a == b:
            return 1.0

        token_overlap = 0.0
        tokens_a = set(a.split())
        tokens_b = set(b.split())
        if tokens_a and tokens_b:
            token_overlap = len(tokens_a.intersection(tokens_b)) / len(tokens_a.union(tokens_b))

        seq_ratio = SequenceMatcher(None, a, b).ratio()
        return self._clamp((0.55 * token_overlap) + (0.45 * seq_ratio))

    def _nutrition_completeness(self, nutrition: dict[str, float]) -> float:
        keys = ("protein_g", "lipid_g", "carb_g", "sodium_mg", "fiber_g")
        valid_count = 0
        for key in keys:
            value = nutrition.get(key)
            if value is None:
                continue
            if float(value) > 0:
                valid_count += 1
        ratio = valid_count / float(len(keys))
        return max(0.2, self._clamp(ratio))

    def _macro_match_score(self, *, remaining: dict[str, float], dish_nutrition: dict[str, float]) -> float:
        """
        Range-aware macro matching:
        - val in [lower, upper] → score = 1.0 (ideal zone)
        - val < lower           → proportional fill toward midpoint
        - val > upper           → penalize overshoot (×2 steeper)
        remaining keys: protein_g (mid), protein_g_lower, protein_g_upper (and same for other macros)
        """
        weights = {
            "protein_g": 0.4,
            "lipid_g": 0.2,
            "carb_g": 0.4,
        }

        score = 0.0
        total_weight = 0.0

        for k, w in weights.items():
            rem_mid = max(remaining.get(k, 0.0), 0.0)
            rem_lower = max(remaining.get(f"{k}_lower", rem_mid), 0.0)
            rem_upper = max(remaining.get(f"{k}_upper", rem_mid), 0.0)
            val = max(dish_nutrition.get(k, 0.0), 0.0)

            if rem_mid <= 0:
                continue

            if val < rem_lower:
                sub_score = val / rem_mid
            elif val <= rem_upper:
                sub_score = 1.0
            else:
                overflow_ratio = (val - rem_upper) / max(rem_upper, 1.0)
                sub_score = max(0.0, 1.0 - overflow_ratio * 2.0)

            score += sub_score * w
            total_weight += w

        return score / total_weight if total_weight > 0 else 0.5

    def _sodium_penalty(self, *, remaining: dict[str, float], dish_nutrition: dict[str, float]) -> float:
        remaining_sodium = float(remaining.get("sodium_mg", 0.0))
        dish_sodium = max(float(dish_nutrition.get("sodium_mg", 0.0)), 0.0)
        if remaining_sodium > 400:
            return 0.0
        return max(0.0, min(1.0, dish_sodium / 2000.0))

    def _suggest_servings(self, *, remaining: dict[str, float], dish_nutrition: dict[str, float]) -> float:
        candidates: list[float] = []
        for key in ("protein_g", "lipid_g", "carb_g"):
            rem = max(float(remaining.get(key, 0.0)), 0.0)
            val = float(dish_nutrition.get(key, 0.0))
            if rem > 0 and val > 0:
                candidates.append(rem / val)

        if not candidates:
            return 1.0

        candidates.sort()
        median = candidates[len(candidates) // 2]
        return max(0.5, min(2.5, median))

    def _remaining_reasons(self, *, remaining: dict[str, float]) -> list[str]:
        reasons: list[str] = []
        if float(remaining.get("protein_g", 0.0)) > 10:
            reasons.append("Cần bổ sung protein trong ngày")
        if float(remaining.get("carb_g", 0.0)) > 20:
            reasons.append("Cần bổ sung carbohydrate cho mục tiêu năng lượng")
        if float(remaining.get("lipid_g", 0.0)) > 8:
            reasons.append("Cần bổ sung chất béo lành mạnh")
        if float(remaining.get("fiber_g", 0.0)) > 5:
            reasons.append("Cần tăng chất xơ để cân bằng bữa ăn")
        if not reasons:
            reasons.append("Phù hợp cân bằng dinh dưỡng hiện tại")
        return reasons

    def _validate_meal_portion(
        self,
        *,
        servings: float,
        dish_nutrition: dict[str, float],
        daily_target: dict[str, float]
    ) -> float:
        """
        ⭐ MEAL PORTION VALIDATION: Ensure no single meal exceeds 60% of daily targets
        
        Rule: MAX_MEAL_RATIO = 0.60 (60%)
        - If suggested servings cause meal to exceed 60% of ANY macro target, scale down
        - Returns adjusted servings (or original if within limits)
        
        Example:
        - Daily protein target: 75g
        - Dish protein per 100g: 25g
        - Suggested servings: 3.0 (= 75g protein = 100% of target) ❌ TOO HIGH
        - Adjusted: 1.8 (= 45g protein = 60% of target) ✅ ACCEPTABLE
        
        Args:
            servings: Suggested servings (quantity multiplier)
            dish_nutrition: Nutrition per 100g of dish
            daily_target: Daily macro targets
        
        Returns:
            Adjusted servings if exceeds limit, otherwise original servings
        """
        max_servings = float('inf')
        
        for macro_key in ("protein_g", "lipid_g", "carb_g", "sodium_mg", "fiber_g"):
            dish_value = float(dish_nutrition.get(macro_key, 0.0))
            target_value = float(daily_target.get(macro_key, 0.0))
            
            if dish_value > 0 and target_value > 0:
                # Max servings where meal = 60% of daily target
                # meal_nutrition = dish_value * servings
                # meal_nutrition ≤ 0.60 * target_value
                # servings ≤ (0.60 * target_value) / dish_value
                max_for_this_macro = (self.MAX_MEAL_RATIO * target_value) / dish_value
                max_servings = min(max_servings, max_for_this_macro)
        
        # If limit is infinity (no macros to check), return original servings
        if max_servings == float('inf'):
            return servings
        
        # Return original servings if within limit, otherwise return adjusted
        if servings <= max_servings:
            return servings
        
        # Scale down to fit within limit
        return max(0.5, max_servings)  # Never go below 0.5 servings (minimum portion)
