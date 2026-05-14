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
            'id', 'name', 'slug', 'color', 'order', 'description',
            'min_points', 'points_multiplier', 'benefits', 'perks',
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
            'points_balance', 'lifetime_points', 'tier_qualifying_points',
            'tier_expires_at', 'joined_at', 'last_activity',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'member_id', 'points_balance', 'lifetime_points',
            'tier_qualifying_points', 'joined_at', 'last_activity', 'created_at', 'updated_at'
        ]


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions"""
    membership = LoyaltyMembershipSerializer(read_only=True)
    membership_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'membership', 'membership_id', 'transaction_type', 'points',
            'description', 'reference_type', 'reference_id', 'booking_reference',
            'expires_at', 'is_expired', 'processed_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_expired', 'processed_at', 'created_at']


class RewardSerializer(serializers.ModelSerializer):
    """Serializer for rewards"""
    
    class Meta:
        model = Reward
        fields = [
            'id', 'name', 'slug', 'description', 'points_required',
            'category', 'reward_type', 'terms_conditions', 'stock_quantity',
            'unlimited_stock', 'min_tier_required', 'valid_from', 'valid_until',
            'is_active', 'created_at', 'updated_at'
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
            'points_used', 'status', 'redemption_code', 'notes',
            'redeemed_at', 'fulfilled_at', 'cancelled_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'points_used', 'redemption_code', 'redeemed_at', 
            'fulfilled_at', 'cancelled_at', 'created_at'
        ]


class LoyaltyPromotionSerializer(serializers.ModelSerializer):
    """Serializer for loyalty promotions"""
    
    class Meta:
        model = LoyaltyPromotion
        fields = [
            'id', 'name', 'slug', 'description', 'promotion_type',
            'bonus_multiplier', 'bonus_points', 'min_spend', 'max_bonus',
            'eligible_tiers', 'terms_conditions', 'promo_code',
            'usage_limit_per_user', 'total_usage_limit', 'current_usage',
            'valid_from', 'valid_until', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'current_usage', 'created_at', 'updated_at']


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
            'booking_amount', 'points_earned', 'bonus_points', 'used_at', 'created_at'
        ]
        read_only_fields = ['id', 'used_at', 'created_at']


# Custom serializers for specific API endpoints
class MembershipStatsSerializer(serializers.Serializer):
    """Serializer for membership statistics"""
    total_points = serializers.IntegerField()
    lifetime_points = serializers.IntegerField()
    tier_qualifying_points = serializers.IntegerField()
    current_tier = LoyaltyTierSerializer()
    next_tier = LoyaltyTierSerializer(allow_null=True)
    points_to_next_tier = serializers.IntegerField(allow_null=True)
    tier_expires_at = serializers.DateTimeField(allow_null=True)
    total_redemptions = serializers.IntegerField()
    last_activity = serializers.DateTimeField(allow_null=True)


class TierProgressSerializer(serializers.Serializer):
    """Serializer for tier progress information"""
    current_tier = LoyaltyTierSerializer()
    next_tier = LoyaltyTierSerializer(allow_null=True)
    progress_percentage = serializers.FloatField()
    points_earned_this_period = serializers.IntegerField()
    points_needed = serializers.IntegerField(allow_null=True)
    tier_expires_at = serializers.DateTimeField(allow_null=True)


class PointsCalculationSerializer(serializers.Serializer):
    """Serializer for points calculation preview"""
    base_points = serializers.IntegerField()
    tier_multiplier = serializers.FloatField()
    promotion_bonus = serializers.IntegerField()
    total_points = serializers.IntegerField()
    tier_qualifying_points = serializers.IntegerField()


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
            'reward_type', 'min_tier_required', 'is_active'
        ]


class PublicLoyaltyTierSerializer(serializers.ModelSerializer):
    """Public serializer for loyalty tiers (limited fields)"""
    
    class Meta:
        model = LoyaltyTier
        fields = [
            'id', 'name', 'color', 'description', 'min_points',
            'points_multiplier', 'benefits', 'perks', 'is_active'
        ]


class PublicPromotionSerializer(serializers.ModelSerializer):
    """Public serializer for promotions (limited fields)"""
    
    class Meta:
        model = LoyaltyPromotion
        fields = [
            'id', 'name', 'description', 'promotion_type',
            'bonus_multiplier', 'bonus_points', 'min_spend',
            'valid_from', 'valid_until', 'is_active'
        ]