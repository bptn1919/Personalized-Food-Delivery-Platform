from ninja import ModelSchema, Schema
from typing import Literal, List, Optional

from recommendation.models import UserFoodPreferenceFeature


class UserIssueSensitivityProfileResponse(Schema):
	user_id: int
	issue_profile: dict[str, float]
	confidence: float
	data_points: int

class UserFoodPreferenceFeatureResponse(ModelSchema):
	class Meta:
		model = UserFoodPreferenceFeature
		exclude = [
			"updated_at",
			"created_at"
		]


class RecommendationDishItemResponse(Schema):
	dish_uid: str
	dish_name: str
	public_url: Optional[str]
	price: float
	avg_rating: float
	is_favorite: bool
	allergy_warning: bool
	score: float
	base_score: float
	favorite_score: float
	history_score: float
	issue_penalty: float
	# Backward-compatible field name (deprecated)
	nutrition_penalty: float | None = None
	# Preferred field name: cosine-based preference mismatch (not quantity gap)
	preference_nutrition_mismatch_penalty: float | None = None
	reasons: list[str]


class RecommendationFeedMetaResponse(Schema):
	limit: int
	offset: int
	candidate_count: int
	scored_count: int
	reranked_count: int
	issue_confidence: float
	issue_data_points: int
	latency_ms: int
	weights: dict[str, float]
	mmr_lambda: float
	penalty_gamma: float
	ann_candidates_enabled: bool | None = None
	user_vector_source: str | None = None


class RecommendationFeedResponse(Schema):
	items: list[RecommendationDishItemResponse]
	meta: RecommendationFeedMetaResponse


class DailyNutritionTargetResponse(Schema):
	protein_g: float
	lipid_g: float
	carb_g: float
	sodium_mg: float
	fiber_g: float


class DailyNutritionSummaryResponse(Schema):
	date: str
	bmr_kcal: float
	tdee_kcal: float
	target: DailyNutritionTargetResponse
	consumed: DailyNutritionTargetResponse
	remaining: DailyNutritionTargetResponse


class DailyNutritionProfileResponse(Schema):
	"""User's daily nutrition profile with personal info + nutrition data"""
	# Profile fields
	age: int
	gender: str  # FEMALE|MALE|OTHER
	height_cm: float
	weight_kg: float
	activity_level: str  # SEDENTARY|LIGHT|MODERATE|ACTIVE|VERY_ACTIVE
	goal: str  # MAINTAIN|LOSE|GAIN
	# Computed nutrition fields
	date: str
	bmr_kcal: float
	tdee_kcal: float
	target: DailyNutritionTargetResponse
	consumed: DailyNutritionTargetResponse
	remaining: DailyNutritionTargetResponse


class DailyNutritionMealParseResponse(Schema):
	summary: DailyNutritionSummaryResponse
	parsed_count: int
	unresolved_meals: list[str]


class DailyNutritionRecommendationItemResponse(Schema):
	dish_uid: str
	dish_name: str
	public_url: Optional[str]
	price: float
	avg_rating: float
	base_recommendation_score: float
	macro_match_score: float
	final_score: float
	suggested_servings: float
	nutrition_impact: DailyNutritionTargetResponse
	reasons: list[str]


class DailyNutritionRecommendationResponse(Schema):
	summary: DailyNutritionSummaryResponse
	items: list[DailyNutritionRecommendationItemResponse]


class DailyMealLogItemResponse(Schema):
	uid: str
	source: Literal["APP", "PARSED", "USDA", "MANUAL"]  # Meal source
	meal_time: Literal["BREAKFAST", "LUNCH", "DINNER", "SNACK", "UNKNOWN"]  # When meal was eaten
	dish_uid: str | None
	dish_name: str | None
	meal_name: str
	quantity_multiplier: float
	nutrition_protein_g: float
	nutrition_lipid_g: float
	nutrition_carb_g: float
	nutrition_sodium_mg: float
	nutrition_fiber_g: float
	confidence_parse: float
	confidence_source: float
	raw_payload: dict
	# For in-app meals from Dish (source=APP)
	image_url: Optional[str] = None
	price: Optional[float] = None
	created_at: str
	updated_at: str


class DailyMealLogListResponse(Schema):
	summary: DailyNutritionSummaryResponse
	items: list[DailyMealLogItemResponse]

class BetterDishItem(Schema):
	dish_uid: str
	dish_name: str
	public_url: Optional[str]
	price: float
	avg_rating: float
	total_reviews: int
	issue_rate: float
	score: float
	explain: str


class BetterDishForIssueResponse(Schema):
    issue: Optional[str]
    source_dish_uid: str
    items: List[BetterDishItem]