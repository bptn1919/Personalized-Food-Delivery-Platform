from admin.permissions import require_admin
from utils.types import AuthenticatedRequest
from exceptions.users import UserNotFound
from exceptions.dishes import DishNotFoundException
from exceptions.recommendation import DailyNutritionProfileNotFoundException
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, patch, post

from .schemas.requests import (
    DailyMealLogUpdateRequest,
    DailyNutritionInitRequest,
    DailyNutritionProfileUpdateRequest,
    DailyNutritionParseMealRequest,
)
from .schemas.responses import (
    DailyMealLogListResponse,
    DailyNutritionMealParseResponse,
    DailyNutritionRecommendationResponse,
    DailyNutritionSummaryResponse,
    DailyNutritionProfileResponse,
    RecommendationFeedResponse,
    UserFoodPreferenceFeatureResponse,
    UserIssueSensitivityProfileResponse,
    BetterDishForIssueResponse,
)
from .services.recommendation import RecommendationService

@api(prefix_or_class="recommendation", tags=["Recommendation"], auth=AuthBear())
class RecommendationController(Controller):
    def __init__(self, service: RecommendationService) -> None:
        self.service = service

    @require_admin
    @get(
        "/users/{user_id}/profile",
        response=UserIssueSensitivityProfileResponse,
        exceptions=(UserNotFound,),
    )
    def get_user_issue_sensitivity_profile(self, user_id: int):
        return self.service.get_user_issue_sensitivity_profile(user_id=user_id)

    @require_admin
    @get(
        "/users/{user_id}/features",
        response=UserFoodPreferenceFeatureResponse,
        exceptions=(UserNotFound,),
    )
    def get_user_food_preference_features(self, user_id: int):
        return self.service.get_user_food_preference_features(user_id=user_id)

    # get my features
    @get(
        "/me/features",
        response=UserFoodPreferenceFeatureResponse,
        exceptions=(UserNotFound,),
    )
    def get_my_food_preference_features(self, request: AuthenticatedRequest):
        return self.service.get_user_food_preference_features(user_id=request.user.id)

    @get(
        "/me/dishes",
        response=RecommendationFeedResponse,
        exceptions=(UserNotFound,),
    )
    def get_my_recommendation_feed(
        self,
        request: AuthenticatedRequest,
        limit: int = 20,
        offset: int = 0,
        include_explain: bool = False,
    ):
        return self.service.get_recommended_dishes(
            user_id=request.user.id,
            limit=limit,
            offset=offset,
            include_explain=include_explain,
        )

    @post(
        "/me/daily-nutrition/init",
        response=DailyNutritionSummaryResponse,
        exceptions=(UserNotFound,),
    )
    def init_daily_nutrition(self, request: AuthenticatedRequest, payload: DailyNutritionInitRequest):
        return self.service.init_daily_nutrition(
            user_id=request.user.id,
            age=payload.age,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            activity_level=payload.activity_level,
            goal=payload.goal,
        )

    @get(
        "/me/daily-nutrition/summary",
        response=DailyNutritionSummaryResponse,
        exceptions=(UserNotFound,),
    )
    def get_my_daily_nutrition_summary(self, request: AuthenticatedRequest):
        return self.service.get_daily_nutrition_summary(user_id=request.user.id)

    @get(
        "/me/daily-nutrition/meals",
        response=DailyMealLogListResponse,
        exceptions=(UserNotFound,),
    )
    def get_my_daily_meal_logs(self, request: AuthenticatedRequest):
        return self.service.get_daily_meal_logs(user_id=request.user.id)

    @post(
        "/me/daily-nutrition/parse-meal",
        response=DailyNutritionMealParseResponse,
        exceptions=(UserNotFound,),
    )
    def parse_my_daily_meal(self, request: AuthenticatedRequest, payload: DailyNutritionParseMealRequest):
        return self.service.parse_daily_meal(
            user_id=request.user.id,
            text=payload.text,
            meal_time=payload.meal_time,
        )

    @get(
        "/me/daily-nutrition/balanced-recommendations",
        response=DailyNutritionRecommendationResponse,
        exceptions=(UserNotFound,),
    )
    def get_my_daily_balanced_recommendations(self, request: AuthenticatedRequest, limit: int = 10):
        return self.service.get_daily_balanced_recommendations(
            user_id=request.user.id,
            limit=limit,
        )

    @patch(
        "/me/daily-nutrition/meals/{meal_uid}",
        response=DailyMealLogListResponse,
        exceptions=(UserNotFound,),
    )
    def update_my_daily_meal_log(
        self,
        request: AuthenticatedRequest,
        meal_uid: str,
        payload: DailyMealLogUpdateRequest,
    ):
        return self.service.update_daily_meal_log(
            user_id=request.user.id,
            log_uid=meal_uid,
            meal_name=payload.meal_name,
            meal_time=payload.meal_time,
            quantity_multiplier=payload.quantity_multiplier,
            dish_uid=payload.dish_uid,
        )

    @delete(
        "/me/daily-nutrition/meals/{meal_uid}",
        response=DailyMealLogListResponse,
        exceptions=(UserNotFound,),
    )
    def delete_my_daily_meal_log(self, request: AuthenticatedRequest, meal_uid: str):
        return self.service.delete_daily_meal_log(user_id=request.user.id, log_uid=meal_uid)

    @patch(
        "/me/daily-nutrition/profile",
        response=DailyNutritionProfileResponse,
        exceptions=(UserNotFound, DailyNutritionProfileNotFoundException),
    )
    def update_my_daily_nutrition_profile(
        self,
        request: AuthenticatedRequest,
        payload: DailyNutritionProfileUpdateRequest,
    ):
        """
        Update user's daily nutrition profile.
        Only provided fields are updated. TDEE and macros are recalculated.
        Returns full profile with personal info and nutrition data.
        """
        return self.service.update_daily_nutrition_profile(
            user_id=request.user.id,
            age=payload.age,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            activity_level=payload.activity_level,
            goal=payload.goal,
        )
    
    @get(
        "/me/daily-nutrition/profile",
        response=DailyNutritionProfileResponse,
        exceptions=(UserNotFound, DailyNutritionProfileNotFoundException),
    )
    def get_my_daily_nutrition_profile(self, request: AuthenticatedRequest):
        """
        Get user's daily nutrition profile with personal info and current nutrition data.
        Returns: age, gender, height_cm, weight_kg, activity_level, goal, BMR, TDEE, targets, consumed, remaining
        """
        return self.service.get_daily_nutrition_profile(user_id=request.user.id)
    
    @get(
        "/me/dishes/{dish_uid}/better-for-issue",response=BetterDishForIssueResponse,
        exceptions=(UserNotFound, DishNotFoundException),
    )
    def find_better_dish_for_issue(self, request: AuthenticatedRequest, dish_uid: str, limit: int = 5):
        limit = max(1, min(limit, 20))
        return self.service.find_better_dish_for_issue(
            user_id=request.user.id,
            dish_uid=dish_uid,
            limit=limit,
        )
