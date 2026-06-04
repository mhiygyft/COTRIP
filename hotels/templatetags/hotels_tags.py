"""
Template tags for hotel-related functionality.

Provides template tags for displaying hotel information
across different pages of the application.
"""
from django import template
from hotels.models import Hotel
import re

register = template.Library()

PUBLIC_SOURCE_NOTE_RE = re.compile(
    r"\s*(?:Du lieu tham khao tu nguon cong khai|Dữ liệu tham khảo từ nguồn công khai):\s*\S+\s*",
    re.IGNORECASE,
)


@register.filter
def without_public_source_note(value):
    if value is None:
        return ""
    return PUBLIC_SOURCE_NOTE_RE.sub("", str(value)).strip()

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
