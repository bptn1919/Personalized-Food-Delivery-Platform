from django.apps import AppConfig


class DishConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dish'

    def ready(self):
        from . import signals  # noqa: F401
