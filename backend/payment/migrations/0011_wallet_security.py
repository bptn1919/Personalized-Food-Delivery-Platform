from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0010_withdrawal_failure_log'),
    ]

    operations = [
        # WalletTransaction: per-user tamper-evident chain (previous_hash + chain_hash).
        migrations.AddField(
            model_name='wallettransaction',
            name='previous_hash',
            field=models.CharField(max_length=64, default='0' * 64),
        ),
        migrations.AddField(
            model_name='wallettransaction',
            name='chain_hash',
            field=models.CharField(max_length=64, blank=True, default=''),
        ),
        # InternalWallet: HMAC-SHA256 balance signature to detect direct DB edits.
        migrations.AddField(
            model_name='internalwallet',
            name='signature',
            field=models.CharField(max_length=64, blank=True, default=''),
        ),
    ]
