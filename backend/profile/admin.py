from django.contrib import admin
from django.utils import timezone
from .models import CustomerProfile, ChefProfile, CustomerAddress, ChefPaymentInfo


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'is_onboarded']
    search_fields = ['user__email', 'user__username']
    list_filter = ['is_onboarded']


@admin.register(ChefProfile)
class ChefProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'number_of_orders']
    search_fields = ['user__email', 'user__username']


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'district', 'selected']
    search_fields = ['user__email', 'city', 'district']
    list_filter = ['selected', 'city']


@admin.register(ChefPaymentInfo)
class ChefPaymentInfoAdmin(admin.ModelAdmin):
    list_display = ['user', 'bank_name', 'bank_code', 'masked_account_number', 'is_verified', 'created_at']
    search_fields = ['user__email', 'bank_account_name', 'bank_name']
    list_filter = ['is_verified', 'bank_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Bank Information', {
            'fields': ('bank_name', 'bank_code', 'bank_account_number', 'bank_account_name', 'bank_branch')
        }),
        ('Identity', {
            'fields': ('citizen_id', 'tax_code')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['verify_payment_info', 'unverify_payment_info']
    
    def masked_account_number(self, obj):
        """Display masked account number in list"""
        if obj.bank_account_number:
            return '*' * (len(obj.bank_account_number) - 4) + obj.bank_account_number[-4:]
        return '-'
    masked_account_number.short_description = 'Account Number'
    
    def verify_payment_info(self, request, queryset):
        """Action to verify selected payment info"""
        updated = queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f"{updated} payment info(s) verified successfully")
    verify_payment_info.short_description = "Verify selected payment info"
    
    def unverify_payment_info(self, request, queryset):
        """Action to unverify selected payment info"""
        updated = queryset.update(is_verified=False, verified_at=None)
        self.message_user(request, f"{updated} payment info(s) unverified")
    unverify_payment_info.short_description = "Unverify selected payment info"
