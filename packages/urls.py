from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.PackageSearchView.as_view(), name='search'),
    path('package/<int:package_id>/', views.PackageDetailView.as_view(), name='detail'),
    path('package/<int:package_id>/book/', views.book_package, name='book'),
    path('api/search/', views.PackageSearchAPIView.as_view(), name='search_api'),
]
