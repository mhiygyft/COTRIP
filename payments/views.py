from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from activities.models import ActivityBooking
from bookings.models import Booking
from hotels.models import HotelReservation, RoomAvailability
from packages.models import PackageBooking
from .models import PaymentTransaction


BOOKING_MODELS = {
    "flight": Booking,
    "hotel": HotelReservation,
    "package": PackageBooking,
    "activity": ActivityBooking,
}


def _get_customer_booking_or_404(user, booking_type, object_id):
    model = BOOKING_MODELS.get(booking_type)
    if not model:
        raise Http404("Booking type is not supported")
    return get_object_or_404(model, id=object_id, user=user)


def _booking_label(booking_type, booking):
    if booking_type == "flight":
        return f"FLT-{booking.booking_reference} - {booking.flight.flight_code}"
    if booking_type == "hotel":
        return f"HTL-{booking.id} - {booking.room_type.hotel.name}"
    if booking_type == "package":
        return f"PKG-{booking.id} - {booking.package.title}"
    if booking_type == "activity":
        return f"ACT-{booking.id} - {booking.activity.title}"
    return f"Booking {booking.id}"


@login_required
def payment_history(request):
    transactions = PaymentTransaction.objects.filter(user=request.user).select_related("booking")
    return render(request, "payments/history.html", {
        "transactions": transactions,
        "page_title": "Payment History",
    })


@login_required
def checkout(request, booking_type, object_id):
    booking = _get_customer_booking_or_404(request.user, booking_type, object_id)
    if booking.status == "cancelled" or booking.payment_status in {"completed", "cancelled", "refunded", "refund_pending"}:
        messages.info(request, "Booking nay da duoc xu ly thanh toan.")
        return redirect("customer_dashboard")
    if booking.status != "pending" or booking.payment_status != "pending":
        messages.error(request, "Booking nay khong o trang thai cho thanh toan.")
        return redirect("customer_dashboard")

    if request.method == "POST":
        method = request.POST.get("payment_method", "manual")
        if method not in {"card", "paypal", "bank_transfer", "manual"}:
            method = "manual"

        PaymentTransaction.objects.create(
            user=request.user,
            booking=booking if booking_type == "flight" else None,
            amount=booking.total_price,
            currency=getattr(booking, "currency", "USD"),
            method=method,
            status="completed",
            booking_type=booking_type,
            object_id=booking.id,
            metadata={"label": _booking_label(booking_type, booking)},
        )
        booking.payment_status = "completed"
        booking.status = "pending"
        booking.save(update_fields=["payment_status", "status", "updated_at"])
        messages.success(request, "Thanh toan thanh cong. Booking cua ban dang cho admin xac nhan.")
        return redirect("customer_dashboard")

    return render(request, "payments/checkout.html", {
        "booking": booking,
        "booking_type": booking_type,
        "booking_label": _booking_label(booking_type, booking),
        "amount": booking.total_price,
        "page_title": "Thanh toan",
    })


@login_required
def cancel_pending_booking(request, booking_type, object_id):
    booking = _get_customer_booking_or_404(request.user, booking_type, object_id)
    if request.method != "POST":
        return redirect("customer_dashboard")

    if booking.status != "pending" or booking.payment_status != "pending":
        messages.error(request, "Chi booking dang cho thanh toan moi co the huy tu tai khoan khach hang.")
        return redirect("customer_dashboard")

    with transaction.atomic():
        booking.status = "cancelled"
        booking.payment_status = "cancelled"
        update_fields = ["status", "payment_status", "updated_at"]
        if booking_type == "flight":
            booking.cancelled_at = timezone.now()
            update_fields.append("cancelled_at")
        booking.save(update_fields=update_fields)

        if booking_type == "hotel":
            availability, _ = RoomAvailability.objects.get_or_create(
                room_type=booking.room_type,
                date=booking.stay_date,
                defaults={"available_rooms": 0, "price": booking.price_per_room},
            )
            availability.available_rooms += booking.rooms
            availability.save(update_fields=["available_rooms", "updated_at"])

    messages.success(request, f"Da huy {_booking_label(booking_type, booking)}.")
    return redirect("customer_dashboard")
