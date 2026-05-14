"""
Custom permissions for the Loyalty Program API
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.utils import timezone


class IsOwnerOrAdmin(BasePermission):
    """
    Permission to only allow owners of an object to edit it, or admin users.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions for admin or owner
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check if user is owner (varies by model)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'membership') and hasattr(obj.membership, 'user'):
            return obj.membership.user == request.user
            
        return False


class IsLoyaltyMemberOrAdmin(BasePermission):
    """
    Permission to only allow loyalty members or admin users.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin users have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check if user has loyalty membership
        from .models import LoyaltyMembership
        return LoyaltyMembership.objects.filter(
            user=request.user,
            status='active'
        ).exists()


class CanRedeemRewards(BasePermission):
    """
    Permission to allow reward redemption based on user's loyalty status.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin users can always redeem
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check loyalty membership status
        from .models import LoyaltyMembership
        try:
            membership = LoyaltyMembership.objects.get(
                user=request.user,
                status='active'
            )
            # User must have points and valid membership
            return membership.points_balance > 0
        except LoyaltyMembership.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Admin users can access any redemption
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Users can only access their own redemptions
        return obj.membership.user == request.user


class IsAdminOrReadOnlyForPublic(BasePermission):
    """
    Permission to allow read-only access for public endpoints,
    but require admin for write operations.
    """
    def has_permission(self, request, view):
        # Read permissions for public endpoints
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for admin users
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class CanAccessPromotions(BasePermission):
    """
    Permission to access promotions based on tier eligibility.
    """
    def has_permission(self, request, view):
        # Public read access for promotion information
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for admin
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
            
        # Write permissions only for admin
        return request.user.is_staff or request.user.is_superuser


class TierBasedAccess(BasePermission):
    """
    Permission based on user's loyalty tier level.
    """
    def __init__(self, min_tier_name=None):
        self.min_tier_name = min_tier_name

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin users have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check tier requirements
        if self.min_tier_name:
            from .models import LoyaltyMembership, LoyaltyTier
            try:
                membership = LoyaltyMembership.objects.select_related('tier').get(
                    user=request.user,
                    status='active'
                )
                min_tier = LoyaltyTier.objects.get(name=self.min_tier_name)
                return membership.tier.min_points >= min_tier.min_points
            except (LoyaltyMembership.DoesNotExist, LoyaltyTier.DoesNotExist):
                return False
                
        return True


class RateLimitByTier(BasePermission):
    """
    Permission to implement different rate limits based on user tier.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return True  # Let rate limiting middleware handle anonymous users
            
        # Admin users bypass rate limiting
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Custom tier-based rate limiting logic would go here
        # For now, allow all authenticated users
        return True


class CanModifyMembership(BasePermission):
    """
    Permission to modify membership details.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin can modify any membership
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Regular users can only view, not modify
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        # Admin can access any membership
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Users can only access their own membership
        if obj.user == request.user:
            # Only allow read operations for regular users
            return request.method in permissions.SAFE_METHODS
            
        return False


class ValidPromotionAccess(BasePermission):
    """
    Permission to ensure users can only access valid, active promotions.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access any promotion
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check if promotion is active and valid
        now = timezone.now()
        if not obj.is_active:
            return False
            
        if obj.valid_from and obj.valid_from > now:
            return False
            
        if obj.valid_until and obj.valid_until < now:
            return False
            
        # Check tier eligibility
        if request.user.is_authenticated:
            from .models import LoyaltyMembership
            try:
                membership = LoyaltyMembership.objects.get(
                    user=request.user,
                    status='active'
                )
                
                # If promotion has tier restrictions, check them
                if obj.eligible_tiers.exists():
                    return membership.tier in obj.eligible_tiers.all()
                    
            except LoyaltyMembership.DoesNotExist:
                return False
                
        return True


# Permission classes for specific viewsets
class LoyaltyTierPermissions(permissions.BasePermission):
    """Specific permissions for loyalty tier operations"""
    def has_permission(self, request, view):
        if view.action == 'public':
            return True  # Public access
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser


class LoyaltyMembershipPermissions(permissions.BasePermission):
    """Specific permissions for membership operations"""
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user == request.user and request.method in permissions.SAFE_METHODS


class RewardPermissions(permissions.BasePermission):
    """Specific permissions for reward operations"""
    def has_permission(self, request, view):
        if view.action in ['public', 'list', 'retrieve']:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action == 'redeem':
            return request.user.is_authenticated
        return request.user.is_staff or request.user.is_superuser


# Utility functions for permission checking
def check_loyalty_membership(user):
    """Check if user has active loyalty membership"""
    if not user.is_authenticated:
        return False
        
    from .models import LoyaltyMembership
    return LoyaltyMembership.objects.filter(
        user=user,
        status='active'
    ).exists()


def check_tier_requirement(user, min_tier_name):
    """Check if user meets minimum tier requirement"""
    if not user.is_authenticated:
        return False
        
    if user.is_staff or user.is_superuser:
        return True
        
    from .models import LoyaltyMembership, LoyaltyTier
    try:
        membership = LoyaltyMembership.objects.select_related('tier').get(
            user=user,
            status='active'
        )
        min_tier = LoyaltyTier.objects.get(name=min_tier_name)
        return membership.tier.min_points >= min_tier.min_points
    except (LoyaltyMembership.DoesNotExist, LoyaltyTier.DoesNotExist):
        return False


def can_redeem_reward(user, reward):
    """Check if user can redeem specific reward"""
    if not user.is_authenticated:
        return False, "Authentication required"
        
    if user.is_staff or user.is_superuser:
        return True, None
        
    from .models import LoyaltyMembership
    try:
        membership = LoyaltyMembership.objects.get(
            user=user,
            status='active'
        )
        
        # Check points requirement
        if reward.points_required > membership.points_balance:
            return False, "Insufficient points"
            
        # Check tier requirement
        if reward.min_tier_required and \
           reward.min_tier_required.min_points > membership.tier.min_points:
            return False, "Tier requirement not met"
            
        # Check stock
        if not reward.unlimited_stock and reward.stock_quantity <= 0:
            return False, "Out of stock"
            
        # Check validity period
        now = timezone.now()
        if reward.valid_from and reward.valid_from > now:
            return False, "Not yet available"
            
        if reward.valid_until and reward.valid_until < now:
            return False, "Expired"
            
        return True, None
        
    except LoyaltyMembership.DoesNotExist:
        return False, "No active loyalty membership found"