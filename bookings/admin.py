from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Booking, BookingFlight, Passenger, BookingPayment

MODEL_LABELS = {
    Booking: ("booking ve bay", "Booking ve bay"),
    BookingFlight: ("chang bay trong booking", "Chang bay trong booking"),
    Passenger: ("hanh khach", "Hanh khach"),
    BookingPayment: ("thanh toan ve bay", "Thanh toan ve bay"),
}
for model, (singular, plural) in MODEL_LABELS.items():
    model._meta.verbose_name = singular
    model._meta.verbose_name_plural = plural


class PassengerInline(admin.TabularInline):
    """Inline for managing passengers within a booking"""
    model = Passenger
    extra = 1
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'title', 'first_name', 'middle_name', 'last_name', 
        'date_of_birth', 'passenger_type',
        'passport_number', 'passport_country', 'passport_expiry',
        'meal_preference', 'seat_preference', 'assigned_seat'
    )


class BookingFlightInline(admin.TabularInline):
    model = BookingFlight
    extra = 0
    fields = ('segment_order', 'flight', 'cabin_class', 'base_price')


class BookingPaymentInline(admin.StackedInline):
    """Inline for payment information"""
    model = BookingPayment
    extra = 0
    readonly_fields = ('created_at', 'processed_at')
    fieldsets = (
        ('Payment Details', {
            'fields': ('amount', 'currency', 'payment_method', 'status')
        }),
        ('Transaction Info', {
            'fields': ('transaction_id', 'gateway_reference', 'payment_gateway', 'card_last_four', 'card_type'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )




@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model"""
    
    list_display = [
        'booking_reference', 
        'user_link',
        'flight_info',
        'cabin_class',
        'passenger_count',
        'total_price',
        'status_badge',
        'payment_status_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'payment_status',
        'cabin_class',
        'payment_method',
        'created_at',
        'flight__airline',
        'flight__origin',
        'flight__destination'
    ]
    
    search_fields = [
        'booking_reference',
        'user__email',
        'user__first_name',
        'user__last_name',
        'contact_email',
        'flight__flight_number',
        'payment_reference'
    ]
    
    readonly_fields = [
        'booking_reference', 
        'uuid',
        'created_at', 
        'updated_at', 
        'confirmed_at', 
        'cancelled_at',
        'passenger_count'
    ]
    
    inlines = [BookingFlightInline, PassengerInline, BookingPaymentInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'uuid', 'user', 'flight', 'cabin_class')
        }),
        ('Pricing', {
            'fields': ('base_price', 'taxes_and_fees', 'total_price', 'currency')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'payment_method', 'payment_reference')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Link to user admin page"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def flight_info(self, obj):
        """Display flight information"""
        if obj.flight:
            return f"{obj.flight.flight_number} ({obj.flight.origin} → {obj.flight.destination})"
        return '-'
    flight_info.short_description = 'Flight'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'cancelled': '#dc3545',
            'completed': '#6f42c1',
            'refunded': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#17a2b8',
            'refund_pending': '#fd7e14',
            'cancelled': '#dc3545',
            'skipped': '#6c757d'
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.payment_status.title()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'flight', 'flight__airline'
        ).prefetch_related('passengers')

    def get_model_perms(self, request):
        return {}


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    """Admin interface for Passenger model"""
    
    list_display = [
        'display_name',
        'booking_reference',
        'passenger_type',
        'age_at_travel',
        'passport_number',
        'assigned_seat',
        'meal_preference',
        'created_at'
    ]
    
    list_filter = [
        'passenger_type',
        'title',
        'meal_preference',
        'seat_preference',
        'created_at',
        'booking__status'
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'passport_number',
        'national_id',
        'booking__booking_reference'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'age_at_travel']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('title', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'passenger_type')
        }),
        ('Travel Documents', {
            'fields': ('passport_number', 'passport_country', 'passport_expiry', 'national_id')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Preferences & Assignment', {
            'fields': ('meal_preference', 'seat_preference', 'assigned_seat', 'special_assistance')
        }),
        ('Booking', {
            'fields': ('booking',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'age_at_travel'),
            'classes': ('collapse',)
        }),
    )
    
    def booking_reference(self, obj):
        """Display booking reference with link"""
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
            return format_html('<a href="{}">{}</a>', url, obj.booking.booking_reference)
        return '-'
    booking_reference.short_description = 'Booking'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking')

    def get_model_perms(self, request):
        return {}


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    """Admin interface for BookingPayment model"""
    
    list_display = [
        'booking_reference',
        'amount',
        'currency',
        'payment_method',
        'status_badge',
        'transaction_id',
        'processed_at',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'payment_method',
        'currency',
        'created_at',
        'processed_at'
    ]
    
    search_fields = [
        'booking__booking_reference',
        'transaction_id',
        'gateway_reference',
        'booking__user__email'
    ]
    
    readonly_fields = [
        'created_at', 
        'processed_at'
    ]
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'amount', 'currency', 'payment_method', 'status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_reference', 'payment_gateway', 'card_last_four', 'card_type', 'failure_reason', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def booking_reference(self, obj):
        """Display booking reference with link"""
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
            return format_html('<a href="{}">{}</a>', url, obj.booking.booking_reference)
        return '-'
    booking_reference.short_description = 'Booking'
    
    def status_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking')

    def get_model_perms(self, request):
        return {}






# Customize admin site header and title
admin.site.site_header = "Vietnam Travel Administration"
admin.site.site_title = "Vietnam Travel Admin"
admin.site.index_title = "Quan tri he thong du lich Viet Nam"
