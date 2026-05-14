from django.urls import path
from . import views

app_name = 'flights'

urlpatterns = [
    # Main flight search and results
    path('', views.flight_search, name='search'),
    path('search/', views.flight_search, name='search'),  # Alternative route
    path('results/', views.flight_search_results, name='search_results'),
    path('quick-search/', views.quick_search_redirect, name='quick_search'),
    
    # Flight details
    path('flight/<int:flight_id>/', views.flight_detail, name='detail'),
    
    # User features (saved searches and flights)
    path('saved-searches/', views.saved_searches, name='saved_searches'),
    path('saved-searches/delete/<int:search_id>/', views.delete_saved_search, name='delete_saved_search'),
    path('save-flight/<int:flight_id>/', views.save_flight, name='save_flight'),
    
    # AJAX endpoints
    path('api/airports/', views.airports_autocomplete, name='airports_autocomplete'),
]
