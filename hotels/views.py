import unicodedata
import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from .models import Hotel, City, Country, Amenity, HotelReservation, RoomAvailability, RoomType, Itinerary, ItineraryStop


def normalize_location(value):
    value = (
        value or ""
    ).replace("Đ", "D").replace("đ", "d").replace("Ä", "D").replace("Ä‘", "d").lower()
    return "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )


def serialize_editable_itinerary(itinerary):
    stops_by_day = {}
    for stop in itinerary.stops.all():
        stops_by_day.setdefault(stop.day_number, []).append({
            'id': stop.id,
            'type': stop.activity_type,
            'time_start': stop.start_time.strftime('%H:%M') if stop.start_time else '',
            'title': stop.place_name,
            'description': stop.description,
            'estimated_cost': int(stop.estimated_cost or 0),
            'google_maps_url': stop.google_maps_url,
            'order': stop.order,
        })
    return {
        'id': itinerary.id,
        'title': itinerary.title,
        'days': [
            {
                'day': day_number,
                'activities': stops_by_day.get(day_number, []),
            }
            for day_number in range(1, itinerary.days + 1)
        ],
    }


def default_activity_suggestions(city_name):
    city_key = normalize_location(city_name)
    city_data = {
        'dong do': [
            ('attraction', 'Ho Dong Do SUP va camping', 'Check-in ven ho, SUP nhe, cam trai va BBQ cuoi tuan gan Ha Noi.', 380000),
            ('attraction', 'Rung thong Soc Son picnic', 'Picnic, chup anh doi thong va ket hop cafe/homestay quanh Soc Son.', 250000),
            ('attraction', 'Hoang hon ven ho Dong Do', 'Khung gio chieu de di dao, chup anh va nghi truoc bua BBQ toi.', 80000),
            ('transport', 'Xe rieng Ha Noi - Dong Do', 'Don tu noi thanh Ha Noi, di Soc Son va tra ve homestay/camping ven ho.', 650000),
            ('transport', 'Taxi/Grab noi khu Soc Son', 'Di chuyen giua homestay, ho Dong Do, cafe va diem picnic gan do.', 220000),
            ('transport', 'Thue xe may Soc Son 1 ngay', 'Phu hop nhom nho muon tu di cac diem quanh ho va doi thong.', 180000),
            ('accommodation', 'Lakeside camping stay Dong Do', 'Luu tru ven ho, hop nhom ban thich BBQ, chill dem va di ngan ngay.', 620000),
            ('accommodation', 'Pine hill homestay Soc Son', 'Homestay doi thong gan ho Dong Do, yen tinh va co goc check-in.', 680000),
            ('food', 'BBQ ven ho Dong Do', 'Bua toi phu hop nhom ban sau khi SUP/cam trai.', 250000),
            ('food', 'Cafe chill Soc Son', 'Dung nghi buoi chieu, chup anh va can bang lich trinh.', 90000),
            ('food', 'Bua sang homestay', 'An sang nhe truoc khi di dao ho hoac quay lai Ha Noi.', 70000),
        ],
        'quan lan': [
            ('attraction', 'Bai bien Quan Lan', 'Tam bien, check-in bai cat dai va ngam hoang hon tren dao.', 120000),
            ('attraction', 'Bai Minh Chau', 'Bai cat trang dep, hop chup anh, tam bien va di ca ngay.', 180000),
            ('attraction', 'Eo Gio Quan Lan', 'Diem ngam bien va chup anh tren cung duong xe dien quanh dao.', 160000),
            ('transport', 'Tau cao toc Van Don - Quan Lan', 'Chang di chinh de ra dao Quan Lan tu cang Van Don.', 300000),
            ('transport', 'Xe dien tren dao Quan Lan', 'Di chuyen giua ben tau, homestay, bai bien Quan Lan, Minh Chau va Eo Gio.', 250000),
            ('transport', 'Taxi/xe rieng Ha Noi - Van Don', 'Ket noi san bay/Ha Noi voi cang Van Don truoc khi len tau cao toc.', 1200000),
            ('accommodation', 'Quan Lan beach local stay', 'Local stay gan bien, tien di xe dien va an hai san buoi toi.', 720000),
            ('accommodation', 'Minh Chau white sand homestay', 'Homestay gan Minh Chau, hop nhom ban thich bien vang va khong gian yen tinh.', 760000),
            ('food', 'Hai san Quan Lan', 'Bua toi hai san dia phuong sau khi tam bien va di xe dien quanh dao.', 320000),
            ('food', 'Cafe/chill gan bien Minh Chau', 'Nghi chieu, uong nuoc va sap xep lich ngam hoang hon.', 100000),
            ('food', 'An sang dia phuong tren dao', 'Bua sang gon nhe truoc khi di bai bien hoac quay ve dat lien.', 80000),
        ],
        'da nang': [
            ('attraction', 'Cầu Rồng', 'Check-in biểu tượng Đà Nẵng, đẹp nhất vào buổi tối cuối tuần khi cầu phun lửa/phun nước.', 0),
            ('attraction', 'Bãi biển Mỹ Khê', 'Tắm biển, đi bộ bờ cát và chụp ảnh bình minh.', 50000),
            ('attraction', 'Ngũ Hành Sơn', 'Tham quan hang động, chùa cổ và làng đá Non Nước.', 150000),
            ('attraction', 'Bán đảo Sơn Trà - chùa Linh Ứng', 'Ngắm biển từ bán đảo Sơn Trà và thăm tượng Quan Âm lớn.', 180000),
            ('attraction', 'Bà Nà Hills - Cầu Vàng', 'Đi cáp treo, chụp ảnh Cầu Vàng và khu làng Pháp.', 950000),
            ('attraction', 'Cầu Thuận Phước ngắm hoàng hôn', 'Điểm ngắm hoàng hôn và skyline thành phố ven vịnh.', 50000),
            ('transport', 'Grab/taxi nội thành Đà Nẵng', 'Di chuyển giữa khách sạn, biển Mỹ Khê, Cầu Rồng và chợ đêm.', 180000),
            ('transport', 'Thuê xe máy Đà Nẵng 1 ngày', 'Phù hợp lịch trình Sơn Trà, biển và ăn uống tự do.', 150000),
            ('transport', 'Xe đưa đón sân bay Đà Nẵng', 'Đón/tiễn sân bay về khách sạn khu trung tâm hoặc Mỹ Khê.', 250000),
            ('accommodation', 'Khách sạn trung tâm gần sông Hàn', 'Ở khu Hải Châu để tiện đi Cầu Rồng, chợ Hàn và ăn uống.', 650000),
            ('accommodation', 'Homestay An Thượng/Mỹ Khê', 'Lựa chọn trẻ trung gần biển, tiện cafe và nightlife.', 450000),
            ('accommodation', 'Resort ven biển Sơn Trà - Ngũ Hành Sơn', 'Nghỉ dưỡng cao cấp, hợp lịch trình thư giãn.', 1500000),
            ('food', 'Mì Quảng Đà Nẵng', 'Ăn mì Quảng đặc sản với gà, tôm thịt hoặc ếch.', 70000),
            ('food', 'Bánh tráng cuốn thịt heo', 'Món đặc sản dễ ăn cho nhóm, kèm rau sống và mắm nêm.', 120000),
            ('food', 'Hải sản Mỹ Khê/Võ Nguyên Giáp', 'Ăn tối hải sản ven biển, phù hợp nhóm bạn.', 300000),
            ('food', 'Cafe Sơn Trà hoặc An Thượng', 'Cafe/chill buổi chiều sau khi đi biển hoặc Sơn Trà.', 90000),
            ('food', 'Chợ đêm Sơn Trà', 'Ăn vặt, hải sản và mua quà lưu niệm gần Cầu Rồng.', 180000),
        ],
        'ha noi': [
            ('attraction', 'Hồ Hoàn Kiếm - đền Ngọc Sơn', 'Check-in trung tâm phố cổ, đi bộ quanh hồ và thăm đền Ngọc Sơn.', 80000),
            ('attraction', 'Văn Miếu - Quốc Tử Giám', 'Di tích văn hóa nổi bật, phù hợp chụp ảnh và tìm hiểu lịch sử.', 100000),
            ('attraction', 'Hoàng thành Thăng Long', 'Di sản lịch sử lớn của Hà Nội, nên đi buổi sáng hoặc đầu chiều.', 120000),
            ('attraction', 'Hồ Tây ngắm hoàng hôn', 'Điểm chill cuối ngày, kết hợp chùa Trấn Quốc và cafe ven hồ.', 80000),
            ('attraction', 'Bảo tàng Dân tộc học Việt Nam', 'Bảo tàng dễ đi, nhiều không gian ngoài trời và nhà truyền thống.', 120000),
            ('transport', 'Grab/taxi phố cổ - Hồ Tây', 'Di chuyển giữa phố cổ, Hồ Tây, Văn Miếu và khu Ba Đình.', 180000),
            ('transport', 'Thuê xe máy Hà Nội 1 ngày', 'Phù hợp đi Hồ Tây, bảo tàng và các điểm ngoài phố cổ.', 150000),
            ('transport', 'Xe đưa đón sân bay Nội Bài', 'Đón/tiễn sân bay Nội Bài về khu phố cổ hoặc Tây Hồ.', 350000),
            ('accommodation', 'Khách sạn phố cổ Hà Nội', 'Ở Hoàn Kiếm để tiện ăn uống, đi bộ và tham quan trung tâm.', 700000),
            ('accommodation', 'Homestay Tây Hồ', 'Không gian trẻ trung, nhiều cafe và quán ăn quốc tế.', 500000),
            ('accommodation', 'Boutique hotel khu Tràng Tiền', 'Lưu trú cao cấp hơn, tiện Nhà hát Lớn và Hồ Gươm.', 1200000),
            ('food', 'Phở bò Hà Nội', 'Bữa sáng kinh điển, nên thử ở khu phố cổ hoặc Hoàn Kiếm.', 70000),
            ('food', 'Bún chả Hà Nội', 'Bữa trưa đặc sản với thịt nướng, nước chấm và rau sống.', 90000),
            ('food', 'Cafe trứng phố cổ', 'Cafe/chill buổi chiều, hợp nghỉ chân giữa lịch trình.', 80000),
            ('food', 'Ẩm thực Tạ Hiện/phố cổ', 'Ăn tối, ăn vặt và cảm nhận không khí phố đêm.', 180000),
        ],
    }
    raw_items = city_data.get(city_key) or city_data.get('da nang')
    return [
        {
            'type': activity_type,
            'title': title,
            'description': description,
            'estimated_cost': cost,
            'google_maps_url': f"https://www.google.com/maps/search/?api=1&query={title.replace(' ', '+')}",
        }
        for activity_type, title, description, cost in raw_items
    ]


def infer_activity_type(title):
    title_key = normalize_location(title)
    if any(keyword in title_key for keyword in ['pho', 'bun', 'mi quang', 'hai san', 'am thuc', 'cho dem', 'cafe', 'an toi', 'mon']):
        return 'food'
    if any(keyword in title_key for keyword in ['khach san', 'homestay', 'resort', 'check-in khach san']):
        return 'accommodation'
    if any(keyword in title_key for keyword in ['grab', 'taxi', 'xe', 'san bay', 'thue']):
        return 'transport'
    return 'attraction'


def default_time_for_activity(activity_type, day_number, sequence):
    if activity_type == 'transport':
        return '08:00' if sequence == 1 else '13:30'
    if activity_type == 'food':
        return '12:00' if sequence <= 4 else '19:00'
    if activity_type == 'accommodation':
        return '15:00' if day_number == 1 else '21:00'
    return '09:00' if sequence <= 2 else '16:30'


def session_for_time(time_value):
    if not time_value:
        return 'morning'
    hour = int(time_value.split(':', 1)[0])
    if hour < 12:
        return 'morning'
    if hour < 18:
        return 'afternoon'
    return 'evening'


def option_to_stop(editable_itinerary, option, day_number, order, time_value):
    return ItineraryStop(
        itinerary=editable_itinerary,
        day_number=day_number,
        activity_type=option['type'],
        session=session_for_time(time_value),
        start_time=parse_time(time_value),
        place_name=option['title'],
        description=option['description'],
        duration_hours=Decimal('1.0'),
        estimated_cost=Decimal(str(option['estimated_cost'])),
        currency='VND',
        cost_note='Gợi ý theo plan',
        google_maps_url=option.get('google_maps_url', ''),
        order=order,
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
    paginate_by = 100
    
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
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
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
            'current_querystring': query_params.urlencode(),
        })
        return context


class HotelListView(ListView):
    """General hotel listing view"""
    model = Hotel
    template_name = 'hotels/search_results.html'
    context_object_name = 'hotels'
    paginate_by = 100
    
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


class ItineraryPlannerView(TemplateView):
    template_name = 'hotels/itinerary_planner.html'


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
            Itinerary.objects.filter(is_active=True, created_by__isnull=True)
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
        editable_payload = None
        replacement_options = []
        suggestion_options = default_activity_suggestions(itinerary.city.name)
        if request.user.is_authenticated:
            editable_itinerary, _ = Itinerary.objects.update_or_create(
                created_by=request.user,
                title=f"Lịch trình {itinerary.city.name} tự chỉnh",
                defaults={
                    'city': itinerary.city,
                    'days': days,
                    'description': f'Lịch trình gợi ý từ {itinerary.title}, có thể chỉnh sửa theo nhu cầu cá nhân.',
                    'is_active': True,
                    'order': 0,
                },
            )
            editable_itinerary.stops.all().delete()
            new_stops = [
                ItineraryStop(
                    itinerary=editable_itinerary,
                    day_number=stop.day_number,
                    activity_type=infer_activity_type(stop.place_name),
                    session=stop.session,
                    start_time=stop.start_time,
                    place_name=stop.place_name,
                    description=stop.description,
                    duration_hours=stop.duration_hours,
                    estimated_cost=stop.estimated_cost,
                    currency=stop.currency,
                    cost_note=stop.cost_note,
                    image_url=stop.image_url,
                    google_maps_url=stop.google_maps_url,
                    latitude=stop.latitude,
                    longitude=stop.longitude,
                    order=stop.order,
                )
                for stop in stops
            ]
            suggestion_by_type = {}
            for option in suggestion_options:
                suggestion_by_type.setdefault(option['type'], []).append(option)
            new_stops = []
            plan_slots = [
                ('transport', 1), ('attraction', 0), ('food', 0),
                ('transport', 2), ('accommodation', 1), ('attraction', 1), ('food', 1),
            ]
            for day_number in range(1, days + 1):
                for order, (activity_type, option_index) in enumerate(plan_slots, start=1):
                    if activity_type == 'accommodation' and day_number != 1:
                        continue
                    options = suggestion_by_type.get(activity_type) or []
                    if not options:
                        continue
                    option = options[(option_index + day_number - 1) % len(options)]
                    time_value = default_time_for_activity(activity_type, day_number, order)
                    new_stops.append(option_to_stop(editable_itinerary, option, day_number, order, time_value))
            ItineraryStop.objects.bulk_create(new_stops)
            editable_itinerary = Itinerary.objects.prefetch_related('stops').get(id=editable_itinerary.id)
            editable_payload = serialize_editable_itinerary(editable_itinerary)
            replacement_options = [
                {
                    'day': stop.day_number,
                    'type': stop.activity_type,
                    'time_start': stop.start_time.strftime('%H:%M') if stop.start_time else '',
                    'title': stop.place_name,
                    'description': stop.description,
                    'estimated_cost': int(stop.estimated_cost or 0),
                    'google_maps_url': stop.google_maps_url,
                }
                for stop in itinerary.stops.all()
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
            'editable_itinerary': editable_payload,
            'replacement_options': replacement_options,
            'suggestion_options': suggestion_options,
        })


@login_required
@require_http_methods(["GET", "PATCH"])
def editable_itinerary_api(request, itinerary_id):
    itinerary = get_object_or_404(
        Itinerary.objects.select_related('city').prefetch_related('stops'),
        id=itinerary_id,
    )
    if itinerary.created_by_id and itinerary.created_by_id != request.user.id:
        return JsonResponse({'ok': False, 'message': 'Bạn không có quyền sửa lịch trình này.'}, status=403)
    if not itinerary.created_by_id and not request.user.is_staff:
        return JsonResponse({'ok': False, 'message': 'Chỉ admin được sửa lịch trình mẫu.'}, status=403)

    if request.method == "GET":
        return JsonResponse({'ok': True, 'itinerary': serialize_editable_itinerary(itinerary)})

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'message': 'Payload không hợp lệ.'}, status=400)

    days = payload.get('days', [])
    if not isinstance(days, list) or not days:
        return JsonResponse({'ok': False, 'message': 'Cần ít nhất một ngày trong lịch trình.'}, status=400)

    with transaction.atomic():
        itinerary.days = len(days)
        itinerary.save(update_fields=['days'])
        itinerary.stops.all().delete()
        valid_types = {choice[0] for choice in ItineraryStop.ACTIVITY_TYPES}
        new_stops = []
        for day_index, day in enumerate(days, start=1):
            for order, activity in enumerate(day.get('activities', []), start=1):
                activity_type = activity.get('type') if activity.get('type') in valid_types else 'attraction'
                new_stops.append(ItineraryStop(
                    itinerary=itinerary,
                    day_number=day_index,
                    activity_type=activity_type,
                    session='morning',
                    start_time=parse_time(activity.get('time_start') or '') or None,
                    place_name=(activity.get('title') or 'Hoạt động mới')[:200],
                    description=activity.get('description') or '',
                    duration_hours=Decimal('1.0'),
                    estimated_cost=Decimal(str(activity.get('estimated_cost') or 0)),
                    currency='VND',
                    google_maps_url=activity.get('google_maps_url') or '',
                    order=order,
                ))
        ItineraryStop.objects.bulk_create(new_stops)

    itinerary = Itinerary.objects.prefetch_related('stops').get(id=itinerary.id)
    return JsonResponse({
        'ok': True,
        'message': 'Đã lưu',
        'itinerary': serialize_editable_itinerary(itinerary),
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
                {'min': 0, 'max': 1000000, 'label': 'Duoi 1.000.000 VND'},
                {'min': 1000000, 'max': 2000000, 'label': '1.000.000 - 2.000.000 VND'},
                {'min': 2000000, 'max': 4000000, 'label': '2.000.000 - 4.000.000 VND'},
                {'min': 4000000, 'max': 8000000, 'label': '4.000.000 - 8.000.000 VND'},
                {'min': 8000000, 'max': 999999999, 'label': 'Tren 8.000.000 VND'},
            ],
            'star_ratings': [1, 2, 3, 4, 5],
        })
