"""
Authentication utilities for the booking system
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def booking_login_required(view_func):
    """
    Enhanced login required decorator with better UX for booking flows
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Store the intended destination
        next_url = request.get_full_path()
        login_url = f"{reverse('account_login')}?next={next_url}"
        
        # Add helpful message for booking flow
        messages.info(
            request,
            "Please log in to continue with your booking. Your flight selection will be saved."
        )
        
        # Store flight selection in session if available
        flight_id = kwargs.get('flight_id')
        cabin_class = request.GET.get('cabin_class')
        if flight_id and cabin_class:
            request.session['pre_auth_flight_id'] = flight_id
            request.session['pre_auth_cabin_class'] = cabin_class
        
        return redirect(login_url)
    
    return _wrapped_view


def restore_booking_session_after_login(request):
    """
    Restore booking session data after user logs in
    """
    if 'pre_auth_flight_ids' in request.session:
        request.session['booking_flight_ids'] = request.session.pop('pre_auth_flight_ids')
        request.session['booking_flight_id'] = request.session['booking_flight_ids'][0]
        request.session['booking_cabin_class'] = request.session.pop('pre_auth_cabin_class', 'economy')
        request.session['booking_is_multi_city'] = request.session.pop('pre_auth_is_multi_city', True)

        try:
            from flights.models import Flight
            flights = Flight.objects.filter(id__in=request.session['booking_flight_ids'])
            total_price = sum(
                flight.get_price_for_class(request.session['booking_cabin_class']) or 0
                for flight in flights
            )
            request.session['booking_price'] = str(total_price)
        except Exception:
            pass

        return True

    if 'pre_auth_flight_id' in request.session:
        request.session['booking_flight_id'] = request.session.pop('pre_auth_flight_id')
        request.session['booking_flight_ids'] = [request.session['booking_flight_id']]
        request.session['booking_is_multi_city'] = False
        request.session['booking_cabin_class'] = request.session.pop('pre_auth_cabin_class', 'economy')
        
        # Calculate price for the stored flight/class
        try:
            from flights.models import Flight
            flight = Flight.objects.get(id=request.session['booking_flight_id'])
            price = flight.get_price_for_class(request.session['booking_cabin_class'])
            request.session['booking_price'] = str(price) if price else None
        except:
            pass
        
        return True
    return False


def require_complete_profile(view_func):
    """
    Decorator to ensure user has complete profile information for bookings
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return booking_login_required(view_func)(request, *args, **kwargs)
        
        # Check if user has required profile information
        user = request.user
        missing_fields = []
        
        if not user.first_name:
            missing_fields.append('first name')
        if not user.last_name:
            missing_fields.append('last name')
        if not user.email:
            missing_fields.append('email')
        if not user.phone_number:
            missing_fields.append('phone number')
        
        if missing_fields:
            messages.warning(
                request,
                f"Please complete your profile ({', '.join(missing_fields)}) before making a booking."
            )
            # Redirect to profile completion with next parameter
            next_url = request.get_full_path()
            profile_url = f"{reverse('users:account_profile')}?next={next_url}"
            return redirect(profile_url)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def get_user_booking_context(request):
    """
    Get user-specific context for booking templates
    """
    context = {}
    
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_bookings_count': user.bookings.count() if hasattr(user, 'bookings') else 0,
            'user_has_profile': bool(user.first_name and user.last_name and user.email and user.phone_number),
            'user_email_verified': getattr(user, 'emailaddress_set', None) and 
                                 user.emailaddress_set.filter(verified=True).exists(),
        })
    
    return context


def create_guest_booking_session(request, booking_data):
    """
    Create a guest booking session for anonymous users (future feature)
    """
    # For now, we require login, but this could be extended
    # to support guest bookings with email confirmation
    guest_session_key = f"guest_booking_{request.session.session_key}"
    request.session[guest_session_key] = booking_data
    request.session['is_guest_booking'] = True
    return guest_session_key


def handle_post_login_redirect(request):
    """
    Handle redirect after successful login, considering booking flow
    """
    # Check if user was in the middle of a booking
    if restore_booking_session_after_login(request):
        messages.success(request, "Welcome back! Continuing with your booking.")
        return redirect('bookings:passenger_details')
    
    # Check for next parameter
    next_url = request.GET.get('next')
    if next_url and is_safe_url(next_url, request.get_host()):
        return redirect(next_url)
    
    # Default redirect
    return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))


def is_safe_url(url, host):
    """
    Check if URL is safe for redirect
    """
    if not url:
        return False
    
    # Basic safety checks
    if url.startswith('//') or url.startswith('http'):
        return False
    
    return True


class UserBookingMixin:
    """
    Mixin for views that handle user bookings
    """
    
    def get_user_bookings(self):
        """Get all bookings for the current user"""
        if not self.request.user.is_authenticated:
            return []
        return self.request.user.bookings.all().order_by('-created_at')
    
    def get_user_active_bookings(self):
        """Get active bookings for the current user"""
        if not self.request.user.is_authenticated:
            return []
        return self.request.user.bookings.filter(
            status__in=['confirmed', 'pending']
        ).order_by('flight__departure_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context.update(get_user_booking_context(self.request))
        return context


def check_booking_ownership(user, booking):
    """
    Check if user owns the booking
    """
    if not user.is_authenticated:
        return False
    
    return booking.user == user


def send_auth_notification_email(user, action):
    """
    Send authentication-related notification emails
    """
    try:
        if action == 'login':
            logger.info(f"User {user.email} logged in for booking")
        elif action == 'signup':
            logger.info(f"New user {user.email} signed up for booking")
            # Could send welcome email here
    except Exception as e:
        logger.warning(f"Failed to send auth notification email: {e}")


def get_booking_session_data(request):
    """
    Get all booking-related session data
    """
    return {
        'flight_id': request.session.get('booking_flight_id'),
        'cabin_class': request.session.get('booking_cabin_class'),
        'price': request.session.get('booking_price'),
        'passenger_data': request.session.get('passenger_data'),
        'contact_data': request.session.get('contact_data'),
        'is_complete': all([
            request.session.get('booking_flight_id'),
            request.session.get('booking_cabin_class'),
            request.session.get('passenger_data'),
            request.session.get('contact_data')
        ])
    }


def clear_booking_session(request):
    """
    Clear all booking-related session data
    """
    keys_to_clear = [
        'booking_flight_id',
        'booking_flight_ids',
        'booking_is_multi_city',
        'booking_cabin_class', 
        'booking_price',
        'passenger_data',
        'contact_data',
        'pre_auth_flight_id',
        'pre_auth_flight_ids',
        'pre_auth_is_multi_city',
        'pre_auth_cabin_class',
        'is_guest_booking'
    ]
    
    for key in keys_to_clear:
        request.session.pop(key, None)
