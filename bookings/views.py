from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .auth_utils import (
    booking_login_required, require_complete_profile, 
    get_user_booking_context, check_booking_ownership,
    clear_booking_session, UserBookingMixin
)
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
import logging
from .emails import send_booking_confirmation_email, send_payment_receipt_email, send_booking_cancellation_email

from flights.models import Flight
from .models import Booking, Passenger, BookingPayment
from .forms import (
    PassengerForm, BookingContactForm, PaymentForm, 
    BookingSearchForm, CancellationForm
)

logger = logging.getLogger(__name__)


def make_session_safe(data):
    """Convert cleaned form data to JSON-serializable values for session storage."""
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            safe_data[key] = value.isoformat()
        elif value is None:
            safe_data[key] = None
        else:
            safe_data[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
    return safe_data


@booking_login_required
def start_booking(request, flight_id):
    """Start the booking process for a specific flight"""
    flight = get_object_or_404(Flight, id=flight_id)
    cabin_class = request.GET.get('cabin_class', 'economy')
    
    # Check if flight has availability for the selected class
    available_seats = flight.get_available_seats_for_class(cabin_class)
    price = flight.get_price_for_class(cabin_class)
    
    if available_seats <= 0 or not price:
        messages.error(request, f'Sorry, {cabin_class.replace("_", " ").title()} class is not available for this flight.')
        return redirect('flights:detail', flight_id=flight_id)
    
    # Store flight and cabin class in session for the booking process
    request.session['booking_flight_id'] = flight_id
    request.session['booking_cabin_class'] = cabin_class
    request.session['booking_price'] = str(price)
    
    return redirect('bookings:passenger_details')


@require_complete_profile
def passenger_details(request):
    """Collect passenger information"""
    # Get flight info from session
    flight_id = request.session.get('booking_flight_id')
    cabin_class = request.session.get('booking_cabin_class', 'economy')
    
    if not flight_id:
        messages.error(request, 'Please select a flight first.')
        return redirect('flights:search')
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    # For simplicity, we'll handle just one passenger for now
    # In a full implementation, you'd handle multiple passengers
    
    if request.method == 'POST':
        passenger_form = PassengerForm(request.POST, flight=flight)
        contact_form = BookingContactForm(request.POST)
        
        if passenger_form.is_valid() and contact_form.is_valid():
            # Store passenger data in session
            request.session['passenger_data'] = make_session_safe(passenger_form.cleaned_data)
            request.session['contact_data'] = make_session_safe(contact_form.cleaned_data)
            
            return redirect('bookings:payment')
    else:
        passenger_form = PassengerForm(flight=flight, initial={
            'email': request.user.email,
            'title': 'mr' if not hasattr(request.user, 'gender') else ('mr' if request.user.gender == 'male' else 'ms')
        })
        contact_form = BookingContactForm(initial={
            'contact_email': request.user.email,
        })
    
    context = {
        'flight': flight,
        'cabin_class': cabin_class,
        'passenger_form': passenger_form,
        'contact_form': contact_form,
        'price': flight.get_price_for_class(cabin_class),
        'page_title': 'Passenger Details'
    }
    
    return render(request, 'bookings/passenger_details.html', context)


@require_complete_profile
def payment(request):
    """Handle payment processing with skip payment option"""
    # Get booking data from session
    flight_id = request.session.get('booking_flight_id')
    cabin_class = request.session.get('booking_cabin_class')
    passenger_data = request.session.get('passenger_data')
    contact_data = request.session.get('contact_data')
    
    if not all([flight_id, cabin_class, passenger_data, contact_data]):
        messages.error(request, 'Missing booking information. Please start over.')
        return redirect('flights:search')
    
    flight = get_object_or_404(Flight, id=flight_id)
    price = flight.get_price_for_class(cabin_class)
    
    # Calculate total price (base price + taxes/fees)
    base_price = Decimal(str(price))
    taxes_and_fees = base_price * Decimal('0.15')  # 15% taxes/fees
    total_price = base_price + taxes_and_fees
    
    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        
        if payment_form.is_valid():
            payment_method = payment_form.cleaned_data['payment_method']
            
            try:
                with transaction.atomic():
                    # Create the booking
                    booking = Booking.objects.create(
                        user=request.user,
                        flight=flight,
                        cabin_class=cabin_class,
                        base_price=base_price,
                        taxes_and_fees=taxes_and_fees,
                        total_price=total_price,
                        contact_email=contact_data['contact_email'],
                        contact_phone=contact_data.get('contact_phone', ''),
                        special_requests=contact_data.get('special_requests', ''),
                        payment_method=payment_method if payment_method != 'skip' else 'skipped'
                    )
                    
                    # Create passenger
                    passenger_data['booking'] = booking
                    passenger = Passenger.objects.create(**passenger_data)
                    
                    # Handle payment
                    if payment_method == 'skip':
                        # Skip payment - mark as completed for testing
                        payment = BookingPayment.objects.create(
                            booking=booking,
                            amount=total_price,
                            payment_method='skipped',
                            status='skipped',
                            notes='Payment skipped for testing purposes'
                        )
                        
                        booking.status = 'pending'
                        booking.payment_status = 'skipped'
                        booking.save()
                        
                        # Update flight availability
                        availability_field = f'{cabin_class}_available'
                        current_availability = getattr(flight, availability_field)
                        setattr(flight, availability_field, current_availability - 1)
                        flight.save()
                        
                        messages.success(request, 'Payment skipped. Booking is waiting for admin confirmation.')

                        # Send confirmation email
                        try:
                            send_booking_confirmation_email(booking)
                        except Exception as e:
                            logger.warning(f'Failed to send confirmation email (skipped payment): {e}')
                    else:
                        # For real payment methods, you'd integrate with payment gateway here
                        # For now, we'll simulate payment processing
                        payment = BookingPayment.objects.create(
                            booking=booking,
                            amount=total_price,
                            payment_method=payment_method,
                            status='processing',
                            notes=f'Processing {payment_method} payment'
                        )
                        
                        # Simulate payment processing (in real app, this would be async)
                        # For demo purposes, we'll mark it as completed
                        payment.status = 'completed'
                        payment.processed_at = timezone.now()
                        payment.save()
                        
                        booking.status = 'pending'
                        booking.payment_status = 'completed'
                        booking.save()
                        
                        # Update flight availability
                        availability_field = f'{cabin_class}_available'
                        current_availability = getattr(flight, availability_field)
                        setattr(flight, availability_field, current_availability - 1)
                        flight.save()
                        
                        messages.success(request, 'Payment successful. Your booking is waiting for admin confirmation.')

                        # Send confirmation and receipt emails
                        try:
                            send_booking_confirmation_email(booking)
                        except Exception as e:
                            logger.warning(f'Failed to send confirmation email: {e}')
                        try:
                            send_payment_receipt_email(booking, payment)
                        except Exception as e:
                            logger.warning(f'Failed to send payment receipt email: {e}')
                    
                    # Clear booking session data
                    clear_booking_session(request)
                    
                    return redirect('bookings:confirmation', booking_reference=booking.booking_reference)
                    
            except Exception as e:
                logger.error(f'Booking creation failed: {e}')
                messages.error(request, 'An error occurred while processing your booking. Please try again.')
    else:
        payment_form = PaymentForm()
    
    context = {
        'flight': flight,
        'cabin_class': cabin_class,
        'passenger_data': passenger_data,
        'contact_data': contact_data,
        'payment_form': payment_form,
        'base_price': base_price,
        'taxes_and_fees': taxes_and_fees,
        'total_price': total_price,
        'page_title': 'Payment'
    }
    
    return render(request, 'bookings/payment.html', context)


@login_required
def booking_confirmation(request, booking_reference):
    """Show booking confirmation"""
    booking = get_object_or_404(
        Booking.objects.select_related('flight__airline', 'flight__origin', 'flight__destination'),
        booking_reference=booking_reference
    )
    
    # Check booking ownership
    if not check_booking_ownership(request.user, booking):
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('bookings:my_bookings')
    
    context = {
        'booking': booking,
        'passengers': booking.passengers.all(),
        'page_title': f'Booking Confirmation - {booking.booking_reference}'
    }
    context.update(get_user_booking_context(request))
    
    return render(request, 'bookings/confirmation.html', context)


@login_required
def my_bookings(request):
    """List user's bookings"""
    bookings = Booking.objects.filter(user=request.user).select_related(
        'flight__airline', 'flight__origin', 'flight__destination'
    ).prefetch_related('passengers').order_by('-created_at')
    
    context = {
        'bookings': bookings,
        'active_bookings': bookings.filter(status__in=['confirmed', 'pending']),
        'past_bookings': bookings.filter(status__in=['completed', 'cancelled']),
        'page_title': 'My Bookings'
    }
    context.update(get_user_booking_context(request))
    
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def booking_detail(request, booking_reference):
    """Show detailed booking information"""
    booking = get_object_or_404(
        Booking.objects.select_related('flight__airline', 'flight__origin', 'flight__destination'),
        booking_reference=booking_reference
    )
    
    # Check booking ownership
    if not check_booking_ownership(request.user, booking):
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('bookings:my_bookings')
    
    context = {
        'booking': booking,
        'passengers': booking.passengers.all(),
        'page_title': f'Booking {booking.booking_reference}'
    }
    context.update(get_user_booking_context(request))
    
    return render(request, 'bookings/booking_detail.html', context)


def booking_search(request):
    """Search for bookings using booking reference and email"""
    booking = None
    
    if request.method == 'POST':
        form = BookingSearchForm(request.POST)
        
        if form.is_valid():
            try:
                booking = Booking.objects.select_related(
                    'flight__airline', 'flight__origin', 'flight__destination'
                ).get(
                    booking_reference=form.cleaned_data['booking_reference'],
                    contact_email=form.cleaned_data['email']
                )
            except Booking.DoesNotExist:
                messages.error(request, 'No booking found with the provided reference and email.')
    else:
        form = BookingSearchForm()
    
    context = {
        'form': form,
        'booking': booking,
        'passengers': booking.passengers.all() if booking else None,
        'page_title': 'Find My Booking'
    }
    
    return render(request, 'bookings/search.html', context)


@login_required
def cancel_booking(request, booking_reference):
    """Cancel a booking"""
    booking = get_object_or_404(
        Booking,
        booking_reference=booking_reference
    )
    
    # Check booking ownership
    if not check_booking_ownership(request.user, booking):
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('bookings:my_bookings')
    
    if not booking.is_cancellable:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_reference=booking_reference)
    
    if request.method == 'POST':
        form = CancellationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update booking status
                    booking.status = 'cancelled'
                    booking.cancelled_at = timezone.now()
                    booking.save()
                    
                    # Restore flight availability
                    flight = booking.flight
                    availability_field = f'{booking.cabin_class}_available'
                    current_availability = getattr(flight, availability_field)
                    setattr(flight, availability_field, current_availability + 1)
                    flight.save()
                    
                    # Send cancellation email
                    try:
                        reason = form.cleaned_data.get('reason', 'Customer requested cancellation')
                        send_booking_cancellation_email(booking, reason)
                    except Exception as e:
                        logger.warning(f'Failed to send cancellation email: {e}')
                    
                    messages.success(request, f'Booking {booking.booking_reference} has been cancelled.')
                    return redirect('bookings:my_bookings')
                    
            except Exception as e:
                logger.error(f'Booking cancellation failed: {e}')
                messages.error(request, 'An error occurred while cancelling your booking.')
    else:
        form = CancellationForm()
    
    context = {
        'booking': booking,
        'form': form,
        'page_title': f'Cancel Booking {booking.booking_reference}'
    }
    
    return render(request, 'bookings/cancel.html', context)
