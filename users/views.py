from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from bookings.models import Booking
from flights.models import FlightSearch, SavedFlight

from .forms import UserProfileForm


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            next_url = request.GET.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("users:account_profile")
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        "form": form,
        "page_title": "My Profile",
    }
    return render(request, "users/profile.html", context)


@login_required
def dashboard(request):
    context = {
        "bookings": Booking.objects.filter(user=request.user).order_by("-created_at")[:5],
        "saved_flights": SavedFlight.objects.filter(user=request.user).select_related("flight")[:5],
        "saved_searches": FlightSearch.objects.filter(user=request.user).order_by("-created_at")[:5],
        "page_title": "Account Dashboard",
    }
    return render(request, "users/dashboard.html", context)


@login_required
def saved_flights(request):
    context = {
        "saved_flights": SavedFlight.objects.filter(user=request.user).select_related(
            "flight",
            "flight__airline",
            "flight__origin",
            "flight__destination",
        ),
        "page_title": "Saved Flights",
    }
    return render(request, "users/saved_flights.html", context)
