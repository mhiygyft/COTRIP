import unicodedata
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Hotel, City, Country, Amenity, HotelReservation, RoomAvailability, RoomType, Itinerary


def normalize_location(value):
    value = (value or "").replace("Đ", "D").replace("đ", "d").lower()
    return "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )


class HomeView(TemplateView):
    """Home page with hotel search functionality"""
    template_name = 'hotels/home.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Popular cities with hotel counts
        popular_cities = City.objects.filter(is_popular=True)[:8]
        for city in popular_cities:
            city.hotel_count = Hotel.objects.filter(city=city, is_active=True).count()
        
        context.update({
            'popular_cities': popular_cities,
            'featured_hotels': Hotel.objects.filter(is_featured=True, is_active=True).prefetch_related('images')[:6],
            'total_hotels': Hotel.objects.filter(is_active=True).count(),
        })
        return context


class HotelSearchView(ListView):
    """Hotel search results view"""
    model = Hotel
    template_name = 'hotels/search_results.html'
    context_object_name = 'hotels'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True).prefetch_related('images', 'amenities')
        
        # Search filters
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(
                Q(city__name__icontains=location) |
                Q(city__country__name__icontains=location) |
                Q(name__icontains=location)
            )
        
        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price_from__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_from__lte=max_price)
        
        # Star rating filter (multiple selections)
        star_ratings = self.request.GET.getlist('stars')
        if star_ratings:
            queryset = queryset.filter(star_rating__in=star_ratings)
        
        # Amenities filter
        selected_amenities = self.request.GET.getlist('amenities')
        if selected_amenities:
            queryset = queryset.filter(amenities__id__in=selected_amenities)
        
        # Sort by
        sort_by = self.request.GET.get('sort', 'featured')
        if sort_by == 'price_low':
            queryset = queryset.order_by('price_from')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price_from')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-average_rating')
        else:  # featured
            queryset = queryset.order_by('-is_featured', '-average_rating')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'location': self.request.GET.get('location', ''),
            'checkin': self.request.GET.get('checkin', ''),
            'checkout': self.request.GET.get('checkout', ''),
            'guests': self.request.GET.get('guests', '2'),
            'popular_amenities': Amenity.objects.filter(is_popular=True),
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'selected_stars': self.request.GET.getlist('stars'),
            'selected_amenities': self.request.GET.getlist('amenities'),
            'sort': self.request.GET.get('sort', 'featured'),
        })
        return context


class HotelListView(ListView):
    """General hotel listing view"""
    model = Hotel
    template_name = 'hotels/search_results.html'
    context_object_name = 'hotels'
    paginate_by = 20
    
    def get_queryset(self):
        return Hotel.objects.filter(is_active=True).prefetch_related('images', 'amenities').order_by('-is_featured', '-average_rating')


class HotelDetailView(DetailView):
    """Hotel detail view"""
    model = Hotel
    template_name = 'hotels/hotel_detail.html'
    context_object_name = 'hotel'
    
    def get_object(self):
        return get_object_or_404(Hotel, slug=self.kwargs['slug'], is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel = self.get_object()
        context.update({
            'room_types': hotel.room_types.filter(is_active=True).prefetch_related('images', 'amenities'),
            'nearby_hotels': Hotel.objects.filter(
                city=hotel.city, is_active=True
            ).exclude(id=hotel.id).prefetch_related('images')[:4],
            'default_stay_date': timezone.localdate() + timedelta(days=1),
        })
        return context


class DestinationListView(ListView):
    """Popular destinations listing"""
    model = City
    template_name = 'hotels/destinations.html'
    context_object_name = 'cities'
    
    def get_queryset(self):
        return City.objects.filter(is_popular=True)


class CountryHotelsView(ListView):
    """Hotels in a specific country"""
    model = Hotel
    template_name = 'hotels/country_hotels.html'
    context_object_name = 'hotels'
    paginate_by = 20
    
    def get_queryset(self):
        country = get_object_or_404(Country, code=self.kwargs['country_code'])
        return Hotel.objects.filter(city__country=country, is_active=True).prefetch_related('images', 'amenities')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['country'] = get_object_or_404(Country, code=self.kwargs['country_code'])
        return context


class CityHotelsView(ListView):
    """Hotels in a specific city"""
    model = Hotel
    template_name = 'hotels/city_hotels.html'
    context_object_name = 'hotels'
    paginate_by = 20
    
    def get_queryset(self):
        city = get_object_or_404(City, id=self.kwargs['city_id'])
        return Hotel.objects.filter(city=city, is_active=True).prefetch_related('images', 'amenities')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = get_object_or_404(City, id=self.kwargs['city_id'])
        
        # Other popular cities in the same country
        other_popular_cities = City.objects.filter(
            country=city.country, 
            is_popular=True
        ).exclude(id=city.id)[:4]
        
        for other_city in other_popular_cities:
            other_city.hotel_count = Hotel.objects.filter(city=other_city, is_active=True).count()
        
        context.update({
            'city': city,
            'other_popular_cities': other_popular_cities,
            'itineraries': Itinerary.objects.filter(
                city=city, is_active=True
            ).prefetch_related('stops'),
        })
        return context


# API Views for AJAX requests
class SearchSuggestionsView(TemplateView):
    """API endpoint for search suggestions"""
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        suggestions = []
        
        if len(query) >= 2:
            # Search cities
            cities = City.objects.filter(
                Q(name__icontains=query) | Q(country__name__icontains=query)
            )[:5]
            
            for city in cities:
                suggestions.append({
                    'type': 'city',
                    'name': f"{city.name}, {city.country.name}",
                    'id': city.id,
                })
            
            # Search hotels
            hotels = Hotel.objects.filter(
                name__icontains=query, is_active=True
            )[:3]
            
            for hotel in hotels:
                suggestions.append({
                    'type': 'hotel',
                    'name': hotel.name,
                    'location': hotel.location_string,
                    'id': hotel.id,
                })
        
        return JsonResponse({'suggestions': suggestions})


class HotelAvailabilityView(TemplateView):
    """API endpoint for hotel availability"""
    
    def get(self, request, *args, **kwargs):
        hotel_id = kwargs.get('hotel_id')
        # This would integrate with booking system
        # For now, return mock data
        return JsonResponse({
            'available': True,
            'rooms': [
                {'type': 'Standard Room', 'price': 120, 'available': 3},
                {'type': 'Deluxe Room', 'price': 180, 'available': 2},
            ]
        })


class ItineraryBuilderAPIView(TemplateView):
    """Compact embeddable itinerary planner API."""

    def get(self, request, *args, **kwargs):
        destination = request.GET.get('destination', '').strip()
        try:
            days = max(1, min(int(request.GET.get('days', 3)), 7))
        except (TypeError, ValueError):
            days = 3
        try:
            budget = int(request.GET.get('budget') or 0)
        except (TypeError, ValueError):
            budget = 0
        try:
            travelers = max(1, min(int(request.GET.get('travelers', 1)), 20))
        except (TypeError, ValueError):
            travelers = 1

        if not destination:
            return JsonResponse({
                'ok': False,
                'message': 'Vui lòng nhập địa điểm bạn muốn đi.',
            }, status=400)

        destination_key = normalize_location(destination)
        itineraries = list(
            Itinerary.objects.filter(is_active=True)
            .select_related('city', 'city__country')
            .prefetch_related('stops')
        )
        matches = [
            itinerary for itinerary in itineraries
            if destination_key in normalize_location(itinerary.city.name)
            or destination_key in normalize_location(itinerary.city.country.name)
        ]
        if not matches:
            return JsonResponse({
                'ok': False,
                'message': f'Chưa có dữ liệu lịch trình cho "{destination}".',
            }, status=404)

        itinerary = sorted(matches, key=lambda item: (abs(item.days - days), item.order, item.days))[0]
        stops = [
            stop for stop in itinerary.stops.all()
            if stop.day_number <= days
        ]
        daily_plan = []
        total_cost = 0
        for day_number in range(1, days + 1):
            day_stops = [stop for stop in stops if stop.day_number == day_number]
            day_cost_per_person = sum(int(stop.estimated_cost or 0) for stop in day_stops)
            day_cost = day_cost_per_person * travelers
            total_cost += day_cost
            daily_plan.append({
                'day': day_number,
                'estimated_cost_per_person': day_cost_per_person,
                'estimated_cost': day_cost,
                'stops': [
                    {
                        'id': stop.id,
                        'time': stop.start_time.strftime('%H:%M') if stop.start_time else '',
                        'session': stop.get_session_display(),
                        'place_name': stop.place_name,
                        'description': stop.description,
                        'duration_hours': float(stop.duration_hours),
                        'estimated_cost_per_person': int(stop.estimated_cost or 0),
                        'estimated_cost': int(stop.estimated_cost or 0) * travelers,
                        'currency': stop.currency,
                        'cost_note': stop.cost_note,
                        'google_maps_url': stop.google_maps_url,
                    }
                    for stop in day_stops
                ],
            })

        return JsonResponse({
            'ok': True,
            'destination': itinerary.city.name,
            'title': itinerary.title,
            'days': days,
            'travelers': travelers,
            'requested_budget': budget,
            'estimated_cost_per_person': total_cost // travelers,
            'estimated_cost': total_cost,
            'over_budget': bool(budget and total_cost > budget),
            'budget_gap': max(total_cost - budget, 0) if budget else 0,
            'daily_plan': daily_plan,
        })


@login_required
def reserve_room(request, room_type_id):
    room_type = get_object_or_404(RoomType.objects.select_related('hotel'), id=room_type_id, is_active=True)
    if request.method != 'POST':
        return redirect('hotels:hotel_detail', slug=room_type.hotel.slug)

    stay_date_raw = request.POST.get('stay_date')
    try:
        stay_date = datetime.strptime(stay_date_raw, '%Y-%m-%d').date() if stay_date_raw else timezone.localdate()
    except ValueError:
        stay_date = timezone.localdate()

    if stay_date < timezone.localdate():
        messages.error(request, 'Ngày nhận phòng không được ở quá khứ.')
        return redirect('hotels:hotel_detail', slug=room_type.hotel.slug)

    with transaction.atomic():
        availability, _ = RoomAvailability.objects.select_for_update().get_or_create(
            room_type=room_type,
            date=stay_date,
            defaults={
                'available_rooms': max(1, int(room_type.total_rooms * 0.7)),
                'price': room_type.base_price,
            },
        )
        if availability.available_rooms <= 0:
            messages.error(request, 'Phòng này đã hết chỗ cho ngày bạn chọn.')
            return redirect('hotels:hotel_detail', slug=room_type.hotel.slug)

        availability.available_rooms -= 1
        availability.save()
        reservation = HotelReservation.objects.create(
            user=request.user,
            room_type=room_type,
            stay_date=stay_date,
            rooms=1,
            price_per_room=availability.price,
            total_price=availability.price,
            contact_email=request.user.email,
            status='pending',
            payment_status='pending',
        )

    messages.info(request, f'Đã giữ 1 phòng {room_type.name}. Vui lòng thanh toán để gửi admin xác nhận.')
    return redirect('payments:checkout', booking_type='hotel', object_id=reservation.id)


class FilterOptionsView(TemplateView):
    """API endpoint for filter options"""
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'amenities': list(Amenity.objects.filter(is_popular=True).values('id', 'name')),
            'price_ranges': [
                {'min': 0, 'max': 50, 'label': 'Under $50'},
                {'min': 50, 'max': 100, 'label': '$50 - $100'},
                {'min': 100, 'max': 200, 'label': '$100 - $200'},
                {'min': 200, 'max': 500, 'label': '$200 - $500'},
                {'min': 500, 'max': 9999, 'label': 'Over $500'},
            ],
            'star_ratings': [1, 2, 3, 4, 5],
        })
