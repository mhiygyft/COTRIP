from django.contrib import admin
from .models import TravelPackage, PackageComponent, PackageBooking

class PackageComponentInline(admin.TabularInline):
    model = PackageComponent
    extra = 1
    fields = ['day_number', 'component_type', 'title', 'description', 'is_optional']

@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    list_display = ['title', 'package_type', 'destination_city', 'duration_days', 'base_price_per_person', 'is_active', 'featured']
    list_filter = ['package_type', 'destination_country', 'is_active', 'featured']
    search_fields = ['title', 'destination_city', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PackageComponentInline]
    actions = ['mark_featured', 'mark_active']
    
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'Marked {queryset.count()} packages as featured.')
    mark_featured.short_description = 'Mark as featured'
    
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} packages.')
    mark_active.short_description = 'Activate selected packages'

@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'departure_date', 'adults', 'children', 'total_price', 'status']
    list_filter = ['status', 'departure_date', 'created_at']
    search_fields = ['user__username', 'package__title', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
