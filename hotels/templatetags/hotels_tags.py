"""
Template tags for hotel-related functionality.

Provides template tags for displaying hotel information
across different pages of the application.
"""
from django import template
from hotels.models import Hotel

register = template.Library()

@register.simple_tag
def get_featured_hotels(limit=3):
    """
    Retrieve featured hotels for display on homepage.
    
    Args:
        limit (int): Maximum number of hotels to return. Default is 3.
        
    Returns:
        QuerySet: Featured hotels with related city and country data.
    """
    return Hotel.objects.filter(
        is_active=True, 
        is_featured=True
    ).select_related('city', 'city__country')[:limit]
