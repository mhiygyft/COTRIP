from django.contrib import admin

from .models import PaymentTransaction

PaymentTransaction._meta.verbose_name = "giao dich thanh toan"
PaymentTransaction._meta.verbose_name_plural = "Giao dich thanh toan"


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "short_id", "user", "booking_label", "booking_type", "object_id",
        "amount", "currency", "method", "status", "created_at",
    )
    list_filter = ("status", "method", "booking_type", "currency", "created_at")
    search_fields = (
        "id", "user__email", "booking__booking_reference",
        "booking_type", "provider_reference",
    )
    readonly_fields = ("id", "created_at", "updated_at")

    def short_id(self, obj):
        return str(obj.id)[:8]
    short_id.short_description = "Transaction"

    def booking_label(self, obj):
        if obj.booking:
            return obj.booking.booking_reference
        if obj.booking_type and obj.object_id:
            return f"{obj.booking_type.upper()}-{obj.object_id}"
        return "-"
    booking_label.short_description = "Booking"

    def get_model_perms(self, request):
        return {}
