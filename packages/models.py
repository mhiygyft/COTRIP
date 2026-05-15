from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from hotels.models import Hotel
from flights.models import Flight
from activities.models import Activity

User = get_user_model()

class TravelPackage(models.Model):
    PACKAGE_TYPE_CHOICES = [
        ('honeymoon', 'Honeymoon'),
        ('family', 'Family'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('business', 'Business'),
        ('luxury', 'Luxury'),
        ('budget', 'Budget'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    # Destination
    destination_city = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)
    
    # Package details
    duration_days = models.PositiveIntegerField()
    duration_nights = models.PositiveIntegerField()
    
    # Pricing
    base_price_per_person = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    child_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    single_supplement = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # What's included
    includes_flight = models.BooleanField(default=True)
    includes_hotel = models.BooleanField(default=True)
    includes_meals = models.BooleanField(default=False)
    includes_activities = models.BooleanField(default=False)
    includes_transport = models.BooleanField(default=False)
    includes_insurance = models.BooleanField(default=False)
    
    # Package settings
    min_participants = models.PositiveIntegerField(default=1)
    max_participants = models.PositiveIntegerField(default=20)
    
    # Media
    image_url = models.URLField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured', 'title']
    
    def __str__(self):
        return f'{self.title} - {self.duration_days}D/{self.duration_nights}N'
    
    @property
    def total_base_price(self):
        """Calculate total package price for minimum participants"""
        return self.base_price_per_person * self.min_participants

class PackageComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('activity', 'Activity'),
        ('transport', 'Transport'),
        ('meal', 'Meal'),
        ('other', 'Other'),
    ]
    
    package = models.ForeignKey(TravelPackage, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Optional foreign keys to specific items
    flight = models.ForeignKey(Flight, on_delete=models.SET_NULL, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Component details
    day_number = models.PositiveIntegerField()  # Which day of the package
    duration = models.CharField(max_length=100, blank=True)  # e.g., "2 hours", "Full day"
    
    # Pricing (optional override)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    is_optional = models.BooleanField(default=False)
    is_included = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['day_number', 'id']
    
    def __str__(self):
        return f'Day {self.day_number}: {self.title}'

class PackageBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refund_pending', 'Refund Pending'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_bookings')
    package = models.ForeignKey(TravelPackage, on_delete=models.CASCADE, related_name='bookings')
    
    # Travel dates
    departure_date = models.DateField()
    return_date = models.DateField()
    
    # Travelers
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    infants = models.PositiveIntegerField(default=0)
    
    # Contact info
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    additional_services_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customizations
    special_requests = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.email} - {self.package.title} ({self.departure_date})'
