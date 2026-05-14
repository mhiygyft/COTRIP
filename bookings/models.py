from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from decimal import Decimal
import uuid

from flights.models import Flight

User = get_user_model()


class Booking(models.Model):
    """Main booking model for flight reservations"""
    
    # Booking identification
    booking_reference = models.CharField(max_length=10, unique=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # User and flight information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flight_bookings')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    CABIN_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first_class', 'First Class'),
    ]
    cabin_class = models.CharField(max_length=20, choices=CABIN_CLASS_CHOICES, default='economy')
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    taxes_and_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Booking status
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Contact information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Payment information
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('skipped', 'Payment Skipped (Testing)'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Special requests and notes
    special_requests = models.TextField(blank=True, help_text="Meal preferences, accessibility needs, etc.")
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['flight', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate a unique booking reference"""
        import random
        import string
        
        while True:
            # Generate 6-character alphanumeric code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Booking.objects.filter(booking_reference=code).exists():
                return code
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.flight.flight_code}"
    
    @property
    def passenger_count(self):
        return self.passengers.count()
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    @property
    def is_cancellable(self):
        return self.status in ['pending', 'confirmed']
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bookings:booking_detail', args=[self.booking_reference])


class Passenger(models.Model):
    """Individual passenger information for bookings"""
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    
    # Personal information
    TITLE_CHOICES = [
        ('mr', 'Mr.'),
        ('mrs', 'Mrs.'),
        ('ms', 'Ms.'),
        ('dr', 'Dr.'),
        ('prof', 'Prof.'),
        ('child', 'Child'),
        ('infant', 'Infant'),
    ]
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    
    # Date of birth and passenger type
    date_of_birth = models.DateField()
    
    PASSENGER_TYPE_CHOICES = [
        ('adult', 'Adult (12+ years)'),
        ('child', 'Child (2-11 years)'),
        ('infant', 'Infant (under 2 years)'),
    ]
    passenger_type = models.CharField(max_length=10, choices=PASSENGER_TYPE_CHOICES, default='adult')
    
    # Travel document information
    passport_number = models.CharField(max_length=20, blank=True)
    passport_country = models.CharField(max_length=2, blank=True, help_text="ISO country code")
    passport_expiry = models.DateField(null=True, blank=True)
    
    # National ID (alternative to passport for domestic flights)
    national_id = models.CharField(max_length=30, blank=True)
    
    # Contact information (usually same as booking contact for main passenger)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Preferences
    MEAL_PREFERENCE_CHOICES = [
        ('', 'No Preference'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('kosher', 'Kosher'),
        ('halal', 'Halal'),
        ('gluten_free', 'Gluten Free'),
        ('diabetic', 'Diabetic'),
        ('child_meal', 'Child Meal'),
        ('baby_meal', 'Baby Meal'),
    ]
    meal_preference = models.CharField(max_length=20, choices=MEAL_PREFERENCE_CHOICES, blank=True)
    
    # Seat preference
    SEAT_PREFERENCE_CHOICES = [
        ('', 'No Preference'),
        ('window', 'Window'),
        ('aisle', 'Aisle'),
        ('middle', 'Middle'),
    ]
    seat_preference = models.CharField(max_length=10, choices=SEAT_PREFERENCE_CHOICES, blank=True)
    
    # Special needs
    special_assistance = models.TextField(blank=True, help_text="Wheelchair, visual/hearing assistance, etc.")
    
    # Seat assignment (will be assigned later)
    assigned_seat = models.CharField(max_length=5, blank=True, help_text="e.g., 12A")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['passenger_type', 'last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_title_display()} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        return f"{self.get_title_display()} {self.full_name}"
    
    @property
    def age_at_travel(self):
        """Calculate age at the time of travel"""
        travel_date = self.booking.flight.departure_time.date()
        age = travel_date.year - self.date_of_birth.year
        
        if travel_date.month < self.date_of_birth.month or \
           (travel_date.month == self.date_of_birth.month and travel_date.day < self.date_of_birth.day):
            age -= 1
        
        return age


class BookingPayment(models.Model):
    """Payment information for bookings"""
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment method specific fields
    payment_method = models.CharField(max_length=20, choices=Booking.PAYMENT_METHOD_CHOICES)
    
    # Card information (encrypted in production)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_type = models.CharField(max_length=20, blank=True)  # Visa, MasterCard, etc.
    
    # External payment references
    payment_gateway = models.CharField(max_length=50, blank=True)  # Stripe, PayPal, etc.
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_reference = models.CharField(max_length=100, blank=True)
    
    # Payment status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('skipped', 'Skipped (Testing)'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    failure_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment for {self.booking.booking_reference} - {self.status}"
    
    @property
    def is_successful(self):
        return self.status in ['completed', 'skipped']
