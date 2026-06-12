from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_userotp_purpose'),
    ]

    operations = [
        # Replace plaintext OTP with Argon2id hash (salt embedded in string) + attempts counter.
        migrations.RemoveField(
            model_name='userotp',
            name='otp',
        ),
        migrations.AddField(
            model_name='userotp',
            name='otp_hash',
            # Argon2id hash string ~100 chars; 128 gives headroom for future param bumps.
            field=models.CharField(max_length=128, default='$invalid$'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userotp',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
