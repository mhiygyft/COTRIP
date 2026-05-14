from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking flow
    path('book/<int:flight_id>/', views.start_booking, name='start_booking'),
    path('passenger-details/', views.passenger_details, name='passenger_details'),
    path('payment/', views.payment, name='payment'),
    path('confirmation/<str:booking_reference>/', views.booking_confirmation, name='confirmation'),
    
    # User bookings
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<str:booking_reference>/', views.booking_detail, name='booking_detail'),
    path('cancel/<str:booking_reference>/', views.cancel_booking, name='cancel_booking'),
    
    # Public booking search
    path('search/', views.booking_search, name='search'),
    
    # Legacy/compatibility routes
    path('', views.my_bookings, name='list'),  # Redirect to my_bookings for logged-in users
]
