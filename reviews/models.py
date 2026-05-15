from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from hotels.models import Hotel
from flights.models import Flight
from bookings.models import Booking

User = get_user_model()

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    REVIEW_TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('flight', 'Flight'),
        ('service', 'Service'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='user_reviews', null=True, blank=True)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Specific rating categories
    cleanliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    service_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    value_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    location_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    # Review status
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'booking']  # One review per booking per user
    
    def __str__(self):
        return f'{self.user.email} - {self.title} ({self.rating}/5)'
    
    @property
    def average_category_rating(self):
        """Calculate average of category ratings if available"""
        ratings = [r for r in [self.cleanliness_rating, self.service_rating, 
                              self.value_rating, self.location_rating] if r is not None]
        return sum(ratings) / len(ratings) if ratings else self.rating


class ReviewHelpful(models.Model):
    """Track if users find reviews helpful"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField()  # True for helpful, False for not helpful
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']  # One vote per user per review
    
    def __str__(self):
        return f'{self.user.username} - {"Helpful" if self.is_helpful else "Not Helpful"}'
