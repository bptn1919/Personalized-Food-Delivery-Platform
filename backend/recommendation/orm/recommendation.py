class RecommendationORM:
    @staticmethod
    def get_user_food_preference_features (user_id: int):
        from recommendation.models import UserFoodPreferenceFeature
        return UserFoodPreferenceFeature.objects.filter(user_id=user_id).first()