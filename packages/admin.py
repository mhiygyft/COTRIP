from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import TravelPackage, PackageComponent, PackageBooking, PackageImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(file, initial) for file in files]


class TravelPackageAdminForm(forms.ModelForm):
    additional_images = MultipleImageField(
        required=False,
        label='Thêm nhiều ảnh',
        help_text='Chọn một hoặc nhiều ảnh để thêm vào thư viện ảnh tour.',
    )

    class Meta:
        model = TravelPackage
        fields = '__all__'


class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1
    fields = ['image', 'external_url', 'caption', 'alt_text', 'is_primary', 'display_order']

MODEL_LABELS = {
    TravelPackage: ("tour trọn gói", "Tour trọn gói"),
    PackageImage: ("ảnh tour", "Ảnh tour"),
    PackageComponent: ("lịch trình tour", "Lịch trình tour"),
    PackageBooking: ("booking tour", "Booking tour"),
}
for model, (singular, plural) in MODEL_LABELS.items():
    model._meta.verbose_name = singular
    model._meta.verbose_name_plural = plural

class PackageComponentInline(admin.TabularInline):
    model = PackageComponent
    extra = 1
    fields = ['day_number', 'component_type', 'title', 'description', 'is_optional']

@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    form = TravelPackageAdminForm
    list_display = [
        'title', 'package_type', 'destination_city', 'duration_days',
        'base_price_per_person', 'max_participants', 'booking_count_display',
        'paid_count_display', 'is_active', 'featured'
    ]
    list_filter = ['package_type', 'destination_country', 'is_active', 'featured']
    search_fields = ['title', 'destination_city', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PackageImageInline, PackageComponentInline]
    actions = ['mark_featured', 'mark_active']
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'package_type', 'description', 'short_description')
        }),
        ('Điểm đến và thời lượng', {
            'fields': ('destination_city', 'destination_country', 'duration_days', 'duration_nights')
        }),
        ('Giá và sức chứa', {
            'fields': ('base_price_per_person', 'child_price', 'single_supplement', 'min_participants', 'max_participants')
        }),
        ('Hình ảnh và video', {
            'fields': ('image_url', 'additional_images', 'video_url', 'affiliate_url', 'affiliate_label')
        }),
        ('Bao gồm', {
            'fields': ('includes_flight', 'includes_hotel', 'includes_meals', 'includes_activities', 'includes_transport', 'includes_insurance')
        }),
        ('Trạng thái', {
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
    paid_count_display.short_description = 'Đã thanh toán'
    paid_count_display.admin_order_field = 'paid_total'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        images = request.FILES.getlist('additional_images')
        has_primary = obj.images.filter(is_primary=True).exists()
        base_order = obj.images.count()
        for index, image in enumerate(images):
            PackageImage.objects.create(
                package=obj,
                image=image,
                is_primary=not has_primary and index == 0,
                display_order=base_order + index,
            )
    
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f'Marked {queryset.count()} packages as featured.')
    mark_featured.short_description = 'Mark as featured'
    
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} packages.')
    mark_active.short_description = 'Activate selected packages'


@admin.register(PackageImage)
class PackageImageAdmin(admin.ModelAdmin):
    list_display = ['package', 'is_primary', 'display_order', 'image_preview']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['package__title', 'caption']
    list_editable = ['is_primary', 'display_order']

    def image_preview(self, obj):
        if obj.image_source_url:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover;"/>', obj.image_source_url)
        return 'No image'
    image_preview.short_description = 'Preview'

@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'departure_date', 'adults', 'children', 'total_price', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'departure_date', 'created_at']
    search_fields = ['user__email', 'package__title', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']

    def get_model_perms(self, request):
        return {}
