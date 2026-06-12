from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0005_alter_settlementrecord_status_delete_payoutjob"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settlementrecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("SUCCESS", "Success"),
                    ("FAILED", "Failed"),
                    ("RETRYABLE", "Retryable"),
                    ("FAILED_INSUFFICIENT_BALANCE", "Failed - Insufficient Balance"),
                ],
                default="PENDING",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="settlementrecord",
            name="last_retry_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="settlementrecord",
            name="retry_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="settlementrecord",
            name="retry_lock",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="settlementrecord",
            index=models.Index(fields=["retry_lock", "status"], name="settlement_r_retry_l_fbb95f_idx"),
        ),
    ]
