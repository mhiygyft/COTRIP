from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Q
from .models import Activity, ActivityBooking, ActivityCategory

class ActivitySearchView(TemplateView):
    template_name = 'activities/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activities = Activity.objects.filter(is_active=True).select_related('category')
        location = self.request.GET.get('location', '').strip()
        category = self.request.GET.get('category', '').strip()

        if location:
            activities = activities.filter(Q(city__icontains=location) | Q(country__icontains=location))
        if category:
            activities = activities.filter(category_id=category)

        context.update({
            'activities': activities.order_by('-featured', 'title'),
            'categories': ActivityCategory.objects.order_by('name'),
            'location': location,
            'category': category,
        })
        return context

class ActivityDetailView(TemplateView):
    template_name = 'activities/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = Activity.objects.filter(id=kwargs.get('activity_id'), is_active=True).select_related('category').first()
        return context

class ActivitySearchAPIView(TemplateView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Activities API endpoint'})


@login_required
def book_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id, is_active=True)
    if request.method != 'POST':
        return redirect('activities:detail', activity_id=activity.id)

    booking_date = request.POST.get('booking_date') or timezone.localdate().isoformat()
    adults = max(1, int(request.POST.get('adults') or 1))
    children = max(0, int(request.POST.get('children') or 0))
    child_price = activity.price_child if activity.price_child is not None else activity.price_adult * Decimal('0.70')
    total_price = activity.price_adult * adults + child_price * children

    booking, created = ActivityBooking.objects.update_or_create(
        user=request.user,
        activity=activity,
        booking_date=booking_date,
        defaults={
            'adults': adults,
            'children': children,
            'contact_name': request.user.get_full_name() or request.user.email,
            'contact_email': request.user.email,
            'adult_price': activity.price_adult,
            'child_price': child_price,
            'total_price': total_price,
            'status': 'pending',
            'payment_status': 'pending',
        },
    )
    messages.info(request, 'Vui long hoan tat thanh toan de gui booking toi admin xac nhan.')
    return redirect('payments:checkout', booking_type='activity', object_id=booking.id)
