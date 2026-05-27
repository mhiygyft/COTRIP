from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .forms import TransportPassengerForm, TransportPaymentForm, TransportSearchForm, calculate_transport_price
from .models import TransportBooking, TransportStation, TransportTrip


def transport_home(request):
    form = TransportSearchForm(request.GET or None)
    stations = TransportStation.objects.filter(is_active=True, is_popular=True).order_by('city', 'name')

    if form.is_valid():
        cleaned = form.cleaned_data
        url = (
            f"{reverse('transport:results')}?"
            f"transport_type={cleaned['transport_type']}"
            f"&origin={cleaned['origin'].id}"
            f"&destination={cleaned['destination'].id}"
            f"&departure_date={cleaned['departure_date'].isoformat()}"
            f"&passengers={cleaned['passengers']}"
            f"&seat_class={cleaned.get('seat_class') or ''}"
        )
        return redirect(url)

    featured_trips = (
        TransportTrip.objects
        .filter(is_active=True, status='scheduled', departure_time__gte=timezone.now())
        .select_related('provider', 'route__origin', 'route__destination')
        .order_by('departure_time')[:8]
    )
    return render(request, 'transport/search.html', {
        'form': form,
        'stations': stations,
        'featured_trips': featured_trips,
        'page_title': 'Dat ve tau va xe khach',
    })


def transport_results(request):
    form = TransportSearchForm(request.GET)
    if not form.is_valid():
        messages.error(request, 'Vui long kiem tra lai thong tin tim kiem.')
        return redirect('transport:search')

    cleaned = form.cleaned_data
    trips = (
        TransportTrip.objects
        .filter(
            is_active=True,
            status='scheduled',
            route__transport_type=cleaned['transport_type'],
            route__origin=cleaned['origin'],
            route__destination=cleaned['destination'],
            departure_time__date=cleaned['departure_date'],
            available_seats__gte=cleaned['passengers'],
        )
        .select_related('provider', 'route__origin', 'route__destination')
        .order_by('departure_time', 'base_price')
    )

    seat_class = cleaned.get('seat_class')
    if seat_class:
        trips = trips.filter(seat_class=seat_class)

    if not trips.exists():
        trips = (
            TransportTrip.objects
            .filter(
                is_active=True,
                status='scheduled',
                route__transport_type=cleaned['transport_type'],
                route__origin=cleaned['origin'],
                route__destination=cleaned['destination'],
                departure_time__date__range=(cleaned['departure_date'], cleaned['departure_date'] + timedelta(days=14)),
                available_seats__gte=cleaned['passengers'],
            )
            .select_related('provider', 'route__origin', 'route__destination')
            .order_by('departure_time', 'base_price')
        )
        if seat_class:
            trips = trips.filter(seat_class=seat_class)
        messages.info(request, 'Khong co chuyen dung ngay da chon. Dang hien thi cac chuyen gan nhat trong 14 ngay tiep theo.')

    return render(request, 'transport/results.html', {
        'form': form,
        'trips': trips[:30],
        'search': cleaned,
        'page_title': 'Ket qua tim ve',
    })


@login_required
def start_booking(request, trip_id):
    trip = get_object_or_404(TransportTrip, id=trip_id, is_active=True, status='scheduled')
    try:
        passengers = int(request.GET.get('passengers', 1))
    except (TypeError, ValueError):
        passengers = 1
    passengers = max(1, min(passengers, 10))

    if trip.available_seats < passengers:
        messages.error(request, 'Chuyen nay khong con du cho trong.')
        return redirect('transport:search')

    request.session['transport_trip_id'] = trip.id
    request.session['transport_passengers'] = passengers
    return redirect('transport:passenger_details')


@login_required
def passenger_details(request):
    trip = get_session_trip(request)
    if not trip:
        messages.error(request, 'Vui long chon chuyen truoc.')
        return redirect('transport:search')

    passengers = int(request.session.get('transport_passengers', 1))
    if request.method == 'POST':
        form = TransportPassengerForm(trip, request.POST)
        if form.is_valid():
            request.session['transport_contact_data'] = {
                key: (value.id if hasattr(value, 'id') else value)
                for key, value in form.cleaned_data.items()
            }
            return redirect('transport:payment')
    else:
        form = TransportPassengerForm(trip, initial={
            'contact_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'contact_email': request.user.email,
            'contact_phone': getattr(request.user, 'phone_number', ''),
        })

    base_price, service_fee, total_price = calculate_transport_price(trip, passengers)
    return render(request, 'transport/passenger_details.html', {
        'form': form,
        'trip': trip,
        'passengers': passengers,
        'base_price': base_price,
        'service_fee': service_fee,
        'total_price': total_price,
        'page_title': 'Thong tin dat ve',
    })


@login_required
def payment(request):
    trip = get_session_trip(request)
    contact_data = request.session.get('transport_contact_data')
    if not trip or not contact_data:
        messages.error(request, 'Thieu thong tin dat ve. Vui long bat dau lai.')
        return redirect('transport:search')

    passengers = int(request.session.get('transport_passengers', 1))
    base_price, service_fee, total_price = calculate_transport_price(trip, passengers)

    if request.method == 'POST':
        form = TransportPaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            try:
                with transaction.atomic():
                    trip = TransportTrip.objects.select_for_update().get(id=trip.id)
                    if trip.available_seats < passengers:
                        messages.error(request, 'Chuyen nay vua het cho. Vui long chon chuyen khac.')
                        return redirect('transport:search')

                    booking = TransportBooking.objects.create(
                        user=request.user,
                        trip=trip,
                        passengers=passengers,
                        contact_name=contact_data['contact_name'],
                        contact_phone=contact_data['contact_phone'],
                        contact_email=contact_data['contact_email'],
                        pickup_location_id=contact_data.get('pickup_location'),
                        dropoff_location_id=contact_data.get('dropoff_location'),
                        special_requests=contact_data.get('special_requests', ''),
                        base_price=base_price,
                        service_fee=service_fee,
                        total_price=total_price,
                        payment_method='skipped' if payment_method == 'skip' else payment_method,
                        payment_status='skipped' if payment_method == 'skip' else 'completed',
                        status='pending',
                    )
                    trip.available_seats -= passengers
                    trip.save(update_fields=['available_seats'])
                    clear_transport_session(request)
                    messages.success(request, 'Dat ve thanh cong. Don hang dang cho xac nhan.')
                    return redirect('transport:confirmation', booking_reference=booking.booking_reference)
            except Exception:
                messages.error(request, 'Khong the tao booking. Vui long thu lai.')
    else:
        form = TransportPaymentForm()

    return render(request, 'transport/payment.html', {
        'form': form,
        'trip': trip,
        'passengers': passengers,
        'base_price': base_price,
        'service_fee': service_fee,
        'total_price': total_price,
        'page_title': 'Thanh toan ve',
    })


@login_required
def confirmation(request, booking_reference):
    booking = get_object_or_404(
        TransportBooking.objects.select_related(
            'trip__provider',
            'trip__route__origin',
            'trip__route__destination',
            'pickup_location',
            'dropoff_location',
        ),
        booking_reference=booking_reference,
        user=request.user,
    )
    return render(request, 'transport/confirmation.html', {'booking': booking})


@login_required
def booking_detail(request, booking_reference):
    booking = get_object_or_404(
        TransportBooking.objects.select_related(
            'trip__provider',
            'trip__route__origin',
            'trip__route__destination',
            'pickup_location',
            'dropoff_location',
        ),
        booking_reference=booking_reference,
        user=request.user,
    )
    return render(request, 'transport/booking_detail.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = (
        TransportBooking.objects
        .filter(user=request.user)
        .select_related('trip__provider', 'trip__route__origin', 'trip__route__destination')
        .order_by('-created_at')
    )
    return render(request, 'transport/my_bookings.html', {'bookings': bookings})


def get_session_trip(request):
    trip_id = request.session.get('transport_trip_id')
    if not trip_id:
        return None
    try:
        return TransportTrip.objects.select_related('provider', 'route__origin', 'route__destination').get(id=trip_id)
    except TransportTrip.DoesNotExist:
        return None


def clear_transport_session(request):
    for key in ['transport_trip_id', 'transport_passengers', 'transport_contact_data']:
        request.session.pop(key, None)

# Create your views here.
