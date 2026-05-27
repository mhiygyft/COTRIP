from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from activities.models import Activity, ActivityBooking
from bookings.models import Booking, BookingFlight, BookingPayment
from flights.models import Flight, Route
from hotels.models import Hotel, HotelReservation, RoomAvailability, RoomType
from packages.models import PackageBooking, PackageComponent, TravelPackage
from payments.models import PaymentTransaction


VND_RATE = Decimal("25000")
VND_THRESHOLD = Decimal("10000")


class Command(BaseCommand):
    help = "Convert existing demo prices from USD-like values to VND and set currencies to VND."

    def handle(self, *args, **options):
        counters = {}
        with transaction.atomic():
            counters["hotels"] = self.convert_hotels()
            counters["flights"] = self.convert_flights()
            counters["bookings"] = self.convert_flight_bookings()
            counters["activities"] = self.convert_activities()
            counters["packages"] = self.convert_packages()
            counters["payments"] = self.convert_payments()

        for key, value in counters.items():
            self.stdout.write(f"{key}: {value} rows updated")
        self.stdout.write(self.style.SUCCESS("All price data is now normalized to VND."))

    def to_vnd(self, value):
        if value is None:
            return None
        amount = Decimal(value)
        if amount == 0:
            return amount
        if amount < VND_THRESHOLD:
            return (amount * VND_RATE).quantize(Decimal("1"))
        return amount

    def convert_hotels(self):
        updated = 0
        for hotel in Hotel.objects.all():
            hotel.price_from = self.to_vnd(hotel.price_from)
            hotel.currency = "VND"
            hotel.save(update_fields=["price_from", "currency"])
            updated += 1
        for room in RoomType.objects.all():
            room.base_price = self.to_vnd(room.base_price)
            room.save(update_fields=["base_price"])
            updated += 1
        for availability in RoomAvailability.objects.all():
            availability.price = self.to_vnd(availability.price)
            availability.save(update_fields=["price"])
            updated += 1
        for reservation in HotelReservation.objects.all():
            reservation.price_per_room = self.to_vnd(reservation.price_per_room)
            reservation.total_price = self.to_vnd(reservation.total_price)
            reservation.currency = "VND"
            reservation.save(update_fields=["price_per_room", "total_price", "currency"])
            updated += 1
        return updated

    def convert_flights(self):
        updated = 0
        for route in Route.objects.all():
            route.base_price = self.to_vnd(route.base_price)
            route.save(update_fields=["base_price"])
            updated += 1
        for flight in Flight.objects.all():
            flight.economy_price = self.to_vnd(flight.economy_price)
            flight.premium_economy_price = self.to_vnd(flight.premium_economy_price)
            flight.business_price = self.to_vnd(flight.business_price)
            flight.first_class_price = self.to_vnd(flight.first_class_price)
            flight.save(update_fields=[
                "economy_price",
                "premium_economy_price",
                "business_price",
                "first_class_price",
            ])
            updated += 1
        return updated

    def convert_flight_bookings(self):
        updated = 0
        for booking in Booking.objects.all():
            booking.base_price = self.to_vnd(booking.base_price)
            booking.taxes_and_fees = self.to_vnd(booking.taxes_and_fees)
            booking.total_price = self.to_vnd(booking.total_price)
            booking.currency = "VND"
            booking.save(update_fields=["base_price", "taxes_and_fees", "total_price", "currency"])
            updated += 1
        for segment in BookingFlight.objects.all():
            segment.base_price = self.to_vnd(segment.base_price)
            segment.save(update_fields=["base_price"])
            updated += 1
        for payment in BookingPayment.objects.all():
            payment.amount = self.to_vnd(payment.amount)
            payment.currency = "VND"
            payment.save(update_fields=["amount", "currency"])
            updated += 1
        return updated

    def convert_activities(self):
        updated = 0
        for activity in Activity.objects.all():
            activity.price_adult = self.to_vnd(activity.price_adult)
            activity.price_child = self.to_vnd(activity.price_child)
            activity.save(update_fields=["price_adult", "price_child"])
            updated += 1
        for booking in ActivityBooking.objects.all():
            booking.adult_price = self.to_vnd(booking.adult_price)
            booking.child_price = self.to_vnd(booking.child_price)
            booking.total_price = self.to_vnd(booking.total_price)
            booking.save(update_fields=["adult_price", "child_price", "total_price"])
            updated += 1
        return updated

    def convert_packages(self):
        updated = 0
        for package in TravelPackage.objects.all():
            package.base_price_per_person = self.to_vnd(package.base_price_per_person)
            package.child_price = self.to_vnd(package.child_price)
            package.single_supplement = self.to_vnd(package.single_supplement)
            package.save(update_fields=["base_price_per_person", "child_price", "single_supplement"])
            updated += 1
        for component in PackageComponent.objects.exclude(price_override__isnull=True):
            component.price_override = self.to_vnd(component.price_override)
            component.save(update_fields=["price_override"])
            updated += 1
        for booking in PackageBooking.objects.all():
            booking.base_price = self.to_vnd(booking.base_price)
            booking.additional_services_cost = self.to_vnd(booking.additional_services_cost)
            booking.total_price = self.to_vnd(booking.total_price)
            booking.save(update_fields=["base_price", "additional_services_cost", "total_price"])
            updated += 1
        return updated

    def convert_payments(self):
        updated = 0
        for transaction in PaymentTransaction.objects.all():
            transaction.amount = self.to_vnd(transaction.amount)
            transaction.currency = "VND"
            transaction.save(update_fields=["amount", "currency"])
            updated += 1
        return updated
