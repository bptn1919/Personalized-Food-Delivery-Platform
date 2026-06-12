from report.models import ChefReport, ChefSuspension, ChefWarning
from utils.enums import SuspensionStatusEnum


def get_reports_for_chef(chef_id: int, status=None):
    qs = ChefReport.objects.filter(chef_id=chef_id, deleted=False).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    return qs


def get_reports_by_customer(reporter_id: int):
    return ChefReport.objects.filter(reporter_id=reporter_id, deleted=False).order_by("-created_at")


def get_all_reports(chef_id=None, status=None, category=None):
    qs = ChefReport.objects.filter(deleted=False).select_related("reporter", "chef", "dish").order_by("-created_at")
    if chef_id:
        qs = qs.filter(chef_id=chef_id)
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    return qs


def get_active_suspension(chef_id: int):
    return (
        ChefSuspension.objects.filter(
            chef_id=chef_id,
            status__in=[SuspensionStatusEnum.ACTIVE, SuspensionStatusEnum.APPEALING],
        )
        .select_related("locked_dish")
        .order_by("-created_at")
        .first()
    )


def get_suspension_history(chef_id: int):
    return (
        ChefSuspension.objects.filter(chef_id=chef_id)
        .select_related("locked_dish", "lifted_by")
        .order_by("-created_at")
    )


def get_all_suspensions(chef_id=None, status=None):
    qs = ChefSuspension.objects.select_related("chef", "locked_dish").order_by("-created_at")
    if chef_id:
        qs = qs.filter(chef_id=chef_id)
    if status:
        qs = qs.filter(status=status)
    return qs
