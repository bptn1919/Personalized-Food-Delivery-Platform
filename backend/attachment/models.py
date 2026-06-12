import uuid
from enum import unique

from django.db import models

from utils.types import User


@unique
class AttachmentType(models.TextChoices):
    INGREDIENT = "INGREDIENT", "Ingredient"
    DISH = "DISH", "Dish"
    CERTIFICATE = "CERTIFICATE", "Certificate"
    CHEF_AVATAR = "CHEF_AVATAR", "Chef Avatar"
    CUSTOMER_AVATAR = "CUSTOMER_AVATAR", "Customer Avatar"
    REVIEW = "REVIEW", "Review"
    REPORT = "REPORT", "Report"
    OTHER = "OTHER", "Other"
    CHAT = 'CHAT', 'Chat'


class Attachment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    type = models.CharField(
        max_length=255,
        choices=AttachmentType.choices,
        null=False,
        blank=False,
        default=AttachmentType.OTHER,
    )

    # Metadata
    original_name = models.TextField()
    hashed_name = models.TextField()

    size = models.IntegerField()
    content_type = models.CharField(max_length=255)

    # Storage
    bucket = models.CharField(max_length=255)
    directory = models.TextField()

    is_public = models.BooleanField(default=True)
    public_url = models.URLField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_file_deleted = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)

    is_completed = models.BooleanField(default=False)

    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="attachment_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )

    updater = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="updater_id",
        related_name="attachment_fk_updater",
        db_constraint=True,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        self.directory = self.type.lower()
        return super().save(*args, **kwargs)
