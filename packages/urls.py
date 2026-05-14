from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.PackageSearchView.as_view(), name='search'),
    path('package/<int:package_id>/', views.PackageDetailView.as_view(), name='detail'),
    path('api/search/', views.PackageSearchAPIView.as_view(), name='search_api'),
]