# Generated migration to add confidence field to DishIngredient

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dish', '0016_alter_dishingredient_approval_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dishingredient',
            name='confidence',
            field=models.FloatField(default=1.0, null=True, blank=True, help_text='Confidence score (0-1) based on ingredient validation flags, source, and status'),
        ),
    ]
