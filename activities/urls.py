from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.ActivitySearchView.as_view(), name='search'),
    path('activity/<int:activity_id>/', views.ActivityDetailView.as_view(), name='detail'),
    path('activity/<int:activity_id>/book/', views.book_activity, name='book'),
    path('api/search/', views.ActivitySearchAPIView.as_view(), name='search_api'),
]
