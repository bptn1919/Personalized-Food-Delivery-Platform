from typing import List
from uuid import UUID

from ninja import Query

from exceptions.report import (
    AppealAlreadySubmitted,
    AppealNotAllowed,
    ReportAlreadyExists,
    ReportEvidenceRequired,
    ReportNotFound,
    ReportOrderNotCompleted,
    ReportOrderNotOwned,
    ReportRateLimitExceeded,
    ReportTargetNotFound,
    ReportTargetRequired,
    SuspensionNotFound,
)
from utils.exceptions import PermissionDeniedError
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, patch, post
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from utils.enums import UserTypeEnum
from utils.permissions.decorators import require_group

from .queries import (
    get_active_suspension,
    get_all_reports,
    get_all_suspensions,
    get_reports_by_customer,
    get_reports_for_chef,
    get_suspension_history,
)
from .schemas.requests import (
    CreateReportSchema,
    DismissReportSchema,
    FilterReportSchema,
    FilterSuspensionSchema,
    LiftSuspensionSchema,
    ManualSuspensionSchema,
    SubmitAppealSchema,
)
from .schemas.responses import (
    ChefSuspensionStatusSchema,
    ReportSchema,
    SuspensionSchema,
)
from .services.report_service import ReportService


def _require_customer_or_chef(request: AuthenticatedRequest):
    if not request.user.groups.filter(
        name__in=[UserTypeEnum.CUSTOMER, UserTypeEnum.CHEF]
    ).exists():
        raise PermissionDeniedError()


def _suspension_to_schema(s) -> dict:
    return {
        "uid": s.uid,
        "chef_id": s.chef_id,
        "suspension_type": s.suspension_type,
        "locked_dish_uid": s.locked_dish.uid if s.locked_dish else None,
        "reason": s.reason,
        "trigger_source": s.trigger_source,
        "trigger_data": s.trigger_data,
        "status": s.status,
        "appeal_text": s.appeal_text,
        "appealed_at": s.appealed_at,
        "lift_note": s.lift_note,
        "lifted_at": s.lifted_at,
        "created_at": s.created_at,
    }


# ── Customer endpoints ────────────────────────────────────────────────────────

@api(prefix_or_class="report", tags=["Report - Customer"], auth=AuthBear())
class CustomerReportController(Controller):

    @post(
        "",
        auth=True,
        response=ReportSchema,
        exceptions=(
            ReportAlreadyExists,
            ReportEvidenceRequired,
            ReportOrderNotCompleted,
            ReportOrderNotOwned,
            ReportRateLimitExceeded,
            ReportTargetNotFound,
            ReportTargetRequired,
        ),
    )
    def create_report(self, request: AuthenticatedRequest, body: CreateReportSchema):
        """Gửi phản ánh về chef (có thể kèm đơn hoặc không)."""
        _require_customer_or_chef(request)
        report, chef_id, dish = ReportService.create_report(
            reporter=request.user,
            order_uid=body.order_uid,
            dish_uid=body.dish_uid,
            chef_id=body.chef_id,
            category=body.category,
            description=body.description,
            evidence_uid=body.evidence_uid,
        )
        # Chạy Gemini + analyze ngoài transaction
        ReportService.run_post_create(report, chef_id, dish)
        return ReportSchema(**ReportSchema.from_orm_dish_uid(report))

    @get("/my-reports", auth=True, response=List[ReportSchema])
    def my_reports(self, request: AuthenticatedRequest):
        """Danh sách phản ánh tôi đã gửi."""
        _require_customer_or_chef(request)
        reports = get_reports_by_customer(request.user.id)
        return [ReportSchema(**ReportSchema.from_orm_dish_uid(r)) for r in reports]


# ── Chef endpoints ────────────────────────────────────────────────────────────

@api(prefix_or_class="report", tags=["Report - Chef"], auth=AuthBear())
class ChefReportController(Controller):

    @get("", auth=True, response=List[ReportSchema])
    @require_group(UserTypeEnum.CHEF)
    def my_reports_as_chef(self, request: AuthenticatedRequest):
        """Danh sách phản ánh từ khách về bếp của tôi."""
        reports = get_reports_for_chef(request.user.id)
        return [ReportSchema(**ReportSchema.from_orm_dish_uid(r)) for r in reports]

    @get("/suspension/current", auth=True, response=ChefSuspensionStatusSchema)
    @require_group(UserTypeEnum.CHEF)
    def current_suspension(self, request: AuthenticatedRequest):
        """Trạng thái khóa hiện tại của chef."""
        profile = request.user.chef_profile
        suspension = get_active_suspension(request.user.id)
        return {
            "is_accepting_orders": profile.is_accepting_orders,
            "suspension_level": profile.suspension_level,
            "active_suspension": _suspension_to_schema(suspension) if suspension else None,
        }

    @get("/suspension/history", auth=True, response=List[SuspensionSchema])
    @require_group(UserTypeEnum.CHEF)
    def suspension_history(self, request: AuthenticatedRequest):
        """Lịch sử khóa của chef."""
        suspensions = get_suspension_history(request.user.id)
        return [SuspensionSchema(**_suspension_to_schema(s)) for s in suspensions]

    @post(
        "/suspension/{suspension_uid}/appeal",
        auth=True,
        response=SuspensionSchema,
        exceptions=(SuspensionNotFound, AppealAlreadySubmitted, AppealNotAllowed),
    )
    @require_group(UserTypeEnum.CHEF)
    def submit_appeal(
        self,
        request: AuthenticatedRequest,
        suspension_uid: UUID,
        body: SubmitAppealSchema,
    ):
        """Gửi giải trình để xem xét mở khóa."""
        suspension = ReportService.submit_appeal(
            chef=request.user,
            suspension_uid=suspension_uid,
            appeal_text=body.appeal_text,
        )
        return SuspensionSchema(**_suspension_to_schema(suspension))


# ── Admin endpoints ───────────────────────────────────────────────────────────

@api(prefix_or_class="admin/reports", tags=["Report - Admin"], auth=AuthBear())
class AdminReportController(Controller):

    @get("", auth=True, response=List[ReportSchema], paginate=True, exceptions=(PermissionDeniedError,))
    @paginate
    @require_group(UserTypeEnum.ADMIN)
    def list_reports(
        self,
        request: AuthenticatedRequest,
        filter: FilterReportSchema = Query(...),
    ):
        """Danh sách toàn bộ report — filter theo chef, status, category."""
        return get_all_reports(
            chef_id=filter.chef_id,
            status=filter.status,
            category=filter.category,
        )

    @patch(
        "/{report_uid}/dismiss",
        auth=True,
        response=ReportSchema,
        exceptions=(PermissionDeniedError, ReportNotFound),
    )
    @require_group(UserTypeEnum.ADMIN)
    def dismiss_report(
        self,
        request: AuthenticatedRequest,
        report_uid: UUID,
        body: DismissReportSchema,
    ):
        """Bác bỏ một report — không tính vào metrics."""
        report = ReportService.dismiss_report(
            admin_user=request.user,
            report_uid=report_uid,
            admin_note=body.admin_note,
        )
        return ReportSchema(**ReportSchema.from_orm_dish_uid(report))

    @patch(
        "/{report_uid}/confirm",
        auth=True,
        response=ReportSchema,
        exceptions=(PermissionDeniedError, ReportNotFound),
    )
    @require_group(UserTypeEnum.ADMIN)
    def confirm_report(
        self,
        request: AuthenticatedRequest,
        report_uid: UUID,
    ):
        """Admin xác nhận report → weight=5.0 → re-analyze."""
        report = ReportService.admin_confirm_report(
            admin_user=request.user,
            report_uid=report_uid,
        )
        return ReportSchema(**ReportSchema.from_orm_dish_uid(report))

    @get("/suspensions", auth=True, response=List[SuspensionSchema], paginate=True, exceptions=(PermissionDeniedError,))
    @paginate
    @require_group(UserTypeEnum.ADMIN)
    def list_suspensions(
        self,
        request: AuthenticatedRequest,
        filter: FilterSuspensionSchema = Query(...),
    ):
        """Danh sách toàn bộ lệnh khóa."""
        return get_all_suspensions(chef_id=filter.chef_id, status=filter.status)

    @post(
        "/suspensions/manual",
        auth=True,
        response=SuspensionSchema,
        exceptions=(PermissionDeniedError,),
    )
    @require_group(UserTypeEnum.ADMIN)
    def manual_suspension(self, request: AuthenticatedRequest, body: ManualSuspensionSchema):
        """Admin khóa thủ công (bypass threshold)."""
        suspension = ReportService.manual_suspension(
            admin_user=request.user,
            chef_id=body.chef_id,
            suspension_type=body.suspension_type,
            dish_uid=body.dish_uid,
            reason=body.reason,
        )
        return SuspensionSchema(**_suspension_to_schema(suspension))

    @patch(
        "/suspensions/{suspension_uid}/lift",
        auth=True,
        response=SuspensionSchema,
        exceptions=(PermissionDeniedError, SuspensionNotFound, AppealNotAllowed),
    )
    @require_group(UserTypeEnum.ADMIN)
    def lift_suspension(
        self,
        request: AuthenticatedRequest,
        suspension_uid: UUID,
        body: LiftSuspensionSchema,
    ):
        """Mở khóa — có thể thêm ghi chú."""
        suspension = ReportService.lift_suspension(
            admin_user=request.user,
            suspension_uid=suspension_uid,
            lift_note=body.lift_note,
        )
        return SuspensionSchema(**_suspension_to_schema(suspension))

    @patch(
        "/suspensions/{suspension_uid}/reject-appeal",
        auth=True,
        response=SuspensionSchema,
        exceptions=(PermissionDeniedError, SuspensionNotFound, AppealNotAllowed),
    )
    @require_group(UserTypeEnum.ADMIN)
    def reject_appeal(
        self,
        request: AuthenticatedRequest,
        suspension_uid: UUID,
        body: LiftSuspensionSchema,
    ):
        """Bác bỏ giải trình của chef — giữ trạng thái ACTIVE."""
        from report.models import ChefSuspension
        from utils.enums import SuspensionStatusEnum

        try:
            suspension = ChefSuspension.objects.get(uid=suspension_uid)
        except ChefSuspension.DoesNotExist:
            raise SuspensionNotFound()

        if suspension.status != SuspensionStatusEnum.APPEALING:
            raise AppealNotAllowed()

        suspension.status = SuspensionStatusEnum.REJECTED
        suspension.lift_note = body.lift_note
        suspension.lifted_by = request.user
        from django.utils import timezone
        suspension.lifted_at = timezone.now()
        suspension.save(update_fields=["status", "lift_note", "lifted_by", "lifted_at"])
        return SuspensionSchema(**_suspension_to_schema(suspension))
