from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Country, City, HotelChain, Amenity, Hotel, HotelImage, 
    RoomType, RoomImage, RoomAvailability, HotelFacility
)


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
    fields = ['image', 'caption', 'category', 'is_primary', 'display_order']
    

class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ['name', 'base_price', 'max_occupancy', 'is_active']
    readonly_fields = ['slug']


class HotelFacilityInline(admin.TabularInline):
    model = HotelFacility
    extra = 1
    fields = ['name', 'category', 'is_free', 'additional_cost']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'city', 'star_rating', 'price_from', 'average_rating', 
        'total_reviews', 'is_active', 'is_featured', 'is_verified'
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city', 'city__country', 'hotel_chain')


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'category', 'is_primary', 'display_order', 'image_preview']
    list_filter = ['category', 'is_primary', 'created_at']
    search_fields = ['hotel__name', 'caption']
    list_editable = ['is_primary', 'display_order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px;"/>',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'display_order']


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


@admin.register(HotelFacility)
class HotelFacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel', 'category', 'is_free', 'additional_cost', 'is_24_hours']
    list_filter = ['category', 'is_free', 'is_24_hours']
    search_fields = ['name', 'hotel__name']
    list_editable = ['is_free', 'additional_cost']


# Custom admin site configuration
admin.site.site_header = 'Novaryo Administration'
admin.site.site_title = 'Novaryo Admin'
admin.site.index_title = 'Welcome to Novaryo Administration Portal'
