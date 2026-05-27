from django.urls import path

from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.transport_home, name='search'),
    path('results/', views.transport_results, name='results'),
    path('book/<int:trip_id>/', views.start_booking, name='start_booking'),
    path('passenger-details/', views.passenger_details, name='passenger_details'),
    path('payment/', views.payment, name='payment'),
    path('confirmation/<str:booking_reference>/', views.confirmation, name='confirmation'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<str:booking_reference>/', views.booking_detail, name='booking_detail'),
]
