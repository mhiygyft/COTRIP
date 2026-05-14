from django.contrib import admin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "booking", "amount", "currency", "method", "status", "created_at")
    list_filter = ("status", "method", "currency", "created_at")
    search_fields = ("id", "user__email", "booking__booking_reference", "provider_reference")
    readonly_fields = ("id", "created_at", "updated_at")
