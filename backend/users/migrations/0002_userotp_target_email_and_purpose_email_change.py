from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userotp",
            name="target_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name="userotp",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("SIGNUP", "Sign Up"),
                    ("RESET_PASSWORD", "Reset Password"),
                    ("EMAIL_CHANGE", "Email Change"),
                ],
                max_length=16,
            ),
        ),
    ]
