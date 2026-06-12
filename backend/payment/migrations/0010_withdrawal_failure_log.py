from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0009_alter_paymenttransaction_status_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WithdrawalFailureLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("stage", models.CharField(max_length=40)),
                ("error_type", models.CharField(blank=True, default="", max_length=120)),
                ("error_message", models.TextField(blank=True, default="")),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="withdrawal_failures",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "wallet_transaction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="failure_logs",
                        to="payment.wallettransaction",
                    ),
                ),
            ],
            options={
                "db_table": "wallet_withdrawal_failures",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["user", "created_at"], name="wallet_with_user_id_idx"),
                    models.Index(fields=["stage"], name="wallet_with_stage_idx"),
                ],
            },
        ),
    ]
