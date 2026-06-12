from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from order.models import Order
from recommendation.services.vector_index import VectorIndexService
from utils.enums import OrderStatusEnum


@receiver(pre_save, sender=Order)
def cache_previous_order_status(sender, instance: Order, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    previous = Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    instance._previous_status = previous


@receiver(post_save, sender=Order)
def refresh_user_vector_on_order_completed(sender, instance: Order, created: bool, **kwargs):
    if not instance.owner_id:
        return

    previous_status = getattr(instance, "_previous_status", None)
    is_completed = instance.status == OrderStatusEnum.COMPLETED
    was_completed = previous_status == OrderStatusEnum.COMPLETED

    if not is_completed or was_completed:
        return

    def _refresh():
        config = getattr(settings, "RECOMMENDATION_CONFIG", {})
        decay_lambda = float(config.get("history_decay_lambda", 0.03))
        VectorIndexService().refresh_user_vector(user_id=instance.owner_id, decay_lambda=decay_lambda)

    transaction.on_commit(_refresh)
