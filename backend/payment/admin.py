from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('uid', 'checkout', 'payment_method', 'amount', 'current_status', 'gateway_transaction_id', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('uid', 'checkout__uid', 'payos_order_code')
    readonly_fields = ('uid', 'created_at')

    def current_status(self, obj):
        state = getattr(obj, "state", None)
        return state.status if state else None
    current_status.short_description = "status"

    def gateway_transaction_id(self, obj):
        state = getattr(obj, "state", None)
        return state.transaction_id if state else None
    gateway_transaction_id.short_description = "transaction_id"
