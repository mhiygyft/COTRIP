from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class ActivityCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-star')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Activity Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Activity(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('difficult', 'Difficult'),
        ('extreme', 'Extreme'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name='activities')
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    # Location
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.TextField()
    
    # Pricing
    price_adult = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    price_child = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    
    # Activity details
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(Decimal('0.5'))])
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    max_participants = models.PositiveIntegerField()
    min_age = models.PositiveIntegerField(default=0)
    
    # Media
    image_url = models.URLField(blank=True)
    
    # Features
    includes_equipment = models.BooleanField(default=False)
    includes_transport = models.BooleanField(default=False)
    includes_meals = models.BooleanField(default=False)
    includes_guide = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured', 'title']
    
    def __str__(self):
        return f'{self.title} - {self.city}'
    
    @property
    def average_rating(self):
        from reviews.models import Review
        reviews = Review.objects.filter(review_type='service', is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

class ActivityBooking(models.Model):
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_bookings')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    booking_date = models.DateField()
    booking_time = models.TimeField(null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    
    # Contact
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    child_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'activity', 'booking_date']  # One booking per day per activity
    
    def __str__(self):
        return f'{self.user.email} - {self.activity.title} ({self.booking_date})'
