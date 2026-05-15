from django.urls import path

from . import views


app_name = "payments"

urlpatterns = [
    path("", views.payment_history, name="history"),
    path("checkout/<str:booking_type>/<int:object_id>/", views.checkout, name="checkout"),
]
