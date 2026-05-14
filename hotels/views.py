from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.db.models import Q
from .models import Hotel, City, Country, Amenity


class HomeView(TemplateView):
    """Home page with hotel search functionality"""
    template_name = 'hotels/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Popular cities with hotel counts
        popular_cities = City.objects.filter(is_popular=True)[:8]
        for city in popular_cities:
            city.hotel_count = Hotel.objects.filter(city=city, is_active=True).count()
        
        context.update({
            'popular_cities': popular_cities,
            'featured_hotels': Hotel.objects.filter(is_featured=True, is_active=True)[:6],
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
        queryset = Hotel.objects.filter(is_active=True)
        
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
            for amenity in selected_amenities:
                if amenity == 'wifi':
                    queryset = queryset.filter(amenities__name__icontains='WiFi')
                elif amenity == 'pool':
                    queryset = queryset.filter(amenities__name__icontains='Pool')
                elif amenity == 'gym':
                    queryset = queryset.filter(amenities__name__icontains='Fitness')
                elif amenity == 'parking':
                    queryset = queryset.filter(amenities__name__icontains='Parking')
        
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
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'location': self.request.GET.get('location', ''),
            'checkin': self.request.GET.get('checkin', ''),
            'checkout': self.request.GET.get('checkout', ''),
            'guests': self.request.GET.get('guests', '2'),
            'popular_amenities': Amenity.objects.filter(is_popular=True),
        })
        return context


class HotelListView(ListView):
    """General hotel listing view"""
    model = Hotel
    template_name = 'hotels/search_results.html'
    context_object_name = 'hotels'
    paginate_by = 20
    
    def get_queryset(self):
        return Hotel.objects.filter(is_active=True).order_by('-is_featured', '-average_rating')


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
            'room_types': hotel.room_types.filter(is_active=True),
            'nearby_hotels': Hotel.objects.filter(
                city=hotel.city, is_active=True
            ).exclude(id=hotel.id)[:4],
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
        return Hotel.objects.filter(city__country=country, is_active=True)
    
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
        return Hotel.objects.filter(city=city, is_active=True)
    
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
