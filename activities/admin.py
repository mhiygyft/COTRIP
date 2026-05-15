from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Activity, ActivityCategory, ActivityBooking, ActivityImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(file, initial) for file in files]


class ActivityAdminForm(forms.ModelForm):
    additional_images = MultipleImageField(
        required=False,
        label='Them nhieu anh',
        help_text='Chon mot hoac nhieu anh de them vao thu vien anh trai nghiem.',
    )

    class Meta:
        model = Activity
        fields = '__all__'


class ActivityImageInline(admin.TabularInline):
    model = ActivityImage
    extra = 1
    fields = ['image', 'caption', 'alt_text', 'is_primary', 'display_order']

MODEL_LABELS = {
    ActivityCategory: ("loai trai nghiem", "Loai trai nghiem"),
    Activity: ("trai nghiem", "Trai nghiem"),
    ActivityImage: ("anh trai nghiem", "Anh trai nghiem"),
    ActivityBooking: ("booking trai nghiem", "Booking trai nghiem"),
}
for model, (singular, plural) in MODEL_LABELS.items():
    model._meta.verbose_name = singular
    model._meta.verbose_name_plural = plural

@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    form = ActivityAdminForm
    list_display = [
        'title', 'category', 'city', 'price_adult', 'difficulty',
        'max_participants', 'booking_count_display', 'paid_count_display',
        'is_active', 'featured'
    ]
    list_filter = ['category', 'difficulty', 'is_active', 'featured', 'city']
    search_fields = ['title', 'city', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ActivityImageInline]
    actions = ['mark_featured', 'mark_active']
    fieldsets = (
        ('Thong tin co ban', {
            'fields': ('title', 'slug', 'category', 'description', 'short_description')
        }),
        ('Dia diem', {
            'fields': ('city', 'country', 'address')
        }),
        ('Gia va chi tiet', {
            'fields': ('price_adult', 'price_child', 'duration_hours', 'difficulty', 'max_participants', 'min_age')
        }),
        ('Hinh anh', {
            'fields': ('image_url', 'additional_images')
        }),
        ('Bao gom', {
            'fields': ('includes_equipment', 'includes_transport', 'includes_meals', 'includes_guide')
        }),
        ('Trang thai', {
            'fields': ('is_active', 'featured')
        }),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                booking_total=Count('bookings', distinct=True),
                paid_total=Count('bookings', filter=Q(bookings__payment_status='completed'), distinct=True),
            )
        )

    def booking_count_display(self, obj):
        return obj.booking_total
    booking_count_display.short_description = 'Booking'
    booking_count_display.admin_order_field = 'booking_total'

    def paid_count_display(self, obj):
        return obj.paid_total
    paid_count_display.short_description = 'Da thanh toan'
    paid_count_display.admin_order_field = 'paid_total'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        images = request.FILES.getlist('additional_images')
        has_primary = obj.images.filter(is_primary=True).exists()
        base_order = obj.images.count()
        for index, image in enumerate(images):
            ActivityImage.objects.create(
                activity=obj,
                image=image,
                is_primary=not has_primary and index == 0,
                display_order=base_order + index,
            )
    
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'Marked {queryset.count()} activities as featured.')
    mark_featured.short_description = 'Mark as featured'
    
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} activities.')
    mark_active.short_description = 'Activate selected activities'


@admin.register(ActivityImage)
class ActivityImageAdmin(admin.ModelAdmin):
    list_display = ['activity', 'is_primary', 'display_order', 'image_preview']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['activity__title', 'caption']
    list_editable = ['is_primary', 'display_order']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover;"/>', obj.image.url)
        return 'No image'
    image_preview.short_description = 'Preview'

@admin.register(ActivityBooking)
class ActivityBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'booking_date', 'adults', 'children', 'total_price', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'booking_date', 'created_at']
    search_fields = ['user__email', 'activity__title', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']

    def get_model_perms(self, request):
        return {}
