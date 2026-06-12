import math
import logging
from datetime import timedelta

from django.db import connection
from django.db.models import Avg, Count, Max
from django.utils import timezone

from dish.models import DishIngredient
from order.models import OrderItem
from utils.enums import OrderStatusEnum


class VectorIndexService:
    VECTOR_DIMENSION = 5
    VECTOR_REFRESH_WINDOW_MINUTES = 60
    VECTOR_REFRESH_COOLDOWN_MINUTES = 5
    VECTOR_REFRESH_BATCH_LIMIT = 500
    USER_VECTOR_REFRESH_COOLDOWN_MINUTES = 1

    _logger = logging.getLogger(__name__)

    @staticmethod
    def _to_vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    @staticmethod
    def _parse_vector_literal(value: str | None) -> list[float]:
        if not value:
            return []
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        if not raw:
            return []
        try:
            vector = [float(part.strip()) for part in raw.split(",") if part.strip()]
            return vector
        except Exception:
            return []

    def ensure_dish_vectors(
        self,
        *,
        refresh_window_minutes: int | None = None,
        max_batch_size: int | None = None,
    ) -> int:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM recommendation_dish_vector_index")
                row = cursor.fetchone()
                current_count = int((row or [0])[0] or 0)
        except Exception:
            return 0

        if current_count > 0:
            refresh_window = refresh_window_minutes or self.VECTOR_REFRESH_WINDOW_MINUTES
            batch_limit = max_batch_size or self.VECTOR_REFRESH_BATCH_LIMIT

            refreshed = self.refresh_dish_vectors_incremental(
                since_minutes=refresh_window,
                limit=batch_limit,
            )
            return refreshed or current_count

        return self.refresh_dish_vectors()

    def refresh_dish_vectors(self, *, dish_ids: list[str] | None = None) -> int:
        """
        Build dish vectors using weighted aggregation with confidence scores.
        
        Formula: dish_vector = Σ(w_i × c_i × v_i) / Σ(w_i × c_i)
        where:
          - w_i = weight of ingredient i (in grams)
          - c_i = confidence score of ingredient i (0-1)
          - v_i = nutrient vector of ingredient i (protein, lipid, carb, sodium, fiber)
        
        Dish confidence = weighted average: Σ(w_i × c_i) / Σ(w_i)
          - Heavier ingredients have more impact on dish confidence
          - Ingredients with low confidence reduce overall dish confidence proportionally to their weight
        """
        # Fetch all active dish ingredients with their nutritional and confidence data
        ingredients_qs = DishIngredient.objects.filter(deleted=False, dish__deleted=False)
        if dish_ids:
            ingredients_qs = ingredients_qs.filter(dish_id__in=dish_ids)

        ingredients = (
            ingredients_qs
            .values(
                "dish_id",
                "weight",
                "protein",
                "lipid",
                "carbohydrate",
                "natri",
                "fiber",
                "confidence",
            )
            .order_by("dish_id")
        )

        # Group ingredients by dish_id and compute weighted vectors
        dish_vectors = {}  # dish_id -> (vector, dish_confidence)

        for ingredient in ingredients:
            dish_id = ingredient["dish_id"]
            weight = float(ingredient.get("weight") or 1.0)
            confidence = float(ingredient.get("confidence") or 1.0)
            
            # Skip invalid entries
            if weight <= 0 or confidence < 0 or confidence > 1.0:
                continue

            # Extract nutrient values
            protein = float(ingredient.get("protein") or 0.0)
            lipid = float(ingredient.get("lipid") or 0.0)
            carb = float(ingredient.get("carbohydrate") or 0.0)
            sodium = float(ingredient.get("natri") or 0.0) / 1000.0  # mg → g
            fiber = float(ingredient.get("fiber") or 0.0)

            # Initialize dish entry if not exists
            if dish_id not in dish_vectors:
                dish_vectors[dish_id] = {
                    "weighted_protein": 0.0,
                    "weighted_lipid": 0.0,
                    "weighted_carb": 0.0,
                    "weighted_sodium": 0.0,
                    "weighted_fiber": 0.0,
                    "weight_confidence_sum": 0.0,
                    "weight_sum": 0.0,
                }

            # Compute weighted values: w_i × c_i × v_i
            weight_conf = weight * confidence
            dish_vectors[dish_id]["weighted_protein"] += weight_conf * protein
            dish_vectors[dish_id]["weighted_lipid"] += weight_conf * lipid
            dish_vectors[dish_id]["weighted_carb"] += weight_conf * carb
            dish_vectors[dish_id]["weighted_sodium"] += weight_conf * sodium
            dish_vectors[dish_id]["weighted_fiber"] += weight_conf * fiber
            
            # Track sums for normalization: Σ(w_i × c_i) and Σ(w_i)
            dish_vectors[dish_id]["weight_confidence_sum"] += weight_conf
            dish_vectors[dish_id]["weight_sum"] += weight

        # Build payload for bulk insert
        payload = []
        for dish_id, aggregates in dish_vectors.items():
            weight_conf_sum = aggregates["weight_confidence_sum"]
            
            # Skip if no valid weighted ingredients
            if weight_conf_sum <= 0:
                continue

            # Normalize by Σ(w_i × c_i) to get final vector
            protein = aggregates["weighted_protein"] / weight_conf_sum
            lipid = aggregates["weighted_lipid"] / weight_conf_sum
            carb = aggregates["weighted_carb"] / weight_conf_sum
            sodium = aggregates["weighted_sodium"] / weight_conf_sum
            fiber = aggregates["weighted_fiber"] / weight_conf_sum

            vector = [protein, lipid, carb, sodium, fiber]

            # Dish confidence = weighted average of ingredient confidences
            # Formula: Σ(w_i × c_i) / Σ(w_i)
            weight_sum = aggregates["weight_sum"]
            dish_confidence = (
                aggregates["weight_confidence_sum"] / weight_sum 
                if weight_sum > 0 else 1.0
            )
            # Already bounded [0, 1] by construction (c_i and w_i are non-negative)

            payload.append(
                (str(dish_id), self._to_vector_literal(vector), dish_confidence)
            )

        if not payload:
            return 0

        try:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO recommendation_dish_vector_index (dish_uid, embedding, confidence, updated_at)
                    VALUES (CAST(%s AS uuid), CAST(%s AS vector), %s, NOW())
                    ON CONFLICT (dish_uid)
                    DO UPDATE
                       SET embedding = EXCLUDED.embedding,
                           confidence = EXCLUDED.confidence,
                           updated_at = NOW()
                    """,
                    payload,
                )
            return len(payload)
        except Exception:
            return 0

    def refresh_dish_vectors_incremental(self, *, since_minutes: int, limit: int) -> int:
        since_time = timezone.now() - timedelta(minutes=max(1, since_minutes))

        dish_ids = list(
            DishIngredient.objects.filter(
                deleted=False,
                dish__deleted=False,
                updated_at__gte=since_time,
            )
            .values("dish_id")
            .annotate(last_updated=Max("updated_at"))
            .order_by("-last_updated")
            .values_list("dish_id", flat=True)[:max(1, limit)]
        )

        if not dish_ids:
            return 0

        self._logger.debug(
            "refresh_dish_vectors_incremental: dish_ids",
            extra={"count": len(dish_ids), "since_minutes": since_minutes},
        )

        return self.refresh_dish_vectors(dish_ids=[str(d) for d in dish_ids])

    def refresh_dish_vectors_for_dishes(
        self,
        *,
        dish_ids: list[str],
        freshness_minutes: int | None = None,
    ) -> int:
        if not dish_ids:
            return 0

        freshness = freshness_minutes or self.VECTOR_REFRESH_COOLDOWN_MINUTES
        stale_ids = self._filter_stale_dish_ids(dish_ids=dish_ids, freshness_minutes=freshness)
        if not stale_ids:
            return 0

        return self.refresh_dish_vectors(dish_ids=stale_ids)

    def _filter_stale_dish_ids(self, *, dish_ids: list[str], freshness_minutes: int) -> list[str]:
        if not dish_ids:
            return []

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT dish_uid::text
                    FROM recommendation_dish_vector_index
                    WHERE dish_uid = ANY(CAST(%s AS uuid[]))
                      AND updated_at >= NOW() - (%s || ' minutes')::interval
                    """,
                    [dish_ids, max(1, freshness_minutes)],
                )
                rows = cursor.fetchall()
        except Exception:
            rows = []

        recent_ids = {str(row[0]) for row in rows}
        return [str(dish_id) for dish_id in dish_ids if str(dish_id) not in recent_ids]

    def get_or_build_user_vector(
        self,
        *,
        user_id: int,
        decay_lambda: float,
    ) -> tuple[list[float], str]:
        persisted = self._get_persisted_user_vector(user_id)
        if persisted:
            return persisted, "persisted"

        history_vector = self._build_user_vector_from_history(user_id=user_id, decay_lambda=decay_lambda)
        if history_vector:
            self._upsert_user_vector(user_id=user_id, vector=history_vector, confidence=0.8)
            return history_vector, "history"

        global_mean = self._global_mean_dish_vector()
        if global_mean:
            self._upsert_user_vector(user_id=user_id, vector=global_mean, confidence=0.4)
            return global_mean, "global_mean"

        return [], "empty"

    def refresh_user_vector(
        self,
        *,
        user_id: int,
        decay_lambda: float | None = None,
        force: bool = False,
    ) -> str:
        if not force and self._is_user_vector_fresh(
            user_id=user_id,
            freshness_minutes=self.USER_VECTOR_REFRESH_COOLDOWN_MINUTES,
        ):
            return "cooldown"

        history_vector = self._build_user_vector_from_history(
            user_id=user_id,
            decay_lambda=decay_lambda or 0.03,
        )
        if history_vector:
            self._upsert_user_vector(user_id=user_id, vector=history_vector, confidence=0.8)
            return "history"

        global_mean = self._global_mean_dish_vector()
        if global_mean:
            self._upsert_user_vector(user_id=user_id, vector=global_mean, confidence=0.4)
            return "global_mean"

        return "empty"

    def _get_persisted_user_vector(self, user_id: int) -> list[float]:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT embedding::text
                    FROM recommendation_user_vector_index
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                row = cursor.fetchone()
                if not row:
                    return []
                return self._parse_vector_literal(str(row[0]))
        except Exception:
            return []

    def _is_user_vector_fresh(self, *, user_id: int, freshness_minutes: int) -> bool:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT updated_at
                    FROM recommendation_user_vector_index
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                row = cursor.fetchone()
                if not row or not row[0]:
                    return False
                updated_at = row[0]
        except Exception:
            return False

        freshness = max(1, freshness_minutes)
        return updated_at >= timezone.now() - timedelta(minutes=freshness)

    def _build_user_vector_from_history(self, *, user_id: int, decay_lambda: float) -> list[float]:
        rows = (
            OrderItem.objects.filter(
                order__owner_id=user_id,
                order__status=OrderStatusEnum.COMPLETED,
                order__created_at__gte=timezone.now() - timedelta(days=180),
            )
            .values("dish_id", "quantity", "order__created_at")
            .order_by("-order__created_at")
        )

        if not rows:
            return []

        dish_ids = list({str(row["dish_id"]) for row in rows})
        vectors = self._get_dish_vectors(dish_ids)
        if not vectors:
            return []

        accum = [0.0] * self.VECTOR_DIMENSION
        total_weight = 0.0
        now = timezone.now()

        for row in rows:
            vector = vectors.get(str(row["dish_id"]))
            if not vector:
                continue
            created_at = row.get("order__created_at")
            age_days = 0.0
            if created_at:
                age_days = max((now - created_at).total_seconds(), 0.0) / 86400

            decay = math.exp(-decay_lambda * age_days)
            weight = float(row.get("quantity") or 1) * decay
            total_weight += weight

            for idx in range(self.VECTOR_DIMENSION):
                accum[idx] += vector[idx] * weight

        if total_weight <= 0:
            return []

        return [value / total_weight for value in accum]

    def _global_mean_dish_vector(self) -> list[float]:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT AVG((embedding::text)::vector)::text
                    FROM recommendation_dish_vector_index
                    """
                )
                row = cursor.fetchone()
                if not row:
                    return []
                return self._parse_vector_literal(str(row[0]))
        except Exception:
            return []

    def _upsert_user_vector(self, *, user_id: int, vector: list[float], confidence: float) -> None:
        if not vector:
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recommendation_user_vector_index (user_id, embedding, confidence, updated_at)
                    VALUES (%s, CAST(%s AS vector), %s, NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE
                       SET embedding = EXCLUDED.embedding,
                           confidence = EXCLUDED.confidence,
                           updated_at = NOW()
                    """,
                    [user_id, self._to_vector_literal(vector), confidence],
                )
        except Exception:
            return

    def _get_dish_vectors(self, dish_ids: list[str]) -> dict[str, list[float]]:
        if not dish_ids:
            return {}
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT dish_uid::text, embedding::text
                    FROM recommendation_dish_vector_index
                    WHERE dish_uid = ANY(CAST(%s AS uuid[]))
                    """,
                    [dish_ids],
                )
                rows = cursor.fetchall()
            return {str(row[0]): self._parse_vector_literal(str(row[1])) for row in rows}
        except Exception:
            return {}
