from django.db import models

from utils.types import User


class CreatorAndUpdaterModel(models.Model):
    creator = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="creator_id",
        related_name="%(class)s_fk_creator",
        db_constraint=True,
        blank=True,
        null=True,
    )

    updater = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updater_id",
        related_name="%(class)s_fk_updater",
        db_constraint=True,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True
