from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Q
from .models import PackageBooking, TravelPackage

class PackageSearchView(TemplateView):
    template_name = 'packages/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        packages = TravelPackage.objects.filter(is_active=True).prefetch_related('images')
        destination = self.request.GET.get('destination', '').strip()
        package_type = self.request.GET.get('type', '').strip()

        if destination:
            packages = packages.filter(
                Q(destination_city__icontains=destination) |
                Q(destination_country__icontains=destination)
            )
        if package_type:
            packages = packages.filter(package_type=package_type)

        context.update({
            'packages': packages.order_by('-featured', 'title'),
            'package_types': TravelPackage.PACKAGE_TYPE_CHOICES,
            'destination': destination,
            'package_type': package_type,
        })
        return context

class PackageDetailView(TemplateView):
    template_name = 'packages/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['package'] = TravelPackage.objects.filter(
            id=kwargs.get('package_id'),
            is_active=True,
        ).prefetch_related('images', 'components').first()
        return context

class PackageSearchAPIView(TemplateView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Packages API endpoint'})


@login_required
def book_package(request, package_id):
    package = get_object_or_404(TravelPackage, id=package_id, is_active=True)
    if request.method != 'POST':
        return redirect('packages:detail', package_id=package.id)

    departure_raw = request.POST.get('departure_date')
    try:
        departure_date = timezone.datetime.strptime(departure_raw, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        departure_date = timezone.localdate() + timedelta(days=7)

    adults = max(1, int(request.POST.get('adults') or 1))
    children = max(0, int(request.POST.get('children') or 0))
    infants = max(0, int(request.POST.get('infants') or 0))
    child_price = package.child_price if package.child_price is not None else package.base_price_per_person * Decimal('0.70')
    base_price = package.base_price_per_person * adults + child_price * children

    booking = PackageBooking.objects.create(
        user=request.user,
        package=package,
        departure_date=departure_date,
        return_date=departure_date + timedelta(days=package.duration_days),
        adults=adults,
        children=children,
        infants=infants,
        contact_name=request.user.get_full_name() or request.user.email,
        contact_email=request.user.email,
        base_price=base_price,
        total_price=base_price,
        status='pending',
        payment_status='pending',
    )
    messages.info(request, 'Vui lòng hoàn tất thanh toán để gửi booking tới admin xác nhận.')
    return redirect('payments:checkout', booking_type='package', object_id=booking.id)
