from django import template
from django.contrib.auth import get_user_model
from loyalty.utils import calculate_points_preview, get_member_tier_benefits

User = get_user_model()
register = template.Library()


@register.inclusion_tag('loyalty/tags/points_preview.html', takes_context=True)
def show_points_preview(context, amount):
    """
    Display points that would be earned for a booking amount
    Usage: {% show_points_preview booking_amount %}
    """
    user = context.get('user')
    points_info = None
    
    if user and user.is_authenticated:
        points_info = calculate_points_preview(user, float(amount))
    
    return {
        'user': user,
        'amount': amount,
        'points_info': points_info,
        'is_authenticated': user.is_authenticated if user else False
    }


@register.inclusion_tag('loyalty/tags/tier_benefits.html', takes_context=True)
def show_tier_benefits(context):
    """
    Display current user's tier benefits
    Usage: {% show_tier_benefits %}
    """
    user = context.get('user')
    benefits = None
    
    if user and user.is_authenticated:
        benefits = get_member_tier_benefits(user)
    
    return {
        'user': user,
        'benefits': benefits,
        'is_authenticated': user.is_authenticated if user else False
    }


@register.simple_tag
def get_points_for_amount(user, amount):
    """
    Simple tag to get points amount for a booking
    Usage: {% get_points_for_amount user booking_amount as points %}
    """
    if not user or not user.is_authenticated:
        return int(float(amount))  # Base rate for non-members
    
    points_info = calculate_points_preview(user, float(amount))
    return points_info.get('total_points', int(float(amount)))


@register.filter
def has_loyalty_membership(user):
    """
    Check if user has a loyalty membership
    Usage: {{ user|has_loyalty_membership }}
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        return hasattr(user, 'loyalty_membership') and user.loyalty_membership is not None
    except:
        return False


@register.filter
def loyalty_tier_name(user):
    """
    Get user's loyalty tier name
    Usage: {{ user|loyalty_tier_name }}
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        return user.loyalty_membership.tier.name
    except:
        return None


@register.filter
def loyalty_tier_color(user):
    """
    Get user's loyalty tier color
    Usage: {{ user|loyalty_tier_color }}
    """
    if not user or not user.is_authenticated:
        return '#6c757d'  # Default gray
    
    try:
        return user.loyalty_membership.tier.color_code
    except:
        return '#6c757d'


@register.filter
def points_balance(user):
    """
    Get user's current points balance
    Usage: {{ user|points_balance }}
    """
    if not user or not user.is_authenticated:
        return 0
    
    try:
        return user.loyalty_membership.points_balance
    except:
        return 0


@register.simple_tag
def tier_benefit_check(user, benefit_name):
    """
    Check if user's tier includes a specific benefit
    Usage: {% tier_benefit_check user 'priority_boarding' as has_priority %}
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        tier = user.loyalty_membership.tier
        return getattr(tier, benefit_name, False)
    except:
        return False