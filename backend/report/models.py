import uuid

from django.db import models

from utils.enums import (
    ReportCategoryEnum,
    ReportStatusEnum,
    SeverityLevelEnum,
    SuspensionStatusEnum,
    SuspensionTriggerEnum,
    SuspensionTypeEnum,
    WarningTypeEnum,
)
from utils.types import User


class ChefReport(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    reporter = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_fk_reporter",
        db_column="reporter_id",
    )
    chef = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="report_fk_chef",
        db_column="chef_id",
    )
    order = models.ForeignKey(
        to="order.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_fk_order",
        db_column="order_id",
    )
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_fk_dish",
        to_field="uid",
        db_column="dish_uid",
    )
    evidence = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_fk_evidence",
        to_field="uid",
        db_column="evidence_uid",
    )

    category = models.CharField(max_length=20, choices=ReportCategoryEnum.choices)
    description = models.TextField()

    # ── Credibility ────────────────────────────────────────────────────────────
    # Tier: plain=1.0, has_text_review=1.5, has_image=2.0, ai_confirmed=3.0, admin=5.0
    credibility_weight = models.FloatField(default=1.0)

    # ── AI severity ────────────────────────────────────────────────────────────
    ai_severity = models.CharField(
        max_length=10,
        choices=SeverityLevelEnum.choices,
        null=True,
        blank=True,
    )
    ai_food_safety_risk = models.BooleanField(null=True, blank=True)
    ai_severity_reason = models.TextField(null=True, blank=True)
    ai_analyzed_at = models.DateTimeField(null=True, blank=True)

    # ── Admin review ───────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=12,
        choices=ReportStatusEnum.choices,
        default=ReportStatusEnum.PENDING,
        db_index=True,
    )
    admin_note = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_fk_reviewer",
        db_column="reviewed_by_id",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        # 1 customer chỉ report 1 lần cho mỗi (order, dish)
        unique_together = [["reporter", "order", "dish"]]
        indexes = [
            models.Index(fields=["chef", "created_at"]),
            models.Index(fields=["chef", "status"]),
            models.Index(fields=["dish", "created_at"]),
        ]


class ChefSuspension(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    chef = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="suspension_fk_chef",
        db_column="chef_id",
        db_index=True,
    )
    suspension_type = models.CharField(max_length=12, choices=SuspensionTypeEnum.choices)
    locked_dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspension_fk_dish",
        to_field="uid",
        db_column="locked_dish_uid",
    )

    reason = models.TextField()
    trigger_source = models.CharField(
        max_length=8,
        choices=SuspensionTriggerEnum.choices,
        default=SuspensionTriggerEnum.SYSTEM,
    )
    # Snapshot metrics tại thời điểm trigger để audit
    trigger_data = models.JSONField(default=dict)

    status = models.CharField(
        max_length=12,
        choices=SuspensionStatusEnum.choices,
        default=SuspensionStatusEnum.ACTIVE,
        db_index=True,
    )

    # ── Chef appeal ────────────────────────────────────────────────────────────
    appeal_text = models.TextField(null=True, blank=True)
    appealed_at = models.DateTimeField(null=True, blank=True)

    # ── Admin action ───────────────────────────────────────────────────────────
    lifted_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suspension_fk_lifted_by",
        db_column="lifted_by_id",
    )
    lifted_at = models.DateTimeField(null=True, blank=True)
    lift_note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["chef", "status"]),
            models.Index(fields=["chef", "created_at"]),
        ]


class ChefWarning(models.Model):
    """
    Cảnh báo gửi email cho chef — không chặn đơn.

    warning_type phân biệt nguồn gốc:
      FOOD_QUALITY — tỉ lệ phản ánh chất lượng thức ăn tăng
      DELIVERY     — tỉ lệ giao sai/thiếu tăng
      FINANCIAL    — báo cáo tài chính được ghi nhận (admin cần xem xét)
    """
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    chef = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="warning_fk_chef",
        db_column="chef_id",
        db_index=True,
    )
    warned_dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warning_fk_dish",
        to_field="uid",
        db_column="warned_dish_uid",
    )

    warning_type = models.CharField(
        max_length=16,
        choices=WarningTypeEnum.choices,
        default=WarningTypeEnum.FOOD_QUALITY,
        db_index=True,
    )

    # Snapshot metrics để audit
    metrics_snapshot = models.JSONField(default=dict)
    email_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["chef", "created_at"]),
            models.Index(fields=["chef", "warning_type", "created_at"]),
        ]
