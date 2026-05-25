from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    # Hotel search and listing (home page moved to main urls.py)
    path('', views.HotelListView.as_view(), name='hotel_list_root'),
    path('search/', views.HotelSearchView.as_view(), name='search'),
    path('hotels/', views.HotelListView.as_view(), name='hotel_list'),
    path('hotel/<slug:slug>/', views.HotelDetailView.as_view(), name='hotel_detail'),
    path('rooms/<int:room_type_id>/reserve/', views.reserve_room, name='reserve_room'),
    
    # Location-based URLs
    path('destinations/', views.DestinationListView.as_view(), name='destinations'),
    path('destinations/<str:country_code>/', views.CountryHotelsView.as_view(), name='country_hotels'),
    path('destinations/<str:country_code>/<int:city_id>/', views.CityHotelsView.as_view(), name='city_hotels'),
    
    # API endpoints for AJAX requests
    path('api/search-suggestions/', views.SearchSuggestionsView.as_view(), name='search_suggestions'),
    path('api/hotel/<int:hotel_id>/availability/', views.HotelAvailabilityView.as_view(), name='hotel_availability'),
    path('api/filters/', views.FilterOptionsView.as_view(), name='filter_options'),
    path('api/itinerary-builder/', views.ItineraryBuilderAPIView.as_view(), name='itinerary_builder_api'),
]
