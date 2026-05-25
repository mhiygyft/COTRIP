from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum
from django.utils import timezone
from .models import (
    Country, City, HotelChain, Amenity, Hotel, HotelImage, 
    RoomType, RoomImage, RoomAvailability, HotelReservation, HotelFacility,
    Itinerary, ItineraryStop
)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(file, initial) for file in files]


class HotelAdminForm(forms.ModelForm):
    additional_images = MultipleImageField(
        required=False,
        label='Them nhieu anh',
        help_text='Chon mot hoac nhieu anh de them vao thu vien anh khach san.',
    )

    class Meta:
        model = Hotel
        fields = '__all__'

MODEL_LABELS = {
    Country: ('quoc gia', 'Quoc gia'),
    City: ('thanh pho', 'Thanh pho'),
    HotelChain: ('chuoi khach san', 'Chuoi khach san'),
    Amenity: ('tien nghi', 'Tien nghi'),
    Hotel: ('khach san', 'Khach san'),
    HotelImage: ('anh khach san', 'Anh khach san'),
    RoomType: ('loai phong', 'Loai phong'),
    RoomImage: ('anh phong', 'Anh phong'),
    RoomAvailability: ('lich phong', 'Lich phong'),
    HotelReservation: ('booking khach san', 'Booking khach san'),
    HotelFacility: ('co so vat chat', 'Co so vat chat'),
    Itinerary: ('lich trinh goi y', 'Lich trinh goi y'),
    ItineraryStop: ('diem dung lich trinh', 'Diem dung lich trinh'),
}
for model, (singular, plural) in MODEL_LABELS.items():
    model._meta.verbose_name = singular
    model._meta.verbose_name_plural = plural


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_popular', 'cities_count', 'created_at']
    list_filter = ['is_popular', 'created_at']
    search_fields = ['name', 'code']
    list_editable = ['is_popular']
    
    def cities_count(self, obj):
        return obj.cities.count()
    cities_count.short_description = 'Cities'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'is_popular', 'hotels_count', 'has_coordinates']
    list_filter = ['is_popular', 'country', 'created_at']
    search_fields = ['name', 'country__name']
    list_editable = ['is_popular']
    autocomplete_fields = ['country']
    
    def hotels_count(self, obj):
        return obj.hotels.count()
    hotels_count.short_description = 'Hotels'
    
    def has_coordinates(self, obj):
        return bool(obj.latitude and obj.longitude)
    has_coordinates.boolean = True
    has_coordinates.short_description = 'Coordinates'


@admin.register(HotelChain)
class HotelChainAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotels_count', 'created_at']
    search_fields = ['name']
    
    def hotels_count(self, obj):
        return obj.hotel_set.count()
    hotels_count.short_description = 'Hotels'


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_popular', 'icon', 'usage_count']
    list_filter = ['category', 'is_popular', 'created_at']
    search_fields = ['name']
    list_editable = ['is_popular', 'category']
    
    def usage_count(self, obj):
        return obj.hotel_set.count() + obj.roomtype_set.count()
    usage_count.short_description = 'Usage'


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ['image', 'external_url', 'caption', 'category', 'is_primary', 'display_order']
    

class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ['name', 'base_price', 'max_occupancy', 'is_active']
    readonly_fields = ['slug']


class HotelFacilityInline(admin.TabularInline):
    model = HotelFacility
    extra = 1
    fields = ['name', 'category', 'is_free', 'additional_cost']


class ItineraryStopInline(admin.TabularInline):
    model = ItineraryStop
    extra = 1
    fields = [
        'day_number', 'session', 'start_time', 'place_name', 'duration_hours',
        'estimated_cost', 'currency', 'cost_note', 'image_url', 'google_maps_url', 'order'
    ]


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm
    list_display = [
        'name', 'city', 'star_rating', 'price_from', 'average_rating', 
        'rooms_available_display', 'reservations_count', 'total_reviews',
        'is_active', 'is_featured', 'is_verified'
    ]
    list_filter = [
        'star_rating', 'is_active', 'is_featured', 'is_verified', 
        'city__country', 'hotel_chain', 'created_at'
    ]
    search_fields = ['name', 'city__name', 'city__country__name']
    list_editable = ['is_active', 'is_featured', 'price_from']
    readonly_fields = ['slug', 'total_rooms', 'average_rating', 'total_reviews']
    autocomplete_fields = ['city', 'hotel_chain']
    filter_horizontal = ['amenities']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'city', 'hotel_chain', 'star_rating', 'description')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Pricing & Features', {
            'fields': ('price_from', 'currency', 'amenities')
        }),
        ('Images', {
            'fields': ('image_url', 'additional_images')
        }),
        ('Policies', {
            'fields': ('check_in_time', 'check_out_time', 'cancellation_policy', 'child_policy', 'pet_policy'),
            'classes': ('collapse',)
        }),
        ('Status & SEO', {
            'fields': ('is_active', 'is_featured', 'is_verified', 'meta_title', 'meta_description')
        }),
        ('Statistics', {
            'fields': ('total_rooms', 'average_rating', 'total_reviews'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [HotelImageInline, RoomTypeInline, HotelFacilityInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        images = request.FILES.getlist('additional_images')
        has_primary = obj.images.filter(is_primary=True).exists()
        base_order = obj.images.count()
        for index, image in enumerate(images):
            HotelImage.objects.create(
                hotel=obj,
                image=image,
                is_primary=not has_primary and index == 0,
                display_order=base_order + index,
            )
    
    def get_queryset(self, request):
        today = timezone.localdate()
        room_availability = (
            RoomAvailability.objects
            .filter(room_type__hotel=OuterRef('pk'), date__gte=today)
            .values('room_type__hotel')
            .annotate(total=Sum('available_rooms'))
            .values('total')
        )
        reservations = (
            HotelReservation.objects
            .filter(room_type__hotel=OuterRef('pk'))
            .values('room_type__hotel')
            .annotate(total=Count('id'))
            .values('total')
        )
        return (
            super()
            .get_queryset(request)
            .select_related('city', 'city__country', 'hotel_chain')
            .annotate(
                rooms_available_total=Subquery(room_availability, output_field=IntegerField()),
                reservations_total=Subquery(reservations, output_field=IntegerField()),
            )
        )

    def rooms_available_display(self, obj):
        return obj.rooms_available_total or 0
    rooms_available_display.short_description = 'Phong con'
    rooms_available_display.admin_order_field = 'rooms_available_total'

    def reservations_count(self, obj):
        return obj.reservations_total
    reservations_count.short_description = 'Booking'
    reservations_count.admin_order_field = 'reservations_total'


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'category', 'is_primary', 'display_order', 'image_preview']
    list_filter = ['category', 'is_primary', 'created_at']
    search_fields = ['hotel__name', 'caption']
    list_editable = ['is_primary', 'display_order']
    
    def image_preview(self, obj):
        if obj.image_source_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px;"/>',
                obj.image_source_url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ['image', 'external_url', 'caption', 'is_primary', 'display_order']


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'hotel', 'base_price', 'max_occupancy', 
        'bed_type', 'total_rooms', 'is_active'
    ]
    list_filter = ['is_active', 'bed_type', 'is_refundable', 'hotel__city__country']
    search_fields = ['name', 'hotel__name']
    list_editable = ['base_price', 'is_active']
    readonly_fields = ['slug']
    autocomplete_fields = ['hotel']
    filter_horizontal = ['amenities']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'name', 'slug', 'description')
        }),
        ('Room Details', {
            'fields': ('size_sqm', 'max_occupancy', 'max_adults', 'max_children')
        }),
        ('Bed Configuration', {
            'fields': ('bed_type', 'number_of_beds')
        }),
        ('Pricing & Policies', {
            'fields': ('base_price', 'is_refundable', 'free_cancellation_hours')
        }),
        ('Features & Status', {
            'fields': ('amenities', 'total_rooms', 'is_active')
        })
    )
    
    inlines = [RoomImageInline]


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'room_type', 'date', 'available_rooms', 'price', 
        'is_weekend', 'is_holiday', 'demand_multiplier'
    ]
    list_filter = ['date', 'is_weekend', 'is_holiday', 'room_type__hotel']
    search_fields = ['room_type__name', 'room_type__hotel__name']
    list_editable = ['available_rooms', 'price', 'demand_multiplier']
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('room_type', 'room_type__hotel')


@admin.register(HotelReservation)
class HotelReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'hotel_name', 'room_type', 'stay_date', 'rooms', 'total_price', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'stay_date', 'created_at']
    search_fields = ['user__email', 'contact_email', 'room_type__hotel__name', 'room_type__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'stay_date'

    def hotel_name(self, obj):
        return obj.room_type.hotel.name
    hotel_name.short_description = 'Hotel'

    def get_model_perms(self, request):
        return {}


@admin.register(HotelFacility)
class HotelFacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel', 'category', 'is_free', 'additional_cost', 'is_24_hours']
    list_filter = ['category', 'is_free', 'is_24_hours']
    search_fields = ['name', 'hotel__name']
    list_editable = ['is_free', 'additional_cost']


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'days', 'total_cost_display', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'days', 'city__country']
    search_fields = ['title', 'city__name', 'description']
    list_editable = ['is_active', 'order']
    autocomplete_fields = ['city']
    inlines = [ItineraryStopInline]

    def total_cost_display(self, obj):
        return f"{obj.total_estimated_cost:,.0f} VND"
    total_cost_display.short_description = 'Chi phi du kien'


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ['place_name', 'itinerary', 'day_number', 'session', 'start_time', 'duration_hours', 'estimated_cost', 'order']
    list_filter = ['session', 'day_number', 'itinerary__city']
    search_fields = ['place_name', 'description', 'itinerary__title']
    list_editable = ['day_number', 'session', 'order']
    autocomplete_fields = ['itinerary']


# Custom admin site configuration
admin.site.site_header = 'Vietnam Travel Administration'
admin.site.site_title = 'Vietnam Travel Admin'
admin.site.index_title = 'Quan tri he thong du lich Viet Nam'
