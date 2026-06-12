import math

from django.conf import settings
from django.db import connection


class MMRReranker:
    def __init__(self, *, lambda_value: float, use_pgvector: bool | None = None) -> None:
        self.lambda_value = max(0.0, min(lambda_value, 1.0))
        config = getattr(settings, "RECOMMENDATION_CONFIG", {})
        if use_pgvector is None:
            self.use_pgvector = bool(config.get("use_pgvector_similarity", False))
        else:
            self.use_pgvector = bool(use_pgvector)
        self._pgvector_unavailable = False

    @staticmethod
    def _cosine_similarity_python(v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    @staticmethod
    def _to_vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    def _cosine_similarity_pgvector(self, v1: list[float], v2: list[float]) -> float | None:
        if not v1 or not v2:
            return 0.0
        if self._pgvector_unavailable:
            return None

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 - (CAST(%s AS vector) <=> CAST(%s AS vector))",
                    [self._to_vector_literal(v1), self._to_vector_literal(v2)],
                )
                row = cursor.fetchone()
                if not row:
                    return 0.0
                return float(row[0] or 0.0)
        except Exception:
            self._pgvector_unavailable = True
            return None

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        if self.use_pgvector:
            pgvector_similarity = self._cosine_similarity_pgvector(v1, v2)
            if pgvector_similarity is not None:
                return pgvector_similarity
        return self._cosine_similarity_python(v1, v2)

    def rerank(self, scored_items: list[dict], *, take: int) -> list[dict]:
        if take <= 0 or not scored_items:
            return []

        candidates = list(scored_items)
        selected: list[dict] = []

        while candidates and len(selected) < take:
            best_index = 0
            best_mmr_score = -1e9

            for idx, item in enumerate(candidates):
                relevance = float(item.get("score", 0.0))
                item_vec = item.get("dish_vector") or []

                max_similarity = 0.0
                if selected:
                    max_similarity = max(
                        self._cosine_similarity(item_vec, selected_item.get("dish_vector") or [])
                        for selected_item in selected
                    )

                mmr_score = self.lambda_value * relevance - (1.0 - self.lambda_value) * max_similarity
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_index = idx

            selected.append(candidates.pop(best_index))

        return selected
