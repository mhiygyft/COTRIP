from django.contrib import admin
from .models import Review, ReviewHelpful

Review._meta.verbose_name = "danh gia"
Review._meta.verbose_name_plural = "Danh gia"
ReviewHelpful._meta.verbose_name = "phan hoi danh gia"
ReviewHelpful._meta.verbose_name_plural = "Phan hoi danh gia"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'rating', 'review_type', 'is_verified', 'is_approved', 'created_at']
    list_filter = ['review_type', 'rating', 'is_verified', 'is_approved', 'created_at']
    search_fields = ['title', 'comment', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'verify_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'Approved {queryset.count()} reviews.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def verify_reviews(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f'Verified {queryset.count()} reviews.')
    verify_reviews.short_description = 'Verify selected reviews'

@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['review__title', 'user__email']
