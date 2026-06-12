"""
ReportService — orchestrator chính cho toàn bộ flow report & suspension.

Luồng chính:
  create_report()
    → validate (rate limit, order ownership, duplicate)
    → compute initial credibility_weight
    → save ChefReport
    → gọi Gemini severity (sync, lỗi không rollback report)
    → update weight nếu AI confirm food_safety
    → gọi analyze_and_act()

  analyze_and_act()
    → compute_chef_metrics()
    → decide_action()
    → apply_warning() / apply_dish_lock() / apply_full_lock()

Mọi DB write trong atomic block. Email nằm ngoài để không rollback khi SMTP lỗi.
"""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from exceptions.report import (
    AppealAlreadySubmitted,
    AppealNotAllowed,
    ReportAlreadyExists,
    ReportEvidenceRequired,
    ReportOrderNotCompleted,
    ReportOrderNotOwned,
    ReportRateLimitExceeded,
    ReportTargetNotFound,
    ReportTargetRequired,
    SuspensionNotFound,
)
from utils.enums import (
    ChefSuspensionLevelEnum,
    OrderStatusEnum,
    ReportStatusEnum,
    SuspensionStatusEnum,
    SuspensionTriggerEnum,
    SuspensionTypeEnum,
    WarningTypeEnum,
)
from utils.services.email.client import EmailClient
from utils.services.email.template import EmailTemplate

from .analysis import (
    DELIVERY_CATEGORIES,
    FINANCIAL_CATEGORIES,
    FOOD_QUALITY_CATEGORIES,
    ORDER_REQUIRED_CATEGORIES,
    PLATFORM_EVIDENCE_REQUIRED,
    check_customer_rate_limit,
    compute_chef_metrics,
    compute_delivery_metrics,
    compute_initial_weight,
    compute_weight_after_ai,
    decide_action,
    decide_delivery_action,
)
from .gemini_severity import analyze_report_severity

logger = logging.getLogger("django")
_email_client = EmailClient()
_email_tpl = EmailTemplate()


class ReportService:

    # ── Public: customer actions ───────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_report(
        *,
        reporter,
        order_uid=None,     # UUID — Order.uid (BaseModel PK)
        dish_uid=None,
        chef_id=None,
        category: str,
        description: str,
        evidence_uid=None,
    ):
        """
        Tạo report mới từ customer.

        Validates:
        - Rate limit 5 reports/24h
        - Order đã COMPLETED
        - reporter là owner của order
        - Không duplicate (reporter + order + dish)

        Sau khi lưu, gọi Gemini + analyze_and_act.
        """
        from order.models import Order
        from report.models import ChefReport

        # 1. Rate limit
        if not check_customer_rate_limit(reporter.id):
            raise ReportRateLimitExceeded()

        order = None
        chef = None

        # 2. Lấy order nếu có
        if order_uid:
            try:
                order = Order.objects.select_related("chef").get(uid=order_uid)
            except Order.DoesNotExist:
                raise ReportTargetNotFound()

            chef = order.chef

            if category in ORDER_REQUIRED_CATEGORIES:
                if order.owner_id != reporter.id:
                    raise ReportOrderNotOwned()
                if order.status != OrderStatusEnum.COMPLETED:
                    raise ReportOrderNotCompleted()
        elif category in ORDER_REQUIRED_CATEGORIES:
            raise ReportTargetRequired()

        # 3. Lấy dish nếu có
        dish = None
        if dish_uid:
            from dish.models import Dish
            try:
                dish = Dish.objects.select_related("owner").get(uid=dish_uid)
            except Dish.DoesNotExist:
                if category in ORDER_REQUIRED_CATEGORIES:
                    dish = None
                else:
                    raise ReportTargetNotFound()

        # 4. Lấy chef nếu không có từ order
        if not chef and dish:
            chef = dish.owner

        if chef_id:
            from utils.types import User
            try:
                chef = User.objects.get(id=chef_id)
            except User.DoesNotExist:
                raise ReportTargetNotFound()

        if dish and chef and dish.owner_id and dish.owner_id != chef.id:
            raise ReportTargetNotFound()

        if not chef:
            raise ReportTargetRequired()

        # 5. Duplicate check
        if ChefReport.objects.filter(
            reporter=reporter,
            order=order,
            dish=dish,
        ).exists():
            raise ReportAlreadyExists()

        # 6. Lấy evidence
        evidence = None
        if evidence_uid:
            from attachment.models import Attachment
            try:
                evidence = Attachment.objects.get(uid=evidence_uid)
            except Attachment.DoesNotExist:
                pass

        if category in PLATFORM_EVIDENCE_REQUIRED and evidence is None:
            raise ReportEvidenceRequired()

        # 7. Tính initial credibility weight
        initial_weight = compute_initial_weight(
            has_evidence=evidence is not None,
            description=description,
            reporter_id=reporter.id,
        )

        # 8. Save report
        report = ChefReport.objects.create(
            reporter=reporter,
            chef=chef,
            order=order,
            dish=dish,
            category=category,
            description=description,
            evidence=evidence,
            credibility_weight=initial_weight,
            status=ReportStatusEnum.PENDING,
        )

        chef_id = chef.id

        # transaction commit trước khi gọi Gemini + email
        # (Gemini/email lỗi không rollback report)

        # End of atomic block — tiếp tục ngoài transaction
        # (Django atomic block kết thúc ở đây nhờ decorator)

        return report, chef_id, dish

    @staticmethod
    def run_post_create(report, chef_id, dish):
        """
        Gọi sau khi create_report() commit xong.
        Chạy Gemini + update weight + analyze_and_act.
        Không nằm trong transaction để email/gemini lỗi không rollback.
        """
        from report.models import ChefReport

        # 8. Gemini severity analysis (chỉ cho food-quality)
        if report.category in FOOD_QUALITY_CATEGORIES:
            try:
                gemini_result = analyze_report_severity(
                    category=report.category,
                    description=report.description,
                )
                new_weight = compute_weight_after_ai(
                    current_weight=report.credibility_weight,
                    ai_severity=gemini_result["severity"],
                    ai_food_safety_risk=gemini_result["food_safety_risk"],
                )
                ChefReport.objects.filter(pk=report.pk).update(
                    ai_severity=gemini_result["severity"],
                    ai_food_safety_risk=gemini_result["food_safety_risk"],
                    ai_severity_reason=gemini_result["reason"],
                    ai_analyzed_at=timezone.now(),
                    credibility_weight=new_weight,
                )
                report.credibility_weight = new_weight
            except Exception as exc:
                logger.warning("Gemini severity call failed for report %s: %s", report.uid, exc)

        # 9. Route sang handler phù hợp theo category
        category = report.category
        if category in FOOD_QUALITY_CATEGORIES:
            ReportService.analyze_and_act(chef_id=chef_id, dish=dish)
        elif category in DELIVERY_CATEGORIES:
            ReportService._analyze_delivery_and_act(chef_id=chef_id)
        elif category in FINANCIAL_CATEGORIES:
            ReportService._handle_financial_report(report=report, chef_id=chef_id)

    # ── Internal: analysis & lock ──────────────────────────────────────────────

    @staticmethod
    def analyze_and_act(chef_id: int, dish=None):
        """Food-quality: tính metrics → quyết định → áp dụng hành động."""
        from report.models import ChefSuspension

        metrics = compute_chef_metrics(chef_id, dish_uid=dish.uid if dish else None)
        decision = decide_action(metrics)

        action = decision["action"]
        reason = decision["reason"]

        if action == "NONE":
            return

        # Không downgrade: nếu đang FULL_LOCK thì không làm gì
        active_suspension = ChefSuspension.objects.filter(
            chef_id=chef_id,
            status=SuspensionStatusEnum.ACTIVE,
        ).first()

        if active_suspension and active_suspension.suspension_type == SuspensionTypeEnum.FULL_LOCK:
            return

        if action == "FULL_LOCK":
            ReportService._apply_full_lock(chef_id, reason, metrics)
        elif action == "DISH_LOCK" and dish:
            if active_suspension and active_suspension.locked_dish == dish:
                return  # Dish đã bị lock rồi
            ReportService._apply_dish_lock(chef_id, dish, reason, metrics)
        elif action == "WARNING":
            ReportService._apply_warning(chef_id, dish, reason, metrics)

    @staticmethod
    @transaction.atomic
    def _apply_full_lock(chef_id: int, reason: str, trigger_data: dict):
        from profile.models import ChefProfile
        from report.models import ChefSuspension

        # Đóng mọi DISH_LOCK cũ trước khi tạo FULL_LOCK
        ChefSuspension.objects.filter(
            chef_id=chef_id,
            status=SuspensionStatusEnum.ACTIVE,
            suspension_type=SuspensionTypeEnum.DISH_LOCK,
        ).update(
            status=SuspensionStatusEnum.LIFTED,
            lift_note="Được đóng tự động khi FULL_LOCK được áp dụng.",
            lifted_at=timezone.now(),
        )

        suspension = ChefSuspension.objects.create(
            chef_id=chef_id,
            suspension_type=SuspensionTypeEnum.FULL_LOCK,
            reason=reason,
            trigger_source=SuspensionTriggerEnum.SYSTEM,
            trigger_data=trigger_data or {},
            status=SuspensionStatusEnum.ACTIVE,
        )

        ChefProfile.objects.filter(user_id=chef_id).update(
            is_accepting_orders=False,
            suspension_level=ChefSuspensionLevelEnum.SUSPENDED,
        )

        logger.info("FULL_LOCK applied to chef %s (suspension %s)", chef_id, suspension.uid)

        # Email ngoài atomic block — gọi sau khi transaction commit
        transaction.on_commit(
            lambda: ReportService._send_full_lock_email(chef_id, suspension)
        )

    @staticmethod
    @transaction.atomic
    def _apply_dish_lock(chef_id: int, dish, reason: str, trigger_data: dict):
        from report.models import ChefSuspension

        suspension = ChefSuspension.objects.create(
            chef_id=chef_id,
            locked_dish=dish,
            suspension_type=SuspensionTypeEnum.DISH_LOCK,
            reason=reason,
            trigger_source=SuspensionTriggerEnum.SYSTEM,
            trigger_data=trigger_data or {},
            status=SuspensionStatusEnum.ACTIVE,
        )

        dish.__class__.objects.filter(uid=dish.uid).update(is_suspended=True)

        logger.info(
            "DISH_LOCK applied: chef %s, dish %s (suspension %s)",
            chef_id, dish.uid, suspension.uid,
        )

        transaction.on_commit(
            lambda: ReportService._send_dish_lock_email(chef_id, dish, suspension)
        )

    @staticmethod
    def _apply_warning(chef_id: int, dish, reason: str, metrics: dict):
        from report.models import ChefWarning

        # Không tạo warning trùng trong cùng ngày (cùng type)
        today_cutoff = timezone.now() - timedelta(hours=24)
        if ChefWarning.objects.filter(
            chef_id=chef_id,
            warned_dish=dish,
            warning_type=WarningTypeEnum.FOOD_QUALITY,
            created_at__gte=today_cutoff,
        ).exists():
            return

        warning = ChefWarning.objects.create(
            chef_id=chef_id,
            warned_dish=dish,
            warning_type=WarningTypeEnum.FOOD_QUALITY,
            metrics_snapshot=metrics or {},
        )

        logger.info("FOOD_QUALITY WARNING issued to chef %s (warning %s)", chef_id, warning.uid)

        try:
            ReportService._send_warning_email(chef_id, dish, reason)
            warning.email_sent = True
            warning.save(update_fields=["email_sent"])
        except Exception as exc:
            logger.warning("Warning email failed for chef %s: %s", chef_id, exc)

    @staticmethod
    def _analyze_delivery_and_act(chef_id: int):
        """Delivery: tính tỉ lệ giao sai/thiếu → warning hoặc admin alert."""
        from report.models import ChefWarning

        metrics = compute_delivery_metrics(chef_id)
        decision = decide_delivery_action(metrics)
        action = decision["action"]
        reason = decision["reason"]

        if action == "NONE":
            return

        # Không spam warning trong 24h
        today_cutoff = timezone.now() - timedelta(hours=24)
        if ChefWarning.objects.filter(
            chef_id=chef_id,
            warning_type=WarningTypeEnum.DELIVERY,
            created_at__gte=today_cutoff,
        ).exists():
            return

        warning = ChefWarning.objects.create(
            chef_id=chef_id,
            warning_type=WarningTypeEnum.DELIVERY,
            metrics_snapshot=metrics or {},
        )
        logger.info("DELIVERY WARNING issued to chef %s (warning %s)", chef_id, warning.uid)

        try:
            ReportService._send_delivery_warning_email(chef_id, reason, metrics, action)
            warning.email_sent = True
            warning.save(update_fields=["email_sent"])
        except Exception as exc:
            logger.warning("Delivery warning email failed for chef %s: %s", chef_id, exc)

    @staticmethod
    def _handle_financial_report(report, chef_id: int):
        """
        Financial: không tự động suspend — ghi nhận và alert admin ngay.
        Email chef biết report đã được ghi nhận, email admin để review.
        """
        from report.models import ChefWarning

        warning = ChefWarning.objects.create(
            chef_id=chef_id,
            warning_type=WarningTypeEnum.FINANCIAL,
            metrics_snapshot={
                "report_uid": str(report.uid),
                "description": report.description[:200],
                "order_id": report.order_id,
            },
        )
        logger.info("FINANCIAL report recorded for chef %s (warning %s)", chef_id, warning.uid)

        try:
            ReportService._send_financial_alert_emails(chef_id, report)
            warning.email_sent = True
            warning.save(update_fields=["email_sent"])
        except Exception as exc:
            logger.warning("Financial alert email failed for chef %s: %s", chef_id, exc)

    # ── Public: chef actions ───────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def submit_appeal(*, chef, suspension_uid, appeal_text: str):
        from report.models import ChefSuspension

        try:
            suspension = ChefSuspension.objects.select_for_update().get(
                uid=suspension_uid, chef=chef
            )
        except ChefSuspension.DoesNotExist:
            raise SuspensionNotFound()

        if suspension.status != SuspensionStatusEnum.ACTIVE:
            raise AppealNotAllowed()

        if suspension.appealed_at is not None:
            raise AppealAlreadySubmitted()

        suspension.appeal_text = appeal_text
        suspension.appealed_at = timezone.now()
        suspension.status = SuspensionStatusEnum.APPEALING
        suspension.save(update_fields=["appeal_text", "appealed_at", "status"])
        return suspension

    # ── Public: admin actions ──────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def lift_suspension(*, admin_user, suspension_uid, lift_note: str):
        from profile.models import ChefProfile
        from report.models import ChefSuspension

        try:
            suspension = ChefSuspension.objects.select_for_update().get(uid=suspension_uid)
        except ChefSuspension.DoesNotExist:
            raise SuspensionNotFound()

        if suspension.status not in (SuspensionStatusEnum.ACTIVE, SuspensionStatusEnum.APPEALING):
            raise AppealNotAllowed()

        suspension.status = SuspensionStatusEnum.LIFTED
        suspension.lifted_by = admin_user
        suspension.lifted_at = timezone.now()
        suspension.lift_note = lift_note
        suspension.save(update_fields=["status", "lifted_by", "lifted_at", "lift_note"])

        chef_id = suspension.chef_id

        if suspension.suspension_type == SuspensionTypeEnum.FULL_LOCK:
            ChefProfile.objects.filter(user_id=chef_id).update(
                is_accepting_orders=True,
                suspension_level=ChefSuspensionLevelEnum.NONE,
            )
        elif suspension.suspension_type == SuspensionTypeEnum.DISH_LOCK and suspension.locked_dish:
            suspension.locked_dish.__class__.objects.filter(
                uid=suspension.locked_dish.uid
            ).update(is_suspended=False)

        transaction.on_commit(
            lambda: ReportService._send_lift_email(chef_id, suspension)
        )
        return suspension

    @staticmethod
    @transaction.atomic
    def manual_suspension(*, admin_user, chef_id: int, suspension_type: str, dish_uid=None, reason: str):
        from profile.models import ChefProfile
        from report.models import ChefSuspension

        dish = None
        if dish_uid and suspension_type == SuspensionTypeEnum.DISH_LOCK:
            from dish.models import Dish
            dish = Dish.objects.get(uid=dish_uid)

        suspension = ChefSuspension.objects.create(
            chef_id=chef_id,
            suspension_type=suspension_type,
            locked_dish=dish,
            reason=reason,
            trigger_source=SuspensionTriggerEnum.ADMIN,
            trigger_data={"admin_id": admin_user.id},
            status=SuspensionStatusEnum.ACTIVE,
        )

        if suspension_type == SuspensionTypeEnum.FULL_LOCK:
            ChefProfile.objects.filter(user_id=chef_id).update(
                is_accepting_orders=False,
                suspension_level=ChefSuspensionLevelEnum.SUSPENDED,
            )
        elif dish:
            dish.__class__.objects.filter(uid=dish.uid).update(is_suspended=True)

        logger.info(
            "Manual %s applied to chef %s by admin %s",
            suspension_type, chef_id, admin_user.id,
        )

        transaction.on_commit(
            lambda: ReportService._send_full_lock_email(chef_id, suspension)
            if suspension_type == SuspensionTypeEnum.FULL_LOCK
            else ReportService._send_dish_lock_email(chef_id, dish, suspension)
        )
        return suspension

    @staticmethod
    @transaction.atomic
    def dismiss_report(*, admin_user, report_uid, admin_note: str = ""):
        from report.models import ChefReport
        from exceptions.report import ReportNotFound

        try:
            report = ChefReport.objects.get(uid=report_uid)
        except ChefReport.DoesNotExist:
            raise ReportNotFound()

        report.status = ReportStatusEnum.DISMISSED
        report.admin_note = admin_note
        report.reviewed_by = admin_user
        report.reviewed_at = timezone.now()
        report.save(update_fields=["status", "admin_note", "reviewed_by", "reviewed_at"])
        return report

    @staticmethod
    @transaction.atomic
    def admin_confirm_report(*, admin_user, report_uid):
        """Admin confirm → weight = 5.0 (highest tier)."""
        from report.models import ChefReport
        from exceptions.report import ReportNotFound
        from .analysis import WEIGHT_ADMIN

        try:
            report = ChefReport.objects.get(uid=report_uid)
        except ChefReport.DoesNotExist:
            raise ReportNotFound()

        report.credibility_weight = WEIGHT_ADMIN
        report.status = ReportStatusEnum.REVIEWED
        report.reviewed_by = admin_user
        report.reviewed_at = timezone.now()
        report.save(update_fields=["credibility_weight", "status", "reviewed_by", "reviewed_at"])

        # Re-analyze sau khi weight tăng
        dish = report.dish
        transaction.on_commit(
            lambda: ReportService.analyze_and_act(chef_id=report.chef_id, dish=dish)
        )
        return report

    # ── Email helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _send_full_lock_email(chef_id: int, suspension):
        try:
            from users.models import CustomUser
            chef = CustomUser.objects.get(id=chef_id)
            msg = _email_tpl.send_full_lock_email(
                user=chef,
                suspension_uid=str(suspension.uid),
                reason=suspension.reason,
                metrics=suspension.trigger_data,
            )
            _email_client.send_messages([msg])
        except Exception as exc:
            logger.error("Failed to send full_lock email to chef %s: %s", chef_id, exc)

    @staticmethod
    def _send_dish_lock_email(chef_id: int, dish, suspension):
        try:
            from users.models import CustomUser
            chef = CustomUser.objects.get(id=chef_id)
            msg = _email_tpl.send_dish_lock_email(
                user=chef,
                dish_name=dish.name if dish else "món ăn",
                suspension_uid=str(suspension.uid),
                reason=suspension.reason,
                metrics=suspension.trigger_data,
            )
            _email_client.send_messages([msg])
        except Exception as exc:
            logger.error("Failed to send dish_lock email to chef %s: %s", chef_id, exc)

    @staticmethod
    def _send_warning_email(chef_id: int, dish, reason: str):
        try:
            from users.models import CustomUser
            chef = CustomUser.objects.get(id=chef_id)
            msg = _email_tpl.send_chef_warning_email(
                user=chef,
                dish_name=dish.name if dish else None,
                reason=reason,
            )
            _email_client.send_messages([msg])
        except Exception as exc:
            logger.error("Failed to send warning email to chef %s: %s", chef_id, exc)

    @staticmethod
    def _send_lift_email(chef_id: int, suspension):
        try:
            from users.models import CustomUser
            chef = CustomUser.objects.get(id=chef_id)
            msg = _email_tpl.send_suspension_lifted_email(
                user=chef,
                suspension_uid=str(suspension.uid),
                lift_note=suspension.lift_note or "",
                suspension_type=suspension.suspension_type,
                dish_name=(
                    suspension.locked_dish.name
                    if suspension.locked_dish
                    else None
                ),
            )
            _email_client.send_messages([msg])
        except Exception as exc:
            logger.error("Failed to send lift email to chef %s: %s", chef_id, exc)

    @staticmethod
    def _send_delivery_warning_email(chef_id: int, reason: str, metrics: dict, action: str):
        try:
            from users.models import CustomUser
            chef = CustomUser.objects.get(id=chef_id)
            msg = _email_tpl.send_delivery_warning_email(
                user=chef,
                reason=reason,
                metrics=metrics,
                is_admin_alert=(action == "ADMIN_ALERT"),
            )
            _email_client.send_messages([msg])
        except Exception as exc:
            logger.error("Failed to send delivery warning email to chef %s: %s", chef_id, exc)

    @staticmethod
    def _send_financial_alert_emails(chef_id: int, report):
        try:
            from users.models import CustomUser
            from django.conf import settings
            chef = CustomUser.objects.get(id=chef_id)

            # Email cho chef — thông báo phản ánh đã được ghi nhận
            chef_msg = _email_tpl.send_financial_report_ack_email(
                user=chef,
                report_uid=str(report.uid),
                order_id=report.order_id,
            )
            _email_client.send_messages([chef_msg])

            # Email cho admin — để review
            admin_email = getattr(settings, "ADMIN_ALERT_EMAIL", None)
            if admin_email:
                admin_msg = _email_tpl.send_financial_admin_alert_email(
                    admin_email=admin_email,
                    chef_email=chef.email,
                    report_uid=str(report.uid),
                    order_id=report.order_id,
                    description=report.description,
                )
                _email_client.send_messages([admin_msg])
        except Exception as exc:
            logger.error("Failed to send financial alert emails for chef %s: %s", chef_id, exc)
