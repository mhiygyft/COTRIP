from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

User = get_user_model()


class Country(models.Model):
    """Countries for flight destinations"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO 3166-1 alpha-3
    iso_code = models.CharField(max_length=2, unique=True)  # ISO 3166-1 alpha-2
    currency = models.CharField(max_length=3, default='VND')
    timezone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Airport(models.Model):
    """Airport information for flight origins and destinations"""
    name = models.CharField(max_length=200)
    iata_code = models.CharField(max_length=3, unique=True)  # e.g., JFK, LHR
    icao_code = models.CharField(max_length=4, unique=True, blank=True)  # e.g., KJFK
    
    # Location
    city = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    
    # Airport details
    timezone = models.CharField(max_length=50)
    elevation_ft = models.IntegerField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_international = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.iata_code})"
    
    @property
    def location_string(self):
        return f"{self.city}, {self.country.name}"


class Airline(models.Model):
    """Airline information"""
    name = models.CharField(max_length=100)
    iata_code = models.CharField(max_length=2, unique=True, blank=True)  # e.g., AA, BA
    icao_code = models.CharField(max_length=3, unique=True, blank=True)  # e.g., AAL, BAW
    
    # Airline details
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    logo = models.ImageField(upload_to='airlines/', blank=True, null=True)
    website = models.URLField(blank=True)
    
    # Policies
    baggage_policy = models.TextField(blank=True)
    cancellation_policy = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_low_cost = models.BooleanField(default=False)
    
    # Rating
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.iata_code})"


class Aircraft(models.Model):
    """Aircraft types and configurations"""
    manufacturer = models.CharField(max_length=50)  # Boeing, Airbus, etc.
    model = models.CharField(max_length=50)  # 737-800, A320, etc.
    variant = models.CharField(max_length=50, blank=True)  # -800, neo, etc.
    
    # Capacity
    total_seats = models.PositiveIntegerField()
    economy_seats = models.PositiveIntegerField()
    premium_economy_seats = models.PositiveIntegerField(default=0)
    business_seats = models.PositiveIntegerField(default=0)
    first_class_seats = models.PositiveIntegerField(default=0)
    
    # Specifications
    max_range_km = models.PositiveIntegerField(blank=True, null=True)
    cruise_speed_kmh = models.PositiveIntegerField(blank=True, null=True)
    wingspan_m = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    length_m = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Features
    has_wifi = models.BooleanField(default=False)
    has_entertainment = models.BooleanField(default=False)
    has_power_outlets = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['manufacturer', 'model', 'variant']
        ordering = ['manufacturer', 'model']
    
    def __str__(self):
        variant_str = f" {self.variant}" if self.variant else ""
        return f"{self.manufacturer} {self.model}{variant_str}"
    
    @property
    def display_name(self):
        return str(self)


class Route(models.Model):
    """Popular flight routes between airports"""
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='routes_to')
    
    # Route information
    distance_km = models.PositiveIntegerField()
    typical_duration_minutes = models.PositiveIntegerField()
    is_popular = models.BooleanField(default=False)
    is_domestic = models.BooleanField(default=False)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['origin', 'destination']
        ordering = ['origin__name', 'destination__name']
    
    def __str__(self):
        return f"{self.origin.iata_code} → {self.destination.iata_code}"
    
    @property
    def route_code(self):
        return f"{self.origin.iata_code}-{self.destination.iata_code}"


class Flight(models.Model):
    """Individual flight instances"""
    # Flight identification
    flight_number = models.CharField(max_length=10)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='flights')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='flights')
    
    # Route
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departing_flights')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arriving_flights')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='flights')
    
    # Schedule
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    departure_terminal = models.CharField(max_length=5, blank=True)
    arrival_terminal = models.CharField(max_length=5, blank=True)
    departure_gate = models.CharField(max_length=10, blank=True)
    arrival_gate = models.CharField(max_length=10, blank=True)
    
    # Flight details
    duration_minutes = models.PositiveIntegerField()
    distance_km = models.PositiveIntegerField()
    stops = models.PositiveIntegerField(default=0)  # 0 = direct
    
    # Status
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('delayed', 'Delayed'),
        ('boarding', 'Boarding'),
        ('departed', 'Departed'),
        ('arrived', 'Arrived'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Pricing (base prices, actual prices are in FlightPrice model)
    economy_price = models.DecimalField(max_digits=10, decimal_places=2)
    premium_economy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    business_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    first_class_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Availability
    economy_available = models.PositiveIntegerField()
    premium_economy_available = models.PositiveIntegerField(default=0)
    business_available = models.PositiveIntegerField(default=0)
    first_class_available = models.PositiveIntegerField(default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['airline', 'flight_number', 'departure_time']
        ordering = ['departure_time']
    
    def __str__(self):
        return f"{self.airline.iata_code}{self.flight_number} ({self.origin.iata_code}-{self.destination.iata_code})"
    
    @property
    def flight_code(self):
        return f"{self.airline.iata_code}{self.flight_number}"
    
    @property
    def is_direct(self):
        return self.stops == 0
    
    @property
    def duration_display(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"
    
    def get_price_for_class(self, cabin_class):
        """Get price for specific cabin class"""
        price_map = {
            'economy': self.economy_price,
            'premium_economy': self.premium_economy_price,
            'business': self.business_price,
            'first_class': self.first_class_price,
        }
        return price_map.get(cabin_class)
    
    def get_available_seats_for_class(self, cabin_class):
        """Get available seats for specific cabin class"""
        availability_map = {
            'economy': self.economy_available,
            'premium_economy': self.premium_economy_available,
            'business': self.business_available,
            'first_class': self.first_class_available,
        }
        return availability_map.get(cabin_class, 0)


class FlightSeat(models.Model):
    """Individual seat configuration for flights"""
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='seats')
    
    # Seat identification
    seat_number = models.CharField(max_length=5)  # e.g., 12A, 1F
    row = models.PositiveIntegerField()
    seat_letter = models.CharField(max_length=1)  # A, B, C, etc.
    
    # Seat class
    CABIN_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first_class', 'First Class'),
    ]
    cabin_class = models.CharField(max_length=20, choices=CABIN_CLASS_CHOICES)
    
    # Seat features
    SEAT_TYPE_CHOICES = [
        ('window', 'Window'),
        ('middle', 'Middle'),
        ('aisle', 'Aisle'),
    ]
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES)
    
    # Special features
    is_exit_row = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    has_extra_legroom = models.BooleanField(default=False)
    
    # Status
    is_occupied = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['flight', 'seat_number']
        ordering = ['row', 'seat_letter']
    
    def __str__(self):
        return f"{self.flight.flight_code} - Seat {self.seat_number}"


class BaggageAllowance(models.Model):
    """Baggage allowances for different fare types"""
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='baggage_allowances')
    
    # Fare type
    FARE_TYPE_CHOICES = [
        ('basic', 'Basic Economy'),
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first_class', 'First Class'),
    ]
    fare_type = models.CharField(max_length=20, choices=FARE_TYPE_CHOICES)
    
    # Carry-on allowance
    carryon_pieces = models.PositiveIntegerField(default=1)
    carryon_weight_kg = models.PositiveIntegerField(default=7)
    carryon_dimensions = models.CharField(max_length=50, blank=True)  # e.g., "56x45x25cm"
    
    # Checked baggage allowance
    checked_pieces_included = models.PositiveIntegerField(default=0)
    checked_weight_kg = models.PositiveIntegerField(default=23)
    checked_dimensions = models.CharField(max_length=50, blank=True)
    
    # Additional baggage fees
    extra_bag_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overweight_fee_per_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['airline', 'fare_type']
    
    def __str__(self):
        return f"{self.airline.name} - {self.get_fare_type_display()}"


class SavedFlight(models.Model):
    """Flights saved by users for later booking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_flights')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='saved_by_users')
    cabin_class = models.CharField(max_length=20, choices=FlightSeat.CABIN_CLASS_CHOICES, default='economy')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('user', 'flight', 'cabin_class')
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.email} saved {self.flight.flight_code}"


class FlightSearch(models.Model):
    """Track flight search queries for analytics and saved searches"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Search parameters
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='searches_from')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='searches_to')
    
    departure_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)  # Null for one-way
    
    # Passenger information - updated to match our forms
    passengers = models.PositiveIntegerField(default=1)  # Total passengers for simplicity
    adults = models.PositiveIntegerField(default=1)      # Keep for analytics
    children = models.PositiveIntegerField(default=0)
    infants = models.PositiveIntegerField(default=0)
    
    # Trip type
    TRIP_TYPE_CHOICES = [
        ('one_way', 'One Way'),
        ('round_trip', 'Round Trip'),
        ('multi_city', 'Multi City'),
    ]
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='one_way')
    
    cabin_class = models.CharField(
        max_length=20, 
        choices=FlightSeat.CABIN_CLASS_CHOICES, 
        default='economy'
    )
    
    # Saved search functionality
    search_name = models.CharField(max_length=100, blank=True, help_text="Name for saved searches")
    is_saved = models.BooleanField(default=False)
    
    # Search metadata
    search_timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    results_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        trip_type = "Round-trip" if self.return_date else "One-way"
        return f"{self.origin.iata_code} → {self.destination.iata_code} ({trip_type})"
    
    @property
    def is_round_trip(self):
        return self.return_date is not None
    
    @property
    def total_passengers(self):
        return self.adults + self.children + self.infants
