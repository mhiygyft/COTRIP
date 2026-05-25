"""
Novaryo Travel Booking Platform - URL Configuration
"Discover Comfort. Discover Novaryo."

© 2025 Aniket Kumar. All rights reserved.
This software is proprietary and confidential.

Developer: Aniket Kumar
Email: aniket.kumar.devpro@gmail.com
WhatsApp: +91 8318601925
GitHub: @Aniket-Dev-IT

Unauthorized use, reproduction, or distribution is strictly prohibited.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from hotels.views import HomeView
from hotels import views as hotel_views
from users import views as user_views
from . import admin_dashboard
from . import chatbot
from .swagger_settings import schema_view

admin.site.site_header = "Vietnam Travel Administration"
admin.site.site_title = "Vietnam Travel Admin"
admin.site.index_title = "Quản trị hệ thống du lịch Việt Nam"

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    path("admin-dashboard/", admin_dashboard.admin_dashboard, name="admin_dashboard"),
    path(
        "admin-dashboard/bookings/<str:booking_type>/<int:object_id>/<str:action>/",
        admin_dashboard.admin_booking_action,
        name="admin_booking_action",
    ),
    
    # Authentication URLs
    path('accounts/', include('allauth.urls')),
    
    # API URLs with namespaces
    path('api/', include([
        path('users/', include(('users.urls', 'users'), namespace='api_users')),
        path('hotels/', include(('hotels.urls', 'hotels'), namespace='api_hotels')),
        path('flights/', include(('flights.urls', 'flights'), namespace='api_flights')),
        path('packages/', include(('packages.urls', 'packages'), namespace='api_packages')),
        path('activities/', include(('activities.urls', 'activities'), namespace='api_activities')),
        path('bookings/', include(('bookings.urls', 'bookings'), namespace='api_bookings')),
        path('payments/', include(('payments.urls', 'payments'), namespace='api_payments')),
        path('reviews/', include(('reviews.urls', 'reviews'), namespace='api_reviews')),
        path('loyalty/', include(('loyalty.urls', 'loyalty'), namespace='api_loyalty')),
    ])),
    
    # Home page
    path('', HomeView.as_view(), name='home'),
    path('api/itineraries/<int:itinerary_id>/', hotel_views.editable_itinerary_api, name='editable_itinerary_api'),
    path('dashboard/', user_views.dashboard, name='customer_dashboard'),
    path('profile/', user_views.profile, name='account_profile'),
    path('chatbot/api/', chatbot.chatbot_api, name='chatbot_api'),
    
    # Web app URLs
    path('hotels/', include('hotels.urls')),
    path('flights/', include('flights.urls')),
    path('packages/', include('packages.urls')),
    path('activities/', include('activities.urls')),
    path('users/', include('users.urls')),
    path('bookings/', include('bookings.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('loyalty/', include('loyalty.urls')),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='api-redoc'),
    path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='api-schema-json'),
    path('api/swagger.yaml', schema_view.without_ui(cache_timeout=0), name='api-schema-yaml'),
    
    # Performance Monitoring (Development only) - TEMPORARILY DISABLED
    # path('silk/', include('silk.urls', namespace='silk')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
