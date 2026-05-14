from django.contrib import admin
from .models import Activity, ActivityCategory, ActivityBooking

@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'city', 'price_adult', 'difficulty', 'is_active', 'featured']
    list_filter = ['category', 'difficulty', 'is_active', 'featured', 'city']
    search_fields = ['title', 'city', 'description']
    prepopulated_fields = {'slug': ('title',)}
    actions = ['mark_featured', 'mark_active']
    
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'Marked {queryset.count()} activities as featured.')
    mark_featured.short_description = 'Mark as featured'
    
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} activities.')
    mark_active.short_description = 'Activate selected activities'

@admin.register(ActivityBooking)
class ActivityBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'booking_date', 'adults', 'children', 'total_price', 'status']
    list_filter = ['status', 'booking_date', 'created_at']
    search_fields = ['user__username', 'activity__title', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
