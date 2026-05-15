"""
Serializers for the Loyalty Program API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    LoyaltyTier, LoyaltyMembership, PointsTransaction, Reward, 
    RewardRedemption, LoyaltyPromotion, PromotionUsage
)

User = get_user_model()


class LoyaltyTierSerializer(serializers.ModelSerializer):
    """Serializer for loyalty tiers"""
    
    class Meta:
        model = LoyaltyTier
        fields = [
            'id', 'name', 'slug', 'color_code', 'icon', 'order', 'description',
            'min_spending', 'min_flights', 'min_points', 'points_multiplier',
            'priority_boarding', 'free_baggage_allowance', 'lounge_access',
            'free_seat_selection', 'upgrade_priority',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoyaltyMembershipSerializer(serializers.ModelSerializer):
    """Serializer for loyalty membership"""
    tier = LoyaltyTierSerializer(read_only=True)
    tier_id = serializers.IntegerField(write_only=True, required=False)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = LoyaltyMembership
        fields = [
            'id', 'user', 'user_email', 'member_id', 'tier', 'tier_id',
            'points_balance', 'lifetime_points', 'annual_spending',
            'annual_flights', 'annual_points_earned', 'tier_achieved_date',
            'tier_expires_date', 'joined_date', 'last_activity_date',
            'tracking_year', 'is_active'
        ]
        read_only_fields = [
            'id', 'user', 'member_id', 'points_balance', 'lifetime_points',
            'annual_spending', 'annual_flights', 'annual_points_earned',
            'tier_achieved_date', 'joined_date', 'last_activity_date'
        ]


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions"""
    membership = LoyaltyMembershipSerializer(read_only=True)
    membership_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'membership', 'membership_id', 'transaction_type', 'points',
            'balance_after', 'description', 'reference_id',
            'expires_at', 'is_expired', 'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'is_expired', 'created_at']


class RewardSerializer(serializers.ModelSerializer):
    """Serializer for rewards"""
    
    class Meta:
        model = Reward
        fields = [
            'id', 'name', 'slug', 'description', 'points_required',
            'cash_equivalent', 'category', 'stock_quantity', 'minimum_tier',
            'valid_from', 'valid_until', 'is_available', 'featured', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class RewardRedemptionSerializer(serializers.ModelSerializer):
    """Serializer for reward redemptions"""
    membership = LoyaltyMembershipSerializer(read_only=True)
    membership_id = serializers.IntegerField(write_only=True)
    reward = RewardSerializer(read_only=True)
    reward_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RewardRedemption
        fields = [
            'id', 'membership', 'membership_id', 'reward', 'reward_id',
            'redemption_id', 'points_redeemed', 'status', 'booking_reference',
            'notes', 'fulfilled_at', 'fulfilled_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'redemption_id', 'points_redeemed', 'fulfilled_at',
            'fulfilled_by', 'created_at', 'updated_at'
        ]


class LoyaltyPromotionSerializer(serializers.ModelSerializer):
    """Serializer for loyalty promotions"""
    
    class Meta:
        model = LoyaltyPromotion
        fields = [
            'id', 'name', 'slug', 'description', 'promotion_type',
            'multiplier', 'bonus_points', 'minimum_spending',
            'eligible_tiers', 'max_uses_per_member',
            'valid_from', 'valid_until', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class PromotionUsageSerializer(serializers.ModelSerializer):
    """Serializer for promotion usage tracking"""
    membership = LoyaltyMembershipSerializer(read_only=True)
    membership_id = serializers.IntegerField(write_only=True)
    promotion = LoyaltyPromotionSerializer(read_only=True)
    promotion_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PromotionUsage
        fields = [
            'id', 'membership', 'membership_id', 'promotion', 'promotion_id',
            'spending_amount', 'points_earned', 'booking_reference', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']


# Custom serializers for specific API endpoints
class MembershipStatsSerializer(serializers.Serializer):
    """Serializer for membership statistics"""
    total_points = serializers.IntegerField()
    lifetime_points = serializers.IntegerField()
    annual_points_earned = serializers.IntegerField()
    current_tier = LoyaltyTierSerializer()
    next_tier = LoyaltyTierSerializer(allow_null=True)
    points_to_next_tier = serializers.IntegerField(allow_null=True)
    tier_expires_date = serializers.DateTimeField(allow_null=True)
    total_redemptions = serializers.IntegerField()
    last_activity = serializers.DateTimeField(allow_null=True)


class TierProgressSerializer(serializers.Serializer):
    """Serializer for tier progress information"""
    current_tier = LoyaltyTierSerializer()
    next_tier = LoyaltyTierSerializer(allow_null=True)
    progress_percentage = serializers.FloatField()
    points_earned_this_period = serializers.IntegerField()
    points_needed = serializers.IntegerField(allow_null=True)
    tier_expires_date = serializers.DateTimeField(allow_null=True)


class PointsCalculationSerializer(serializers.Serializer):
    """Serializer for points calculation preview"""
    base_points = serializers.IntegerField()
    tier_multiplier = serializers.FloatField()
    promotion_bonus = serializers.IntegerField()
    total_points = serializers.IntegerField()
    annual_points_earned = serializers.IntegerField()


class RewardAvailabilitySerializer(serializers.Serializer):
    """Serializer for reward availability check"""
    reward = RewardSerializer()
    can_redeem = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)
    points_needed = serializers.IntegerField(allow_null=True)
    tier_required = LoyaltyTierSerializer(allow_null=True)


# Bulk operation serializers
class BulkPointsTransactionSerializer(serializers.Serializer):
    """Serializer for bulk points operations"""
    membership_ids = serializers.ListField(child=serializers.IntegerField())
    transaction_type = serializers.ChoiceField(choices=PointsTransaction.TRANSACTION_TYPES)
    points = serializers.IntegerField()
    description = serializers.CharField(max_length=255)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class MembershipUpgradeSerializer(serializers.Serializer):
    """Serializer for membership tier upgrades"""
    membership_id = serializers.IntegerField()
    new_tier_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255, required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


# Public API serializers (limited fields)
class PublicRewardSerializer(serializers.ModelSerializer):
    """Public serializer for rewards (limited fields)"""
    
    class Meta:
        model = Reward
        fields = [
            'id', 'name', 'description', 'points_required', 'category',
            'minimum_tier', 'is_available'
        ]


class PublicLoyaltyTierSerializer(serializers.ModelSerializer):
    """Public serializer for loyalty tiers (limited fields)"""
    
    class Meta:
        model = LoyaltyTier
        fields = [
            'id', 'name', 'color_code', 'description', 'min_points',
            'points_multiplier', 'is_active'
        ]


class PublicPromotionSerializer(serializers.ModelSerializer):
    """Public serializer for promotions (limited fields)"""
    
    class Meta:
        model = LoyaltyPromotion
        fields = [
            'id', 'name', 'description', 'promotion_type',
            'multiplier', 'bonus_points', 'minimum_spending',
            'valid_from', 'valid_until', 'is_active'
        ]
