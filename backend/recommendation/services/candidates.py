from datetime import timedelta
from uuid import UUID

from django.db import connection
from django.db.models import Count, Q
from django.utils import timezone

from dish.models import Dish
from utils.enums import OrderStatusEnum


class CandidateGenerator:
    def __init__(self, *, candidate_pool_size: int) -> None:
        self.candidate_pool_size = candidate_pool_size

    @staticmethod
    def _as_uuid_list(values: list) -> list[str]:
        normalized: list[str] = []
        for value in values:
            if value is None:
                continue
            if isinstance(value, UUID):
                normalized.append(str(value))
                continue
            text_value = str(value).strip()
            if text_value:
                normalized.append(text_value)
        return normalized

    def generate(
        self,
        *,
        favorite_dish_ids: list,
        favorite_ingredient_ids: list,
        allergic_ingredient_ids: list,
        allergy_mode: str,
        user_vector: list[float] | None = None,
        use_ann: bool = False,
        max_per_category: int | None = None,
    ):
        ordered_candidate_ids: list[str] = []

        favorite_dish_ids_norm = self._as_uuid_list(favorite_dish_ids)
        favorite_ingredient_ids_norm = self._as_uuid_list(favorite_ingredient_ids)
        allergic_ingredient_ids_norm = self._as_uuid_list(allergic_ingredient_ids)

        quotas = self._resolve_source_quotas(
            use_ann=use_ann,
            has_user_vector=bool(user_vector),
        )

        source_candidates: dict[str, list[str]] = {
            "ann": [],
            "vector_fallback": [],
            "favorite": [],
            "ingredient_similar": [],
            "popular": [],
            "trending": [],
        }

        # Source 0: ANN candidate retrieval from pgvector index.
        if use_ann and user_vector and quotas["ann"] > 0:
            source_candidates["ann"] = self._vector_source_ids(
                user_vector=user_vector,
                allergic_ingredient_ids=allergic_ingredient_ids_norm,
                allergy_mode=allergy_mode,
                limit=quotas["ann"],
            )

        # When ANN is disabled but vector exists, still use vector retrieval to avoid wasting user signal.
        if (not use_ann) and user_vector and quotas["vector_fallback"] > 0:
            source_candidates["vector_fallback"] = self._vector_source_ids(
                user_vector=user_vector,
                allergic_ingredient_ids=allergic_ingredient_ids_norm,
                allergy_mode=allergy_mode,
                limit=quotas["vector_fallback"],
            )

        # Source 1: popular dishes from completed orders.
        if quotas["popular"] > 0:
            popular_ids = (
                Dish.objects.filter(deleted=False)
                .annotate(
                    completed_orders=Count(
                        "orderitem_fk_dish",
                        filter=Q(orderitem_fk_dish__order__status=OrderStatusEnum.COMPLETED),
                        distinct=True,
                    )
                )
                .order_by("-completed_orders", "-avg_rating", "-created_at")
                .values_list("uid", flat=True)[: quotas["popular"]]
            )
            source_candidates["popular"] = [str(uid) for uid in popular_ids]

        # Source 2: favorite dishes.
        source_candidates["favorite"] = favorite_dish_ids_norm[: quotas["favorite"]]

        # Source 3: ingredient-similar dishes.
        if favorite_ingredient_ids_norm and quotas["ingredient_similar"] > 0:
            ingredient_similar_ids = (
                Dish.objects.filter(
                    deleted=False,
                    dish_ingredient_fk_dish__deleted=False,
                    dish_ingredient_fk_dish__ingredient__uid__in=favorite_ingredient_ids_norm,
                )
                .annotate(
                    fav_ingredient_hits=Count(
                        "dish_ingredient_fk_dish",
                        filter=Q(
                            dish_ingredient_fk_dish__deleted=False,
                            dish_ingredient_fk_dish__ingredient__uid__in=favorite_ingredient_ids_norm,
                        ),
                    )
                )
                .order_by("-fav_ingredient_hits", "-avg_rating", "-created_at")
                .values_list("uid", flat=True)[: quotas["ingredient_similar"]]
            )
            source_candidates["ingredient_similar"] = [str(uid) for uid in ingredient_similar_ids]

        # Source 4: trending dishes from recent completed orders.
        if quotas["trending"] > 0:
            recent_cutoff = timezone.now() - timedelta(days=14)
            trending_ids = (
                Dish.objects.filter(deleted=False)
                .annotate(
                    recent_completed_orders=Count(
                        "orderitem_fk_dish",
                        filter=Q(
                            orderitem_fk_dish__order__status=OrderStatusEnum.COMPLETED,
                            orderitem_fk_dish__order__created_at__gte=recent_cutoff,
                        ),
                        distinct=True,
                    )
                )
                .order_by("-recent_completed_orders", "-avg_rating", "-created_at")
                .values_list("uid", flat=True)[: quotas["trending"]]
            )
            source_candidates["trending"] = [str(uid) for uid in trending_ids]

        priority_order = [
            "ann",
            "vector_fallback",
            "favorite",
            "ingredient_similar",
            "popular",
            "trending",
        ]
        seen: set[str] = set()
        for source_name in priority_order:
            for dish_id in source_candidates[source_name]:
                if dish_id in seen:
                    continue
                seen.add(dish_id)
                ordered_candidate_ids.append(dish_id)
                if len(ordered_candidate_ids) >= self.candidate_pool_size:
                    break
            if len(ordered_candidate_ids) >= self.candidate_pool_size:
                break

        if not ordered_candidate_ids:
            return []

        query = Dish.objects.filter(deleted=False, uid__in=ordered_candidate_ids).distinct()

        # Hard filtering for allergy mode HIDE.
        if allergy_mode and allergy_mode.upper() == "HIDE" and allergic_ingredient_ids_norm:
            query = query.exclude(
                dish_ingredient_fk_dish__ingredient__uid__in=allergic_ingredient_ids_norm
            )

        dishes = list(query.select_related("owner", "attachment"))

        dish_map = {str(dish.uid): dish for dish in dishes}
        ordered_dishes = [dish_map[dish_id] for dish_id in ordered_candidate_ids if dish_id in dish_map]

        # Optional diversity cap to avoid over-concentration of one category in stage 1 candidates.
        if max_per_category and max_per_category > 0:
            category_counts: dict[str, int] = {}
            diversity_dishes = []
            for dish in ordered_dishes:
                category_key = str(dish.category)
                category_counts[category_key] = category_counts.get(category_key, 0)
                if category_counts[category_key] >= max_per_category:
                    continue
                category_counts[category_key] += 1
                diversity_dishes.append(dish)
                if len(diversity_dishes) >= self.candidate_pool_size:
                    break
            ordered_dishes = diversity_dishes

        if len(ordered_dishes) > self.candidate_pool_size:
            ordered_dishes = ordered_dishes[: self.candidate_pool_size]

        return ordered_dishes

    def _resolve_source_quotas(self, *, use_ann: bool, has_user_vector: bool) -> dict[str, int]:
        total = self.candidate_pool_size
        source_ratios = {
            "ann": 0.35,
            "vector_fallback": 0.25,
            "favorite": 0.10,
            "ingredient_similar": 0.20,
            "popular": 0.20,
            "trending": 0.15,
        }

        if not (use_ann and has_user_vector):
            source_ratios["ann"] = 0.0
        if not ((not use_ann) and has_user_vector):
            source_ratios["vector_fallback"] = 0.0

        quotas = {name: int(total * ratio) for name, ratio in source_ratios.items()}

        # Coverage guarantee: keep at least 1 candidate for active sources.
        for source_name, ratio in source_ratios.items():
            if ratio > 0 and quotas[source_name] == 0:
                quotas[source_name] = 1

        allocated = sum(quotas.values())
        if allocated < total:
            quotas["popular"] += total - allocated
        elif allocated > total:
            overflow = allocated - total
            reduce_order = ["trending", "popular", "ingredient_similar", "vector_fallback", "ann", "favorite"]
            for source_name in reduce_order:
                if overflow <= 0:
                    break
                can_reduce = max(quotas[source_name] - (1 if source_ratios[source_name] > 0 else 0), 0)
                step = min(can_reduce, overflow)
                quotas[source_name] -= step
                overflow -= step

        return quotas

    @staticmethod
    def _to_vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    def _vector_source_ids(
        self,
        *,
        user_vector: list[float],
        allergic_ingredient_ids: list[str],
        allergy_mode: str,
        limit: int,
    ) -> list[str]:

        if not user_vector or all(v == 0 for v in user_vector):
            return []

        sql_base = """
            SELECT idx.dish_uid::text
            FROM recommendation_dish_vector_index idx
            INNER JOIN dish_dish d
                ON d.uid = idx.dish_uid
            AND d.deleted = FALSE
        """

        params: list[object] = []
        where_clause = ""

        # ======================
        # allergy filter (FIXED)
        # ======================
        if allergy_mode and allergy_mode.upper() == "HIDE" and allergic_ingredient_ids:
            where_clause = """
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dish_dishingredient di
                    WHERE di.dish_uid = d.uid
                    AND di.deleted = FALSE
                    AND di.ingredient_uid = ANY(%s::uuid[])
                )
            """
            params.append(allergic_ingredient_ids)

        sql_order = """
            ORDER BY idx.embedding <=> CAST(%s AS vector)
            LIMIT %s
        """

        params.extend([
            self._to_vector_literal(user_vector),
            limit
        ])

        sql = sql_base + where_clause + sql_order

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            return [str(row[0]) for row in rows]

        except Exception:
            return []