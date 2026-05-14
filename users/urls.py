from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="account_profile"),
    path("profile/", views.profile, name="profile"),
    path("saved-flights/", views.saved_flights, name="saved_flights"),
]
