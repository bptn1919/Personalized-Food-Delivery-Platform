import math
from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from dish.models import DishIngredient
from order.models import OrderItem
from review.models import Review
from utils.enums import OrderStatusEnum


class ScoringEngine:
    def __init__(
        self,
        *,
        time_decay_lambda: float,
        recency_decay_lambda: float,
        weights: dict,
        penalty_gamma: float,
        penalty_correlation_threshold: float,
        balanced_target: tuple[float, float, float] | list[float] | None = None,
        favorite_recency_decay_lambda: float | None = None,
        user_vector_ema_alpha: float = 0.35,
        prioritize_unordered_dishes: bool = False,
    ) -> None:
        self.time_decay_lambda = time_decay_lambda
        self.recency_decay_lambda = recency_decay_lambda
        self.weights = weights
        self.penalty_gamma = penalty_gamma
        self.penalty_correlation_threshold = penalty_correlation_threshold
        self.favorite_recency_decay_lambda = (
            float(favorite_recency_decay_lambda)
            if favorite_recency_decay_lambda is not None
            else float(time_decay_lambda)
        )
        self.user_vector_ema_alpha = self._clamp(float(user_vector_ema_alpha))
        self.prioritize_unordered_dishes = bool(prioritize_unordered_dishes)
        self.unified_penalty_weight = float(
            self.weights.get("w_penalty", self.weights.get("w4", 0.0) + self.weights.get("w5", 0.0))
        )

        if balanced_target and len(balanced_target) == 3:
            p_target = max(float(balanced_target[0]), 0.0)
            f_target = max(float(balanced_target[1]), 0.0)
            c_target = max(float(balanced_target[2]), 0.0)
            target_sum = p_target + f_target + c_target
            if target_sum > 0:
                self.balanced_target = (
                    p_target / target_sum,
                    f_target / target_sum,
                    c_target / target_sum,
                )
            else:
                self.balanced_target = (0.3, 0.3, 0.4)
        else:
            self.balanced_target = (0.3, 0.3, 0.4)

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(value, upper))

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _diet_level_weight(self, diet_level: str) -> float:
        level = (diet_level or "NONE").upper()
        if level == "SOFT":
            return 0.05
        if level == "MEDIUM":
            return 0.10
        if level == "STRONG":
            return 0.15
        return 0.0

    def _diet_macro_ratios(self, dish_vector: list[float]) -> tuple[float, float, float, float]:
        protein = max(float(dish_vector[0]) if len(dish_vector) > 0 else 0.0, 0.0)
        fat = max(float(dish_vector[1]) if len(dish_vector) > 1 else 0.0, 0.0)
        carb = max(float(dish_vector[2]) if len(dish_vector) > 2 else 0.0, 0.0)
        fiber = max(float(dish_vector[4]) if len(dish_vector) > 4 else 0.0, 0.0)
        total = protein + fat + carb
        if total <= 0:
            return 0.0, 0.0, 0.0, fiber
        return protein / total, fat / total, carb / total, fiber

    def _diet_alignment(self, diet_mode: str, dish_vector: list[float]) -> float:
        mode = (diet_mode or "NONE").upper()
        if mode == "NONE":
            return 0.5

        protein_ratio, fat_ratio, carb_ratio, fiber = self._diet_macro_ratios(dish_vector)
        if (protein_ratio + fat_ratio + carb_ratio) <= 0:
            return 0.5

        if mode == "LOW_CARB":
            return self._clamp(1.0 - carb_ratio)

        if mode == "HIGH_PROTEIN":
            return self._clamp(protein_ratio)

        if mode == "LOW_FAT":
            return self._clamp(1.0 - fat_ratio)

        if mode == "BALANCED":
            p_target, f_target, c_target = self.balanced_target
            distance = abs(protein_ratio - p_target) + abs(fat_ratio - f_target) + abs(carb_ratio - c_target)
            return self._clamp(1.0 - (distance / 1.4))

        if mode == "LIGHT":
            low_density = self._clamp(1.0 - (0.7 * fat_ratio + 0.3 * carb_ratio))
            fiber_bonus = self._clamp(fiber / 8.0)
            return self._clamp(0.85 * low_density + 0.15 * fiber_bonus)

        return 0.5

    def _get_popularity_map(self, dish_ids: list[str]) -> dict[str, int]:
        rows = (
            OrderItem.objects.filter(
                dish_id__in=dish_ids,
                order__status=OrderStatusEnum.COMPLETED,
            )
            .values("dish_id")
            .annotate(count=Count("id"))
        )
        return {str(item["dish_id"]): int(item["count"]) for item in rows}

    def _get_history_raw_map(self, user_id: int, dish_ids: list[str]) -> dict[str, float]:
        rows = (
            OrderItem.objects.filter(
                order__owner_id=user_id,
                order__status=OrderStatusEnum.COMPLETED,
                dish_id__in=dish_ids,
            )
            .select_related("order")
            .values("dish_id", "quantity", "order__created_at")
        )
        now = timezone.now()
        history_raw: dict[str, float] = defaultdict(float)
        for row in rows:
            created_at = row.get("order__created_at")
            age_days = 0.0
            if created_at:
                age_days = max((now - created_at).total_seconds(), 0.0) / 86400
            decay = math.exp(-self.time_decay_lambda * age_days)
            history_raw[str(row["dish_id"])] += float(row.get("quantity") or 1) * decay
        return history_raw

    def _get_ingredient_ratio_map(
        self,
        dish_ids: list[str],
        favorite_ingredient_ids: list[str],
    ) -> dict[str, float]:
        if not dish_ids:
            return {}

        total_rows = (
            DishIngredient.objects.filter(dish_id__in=dish_ids, deleted=False)
            .values("dish_id")
            .annotate(total=Count("uid"))
        )
        total_map = {str(item["dish_id"]): int(item["total"]) for item in total_rows}

        if not favorite_ingredient_ids:
            return {dish_id: 0.0 for dish_id in total_map}

        match_rows = (
            DishIngredient.objects.filter(
                dish_id__in=dish_ids,
                deleted=False,
                ingredient_id__in=favorite_ingredient_ids,
            )
            .values("dish_id")
            .annotate(matched=Count("uid"))
        )
        matched_map = {str(item["dish_id"]): int(item["matched"]) for item in match_rows}

        ratio_map: dict[str, float] = {}
        for dish_id, total_count in total_map.items():
            if total_count <= 0:
                ratio_map[dish_id] = 0.0
                continue
            ratio_map[dish_id] = self._clamp(matched_map.get(dish_id, 0) / total_count)
        return ratio_map

    def _get_favorite_recency_map(self, user_id: int, dish_ids: list[str]) -> dict[str, float]:
        if not dish_ids:
            return {}

        from profile.models import CustomerFavoriteDish

        rows = CustomerFavoriteDish.objects.filter(
            user_id=user_id,
            deleted=False,
            dish_id__in=dish_ids,
        ).values("dish_id", "created_at")

        now = timezone.now()
        result: dict[str, float] = {dish_id: 0.0 for dish_id in dish_ids}
        for row in rows:
            created_at = row.get("created_at")
            age_days = 0.0
            if created_at:
                age_days = max((now - created_at).total_seconds(), 0.0) / 86400
            recency = math.exp(-self.favorite_recency_decay_lambda * age_days)
            result[str(row["dish_id"])] = self._clamp(recency)

        return result

    def _get_dish_issue_map(self, dish_ids: list[str], issue_keys: list[str]) -> dict[str, dict[str, float]]:
        if not dish_ids:
            return {}

        rows = (
            Review.objects.filter(
                deleted=False,
                dish_id__in=dish_ids,
                issue__isnull=False,
            )
            .exclude(issue="")
            .values("dish_id", "issue")
            .annotate(avg_weight=Avg("weight"))
        )

        result = {dish_id: {issue: 0.0 for issue in issue_keys} for dish_id in dish_ids}
        for row in rows:
            issue = str(row["issue"] or "").strip().lower()
            if issue not in result[str(row["dish_id"])]:
                continue
            value = float(row.get("avg_weight") or 0.0)
            result[str(row["dish_id"])][issue] = self._clamp(value)
        return result

    def _get_dish_nutrition_vector_map(self, dish_ids: list[str]) -> dict[str, list[float]]:
        if not dish_ids:
            return {}

        rows = DishIngredient.objects.filter(dish_id__in=dish_ids, deleted=False).values(
            "dish_id",
            "weight",
            "protein",
            "lipid",
            "carbohydrate",
            "natri",
            "fiber",
        )

        weighted_sums: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
        sum_weights: dict[str, float] = defaultdict(float)
        unweighted_sums: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
        unweighted_counts: dict[str, list[int]] = defaultdict(lambda: [0] * 5)

        for row in rows:
            dish_id = str(row["dish_id"])
            weight_value = float(row.get("weight") or 0.0)
            weight = weight_value if weight_value > 0 else 0.0

            nutrient_keys = ["protein", "lipid", "carbohydrate", "natri", "fiber"]

            values = [
                float(row.get("protein") or 0.0),
                float(row.get("lipid") or 0.0),
                float(row.get("carbohydrate") or 0.0),
                float(row.get("natri") or 0.0),
                float(row.get("fiber") or 0.0),
            ]

            for idx, value in enumerate(values):
                if row.get(nutrient_keys[idx]) is not None:
                    unweighted_sums[dish_id][idx] += value
                    unweighted_counts[dish_id][idx] += 1

            if weight > 0:
                for idx, value in enumerate(values):
                    weighted_sums[dish_id][idx] += value * weight
                sum_weights[dish_id] += weight

        vector_map: dict[str, list[float]] = {}
        for dish_id in {str(item) for item in dish_ids}:
            if sum_weights[dish_id] > 0:
                vector_map[dish_id] = [
                    weighted_sums[dish_id][idx] / sum_weights[dish_id] for idx in range(5)
                ]
            else:
                vector_map[dish_id] = [
                    (unweighted_sums[dish_id][idx] / unweighted_counts[dish_id][idx])
                    if unweighted_counts[dish_id][idx] > 0
                    else 0.0
                    for idx in range(5)
                ]

        return vector_map

    def _get_nutrition_confidence_map(self, dish_ids: list[str]) -> dict[str, float]:
        if not dish_ids:
            return {}

        rows = (
            DishIngredient.objects.filter(dish_id__in=dish_ids, deleted=False)
            .values("dish_id")
            .annotate(
                total_count=Count("uid"),
                protein_count=Count("uid", filter=Q(protein__isnull=False)),
                lipid_count=Count("uid", filter=Q(lipid__isnull=False)),
                carb_count=Count("uid", filter=Q(carbohydrate__isnull=False)),
                sodium_count=Count("uid", filter=Q(natri__isnull=False)),
                fiber_count=Count("uid", filter=Q(fiber__isnull=False)),
            )
        )

        confidence_map: dict[str, float] = {str(dish_id): 0.0 for dish_id in dish_ids}
        for row in rows:
            total_count = int(row.get("total_count") or 0)
            if total_count <= 0:
                confidence_map[str(row["dish_id"])] = 0.0
                continue

            coverage = (
                float(row.get("protein_count") or 0)
                + float(row.get("lipid_count") or 0)
                + float(row.get("carb_count") or 0)
                + float(row.get("sodium_count") or 0)
                + float(row.get("fiber_count") or 0)
            ) / (5.0 * total_count)
            confidence_map[str(row["dish_id"])] = self._clamp(coverage)

        return confidence_map

    def _apply_user_vector_ema(
        self,
        persisted_user_vector: list[float] | None,
        history_vector: list[float],
    ) -> list[float]:
        if not history_vector:
            return persisted_user_vector or []
        if not persisted_user_vector or len(persisted_user_vector) != len(history_vector):
            return history_vector

        alpha = self.user_vector_ema_alpha
        return [
            (1.0 - alpha) * float(persisted_user_vector[idx]) + alpha * float(history_vector[idx])
            for idx in range(len(history_vector))
        ]

    def _build_user_nutrition_vector(
        self,
        *,
        user_id: int,
        dish_vector_map: dict[str, list[float]],
        fallback_vector: list[float],
    ) -> list[float]:
        if not dish_vector_map:
            return fallback_vector

        rows = (
            OrderItem.objects.filter(
                order__owner_id=user_id,
                order__status=OrderStatusEnum.COMPLETED,
                order__created_at__gte=timezone.now() - timedelta(days=180),
                dish_id__in=list(dish_vector_map.keys()),
            )
            .values("dish_id", "quantity", "order__created_at")
        )

        if not rows:
            return fallback_vector

        now = timezone.now()
        accum = [0.0] * 5
        total_weight = 0.0

        for row in rows:
            vector = dish_vector_map.get(str(row["dish_id"]))
            if not vector:
                continue
            created_at = row.get("order__created_at")
            age_days = 0.0
            if created_at:
                age_days = max((now - created_at).total_seconds(), 0.0) / 86400
            decay = math.exp(-self.time_decay_lambda * age_days)
            weight = float(row.get("quantity") or 1) * decay
            for idx, value in enumerate(vector):
                accum[idx] += value * weight
            total_weight += weight

        if total_weight <= 0:
            return fallback_vector

        return [value / total_weight for value in accum]

    def score(
        self,
        *,
        user_id: int,
        dishes,
        favorite_dish_ids: list[str],
        favorite_ingredient_ids: list[str],
        diet_mode: str,
        diet_level: str,
        issue_profile: dict[str, float],
        issue_confidence: float,
        persisted_user_vector: list[float] | None = None,
    ) -> list[dict]:
        if not dishes:
            return []

        dish_ids = [str(dish.uid) for dish in dishes]
        issue_keys = sorted(issue_profile.keys())

        popularity_map = self._get_popularity_map(dish_ids)
        history_raw_map = self._get_history_raw_map(user_id=user_id, dish_ids=dish_ids)
        ingredient_ratio_map = self._get_ingredient_ratio_map(dish_ids, favorite_ingredient_ids)
        favorite_recency_map = self._get_favorite_recency_map(user_id=user_id, dish_ids=dish_ids)
        dish_issue_map = self._get_dish_issue_map(dish_ids, issue_keys)
        dish_vector_map = self._get_dish_nutrition_vector_map(dish_ids)
        nutrition_confidence_map = self._get_nutrition_confidence_map(dish_ids)

        max_popularity = max(popularity_map.values()) if popularity_map else 1
        max_history_raw = max(history_raw_map.values()) if history_raw_map else 1.0

        fallback_vector = [0.0] * 5
        if dish_vector_map:
            count = float(len(dish_vector_map))
            fallback_vector = [
                sum(vector[idx] for vector in dish_vector_map.values()) / count
                for idx in range(5)
            ]
        history_user_vector = self._build_user_nutrition_vector(
            user_id=user_id,
            dish_vector_map=dish_vector_map,
            fallback_vector=fallback_vector,
        )
        user_vector = self._apply_user_vector_ema(
            persisted_user_vector=persisted_user_vector,
            history_vector=history_user_vector,
        )

        scored: list[dict] = []
        diet_weight = self._diet_level_weight(diet_level)
        strong_level = (diet_level or "NONE").upper() == "STRONG"

        for dish in dishes:
            dish_id = str(dish.uid)
            rating_norm = self._clamp(float(dish.avg_rating or 0.0) / 5.0)

            popularity = popularity_map.get(dish_id, 0)
            popularity_norm = self._clamp(
                math.log1p(popularity) / math.log1p(max_popularity) if max_popularity > 0 else 0.0
            )

            age_days = max((timezone.now() - dish.created_at).total_seconds(), 0.0) / 86400
            recency_norm = self._clamp(math.exp(-self.recency_decay_lambda * age_days))

            base_score = self._clamp(0.5 * rating_norm + 0.3 * popularity_norm + 0.2 * recency_norm)

            binary_favorite = 1.0 if dish_id in favorite_dish_ids else 0.0
            ingredient_ratio = ingredient_ratio_map.get(dish_id, 0.0)
            favorite_recency = favorite_recency_map.get(dish_id, 0.0)
            favorite_score = self._clamp(
                0.6 * binary_favorite + 0.2 * ingredient_ratio + 0.2 * favorite_recency
            )

            history_raw = history_raw_map.get(dish_id, 0.0)
            if self.prioritize_unordered_dishes and max_history_raw > 0:
                # Invert history score: dishes with more orders get lower scores
                # This promotes discovering new dishes over re-ordering familiar ones
                order_frequency_normalized = self._clamp(history_raw / max_history_raw)
                history_score = self._clamp(1.0 - order_frequency_normalized)
            else:
                # Default behavior: boost dishes user has ordered frequently
                history_score = self._clamp(history_raw / max_history_raw if max_history_raw > 0 else 0.0)

            dish_issue_profile = dish_issue_map.get(dish_id, {key: 0.0 for key in issue_keys})
            issue_penalty = self._clamp(
                sum(
                    float(issue_profile.get(issue_key, 0.0)) * float(dish_issue_profile.get(issue_key, 0.0))
                    for issue_key in issue_keys
                )
            )

            dish_vector = dish_vector_map.get(dish_id, [0.0] * 5)
            cosine = self._cosine_similarity(user_vector, dish_vector)
            preference_nutrition_mismatch_penalty_raw = self._clamp(1.0 - cosine)
            nutrition_confidence = nutrition_confidence_map.get(dish_id, 0.0)
            preference_nutrition_mismatch_penalty = self._clamp(preference_nutrition_mismatch_penalty_raw * nutrition_confidence)

            diet_alignment = self._diet_alignment(diet_mode=diet_mode, dish_vector=dish_vector)
            # Convert [0,1] alignment to signed preference impact in [-1,1].
            diet_component = diet_weight * ((2.0 * diet_alignment) - 1.0)

            strong_gate_penalty = 0.0
            if strong_level and diet_alignment < 0.35:
                strong_gate_penalty = (0.35 - diet_alignment) * 0.6

            if min(issue_penalty, preference_nutrition_mismatch_penalty) >= self.penalty_correlation_threshold:
                effective_penalty = max(issue_penalty, preference_nutrition_mismatch_penalty) + self.penalty_gamma * min(
                    issue_penalty,
                    preference_nutrition_mismatch_penalty,
                )
            else:
                effective_penalty = issue_penalty + preference_nutrition_mismatch_penalty
            effective_penalty = self._clamp(effective_penalty)

            penalty_confidence = self._clamp(0.5 * issue_confidence + 0.5 * nutrition_confidence)
            final_penalty = self._clamp(effective_penalty * penalty_confidence)

            final_score = (
                self.weights["w1"] * base_score
                + self.weights["w2"] * favorite_score
                + self.weights["w3"] * history_score
                + diet_component
                - self.unified_penalty_weight * final_penalty
                - strong_gate_penalty
            )

            scored.append(
                {
                    "dish": dish,
                    "dish_id": dish_id,
                    "score": round(float(final_score), 6),
                    "base_score": round(float(base_score), 6),
                    "favorite_score": round(float(favorite_score), 6),
                    "history_score": round(float(history_score), 6),
                    "issue_penalty": round(float(issue_penalty), 6),
                    "preference_nutrition_mismatch_penalty": round(float(preference_nutrition_mismatch_penalty), 6),
                    "nutrition_confidence": round(float(nutrition_confidence), 6),
                    "penalty_confidence": round(float(penalty_confidence), 6),
                    "diet_alignment": round(float(diet_alignment), 6),
                    "ingredient_match_ratio": round(float(ingredient_ratio), 6),
                    "dish_vector": dish_vector,
                    "user_vector": user_vector,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored
