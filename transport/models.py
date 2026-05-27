import random
import string

from django.conf import settings
from django.db import models
from django.urls import reverse


class TransportProvider(models.Model):
    TYPE_CHOICES = [
        ('train', 'Tau hoa'),
        ('bus', 'Xe khach'),
    ]

    provider_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['provider_type', 'name']

    def __str__(self):
        return self.name


class TransportStation(models.Model):
    TYPE_CHOICES = [
        ('train_station', 'Ga tau'),
        ('bus_station', 'Ben xe / diem don'),
    ]

    station_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    google_maps_url = models.URLField(blank=True)
    is_popular = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city}"


class TransportRoute(models.Model):
    transport_type = models.CharField(max_length=20, choices=TransportProvider.TYPE_CHOICES)
    origin = models.ForeignKey(TransportStation, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(TransportStation, on_delete=models.CASCADE, related_name='routes_to')
    distance_km = models.PositiveIntegerField(default=0)
    typical_duration_minutes = models.PositiveIntegerField(default=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['transport_type', 'origin', 'destination']
        ordering = ['transport_type', 'origin__city', 'destination__city']

    def __str__(self):
        return f"{self.origin.city} -> {self.destination.city}"


class TransportTrip(models.Model):
    SEAT_CLASS_CHOICES = [
        ('standard', 'Pho thong'),
        ('sleeper', 'Giuong nam'),
        ('vip', 'Limousine/VIP'),
        ('soft_seat', 'Ghe mem'),
        ('soft_sleeper', 'Giuong nam mem'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Dang mo ban'),
        ('sold_out', 'Het cho'),
        ('cancelled', 'Da huy'),
    ]

    route = models.ForeignKey(TransportRoute, on_delete=models.CASCADE, related_name='trips')
    provider = models.ForeignKey(TransportProvider, on_delete=models.CASCADE, related_name='trips')
    trip_code = models.CharField(max_length=30)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    seat_class = models.CharField(max_length=30, choices=SEAT_CLASS_CHOICES)
    vehicle_type = models.CharField(max_length=100, blank=True)
    pickup_note = models.CharField(max_length=255, blank=True)
    dropoff_note = models.CharField(max_length=255, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.PositiveIntegerField(default=20)
    total_seats = models.PositiveIntegerField(default=40)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['departure_time']
        unique_together = ['provider', 'trip_code', 'departure_time']

    def __str__(self):
        return f"{self.trip_code} {self.route.origin.city}-{self.route.destination.city}"

    @property
    def transport_type(self):
        return self.route.transport_type

    @property
    def duration_display(self):
        hours = self.route.typical_duration_minutes // 60
        minutes = self.route.typical_duration_minutes % 60
        return f"{hours}h {minutes}m"


class TransportBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Cho xac nhan'),
        ('confirmed', 'Da xac nhan'),
        ('cancelled', 'Da huy'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'The tin dung / ghi no'),
        ('bank_transfer', 'Chuyen khoan ngan hang'),
        ('cash', 'Thanh toan khi nhan ve'),
        ('skipped', 'Thanh toan demo'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transport_bookings')
    booking_reference = models.CharField(max_length=10, unique=True, editable=False)
    trip = models.ForeignKey(TransportTrip, on_delete=models.CASCADE, related_name='bookings')
    passengers = models.PositiveIntegerField(default=1)
    contact_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=30)
    contact_email = models.EmailField()
    pickup_location = models.ForeignKey(TransportStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_bookings')
    dropoff_location = models.ForeignKey(TransportStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='dropoff_bookings')
    special_requests = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        while True:
            code = 'TR' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not TransportBooking.objects.filter(booking_reference=code).exists():
                return code

    def __str__(self):
        return f"{self.booking_reference} - {self.trip}"

    @property
    def is_cancellable(self):
        return self.status in {'pending', 'confirmed'}

    def get_absolute_url(self):
        return reverse('transport:booking_detail', args=[self.booking_reference])

# Create your models here.
