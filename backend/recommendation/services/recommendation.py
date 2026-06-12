import math
import logging
from uuid import UUID
from collections import defaultdict
from django.contrib.auth import get_user_model

from exceptions.recommendation import PreferencesNotFoundException
from exceptions.users import UserNotFound
from review.orm.review import ReviewORM
from recommendation.orm.recommendation import RecommendationORM
from utils.functions.remove_accents import remove_accents

class RecommendationService:
    def __init__(self):
        self.orm = RecommendationORM()
        self.review_orm = ReviewORM()
        self._pipeline = None
        self._daily_nutrition_service = None

    TIME_DECAY_LAMBDA = 0.03
    MIN_WEIGHT_THRESHOLD = 0.1

    _logger = logging.getLogger(__name__)

    DEFAULT_ISSUES = [
        "mặn",
        "nhạt",
        "cay",
        "ngọt",
        "chua",
        "đắng",
        "dai",
        "khô",
        "nhão",
        "dầu mỡ",
        "tanh",
        "hôi",
        "hư thiu",
        "sạn",
        "giao chậm",
        "giao sai",
        "giao thiếu",
        "đóng gói kém",
        "nguội",
        "ít topping",
        "ít sốt",
        "ít nhân",
        "làm lâu",
        "giá đắt",
        "phục vụ kém",
        "chưa tốt",
    ]
    ISSUE_WHITELIST = set(DEFAULT_ISSUES)

    @staticmethod
    def _normalize_json_id(value):
        if isinstance(value, UUID):
            return str(value)
        return value

    # =========================
    # PUBLIC API
    # =========================
    def get_user_issue_sensitivity_profile(self, user_id: int) -> dict:
        self._validate_user(user_id)

        rows = self.review_orm.get_user_issue_rows(user_id)

        if not rows:
            return self._empty_profile(user_id)

        processed = self._preprocess(rows)
        issue_profile, stats = self._aggregate(processed)
        confidence = self._compute_confidence(stats)

        return {
            "user_id": user_id,
            "issue_profile": issue_profile,
            "confidence": round(confidence, 3),
            "data_points": stats["data_points"],
        }

    # =========================
    # PRIVATE METHODS
    # =========================

    def _validate_user(self, user_id: int):
        user_model = get_user_model()
        if not user_model.objects.filter(id=user_id).exists():
            raise UserNotFound

    def _empty_profile(self, user_id: int):
        return {
            "user_id": user_id,
            "issue_profile": {issue: 0.0 for issue in self.DEFAULT_ISSUES},
            "confidence": 0.0,
            "data_points": 0,
        }

    def _normalize_issue(self, issue: str) -> str:
        normalized = remove_accents((issue or "").strip().lower())
        return normalized.replace(" ", "_").replace("-", "_")

    def _classify_issue(self, raw_issue: str) -> str | None:
        normalized = (raw_issue or "").strip().lower()
        normalized_compact = self._normalize_issue(normalized)

        if normalized in self.ISSUE_WHITELIST:
            return normalized

        if normalized_compact in {
            self._normalize_issue(issue) for issue in self.ISSUE_WHITELIST
        }:
            for issue in self.ISSUE_WHITELIST:
                if self._normalize_issue(issue) == normalized_compact:
                    return issue

        return None

    def _normalize_issue_query(self, issue: str) -> str:
        """Normalize a user-provided issue so accent variants match stored labels."""
        return self._normalize_issue(issue)

    # =========================
    # STEP 1: preprocess
    # =========================
    def _preprocess(self, rows):
        from django.utils import timezone

        now = timezone.now()
        processed = []

        for row in rows:
            raw_issue = row.get("issue")
            if not raw_issue:
                continue

            issue = self._classify_issue(str(raw_issue))

            if issue not in self.ISSUE_WHITELIST:
                continue

            weight = float(row.get("weight") or 0.0)
            weight = max(0.0, min(weight, 1.0))

            if weight < self.MIN_WEIGHT_THRESHOLD:
                continue

            created_at = row.get("created_at")
            age_days = 0.0
            if created_at:
                age_days = max((now - created_at).total_seconds(), 0) / 86400

            decay = math.exp(-self.TIME_DECAY_LAMBDA * age_days)

            processed.append({
                "issue": issue,
                "value": weight * decay,
                "decay": decay
            })

        return processed

    # =========================
    # STEP 2: aggregate (FIXED)
    # =========================
    def _aggregate(self, processed):
        issue_weight_sum = defaultdict(float)
        issue_decay_sum = defaultdict(float)
        issue_values = defaultdict(list)

        total_score = 0.0

        for item in processed:
            issue = item["issue"]
            value = item["value"]
            decay = item["decay"]

            issue_weight_sum[issue] += value
            issue_decay_sum[issue] += decay
            issue_values[issue].append(value)

            total_score += value

        profile = {}

        for issue in self.DEFAULT_ISSUES:
            if issue_decay_sum[issue] > 0:
                score = issue_weight_sum[issue] / issue_decay_sum[issue]
            else:
                score = 0.0

            profile[issue] = round(score, 3)

        stats = {
            "data_points": len(processed),
            "total_score": total_score,
            "issue_values": issue_values
        }

        return profile, stats

    # =========================
    # STEP 3: confidence
    # =========================
    def _compute_confidence(self, stats):
        data_points = stats["data_points"]
        total_score = stats["total_score"]
        issue_values = stats["issue_values"]

        if data_points == 0:
            return 0.0

        # coverage
        coverage = 1 - math.exp(-data_points / 25)

        # signal strength
        avg_signal = total_score / data_points

        # consistency
        variance_sum = 0.0
        count = 0

        for values in issue_values.values():
            if len(values) > 1:
                mean = sum(values) / len(values)
                var = sum((v - mean) ** 2 for v in values) / len(values)
                variance_sum += var
                count += 1

        avg_variance = variance_sum / count if count > 0 else 0.0
        variance_penalty = min(1.0, avg_variance)

        confidence = (
            0.5 * coverage
            + 0.3 * avg_signal
            + 0.2 * (1 - variance_penalty)
        )

        return max(0.0, min(1.0, confidence))
    
    def rebuild_user_feature(self, user_id: int, update_fields=None):
        from profile.models import CustomerProfile, CustomerFavoriteDish
        from ingredient.models import FavouriteIngredient, AllergicIngredient
        from recommendation.models import UserFoodPreferenceFeature

        defaults = {}

        if update_fields is None or "diet" in update_fields:
            profile = CustomerProfile.objects.filter(user_id=user_id).first()
            if profile is not None:
                defaults.update({
                    "diet_mode": profile.diet_mode,
                    "diet_level": profile.diet_level,
                    "allergy_mode": profile.allergy_mode,
                })

        if update_fields is None or "fav_ingredient" in update_fields:
            defaults["favorite_ingredient_ids"] = [
                self._normalize_json_id(value)
                for value in FavouriteIngredient.objects.filter(user_id=user_id, deleted=False)
                .values_list("ingredient_id", flat=True)
            ]

        if update_fields is None or "allergy" in update_fields:
            defaults["allergic_ingredient_ids"] = [
                self._normalize_json_id(value)
                for value in AllergicIngredient.objects.filter(user_id=user_id, deleted=False)
                .values_list("ingredient_id", flat=True)
            ]

        if update_fields is None or "fav_dish" in update_fields:
            defaults["favorite_dish_ids"] = [
                self._normalize_json_id(value)
                for value in CustomerFavoriteDish.objects.filter(user_id=user_id, deleted=False)
                .values_list("dish_id", flat=True)
            ]
        UserFoodPreferenceFeature.objects.update_or_create(
            user_id=user_id,
            defaults=defaults,
        )

    def get_user_food_preference_features(self, user_id: int):
        # check user existence
        user = get_user_model().objects.filter(id=user_id).first()
        if not user:
            raise UserNotFound
        result = self.orm.get_user_food_preference_features(user_id=user_id)
        if result is None:
            raise PreferencesNotFoundException
        return result

    def get_recommended_dishes(
        self,
        *,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        include_explain: bool = False,
    ):
        if self._pipeline is None:
            from recommendation.services.pipeline import RecommendationPipelineService

            self._pipeline = RecommendationPipelineService()

        return self._pipeline.recommend_for_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            include_explain=include_explain,
        )

    def _get_daily_nutrition_service(self):
        if self._daily_nutrition_service is None:
            from recommendation.services.daily_nutrition import DailyNutritionService

            self._daily_nutrition_service = DailyNutritionService()
        return self._daily_nutrition_service

    def init_daily_nutrition(
        self,
        *,
        user_id: int,
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float,
        activity_level: str,
        goal: str,
    ):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().initialize_daily_profile(
            user_id=user_id,
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal,
        )

    def parse_daily_meal(self, *, user_id: int, text: str, meal_time: str = "UNKNOWN"):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().parse_outside_meals(
            user_id=user_id,
            text=text,
            meal_time=meal_time,
        )

    def get_daily_nutrition_summary(self, *, user_id: int):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().get_daily_summary(user_id=user_id)

    def get_daily_meal_logs(self, *, user_id: int):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().get_daily_meal_logs(user_id=user_id)

    def update_daily_meal_log(
        self,
        *,
        user_id: int,
        log_uid: str,
        meal_name: str | None = None,
        meal_time: str | None = None,
        quantity_multiplier: float | None = None,
        dish_uid: str | None = None,
    ):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().update_daily_meal_log(
            user_id=user_id,
            log_uid=log_uid,
            meal_name=meal_name,
            meal_time=meal_time,
            quantity_multiplier=quantity_multiplier,
            dish_uid=dish_uid,
        )

    def delete_daily_meal_log(self, *, user_id: int, log_uid: str):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().delete_daily_meal_log(user_id=user_id, log_uid=log_uid)

    def sync_order_meal_logs(self, *, order_uid: str):
        return self._get_daily_nutrition_service().sync_order_meal_logs(order_uid=order_uid)

    def get_daily_balanced_recommendations(self, *, user_id: int, limit: int = 10):
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().get_balanced_recommendations(
            user_id=user_id,
            limit=limit,
        )

    def find_better_dish_for_issue(
        self,
        *,
        user_id: int,
        dish_uid: str,
        limit: int = 5
    ) -> dict:
        from django.db import connection
        from django.db.models import Count
        from dish.models import Dish
        from review.models import Review
        from exceptions.dishes import DishNotFoundException
        from recommendation.services.vector_index import VectorIndexService
        from recommendation.services.candidates import CandidateGenerator

        # ======================
        # 1. VALIDATE DISH + ISSUE CONTEXT
        # ======================
        from uuid import UUID
        from django.core.exceptions import ObjectDoesNotExist
        
        # ⭐ FIX: Convert string to UUID
        dish_uid_obj: str | UUID = dish_uid
        if isinstance(dish_uid, str):
            try:
                dish_uid_obj = UUID(dish_uid)
            except (ValueError, TypeError):
                pass
        
        dish = Dish.objects.filter(uid=dish_uid_obj, deleted=False).first()
        if not dish:
            raise DishNotFoundException

        latest_review = (
            Review.objects
            .filter(
                dish__uid=dish_uid_obj,
                owner_id=user_id,
                deleted=False
            )
            .order_by("-created_at")
            .first()
        )

        issue = latest_review.issue if latest_review else None

        if not issue:
            self._logger.debug(
                "find_better_dish_for_issue: no issue in latest review",
                extra={"user_id": user_id, "dish_uid": str(dish_uid)},
            )
            return {
                "issue": None,
                "source_dish_uid": dish_uid,
                "items": []
            }

        # ======================
        # 2. VECTOR CANDIDATES
        # ======================
        vector = None
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT embedding::text
                    FROM recommendation_dish_vector_index
                    WHERE dish_uid = %s
                    """,
                    [dish_uid_obj],
                )
                row = cursor.fetchone()
                if row and row[0]:
                    vector = VectorIndexService()._parse_vector_literal(str(row[0]))
        except Exception:
            vector = None

        candidate_ids = set()

        if vector:
            gen = CandidateGenerator(candidate_pool_size=max(100, limit * 10))
            vec_candidates = gen._vector_source_ids(
                user_vector=vector,
                allergic_ingredient_ids=[],
                allergy_mode="",
                limit=max(100, limit * 10),
            )
            candidate_ids.update(vec_candidates)

        # ======================
        # 3. FALLBACK KEYWORD CANDIDATES
        # ======================
        if len(candidate_ids) < max(10, limit * 2):
            # ⭐ FIX: More lenient keyword search (any keyword match, not all)
            words = [
                w for w in (dish.name_no_accent or "").split()
                if len(w) > 2
            ][:3]

            if words:
                from django.db.models import Q
                
                # Try to find dishes with ANY of the keywords in same category
                q_filter = Q(deleted=False, category=dish.category)
                
                # Build OR query for keywords (any match is ok)
                keyword_q = Q()
                for w in words:
                    keyword_q |= Q(name_no_accent__icontains=w)
                
                if keyword_q:
                    keyword_candidates = list(
                        Dish.objects.filter(q_filter & keyword_q)
                        .values_list("uid", flat=True)[: max(50, limit * 5)]
                    )
                    candidate_ids.update([str(x) for x in keyword_candidates])
        
        # ⭐ FIX: Add category fallback (if still not enough candidates)
        if len(candidate_ids) < max(5, limit):
            category_candidates = list(
                Dish.objects.filter(
                    deleted=False,
                    category=dish.category,
                    avg_rating__gte=3.5
                ).values_list("uid", flat=True)[:max(100, limit * 10)]
            )
            candidate_ids.update([str(x) for x in category_candidates])
        
        # ⭐ FIX: Popular dishes fallback (last resort)
        if not candidate_ids:
            popular_candidates = list(
                Dish.objects.filter(
                    deleted=False,
                    avg_rating__gte=4.0
                ).order_by("-avg_rating")
                .values_list("uid", flat=True)[:max(50, limit * 5)]
            )
            candidate_ids.update([str(x) for x in popular_candidates])

        candidate_ids.discard(str(dish_uid))

        self._logger.debug(
            "find_better_dish_for_issue: candidate count",
            extra={"user_id": user_id, "dish_uid": str(dish_uid), "count": len(candidate_ids)},
        )

        if not candidate_ids:
            return {
                "issue": issue,
                "source_dish_uid": dish_uid,
                "items": self._get_popular_dish_fallback_items(limit=limit)
            }

        # ======================
        # 4. BATCH ISSUE STATS (FIX N+1) - WITH CASE-INSENSITIVE MATCHING
        # ======================
        # ⭐ FIX: Case-insensitive issue search (iexact = exact but ignore case)
        from django.db.models import Q
        
        candidate_ids_list = list(candidate_ids)  # Convert set to list for ORM query
        
        issue_stats = (
            Review.objects
            .filter(
                dish__uid__in=candidate_ids_list,
                deleted=False
            )
            .filter(
                Q(issue__iexact=issue) |  # Exact match, case-insensitive
                Q(issue__icontains=issue)  # Partial match, case-insensitive
            )
            .values("dish__uid")
            .annotate(count=Count("uid"))
        )

        issue_map = {
            str(x["dish__uid"]): x["count"]
            for x in issue_stats
        }

        rating_map = {
            d["dish_uid"]: d
            for d in self.review_orm.get_bulk_dish_rating_stats(candidate_ids)
        }

        # ======================
        # 5. SCORE CANDIDATES
        # ======================
        scored = []

        for cid in candidate_ids:
            stats = rating_map.get(cid, {})
            avg_rating = float(stats.get("avg_rating") or 0.0)
            total_reviews = int(stats.get("total_reviews") or 0)

            issue_count = issue_map.get(cid, 0)

            # ⚠️ FIXED: Changed smoothing formula to avoid bias against low-review items
            # OLD (BIASED): (issue_count + 1) / (total_reviews + 5)
            #   Problem: Laplace smoothing too aggressive for sparse data
            #   Example: 1 review with 0 issues → rate = 1/6 = 0.167 (penalized heavily)
            #            100 reviews with 10 issues → rate = 11/105 = 0.105 (less penalty)
            # NEW (FAIR): issue_count / max(total_reviews, 1)
            #   Rationale: Actual rate, only protect against division by zero
            #   Items with few reviews won't be penalized by uncertainty
            issue_rate = issue_count / max(total_reviews, 1)

            popularity = min(total_reviews / 100.0, 1.0)

            score = (
                (1.0 - issue_rate) * 0.5 +
                (avg_rating / 5.0) * 0.3 +
                popularity * 0.2
            )

            scored.append({
                "dish_uid": cid,
                "avg_rating": avg_rating,
                "total_reviews": total_reviews,
                "issue_rate": round(issue_rate, 3),
                "score": round(score, 4),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:max(1, limit)]

        self._logger.debug(
            "find_better_dish_for_issue: scored count",
            extra={"user_id": user_id, "dish_uid": str(dish_uid), "count": len(scored)},
        )

        if not top:
            return {
                "issue": issue,
                "source_dish_uid": dish_uid,
                "items": self._get_popular_dish_fallback_items(limit=limit)
            }

        # ======================
        # 6. ENRICH RESPONSE
        # ======================
        from typing import Dict, Optional
        
        dish_map: Dict[str, Optional[Dish]] = {
            str(dish_item.uid): dish_item
            for dish_item in Dish.objects
            .select_related("attachment")
            .filter(uid__in=[s["dish_uid"] for s in top])
        }

        items = []
        for s in top:
            dish_result: Optional[Dish] = dish_map.get(s["dish_uid"])
            if dish_result is None:
                continue

            items.append({
                "dish_uid": s["dish_uid"],
                "dish_name": dish_result.name,
                "price": float(dish_result.price) if dish_result.price is not None else None,
                "public_url": getattr(dish_result.attachment, "public_url", None) if dish_result.attachment else None,
                "avg_rating": s["avg_rating"],
                "total_reviews": s["total_reviews"],
                "issue_rate": s["issue_rate"],
                "score": s["score"],
                "explain": f"Lower {issue} incidence + better rating",
            })

        if not items:
            return {
                "issue": issue,
                "source_dish_uid": dish_uid,
                "items": self._get_popular_dish_fallback_items(limit=limit)
            }

        return {
            "issue": issue,
            "source_dish_uid": dish_uid,
            "items": items
        }

    def _get_popular_dish_fallback_items(self, *, limit: int) -> list[dict]:
        from dish.models import Dish

        fallback_dishes = (
            Dish.objects
            .filter(deleted=False, avg_rating__gte=4.0)
            .select_related("attachment")
            .order_by("-avg_rating")[:max(1, limit)]
        )

        fallback_items = []
        for dish_item in fallback_dishes:
            fallback_items.append({
                "dish_uid": str(dish_item.uid),
                "dish_name": dish_item.name,
                "public_url": getattr(dish_item.attachment, "public_url", None) if dish_item.attachment else None,
                "price": float(dish_item.price) if dish_item.price is not None else None,
                "avg_rating": float(dish_item.avg_rating or 0),
                "total_reviews": int(dish_item.total_reviews or 0) if hasattr(dish_item, "total_reviews") else 0,
                "issue_rate": 0.0,
                "score": round(float(dish_item.avg_rating or 0) / 5.0, 4),
                "explain": "Popular alternative"
            })

        return fallback_items

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
    ) -> dict:
        """
        Update user's daily nutrition profile.
        Only provided fields are updated. TDEE and targets are recalculated.
        Returns full profile with personal info and nutrition data.
        """
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().update_daily_nutrition_profile(
            user_id=user_id,
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal,
        )

    def get_daily_nutrition_profile(self, *, user_id: int) -> dict:
        """
        Get user's daily nutrition profile with personal info and current nutrition data.
        Returns: age, gender, height_cm, weight_kg, activity_level, goal, BMR, TDEE, targets, consumed, remaining
        """
        self._validate_user(user_id)
        return self._get_daily_nutrition_service().get_daily_nutrition_profile(user_id=user_id)
