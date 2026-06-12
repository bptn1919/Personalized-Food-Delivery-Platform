from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from dish.models import DishIngredient
from recommendation.services.vector_index import VectorIndexService


@receiver(post_save, sender=DishIngredient)
def refresh_dish_vector_on_save(sender, instance: DishIngredient, **kwargs):
    dish_id = str(instance.dish_id)

    def _refresh():
        VectorIndexService().refresh_dish_vectors_for_dishes(dish_ids=[dish_id])

    transaction.on_commit(_refresh)


@receiver(post_delete, sender=DishIngredient)
def refresh_dish_vector_on_delete(sender, instance: DishIngredient, **kwargs):
    dish_id = str(instance.dish_id)

    def _refresh():
        VectorIndexService().refresh_dish_vectors_for_dishes(dish_ids=[dish_id])

    transaction.on_commit(_refresh)
