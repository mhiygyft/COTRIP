from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from activities.models import ActivityBooking
from bookings.models import Booking
from flights.models import FlightSearch, SavedFlight
from hotels.models import HotelReservation
from packages.models import PackageBooking

from .forms import UserProfileForm


def customer_status_label(status, payment_status):
    if payment_status == "pending":
        return "Cho thanh toan"
    if payment_status == "refund_pending":
        return "Cho hoan tien"
    if status == "pending" and payment_status in {"completed", "skipped"}:
        return "Cho admin xac nhan"
    if status == "cancelled":
        return "Da bi huy"
    if status == "refunded":
        return "Da hoan tien"
    if status == "confirmed":
        return "Da xac nhan"
    if status == "completed":
        return "Hoan tat"
    return status


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
    for booking in flight_bookings[:5]:
        recent_items.append({
            "type": "Flight",
            "code": booking.booking_reference,
            "title": f"{booking.flight.flight_code}: {booking.flight.origin.city} - {booking.flight.destination.city}",
            "date": booking.flight.departure_time.date(),
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        })
    for booking in hotel_reservations[:5]:
        recent_items.append({
            "type": "Hotel",
            "code": f"HTL-{booking.id}",
            "title": f"{booking.room_type.hotel.name} - {booking.room_type.name}",
            "date": booking.stay_date,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        })
    for booking in package_bookings[:5]:
        recent_items.append({
            "type": "Tour",
            "code": f"PKG-{booking.id}",
            "title": booking.package.title,
            "date": booking.departure_date,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        })
    for booking in activity_bookings[:5]:
        recent_items.append({
            "type": "Activity",
            "code": f"ACT-{booking.id}",
            "title": booking.activity.title,
            "date": booking.booking_date,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "status_label": customer_status_label(booking.status, booking.payment_status),
            "total": booking.total_price,
        })
    recent_items = sorted(recent_items, key=lambda item: item["date"], reverse=True)[:10]

    total_spent = (
        sum(flight_bookings.filter(payment_status__in=["completed", "skipped"]).values_list("total_price", flat=True))
        + sum(hotel_reservations.filter(payment_status="completed").values_list("total_price", flat=True))
        + sum(package_bookings.filter(payment_status="completed").values_list("total_price", flat=True))
        + sum(activity_bookings.filter(payment_status="completed").values_list("total_price", flat=True))
    )

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
