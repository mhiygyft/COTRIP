from django.contrib import admin

from .models import TransportBooking, TransportProvider, TransportRoute, TransportStation, TransportTrip


@admin.register(TransportProvider)
class TransportProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_type', 'code', 'rating', 'is_active')
    list_filter = ('provider_type', 'is_active')
    search_fields = ('name', 'code')


@admin.register(TransportStation)
class TransportStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'station_type', 'is_popular', 'is_active')
    list_filter = ('station_type', 'city', 'is_popular', 'is_active')
    search_fields = ('name', 'city', 'address')


@admin.register(TransportRoute)
class TransportRouteAdmin(admin.ModelAdmin):
    list_display = ('transport_type', 'origin', 'destination', 'distance_km', 'typical_duration_minutes', 'is_active')
    list_filter = ('transport_type', 'is_active')
    search_fields = ('origin__city', 'destination__city', 'origin__name', 'destination__name')


@admin.register(TransportTrip)
class TransportTripAdmin(admin.ModelAdmin):
    list_display = ('trip_code', 'provider', 'route', 'departure_time', 'seat_class', 'base_price', 'available_seats', 'status')
    list_filter = ('route__transport_type', 'provider', 'seat_class', 'status', 'departure_time')
    search_fields = ('trip_code', 'provider__name', 'route__origin__city', 'route__destination__city')
    date_hierarchy = 'departure_time'


@admin.register(TransportBooking)
class TransportBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'trip', 'passengers', 'total_price', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'trip__route__transport_type', 'created_at')
    search_fields = ('booking_reference', 'contact_name', 'contact_phone', 'contact_email', 'user__email')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
