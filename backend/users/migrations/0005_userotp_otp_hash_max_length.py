from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration 0004 was applied with otp_hash varchar(64) (HMAC-SHA256 era).
    Argon2id hash strings are ~99 chars, so we widen the column to varchar(128).
    """

    dependencies = [
        ('users', '0004_userotp_otp_security'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userotp',
            name='otp_hash',
            field=models.CharField(max_length=128),
        ),
    ]
