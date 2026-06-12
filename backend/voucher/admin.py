from django.contrib import admin
from .models import Voucher, AppliedVoucher
from utils.enums import VoucherReservationStatus


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name", 
        "voucher_type",
        "discount_value",
        "start_date",
        "end_date",
        "active_usage_count",
        "usage_limit",
        "is_active",
    ]
    list_filter = ["voucher_type", "is_active", "start_date", "end_date"]
    search_fields = ["code", "name"]
    readonly_fields = ["active_usage_count", "created_at", "updated_at"]
    
    def active_usage_count(self, obj):
        """Count RESERVED + USED applications"""
        return obj.appliedvoucher_set.filter(
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).count()
    active_usage_count.short_description = "Active Usage"


@admin.register(AppliedVoucher)
class AppliedVoucherAdmin(admin.ModelAdmin):
    list_display = ["voucher", "user", "order", "checkout", "voucher_type", "status", "discount_amount", "created_at"]
    list_filter = ["voucher_type", "status", "created_at"]
    search_fields = ["voucher__code", "user__email", "order__uid", "checkout__uid"]
    readonly_fields = ["created_at", "updated_at"]
