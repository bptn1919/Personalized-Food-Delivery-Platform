from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from recommendation.models import UserFoodPreferenceFeature
from recommendation.services.vector_index import VectorIndexService


@receiver(post_save, sender=UserFoodPreferenceFeature)
def refresh_user_vector_on_feature_change(sender, instance: UserFoodPreferenceFeature, **kwargs):
    if not instance.user_id:
        return

    def _refresh():
        config = getattr(settings, "RECOMMENDATION_CONFIG", {})
        decay_lambda = float(config.get("history_decay_lambda", 0.03))
        VectorIndexService().refresh_user_vector(user_id=instance.user_id, decay_lambda=decay_lambda)

    transaction.on_commit(_refresh)
