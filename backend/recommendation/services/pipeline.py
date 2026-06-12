import time
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model

from exceptions.users import UserNotFound
from recommendation.models import UserFoodPreferenceFeature

from .candidates import CandidateGenerator
from .explain import build_reasons
from .rerank import MMRReranker
from .scoring import ScoringEngine
from .vector_index import VectorIndexService


class RecommendationPipelineService:
    ISSUE_KEYS = [
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

    def __init__(self) -> None:
        self.config = getattr(settings, "RECOMMENDATION_CONFIG", {})
        self.weights = self.config.get(
            "weights",
            {"w1": 0.4, "w2": 0.2, "w3": 0.2, "w4": 0.1, "w5": 0.1},
        )
        self.vector_index_service = VectorIndexService()

    @staticmethod
    def _normalize_json_ids(values) -> list[str]:
        if not values:
            return []
        result: list[str] = []
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                result.append(text)
        return result

    def _default_features(self, user_id: int) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "favorite_dish_ids": [],
            "favorite_ingredient_ids": [],
            "allergic_ingredient_ids": [],
            "allergy_mode": "WARN",
            "diet_mode": "NONE",
            "diet_level": "NONE",
        }

    def _get_user_feature(self, user_id: int) -> dict[str, Any]:
        feature = UserFoodPreferenceFeature.objects.filter(user_id=user_id).first()
        if not feature:
            return self._default_features(user_id)
        return {
            "user_id": user_id,
            "favorite_dish_ids": self._normalize_json_ids(feature.favorite_dish_ids),
            "favorite_ingredient_ids": self._normalize_json_ids(feature.favorite_ingredient_ids),
            "allergic_ingredient_ids": self._normalize_json_ids(feature.allergic_ingredient_ids),
            "allergy_mode": str(feature.allergy_mode or "WARN"),
            "diet_mode": str(feature.diet_mode or "NONE"),
            "diet_level": str(feature.diet_level or "NONE"),
        }

    def _get_user_issue_profile(self, user_id: int) -> tuple[dict[str, float], float, int]:
        from .recommendation import RecommendationService

        profile_resp = RecommendationService().get_user_issue_sensitivity_profile(user_id=user_id)
        issue_profile = profile_resp.get("issue_profile", {}) or {}
        confidence = float(profile_resp.get("confidence", 0.0) or 0.0)
        data_points = int(profile_resp.get("data_points", 0) or 0)
        normalized = {key: float(issue_profile.get(key, 0.0) or 0.0) for key in self.ISSUE_KEYS}
        return normalized, confidence, data_points

    def _get_allergy_warning_map(
        self,
        *,
        dish_ids: list[str],
        allergic_ingredient_ids: list[str],
    ) -> dict[str, bool]:
        if not dish_ids or not allergic_ingredient_ids:
            return {dish_id: False for dish_id in dish_ids}

        from dish.models import DishIngredient

        rows = (
            DishIngredient.objects.filter(
                dish_id__in=dish_ids,
                ingredient_id__in=allergic_ingredient_ids,
                deleted=False,
            )
            .values_list("dish_id", flat=True)
            .distinct()
        )
        flagged = {str(row) for row in rows}
        return {dish_id: dish_id in flagged for dish_id in dish_ids}

    def recommend_for_user(
        self,
        *,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        include_explain: bool = False,
    ) -> dict[str, Any]:
        user_model = get_user_model()
        if not user_model.objects.filter(id=user_id).exists():
            raise UserNotFound

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        start_time = time.perf_counter()

        feature = self._get_user_feature(user_id)
        issue_profile, issue_confidence, issue_points = self._get_user_issue_profile(user_id)

        self.vector_index_service.ensure_dish_vectors()
        user_vector, user_vector_source = self.vector_index_service.get_or_build_user_vector(
            user_id=user_id,
            decay_lambda=float(self.config.get("history_decay_lambda", 0.03)),
        )

        candidate_pool_size = int(self.config.get("candidate_pool_size", 300))
        candidate_generator = CandidateGenerator(candidate_pool_size=candidate_pool_size)
        candidates = candidate_generator.generate(
            favorite_dish_ids=feature["favorite_dish_ids"],
            favorite_ingredient_ids=feature["favorite_ingredient_ids"],
            allergic_ingredient_ids=feature["allergic_ingredient_ids"],
            allergy_mode=feature["allergy_mode"],
            user_vector=user_vector,
            use_ann=bool(self.config.get("use_pgvector_ann_candidates", False)),
            max_per_category=int(self.config.get("candidate_max_per_category", 0) or 0),
        )

        scoring_engine = ScoringEngine(
            time_decay_lambda=float(self.config.get("history_decay_lambda", 0.03)),
            recency_decay_lambda=float(self.config.get("recency_decay_lambda", 0.02)),
            weights=self.weights,
            penalty_gamma=float(self.config.get("penalty_gamma", 0.25)),
            penalty_correlation_threshold=float(self.config.get("penalty_correlation_threshold", 0.35)),
            balanced_target=self.config.get("diet_balanced_target", [0.3, 0.3, 0.4]),
            favorite_recency_decay_lambda=float(
                self.config.get("favorite_recency_decay_lambda", self.config.get("history_decay_lambda", 0.03))
            ),
            user_vector_ema_alpha=float(self.config.get("user_vector_ema_alpha", 0.35)),
            prioritize_unordered_dishes=bool(self.config.get("prioritize_unordered_dishes", False)),
        )
        scored = scoring_engine.score(
            user_id=user_id,
            dishes=candidates,
            favorite_dish_ids=feature["favorite_dish_ids"],
            favorite_ingredient_ids=feature["favorite_ingredient_ids"],
            diet_mode=feature["diet_mode"],
            diet_level=feature["diet_level"],
            issue_profile=issue_profile,
            issue_confidence=issue_confidence,
            persisted_user_vector=user_vector,
        )

        rerank_take = min(len(scored), max(limit + offset, limit))
        reranker = MMRReranker(lambda_value=float(self.config.get("mmr_lambda", 0.5)))
        reranked = reranker.rerank(scored_items=scored, take=rerank_take)

        paged = reranked[offset : offset + limit]

        dish_ids = [str(item["dish"].uid) for item in paged]
        favorite_set = set(feature["favorite_dish_ids"])
        allergy_mode = str(feature.get("allergy_mode", "WARN") or "WARN").upper()
        if allergy_mode == "WARN":
            allergy_warning_map = self._get_allergy_warning_map(
                dish_ids=dish_ids,
                allergic_ingredient_ids=feature["allergic_ingredient_ids"],
            )
        else:
            allergy_warning_map = {dish_id: False for dish_id in dish_ids}

        data = []
        for item in paged:
            dish = item["dish"]
            attachment = getattr(dish, "attachment", None)
            public_url = None
            if attachment and hasattr(attachment, "public_url"):
                public_url = str(attachment.public_url) if attachment.public_url else None
            
            data.append(
                {
                    "dish_uid": str(dish.uid),
                    "dish_name": dish.name,
                    "public_url": public_url,
                    "price": float(dish.price),
                    "avg_rating": float(dish.avg_rating or 0.0),
                    "is_favorite": str(dish.uid) in favorite_set,
                    "allergy_warning": allergy_warning_map.get(str(dish.uid), False),
                    "score": float(item["score"]),
                    "base_score": float(item["base_score"]),
                    "favorite_score": float(item["favorite_score"]),
                    "history_score": float(item["history_score"]),
                    "issue_penalty": float(item["issue_penalty"]),
                    "nutrition_penalty": float(item["preference_nutrition_mismatch_penalty"]),
                    "preference_nutrition_mismatch_penalty": float(item["preference_nutrition_mismatch_penalty"]),
                    "reasons": build_reasons(item) if include_explain else [],
                }
            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "items": data,
            "meta": {
                "limit": limit,
                "offset": offset,
                "candidate_count": len(candidates),
                "scored_count": len(scored),
                "reranked_count": len(reranked),
                "issue_confidence": round(issue_confidence, 3),
                "issue_data_points": issue_points,
                "latency_ms": elapsed_ms,
                "weights": self.weights,
                "mmr_lambda": float(self.config.get("mmr_lambda", 0.5)),
                "penalty_gamma": float(self.config.get("penalty_gamma", 0.25)),
                "ann_candidates_enabled": bool(self.config.get("use_pgvector_ann_candidates", False)),
                "user_vector_source": user_vector_source,
            },
        }
