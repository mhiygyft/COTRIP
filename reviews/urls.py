from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='list'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='detail'),
    path('write/', views.WriteReviewView.as_view(), name='write'),
    path('create/<int:booking_id>/', views.create_review, name='create'),
    path('api/reviews/', views.ReviewAPIView.as_view(), name='reviews_api'),
]
