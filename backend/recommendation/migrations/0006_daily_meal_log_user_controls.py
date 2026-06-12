from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0005_alter_userdailynutrition_gender_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailymeallog",
            name="source_ref",
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="dailymeallog",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]