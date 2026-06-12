from django.test import SimpleTestCase

from recommendation.services.explain import build_reasons
from recommendation.services.rerank import MMRReranker
from recommendation.services.scoring import ScoringEngine


class RecommendationRerankTests(SimpleTestCase):
	def test_mmr_rerank_respects_take(self):
		reranker = MMRReranker(lambda_value=0.5)
		items = [
			{"score": 0.9, "dish_vector": [1.0, 0.0, 0.0, 0.0, 0.0]},
			{"score": 0.8, "dish_vector": [0.0, 1.0, 0.0, 0.0, 0.0]},
			{"score": 0.7, "dish_vector": [0.0, 0.0, 1.0, 0.0, 0.0]},
		]

		result = reranker.rerank(items, take=2)
		self.assertEqual(len(result), 2)


class RecommendationExplainTests(SimpleTestCase):
	def test_build_reasons_has_fallback(self):
		reasons = build_reasons(
			{
				"favorite_score": 0.0,
				"history_score": 0.0,
				"ingredient_match_ratio": 0.0,
				"issue_penalty": 0.8,
				"nutrition_penalty": 0.9,
				"base_score": 0.1,
			}
		)

		self.assertTrue(reasons)
		self.assertEqual(reasons[0], "Đề xuất theo độ phổ biến và hành vi tương đồng")

	def test_build_reasons_supports_new_penalty_name(self):
		reasons = build_reasons(
			{
				"favorite_score": 0.0,
				"history_score": 0.0,
				"ingredient_match_ratio": 0.0,
				"issue_penalty": 0.0,
				"preference_nutrition_mismatch_penalty": 0.1,
				"base_score": 0.1,
			}
		)

		self.assertIn("Cân bằng dinh dưỡng tương đối tốt với xu hướng ăn uống của bạn", reasons)


class RecommendationDietScoringTests(SimpleTestCase):
	def setUp(self):
		self.engine = ScoringEngine(
			time_decay_lambda=0.03,
			recency_decay_lambda=0.02,
			weights={"w1": 0.4, "w2": 0.2, "w3": 0.2, "w4": 0.1, "w5": 0.1},
			penalty_gamma=0.25,
			penalty_correlation_threshold=0.35,
		)

	def test_low_carb_alignment_prefers_low_carb_vector(self):
		low_carb_vector = [40.0, 20.0, 10.0, 0.0, 3.0]
		high_carb_vector = [10.0, 10.0, 60.0, 0.0, 2.0]

		low_carb_alignment = self.engine._diet_alignment("LOW_CARB", low_carb_vector)
		high_carb_alignment = self.engine._diet_alignment("LOW_CARB", high_carb_vector)

		self.assertGreater(low_carb_alignment, high_carb_alignment)

	def test_strong_level_has_higher_weight_than_soft(self):
		self.assertGreater(self.engine._diet_level_weight("STRONG"), self.engine._diet_level_weight("SOFT"))
