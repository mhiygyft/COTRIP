from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity, ActivityBooking
from bookings.models import Booking, BookingPayment
from flights.models import Flight
from hotels.models import Hotel, HotelReservation, RoomAvailability
from packages.models import PackageBooking, TravelPackage
from payments.models import PaymentTransaction


def _money(value):
    return value or Decimal("0")


def _daily_revenue(queryset, amount_field, start_date):
    rows = (
        queryset.filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum(amount_field))
        .order_by("day")
    )
    return {row["day"]: _money(row["total"]) for row in rows}


def _successful_flight_bookings():
    return Booking.objects.filter(status__in=["confirmed", "completed"], payment_status__in=["completed", "skipped"])


def _successful_package_bookings():
    return PackageBooking.objects.filter(status__in=["confirmed", "completed"], payment_status="completed")


def _successful_activity_bookings():
    return ActivityBooking.objects.filter(status__in=["confirmed", "completed"], payment_status="completed")


def _successful_hotel_reservations():
    return HotelReservation.objects.filter(status__in=["confirmed", "completed"], payment_status="completed")


@staff_member_required
def admin_dashboard(request):
    today = timezone.localdate()
    start_date = today - timezone.timedelta(days=6)
    User = get_user_model()

    flight_revenue = _money(_successful_flight_bookings().aggregate(total=Sum("total_price"))["total"])
    hotel_revenue = _money(_successful_hotel_reservations().aggregate(total=Sum("total_price"))["total"])
    package_revenue = _money(_successful_package_bookings().aggregate(total=Sum("total_price"))["total"])
    activity_revenue = _money(_successful_activity_bookings().aggregate(total=Sum("total_price"))["total"])

    flight_count = Booking.objects.count()
    hotel_count = HotelReservation.objects.count()
    package_count = PackageBooking.objects.count()
    activity_count = ActivityBooking.objects.count()
    total_bookings = flight_count + hotel_count + package_count + activity_count
    cancelled_count = (
        Booking.objects.filter(status__in=["cancelled", "refunded"]).count()
        + HotelReservation.objects.filter(status__in=["cancelled", "refunded"]).count()
        + PackageBooking.objects.filter(status__in=["cancelled", "refunded"]).count()
        + ActivityBooking.objects.filter(status__in=["cancelled", "refunded"]).count()
    )
    cancellation_rate = round((cancelled_count / total_bookings * 100), 1) if total_bookings else 0

    daily_totals = defaultdict(Decimal)
    for source in (
        _daily_revenue(_successful_flight_bookings(), "total_price", start_date),
        _daily_revenue(_successful_hotel_reservations(), "total_price", start_date),
        _daily_revenue(_successful_package_bookings(), "total_price", start_date),
        _daily_revenue(_successful_activity_bookings(), "total_price", start_date),
    ):
        for day, total in source.items():
            daily_totals[day] += total

    revenue_chart = []
    max_revenue = max(daily_totals.values(), default=Decimal("1")) or Decimal("1")
    for offset in range(7):
        day = start_date + timezone.timedelta(days=offset)
        total = daily_totals.get(day, Decimal("0"))
        revenue_chart.append({
            "label": day.strftime("%d/%m"),
            "total": total,
            "height": int((total / max_revenue) * 100) if total else 3,
        })

    recent_bookings = []
    for booking in Booking.objects.select_related("user", "flight__airline", "flight__origin", "flight__destination")[:8]:
        recent_bookings.append({
            "id": booking.id,
            "type": "flight",
            "label": booking.booking_reference,
            "customer": booking.user.email,
            "service": f"{booking.flight.flight_code} {booking.flight.origin.iata_code}-{booking.flight.destination.iata_code}",
            "status": booking.status,
            "payment": booking.payment_status,
            "total": booking.total_price,
            "created_at": booking.created_at,
        })
    for booking in HotelReservation.objects.select_related("user", "room_type__hotel")[:8]:
        recent_bookings.append({
            "id": booking.id,
            "type": "hotel",
            "label": f"HTL-{booking.id}",
            "customer": booking.user.email,
            "service": f"{booking.room_type.hotel.name} - {booking.room_type.name}",
            "status": booking.status,
            "payment": booking.payment_status,
            "total": booking.total_price,
            "created_at": booking.created_at,
        })
    for booking in PackageBooking.objects.select_related("user", "package")[:8]:
        recent_bookings.append({
            "id": booking.id,
            "type": "package",
            "label": f"PKG-{booking.id}",
            "customer": booking.user.email,
            "service": booking.package.title,
            "status": booking.status,
            "payment": booking.payment_status,
            "total": booking.total_price,
            "created_at": booking.created_at,
        })
    for booking in ActivityBooking.objects.select_related("user", "activity")[:8]:
        recent_bookings.append({
            "id": booking.id,
            "type": "activity",
            "label": f"ACT-{booking.id}",
            "customer": booking.user.email,
            "service": booking.activity.title,
            "status": booking.status,
            "payment": booking.payment_status,
            "total": booking.total_price,
            "created_at": booking.created_at,
        })
    recent_bookings = sorted(recent_bookings, key=lambda item: item["created_at"], reverse=True)[:10]
    for item in recent_bookings:
        item["can_confirm"] = item["status"] == "pending" and item["payment"] == "completed"
        item["can_cancel"] = item["status"] in {"pending", "confirmed"}
        item["can_refund"] = item["payment"] == "refund_pending"

    top_tours = (
        TravelPackage.objects.annotate(
            sold=Count("bookings", filter=Q(bookings__status__in=["confirmed", "completed"], bookings__payment_status="completed")),
            revenue=Sum("bookings__total_price", filter=Q(bookings__status__in=["confirmed", "completed"], bookings__payment_status="completed")),
        )
        .order_by("-sold", "-revenue")[:6]
    )
    active_services = {
        "hotels": Hotel.objects.filter(is_active=True).count(),
        "flights": Flight.objects.filter(is_active=True).count(),
        "tours": TravelPackage.objects.filter(is_active=True).count(),
        "activities": Activity.objects.filter(is_active=True).count(),
        "rooms_available": _money(RoomAvailability.objects.filter(date__gte=today).aggregate(total=Sum("available_rooms"))["total"]),
    }

    customer_rows = User.objects.filter(is_staff=False).annotate(
        flight_orders=Count(
            "flight_bookings",
            filter=Q(flight_bookings__status__in=["confirmed", "completed"]),
            distinct=True,
        ),
        hotel_orders=Count(
            "hotel_reservations",
            filter=Q(hotel_reservations__status__in=["confirmed", "completed"]),
            distinct=True,
        ),
        package_orders=Count(
            "package_bookings",
            filter=Q(package_bookings__status__in=["confirmed", "completed"], package_bookings__payment_status="completed"),
            distinct=True,
        ),
        activity_orders=Count(
            "activity_bookings",
            filter=Q(activity_bookings__status__in=["confirmed", "completed"], activity_bookings__payment_status="completed"),
            distinct=True,
        ),
    ).order_by("-date_joined")[:8]

    context = {
        "kpis": {
            "revenue": flight_revenue + hotel_revenue + package_revenue + activity_revenue,
            "total_bookings": total_bookings,
            "new_customers": User.objects.filter(
                is_staff=False,
                date_joined__date__gte=today - timezone.timedelta(days=30),
            ).count(),
            "cancellation_rate": cancellation_rate,
        },
        "booking_counts": {
            "flight": flight_count,
            "hotel": hotel_count,
            "package": package_count,
            "activity": activity_count,
            "cancelled": cancelled_count,
        },
        "finance": {
            "flight_revenue": flight_revenue,
            "hotel_revenue": hotel_revenue,
            "package_revenue": package_revenue,
            "activity_revenue": activity_revenue,
            "failed_payments": BookingPayment.objects.filter(status="failed").count() + PaymentTransaction.objects.filter(status="failed").count(),
            "refunds": BookingPayment.objects.filter(status="refunded").count() + PaymentTransaction.objects.filter(status="refunded").count(),
        },
        "revenue_chart": revenue_chart,
        "recent_bookings": recent_bookings,
        "top_tours": top_tours,
        "active_services": active_services,
        "customers": customer_rows,
        "staff_users": User.objects.filter(is_staff=True).order_by("email")[:10],
        "activity_logs": LogEntry.objects.select_related("user", "content_type")[:8],
        "page_title": "Admin Dashboard",
    }
    return render(request, "admin_dashboard/dashboard.html", context)


@staff_member_required
def admin_booking_action(request, booking_type, object_id, action):
    if request.method != "POST":
        return redirect("admin_dashboard")
    if action not in {"confirm", "cancel", "refund"}:
        messages.error(request, "Hanh dong khong hop le.")
        return redirect("admin_dashboard")

    if booking_type == "flight":
        booking = get_object_or_404(Booking.objects.select_related("flight"), id=object_id)
        old_status = booking.status
        passenger_count = max(1, booking.passenger_count)
        availability_field = f"{booking.cabin_class}_available"

        if action == "confirm":
            if booking.payment_status != "completed":
                messages.error(request, "Khach hang chua thanh toan nen khong the xac nhan booking.")
                return redirect("admin_dashboard")
            booking.status = "confirmed"
            booking.confirmed_at = booking.confirmed_at or timezone.now()
        elif action == "cancel":
            booking.status = "cancelled"
            booking.payment_status = "refund_pending" if booking.payment_status in {"completed", "skipped"} else "cancelled"
            booking.cancelled_at = booking.cancelled_at or timezone.now()
        else:
            booking.status = "refunded"
            booking.payment_status = "refunded"
        booking.save()
        if hasattr(booking, "payment") and action == "refund":
            booking.payment.status = "refunded"
            booking.payment.save()
        if action == "refund":
            PaymentTransaction.objects.filter(booking=booking, status="completed").update(status="refunded")
        if action in {"cancel", "refund"} and old_status not in {"cancelled", "refunded"} and booking.payment_status in {"refund_pending", "refunded"}:
            setattr(booking.flight, availability_field, getattr(booking.flight, availability_field) + passenger_count)
            booking.flight.save()
        messages.success(request, f"Da cap nhat booking {booking.booking_reference}.")

    elif booking_type == "package":
        booking = get_object_or_404(PackageBooking, id=object_id)
        if action == "confirm":
            if booking.payment_status != "completed":
                messages.error(request, "Khach hang chua thanh toan nen khong the xac nhan tour.")
                return redirect("admin_dashboard")
            booking.status = "confirmed"
        elif action == "cancel":
            booking.status = "cancelled"
            booking.payment_status = "refund_pending" if booking.payment_status == "completed" else "cancelled"
        else:
            booking.status = "refunded"
            booking.payment_status = "refunded"
            PaymentTransaction.objects.filter(booking_type="package", object_id=booking.id, status="completed").update(status="refunded")
        booking.save()
        messages.success(request, f"Da cap nhat booking tour PKG-{booking.id}.")

    elif booking_type == "hotel":
        booking = get_object_or_404(HotelReservation.objects.select_related("room_type"), id=object_id)
        old_status = booking.status
        if action == "confirm":
            if booking.payment_status != "completed":
                messages.error(request, "Khach hang chua thanh toan nen khong the xac nhan phong.")
                return redirect("admin_dashboard")
            booking.status = "confirmed"
        elif action == "cancel":
            booking.status = "cancelled"
            booking.payment_status = "refund_pending" if booking.payment_status == "completed" else "cancelled"
        else:
            booking.status = "refunded"
            booking.payment_status = "refunded"
            PaymentTransaction.objects.filter(booking_type="hotel", object_id=booking.id, status="completed").update(status="refunded")
        booking.save()
        if action in {"cancel", "refund"} and old_status not in {"cancelled", "refunded"}:
            availability, _ = RoomAvailability.objects.get_or_create(
                room_type=booking.room_type,
                date=booking.stay_date,
                defaults={"available_rooms": 0, "price": booking.price_per_room},
            )
            availability.available_rooms += booking.rooms
            availability.save()
        messages.success(request, f"Da cap nhat booking khach san HTL-{booking.id}.")

    elif booking_type == "activity":
        booking = get_object_or_404(ActivityBooking, id=object_id)
        if action == "confirm":
            if booking.payment_status != "completed":
                messages.error(request, "Khach hang chua thanh toan nen khong the xac nhan trai nghiem.")
                return redirect("admin_dashboard")
            booking.status = "confirmed"
        elif action == "cancel":
            booking.status = "cancelled"
            booking.payment_status = "refund_pending" if booking.payment_status == "completed" else "cancelled"
        else:
            booking.status = "refunded"
            booking.payment_status = "refunded"
            PaymentTransaction.objects.filter(booking_type="activity", object_id=booking.id, status="completed").update(status="refunded")
        booking.save()
        messages.success(request, f"Da cap nhat booking trai nghiem ACT-{booking.id}.")

    else:
        messages.error(request, "Loai booking khong hop le.")

    return redirect(reverse("admin_dashboard"))
