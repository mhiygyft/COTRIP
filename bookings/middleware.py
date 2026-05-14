"""
Middleware for handling booking flows and authentication
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .auth_utils import restore_booking_session_after_login, get_user_booking_context


class BookingFlowMiddleware:
    """
    Middleware to handle booking flow restoration after login
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Handle post-login booking flow restoration
        if (request.user.is_authenticated and 
            request.path in [reverse('account_login'), reverse('account_signup')] and 
            request.method == 'POST'):
            
            # Check if user was in the middle of a booking
            if 'pre_auth_flight_id' in request.session:
                restore_booking_session_after_login(request)
                messages.success(request, "Welcome! Continuing with your booking.")
                response = redirect('bookings:passenger_details')
        
        return response


class BookingContextMiddleware:
    """
    Middleware to add booking context to all requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add booking context to request for templates
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.booking_context = get_user_booking_context(request)
        else:
            request.booking_context = {}
        
        response = self.get_response(request)
        return response


def booking_context_processor(request):
    """
    Context processor to add booking-related context to all templates
    """
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        context.update(get_user_booking_context(request))
        
        # Add booking session status
        context['has_active_booking_session'] = any([
            request.session.get('booking_flight_id'),
            request.session.get('passenger_data'),
            request.session.get('contact_data')
        ])
    
    return context