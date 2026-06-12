from uuid import uuid4

from django.db import models


class BaseModel(models.Model):
    uid = models.UUIDField(default=uuid4, unique=True, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        abstract = True
