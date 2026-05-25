from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from decimal import Decimal

User = get_user_model()


class Country(models.Model):
    """Country model for location hierarchy"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO country code
    flag_url = models.URLField(blank=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class City(models.Model):
    """City model for location hierarchy"""
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    image = models.ImageField(upload_to='cities/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Cities"
        unique_together = ['name', 'country']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"

    @property
    def image_source_url(self):
        if self.image:
            return self.image.url
        city_images = {
            "Ha Noi": "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=900&q=80",
            "Da Nang": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=900&q=80",
            "Hoi An": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=900&q=80",
            "Phu Quoc": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
            "Sa Pa": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
            "Hue": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=900&q=80",
            "Nha Trang": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=900&q=80",
            "Da Lat": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=900&q=80",
            "Quy Nhon": "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=900&q=80",
            "Can Tho": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=900&q=80",
            "Ha Long": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80",
            "Ninh Binh": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=900&q=80",
            "Ha Giang": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
            "Mui Ne": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
            "Con Dao": "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=900&q=80",
        }
        return city_images.get(self.name, "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=900&q=80")


class HotelChain(models.Model):
    """Hotel chain/brand model"""
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='hotel_chains/', blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Amenity(models.Model):
    """Hotel amenities model"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    category = models.CharField(max_length=50, choices=[
        ('general', 'General'),
        ('internet', 'Internet'),
        ('parking', 'Parking'),
        ('transportation', 'Transportation'),
        ('services', 'Services'),
        ('business', 'Business'),
        ('wellness', 'Wellness & Fitness'),
        ('food_drink', 'Food & Drink'),
        ('entertainment', 'Entertainment'),
        ('family', 'Family'),
        ('accessibility', 'Accessibility'),
        ('safety', 'Safety & Security'),
    ], default='general')
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name


class Hotel(models.Model):
    """Main Hotel model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    # Location
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='hotels')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    
    # Basic Information
    description = models.TextField()
    star_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Hotel star rating (1-5)"
    )
    hotel_chain = models.ForeignKey(HotelChain, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact Information
    phone_number = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Features
    amenities = models.ManyToManyField(Amenity, blank=True)
    image_url = models.URLField(blank=True, help_text="Primary hotel image URL")
    
    # Policies
    check_in_time = models.TimeField(default='15:00')
    check_out_time = models.TimeField(default='11:00')
    cancellation_policy = models.TextField(blank=True)
    child_policy = models.TextField(blank=True)
    pet_policy = models.TextField(blank=True)
    
    # Pricing
    price_from = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Starting price per night"
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Statistics (cached values)
    total_rooms = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-average_rating', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city.name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def get_absolute_url(self):
        return reverse('hotels:hotel_detail', kwargs={'slug': self.slug})
    
    @property
    def location_string(self):
        return f"{self.city.name}, {self.city.country.name}"
    
    @property
    def star_range(self):
        return range(self.star_rating)
    
    def get_star_display(self):
        return '★' * self.star_rating + '☆' * (5 - self.star_rating)


    @property
    def primary_image_url(self):
        primary_image = self.images.filter(is_primary=True).first() or self.images.first()
        if primary_image:
            return primary_image.image_source_url
        if self.image_url and not self.image_url.startswith(('http://', 'https://', '/')):
            return f"{settings.MEDIA_URL}{self.image_url.lstrip('/')}"
        return self.image_url


class HotelImage(models.Model):
    """Hotel images model"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotels/', blank=True)
    external_url = models.URLField(blank=True, help_text="Optional real image URL")
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    
    # Image categories
    category = models.CharField(max_length=50, choices=[
        ('exterior', 'Exterior'),
        ('lobby', 'Lobby'),
        ('room', 'Room'),
        ('bathroom', 'Bathroom'),
        ('restaurant', 'Restaurant'),
        ('pool', 'Pool'),
        ('gym', 'Gym/Fitness'),
        ('spa', 'Spa'),
        ('meeting', 'Meeting Room'),
        ('amenity', 'Amenity'),
        ('view', 'View'),
        ('other', 'Other'),
    ], default='other')
    
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', '-is_primary', 'created_at']
    
    def __str__(self):
        return f"{self.hotel.name} - {self.category} Image"

    @property
    def image_source_url(self):
        if self.external_url:
            return self.external_url
        if self.image:
            return self.image.url
        return ""


class RoomType(models.Model):
    """Room types model"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, blank=True)
    
    # Room Details
    description = models.TextField()
    size_sqm = models.PositiveIntegerField(blank=True, null=True, help_text="Room size in square meters")
    max_occupancy = models.PositiveIntegerField(default=2)
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=0)
    
    # Bed Configuration
    bed_type = models.CharField(max_length=50, choices=[
        ('single', 'Single Bed'),
        ('twin', 'Twin Beds'),
        ('double', 'Double Bed'),
        ('queen', 'Queen Bed'),
        ('king', 'King Bed'),
        ('sofa', 'Sofa Bed'),
        ('bunk', 'Bunk Bed'),
        ('murphy', 'Murphy Bed'),
    ], default='double')
    number_of_beds = models.PositiveIntegerField(default=1)
    
    # Room Features
    amenities = models.ManyToManyField(Amenity, blank=True)
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Policies
    is_refundable = models.BooleanField(default=True)
    free_cancellation_hours = models.PositiveIntegerField(
        default=24, 
        help_text="Hours before check-in for free cancellation"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    total_rooms = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hotel', 'slug']
        ordering = ['base_price']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class RoomImage(models.Model):
    """Room type images"""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/', blank=True)
    external_url = models.URLField(blank=True, help_text="Optional real room image URL")
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', '-is_primary']
    
    def __str__(self):
        return f"{self.room_type} - Image"

    @property
    def image_source_url(self):
        if self.external_url:
            return self.external_url
        if self.image:
            return self.image.url
        return ""


class RoomAvailability(models.Model):
    """Room availability and pricing by date"""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    available_rooms = models.PositiveIntegerField(default=0)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Dynamic pricing factors
    is_weekend = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    demand_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('1.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['room_type', 'date']
        ordering = ['date']
    
    def __str__(self):
        return f"{self.room_type} - {self.date} - {self.available_rooms} rooms"


class HotelReservation(models.Model):
    """Operational booking record for hotel room reservations."""

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
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_reservations')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='reservations')
    stay_date = models.DateField()
    rooms = models.PositiveIntegerField(default=1)
    price_per_room = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    contact_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['stay_date']),
        ]

    def __str__(self):
        return f"Hotel reservation {self.id} - {self.room_type.hotel.name}"

    @property
    def hotel(self):
        return self.room_type.hotel


class HotelFacility(models.Model):
    """Detailed hotel facilities with descriptions"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='facilities')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    category = models.CharField(max_length=50, choices=[
        ('dining', 'Dining'),
        ('recreation', 'Recreation'),
        ('business', 'Business'),
        ('wellness', 'Wellness'),
        ('connectivity', 'Connectivity'),
        ('transportation', 'Transportation'),
        ('services', 'Services'),
        ('accessibility', 'Accessibility'),
    ])
    
    is_free = models.BooleanField(default=True)
    additional_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Cost if not free"
    )
    
    operating_hours = models.CharField(max_length=100, blank=True)
    is_24_hours = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class Itinerary(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='itineraries')
    title = models.CharField(max_length=200)
    days = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'days']

    def __str__(self):
        return f"{self.city.name} - {self.title}"

    @property
    def total_estimated_cost(self):
        return sum(stop.estimated_cost or 0 for stop in self.stops.all())


class ItineraryStop(models.Model):
    DAY_SESSION = [
        ('morning', 'Buổi sáng'),
        ('afternoon', 'Buổi chiều'),
        ('evening', 'Buổi tối'),
    ]

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='stops')
    day_number = models.PositiveIntegerField()
    session = models.CharField(max_length=20, choices=DAY_SESSION, default='morning')
    place_name = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.TimeField(blank=True, null=True)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    currency = models.CharField(max_length=3, default='VND')
    cost_note = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['day_number', 'order']

    def __str__(self):
        return f"Ngày {self.day_number} {self.get_session_display()} - {self.place_name}"


class Review(models.Model):
    """Hotel review model"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Helpful for moderation
    is_verified = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hotel', 'user']  # One review per user per hotel
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.hotel.name} ({self.rating}★)"
    
    @property
    def star_display(self):
        return '★' * self.rating + '☆' * (5 - self.rating)
