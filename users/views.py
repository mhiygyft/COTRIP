import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from activities.models import ActivityBooking
from bookings.models import Booking
from flights.models import FlightSearch, SavedFlight
from hotels.models import HotelReservation, Itinerary
from packages.models import PackageBooking

from .forms import UserProfileForm


def normalize_location(value):
    value = (value or "").replace("Đ", "D").replace("đ", "d").lower()
    return "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )


def customer_status_label(status, payment_status):
    if payment_status == "pending":
        return "Chờ thanh toán"
    if payment_status == "refund_pending":
        return "Chờ hoàn tiền"
    if status == "pending" and payment_status in {"completed", "skipped"}:
        return "Chờ admin xác nhận"
    if status == "cancelled":
        return "Đã bị hủy"
    if status == "refunded":
        return "Đã hoàn tiền"
    if status == "confirmed":
        return "Đã xác nhận"
    if status == "completed":
        return "Hoàn tất"
    return status


def customer_booking_actions(booking_type, booking):
    can_pay = booking.status == "pending" and booking.payment_status == "pending"
    can_cancel = booking.status == "pending" and booking.payment_status == "pending"
    return {
        "can_pay": can_pay,
        "can_cancel": can_cancel,
        "payment_url": reverse("payments:checkout", kwargs={"booking_type": booking_type, "object_id": booking.id}) if can_pay else "",
        "cancel_url": reverse("payments:cancel_pending", kwargs={"booking_type": booking_type, "object_id": booking.id}) if can_cancel else "",
    }


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            next_url = request.GET.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("users:account_profile")
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        "form": form,
        "page_title": "My Profile",
    }
    return render(request, "users/profile.html", context)


@login_required
def dashboard(request):
    flight_bookings = Booking.objects.filter(user=request.user).select_related(
        "flight__airline", "flight__origin", "flight__destination"
    )
    hotel_reservations = HotelReservation.objects.filter(user=request.user).select_related(
        "room_type__hotel", "room_type__hotel__city"
    )
    package_bookings = PackageBooking.objects.filter(user=request.user).select_related("package")
    activity_bookings = ActivityBooking.objects.filter(user=request.user).select_related("activity")

    recent_items = []
    for booking in flight_bookings:
        item = {
            "type": "Flight",
            "code": booking.booking_reference,
            "title": f"{booking.flight.flight_code}: {booking.flight.origin.city} - {booking.flight.destination.city}",
            "image_url": "",
            "date": booking.flight.departure_time.date(),
            "created_at": booking.created_at,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        }
        item.update(customer_booking_actions("flight", booking))
        if not item["can_cancel"] and booking.is_cancellable:
            item["can_cancel"] = True
            item["cancel_url"] = reverse("bookings:cancel_booking", kwargs={"booking_reference": booking.booking_reference})
        recent_items.append(item)
    for booking in hotel_reservations:
        item = {
            "type": "Hotel",
            "code": f"HTL-{booking.id}",
            "title": f"{booking.room_type.hotel.name} - {booking.room_type.name}",
            "image_url": booking.room_type.hotel.primary_image_url,
            "date": booking.stay_date,
            "created_at": booking.created_at,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        }
        item.update(customer_booking_actions("hotel", booking))
        recent_items.append(item)
    for booking in package_bookings:
        item = {
            "type": "Tour",
            "code": f"PKG-{booking.id}",
            "title": booking.package.title,
            "image_url": booking.package.primary_image_url,
            "date": booking.departure_date,
            "created_at": booking.created_at,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        }
        item.update(customer_booking_actions("package", booking))
        recent_items.append(item)
    for booking in activity_bookings:
        item = {
            "type": "Activity",
            "code": f"ACT-{booking.id}",
            "title": booking.activity.title,
            "image_url": booking.activity.primary_image_url,
            "date": booking.booking_date,
            "created_at": booking.created_at,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        }
        item.update(customer_booking_actions("activity", booking))
        recent_items.append(item)
    recent_items = sorted(recent_items, key=lambda item: item["created_at"], reverse=True)

    total_spent = (
        sum(flight_bookings.filter(payment_status__in=["completed", "skipped"]).values_list("total_price", flat=True))
        + sum(hotel_reservations.filter(payment_status="completed").values_list("total_price", flat=True))
        + sum(package_bookings.filter(payment_status="completed").values_list("total_price", flat=True))
        + sum(activity_bookings.filter(payment_status="completed").values_list("total_price", flat=True))
    )
    itinerary_location = request.GET.get("itinerary_location", "").strip()
    suggested_itineraries = Itinerary.objects.filter(is_active=True).select_related(
        "city", "city__country"
    ).prefetch_related("stops")
    if itinerary_location:
        location_key = normalize_location(itinerary_location)
        suggested_itineraries = [
            itinerary for itinerary in suggested_itineraries
            if location_key in normalize_location(itinerary.city.name)
            or location_key in normalize_location(itinerary.city.country.name)
        ]
    elif request.user.city:
        user_city_key = normalize_location(request.user.city)
        city_itineraries = [
            itinerary for itinerary in suggested_itineraries
            if user_city_key in normalize_location(itinerary.city.name)
        ]
        suggested_itineraries = city_itineraries or suggested_itineraries

    context = {
        "flight_bookings": flight_bookings,
        "hotel_reservations": hotel_reservations,
        "package_bookings": package_bookings,
        "activity_bookings": activity_bookings,
        "recent_items": recent_items,
        "booking_total": (
            flight_bookings.count()
            + hotel_reservations.count()
            + package_bookings.count()
            + activity_bookings.count()
        ),
        "total_spent": total_spent,
        "saved_flights": SavedFlight.objects.filter(user=request.user).select_related("flight")[:5],
        "saved_searches": FlightSearch.objects.filter(user=request.user).order_by("-created_at")[:5],
        "itinerary_location": itinerary_location,
        "suggested_itineraries": suggested_itineraries[:4],
        "page_title": "Customer Dashboard",
    }
    return render(request, "users/dashboard.html", context)


@login_required
def saved_flights(request):
    context = {
        "saved_flights": SavedFlight.objects.filter(user=request.user).select_related(
            "flight",
            "flight__airline",
            "flight__origin",
            "flight__destination",
        ),
        "page_title": "Saved Flights",
    }
    return render(request, "users/saved_flights.html", context)

