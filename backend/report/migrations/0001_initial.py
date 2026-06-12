import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("attachment", "0007_alter_attachment_type"),
        ("dish", "0020_dish_serving_size"),
        ("order", "0013_order_delivery_address_text_order_delivery_latitude_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChefReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("category", models.CharField(
                    choices=[
                        ("FOOD_SAFETY", "An toàn thực phẩm"),
                        ("FOOD_QUALITY", "Chất lượng thức ăn"),
                        ("WRONG_ITEM", "Giao sai món"),
                        ("MISSING_ITEM", "Giao thiếu món"),
                        ("HYGIENE", "Vệ sinh"),
                        ("FINANCIAL", "Vấn đề tài chính"),
                    ],
                    max_length=20,
                )),
                ("description", models.TextField()),
                ("credibility_weight", models.FloatField(default=1.0)),
                ("ai_severity", models.CharField(
                    blank=True,
                    choices=[
                        ("LOW", "Thấp"),
                        ("MEDIUM", "Trung bình"),
                        ("HIGH", "Cao"),
                        ("CRITICAL", "Nghiêm trọng"),
                    ],
                    max_length=10,
                    null=True,
                )),
                ("ai_food_safety_risk", models.BooleanField(blank=True, null=True)),
                ("ai_severity_reason", models.TextField(blank=True, null=True)),
                ("ai_analyzed_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(
                    choices=[
                        ("PENDING", "Chờ xem xét"),
                        ("REVIEWED", "Đã xem xét"),
                        ("DISMISSED", "Đã bác bỏ"),
                        ("ACTED_ON", "Đã xử lý"),
                    ],
                    db_index=True,
                    default="PENDING",
                    max_length=12,
                )),
                ("admin_note", models.TextField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("deleted", models.BooleanField(default=False)),
                ("chef", models.ForeignKey(
                    db_column="chef_id",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="report_fk_chef",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("dish", models.ForeignKey(
                    blank=True,
                    db_column="dish_uid",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="report_fk_dish",
                    to="dish.dish",
                    to_field="uid",
                )),
                ("evidence", models.ForeignKey(
                    blank=True,
                    db_column="evidence_uid",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="report_fk_evidence",
                    to="attachment.attachment",
                    to_field="uid",
                )),
                ("order", models.ForeignKey(
                    blank=True,
                    db_column="order_id",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="report_fk_order",
                    to="order.order",
                )),
                ("reporter", models.ForeignKey(
                    db_column="reporter_id",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="report_fk_reporter",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("reviewed_by", models.ForeignKey(
                    blank=True,
                    db_column="reviewed_by_id",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="report_fk_reviewer",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"indexes": [
                models.Index(fields=["chef", "created_at"], name="report_chef_report_chef_created_idx"),
                models.Index(fields=["chef", "status"], name="report_chef_report_chef_status_idx"),
                models.Index(fields=["dish", "created_at"], name="report_chef_report_dish_created_idx"),
            ]},
        ),
        migrations.AddConstraint(
            model_name="chefreport",
            constraint=models.UniqueConstraint(
                fields=["reporter", "order", "dish"],
                name="unique_reporter_order_dish",
            ),
        ),
        migrations.CreateModel(
            name="ChefSuspension",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("suspension_type", models.CharField(
                    choices=[
                        ("DISH_LOCK", "Khóa món ăn"),
                        ("FULL_LOCK", "Khóa toàn bộ chef"),
                    ],
                    max_length=12,
                )),
                ("reason", models.TextField()),
                ("trigger_source", models.CharField(
                    choices=[
                        ("SYSTEM", "Hệ thống tự động"),
                        ("ADMIN", "Admin thủ công"),
                    ],
                    default="SYSTEM",
                    max_length=8,
                )),
                ("trigger_data", models.JSONField(default=dict)),
                ("status", models.CharField(
                    choices=[
                        ("ACTIVE", "Đang khóa"),
                        ("APPEALING", "Đang giải trình"),
                        ("LIFTED", "Đã mở khóa"),
                        ("REJECTED", "Giải trình bị bác bỏ"),
                    ],
                    db_index=True,
                    default="ACTIVE",
                    max_length=12,
                )),
                ("appeal_text", models.TextField(blank=True, null=True)),
                ("appealed_at", models.DateTimeField(blank=True, null=True)),
                ("lifted_at", models.DateTimeField(blank=True, null=True)),
                ("lift_note", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("chef", models.ForeignKey(
                    db_column="chef_id",
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="suspension_fk_chef",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("lifted_by", models.ForeignKey(
                    blank=True,
                    db_column="lifted_by_id",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="suspension_fk_lifted_by",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("locked_dish", models.ForeignKey(
                    blank=True,
                    db_column="locked_dish_uid",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="suspension_fk_dish",
                    to="dish.dish",
                    to_field="uid",
                )),
            ],
            options={"indexes": [
                models.Index(fields=["chef", "status"], name="report_chef_suspension_chef_status_idx"),
                models.Index(fields=["chef", "created_at"], name="report_chef_suspension_chef_created_idx"),
            ]},
        ),
        migrations.CreateModel(
            name="ChefWarning",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("warning_type", models.CharField(
                    choices=[
                        ("FOOD_QUALITY", "Chất lượng thức ăn"),
                        ("DELIVERY", "Giao hàng"),
                        ("FINANCIAL", "Tài chính"),
                    ],
                    db_index=True,
                    default="FOOD_QUALITY",
                    max_length=16,
                )),
                ("metrics_snapshot", models.JSONField(default=dict)),
                ("email_sent", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("chef", models.ForeignKey(
                    db_column="chef_id",
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="warning_fk_chef",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("warned_dish", models.ForeignKey(
                    blank=True,
                    db_column="warned_dish_uid",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="warning_fk_dish",
                    to="dish.dish",
                    to_field="uid",
                )),
            ],
            options={"indexes": [
                models.Index(fields=["chef", "created_at"], name="report_chef_warning_chef_created_idx"),
                models.Index(fields=["chef", "warning_type", "created_at"], name="report_chef_warning_type_idx"),
            ]},
        ),
    ]
