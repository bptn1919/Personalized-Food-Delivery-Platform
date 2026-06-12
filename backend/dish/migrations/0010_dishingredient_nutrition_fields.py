from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dish", "0009_rename_private_final_score_dish_final_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="dishingredient",
            name="energy",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="protein",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="lipid",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="carbohydrate",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="fiber",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="natri",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="kali",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="cholesterol",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="retinol",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="caroten",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="vitamin_b_1",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="vitamin_b_2",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="vitamin_pp",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="vitamin_c",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="calcium",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="phosphorus",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="fe",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="mg",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="zn",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="mn",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="cu",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="flo",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="iot",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="se",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="total_fa",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="palmitic",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="stearic",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="linoleic",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dishingredient",
            name="linolenic",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
