from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChefLocation(models.Model):
    chef = models.OneToOneField(User, on_delete=models.CASCADE, related_name='location_profile')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chef_locations'
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"Location of Chef {self.chef.id}"