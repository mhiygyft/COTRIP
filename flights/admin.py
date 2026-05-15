from django.contrib import admin
from django.db.models import Count, Q

from .models import Aircraft, Airline, Airport, BaggageAllowance, Country, Flight, Route

MODEL_LABELS = {
    Country: ("quoc gia bay", "Quoc gia bay"),
    Airport: ("san bay", "San bay"),
    Airline: ("hang bay", "Hang bay"),
    Aircraft: ("may bay", "May bay"),
    Route: ("tuyen bay", "Tuyen bay"),
    Flight: ("chuyen bay", "Chuyen bay"),
    BaggageAllowance: ("hanh ly", "Hanh ly"),
}
for model, (singular, plural) in MODEL_LABELS.items():
    model._meta.verbose_name = singular
    model._meta.verbose_name_plural = plural


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "iso_code", "code", "currency", "is_active"]
    list_filter = ["is_active", "currency"]
    search_fields = ["name", "iso_code", "code"]


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ["iata_code", "name", "city", "country", "is_active", "is_popular"]
    list_filter = ["is_active", "is_popular", "country"]
    search_fields = ["name", "iata_code", "city"]
    list_editable = ["is_active", "is_popular"]


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ["iata_code", "name", "country", "is_active", "is_low_cost", "average_rating"]
    list_filter = ["is_active", "is_low_cost", "country"]
    search_fields = ["name", "iata_code", "icao_code"]
    list_editable = ["is_active"]


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ["manufacturer", "model", "variant", "total_seats", "is_active"]
    list_filter = ["is_active", "manufacturer"]
    search_fields = ["manufacturer", "model", "variant"]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["origin", "destination", "distance_km", "typical_duration_minutes", "base_price", "is_popular"]
    list_filter = ["is_popular", "is_domestic"]
    search_fields = ["origin__iata_code", "destination__iata_code", "origin__city", "destination__city"]


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        "flight_code", "airline", "origin", "destination", "departure_time",
        "economy_price", "economy_available", "booking_count_display",
        "paid_count_display", "status", "is_active",
    ]
    list_filter = ["is_active", "status", "airline", "origin", "destination", "departure_time"]
    search_fields = ["flight_number", "airline__name", "origin__iata_code", "destination__iata_code"]
    list_editable = ["economy_available", "status", "is_active"]
    date_hierarchy = "departure_time"
    autocomplete_fields = ["airline", "aircraft", "origin", "destination", "route"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("airline", "origin", "destination", "aircraft", "route")
            .annotate(
                booking_total=Count("bookings", distinct=True),
                paid_total=Count("bookings", filter=Q(bookings__payment_status="completed"), distinct=True),
            )
        )

    def booking_count_display(self, obj):
        return obj.booking_total
    booking_count_display.short_description = "Booking"
    booking_count_display.admin_order_field = "booking_total"

    def paid_count_display(self, obj):
        return obj.paid_total
    paid_count_display.short_description = "Da thanh toan"
    paid_count_display.admin_order_field = "paid_total"


@admin.register(BaggageAllowance)
class BaggageAllowanceAdmin(admin.ModelAdmin):
    list_display = ["airline", "fare_type", "carryon_pieces", "checked_pieces_included", "checked_weight_kg"]
    list_filter = ["fare_type", "airline"]
    search_fields = ["airline__name", "fare_type"]
