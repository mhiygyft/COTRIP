from django.urls import path

from . import views


app_name = 'hotels'

urlpatterns = [
    path('', views.HotelListView.as_view(), name='hotel_list_root'),
    path('search/', views.HotelSearchView.as_view(), name='search'),
    path('hotels/', views.HotelListView.as_view(), name='hotel_list'),
    path('hotel/<slug:slug>/', views.HotelDetailView.as_view(), name='hotel_detail'),
    path('rooms/<int:room_type_id>/reserve/', views.reserve_room, name='reserve_room'),

    path('destinations/', views.DestinationListView.as_view(), name='destinations'),
    path('itinerary-planner/', views.ItineraryPlannerView.as_view(), name='itinerary_planner'),
    path('itinerary/<int:itinerary_id>/book/', views.itinerary_booking_plan, name='itinerary_booking_plan'),
    path('destinations/<str:country_code>/', views.CountryHotelsView.as_view(), name='country_hotels'),
    path('destinations/<str:country_code>/<int:city_id>/', views.CityHotelsView.as_view(), name='city_hotels'),

    path('api/search-suggestions/', views.SearchSuggestionsView.as_view(), name='search_suggestions'),
    path('api/hotel/<int:hotel_id>/availability/', views.HotelAvailabilityView.as_view(), name='hotel_availability'),
    path('api/filters/', views.FilterOptionsView.as_view(), name='filter_options'),
    path('api/itinerary-builder/', views.ItineraryBuilderAPIView.as_view(), name='itinerary_builder_api'),
    path('api/saved-itineraries/', views.saved_itineraries_api, name='saved_itineraries_api'),
    path('api/editable-itinerary/<int:itinerary_id>/', views.editable_itinerary_api, name='editable_itinerary_api'),
]
