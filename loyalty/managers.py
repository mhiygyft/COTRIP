"""
Optimized managers and querysets for loyalty models
"""
from django.db import models
from django.db.models import Prefetch, F, Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta


class LoyaltyTierQuerySet(models.QuerySet):
    """Optimized queryset for LoyaltyTier model"""
    
    def active(self):
        """Get only active tiers"""
        return self.filter(is_active=True)
    
    def ordered(self):
        """Get tiers in order"""
        return self.order_by('order')
    
    def with_member_counts(self):
        """Annotate with member counts"""
        return self.annotate(
            member_count=Count('members', filter=Q(members__is_active=True))
        )
    
    def for_points(self, points):
        """Get appropriate tier for given points"""
        return self.active().filter(min_points__lte=points).order_by('-min_points').first()


class LoyaltyTierManager(models.Manager):
    """Manager for LoyaltyTier model"""
    
    def get_queryset(self):
        return LoyaltyTierQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def ordered(self):
        return self.get_queryset().ordered()
    
    def with_member_counts(self):
        return self.get_queryset().with_member_counts()
    
    def for_points(self, points):
        return self.get_queryset().for_points(points)


class LoyaltyMembershipQuerySet(models.QuerySet):
    """Optimized queryset for LoyaltyMembership model"""
    
    def active(self):
        """Get only active memberships"""
        return self.filter(is_active=True)
    
    def with_user_and_tier(self):
        """Prefetch user and tier data"""
        return self.select_related('user', 'tier', 'previous_tier')
    
    def with_recent_transactions(self, limit=10):
        """Prefetch recent points transactions"""
        from .models import PointsTransaction
        
        recent_transactions = PointsTransaction.objects.select_related(
            'membership'
        ).order_by('-created_at')[:limit]
        
        return self.prefetch_related(
            Prefetch('points_transactions', queryset=recent_transactions)
        )
    
    def with_statistics(self):
        """Annotate with membership statistics"""
        return self.annotate(
            total_transactions=Count('points_transactions'),
            total_earned_points=Sum(
                'points_transactions__points',
                filter=Q(points_transactions__transaction_type='earn')
            ),
            total_redeemed_points=Sum(
                'points_transactions__points',
                filter=Q(points_transactions__transaction_type='redeem')
            ),
            avg_transaction_amount=Avg('points_transactions__points'),
            last_transaction_date=models.Max('points_transactions__created_at')
        )
    
    def by_tier(self, tier_name):
        """Filter by tier name"""
        return self.filter(tier__name__iexact=tier_name)
    
    def by_tier_level(self, min_order=None, max_order=None):
        """Filter by tier level"""
        filters = {}
        if min_order is not None:
            filters['tier__order__gte'] = min_order
        if max_order is not None:
            filters['tier__order__lte'] = max_order
        return self.filter(**filters)
    
    def high_value(self, min_points=10000):
        """Get high-value members"""
        return self.filter(lifetime_points__gte=min_points)
    
    def recent_activity(self, days=30):
        """Members with recent activity"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(last_activity_date__gte=cutoff_date)
    
    def eligible_for_upgrade(self):
        """Members eligible for tier upgrade"""
        return self.extra(
            where=[
                """
                EXISTS (
                    SELECT 1 FROM loyalty_loyaltytier lt2 
                    WHERE lt2.order > loyalty_loyaltytier.order 
                    AND loyalty_loyaltymembership.annual_spending >= lt2.min_spending
                    AND loyalty_loyaltymembership.annual_flights >= lt2.min_flights
                    AND loyalty_loyaltymembership.lifetime_points >= lt2.min_points
                    AND lt2.is_active = true
                )
                """
            ]
        )


class LoyaltyMembershipManager(models.Manager):
    """Manager for LoyaltyMembership model"""
    
    def get_queryset(self):
        return LoyaltyMembershipQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def with_user_and_tier(self):
        return self.get_queryset().with_user_and_tier()
    
    def with_recent_transactions(self, limit=10):
        return self.get_queryset().with_recent_transactions(limit)
    
    def with_statistics(self):
        return self.get_queryset().with_statistics()
    
    def by_tier(self, tier_name):
        return self.get_queryset().by_tier(tier_name)
    
    def high_value(self, min_points=10000):
        return self.get_queryset().high_value(min_points)
    
    def recent_activity(self, days=30):
        return self.get_queryset().recent_activity(days)
    
    def eligible_for_upgrade(self):
        return self.get_queryset().eligible_for_upgrade()


class PointsTransactionQuerySet(models.QuerySet):
    """Optimized queryset for PointsTransaction model"""
    
    def with_membership_data(self):
        """Prefetch membership and related data"""
        return self.select_related(
            'membership__user',
            'membership__tier'
        )
    
    def earned_points(self):
        """Get only earned points transactions"""
        return self.filter(transaction_type='earn')
    
    def redeemed_points(self):
        """Get only redeemed points transactions"""
        return self.filter(transaction_type='redeem')
    
    def expired_points(self):
        """Get expired points transactions"""
        return self.filter(
            expires_at__lt=timezone.now(),
            transaction_type='earn'
        )
    
    def active_points(self):
        """Get non-expired earned points"""
        return self.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()),
            transaction_type='earn'
        )
    
    def for_user(self, user):
        """Get transactions for specific user"""
        return self.filter(membership__user=user)
    
    def recent(self, days=30):
        """Get recent transactions"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def by_date_range(self, start_date, end_date):
        """Filter by date range"""
        return self.filter(
            created_at__date__range=[start_date, end_date]
        )
    
    def summary_stats(self):
        """Get summary statistics"""
        return self.aggregate(
            total_points=Sum('points'),
            total_earned=Sum('points', filter=Q(transaction_type='earn')),
            total_redeemed=Sum('points', filter=Q(transaction_type='redeem')),
            transaction_count=Count('id'),
            avg_transaction=Avg('points'),
            latest_transaction=models.Max('created_at'),
            earliest_transaction=models.Min('created_at')
        )


class PointsTransactionManager(models.Manager):
    """Manager for PointsTransaction model"""
    
    def get_queryset(self):
        return PointsTransactionQuerySet(self.model, using=self._db)
    
    def with_membership_data(self):
        return self.get_queryset().with_membership_data()
    
    def earned_points(self):
        return self.get_queryset().earned_points()
    
    def redeemed_points(self):
        return self.get_queryset().redeemed_points()
    
    def expired_points(self):
        return self.get_queryset().expired_points()
    
    def active_points(self):
        return self.get_queryset().active_points()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def recent(self, days=30):
        return self.get_queryset().recent(days)
    
    def summary_stats(self):
        return self.get_queryset().summary_stats()


class RewardQuerySet(models.QuerySet):
    """Optimized queryset for Reward model"""
    
    def active(self):
        """Get only active rewards"""
        return self.filter(is_active=True)
    
    def available(self):
        """Get currently available rewards"""
        now = timezone.now()
        return self.filter(
            is_active=True,
            Q(valid_from__isnull=True) | Q(valid_from__lte=now),
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        )
    
    def in_stock(self):
        """Get rewards that are in stock"""
        return self.filter(
            Q(unlimited_stock=True) | Q(stock_quantity__gt=0)
        )
    
    def by_category(self, category):
        """Filter by reward category"""
        return self.filter(category=category)
    
    def by_type(self, reward_type):
        """Filter by reward type"""
        return self.filter(reward_type=reward_type)
    
    def affordable_for_user(self, user):
        """Get rewards user can afford"""
        try:
            membership = user.loyalty_membership
            return self.filter(points_required__lte=membership.points_balance)
        except:
            return self.none()
    
    def for_tier(self, tier):
        """Get rewards available for specific tier"""
        return self.filter(
            Q(min_tier_required__isnull=True) | 
            Q(min_tier_required__order__lte=tier.order)
        )
    
    def with_redemption_counts(self):
        """Annotate with redemption counts"""
        return self.annotate(
            total_redemptions=Count('redemptions'),
            successful_redemptions=Count(
                'redemptions',
                filter=Q(redemptions__status__in=['redeemed', 'fulfilled'])
            )
        )


class RewardManager(models.Manager):
    """Manager for Reward model"""
    
    def get_queryset(self):
        return RewardQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def available(self):
        return self.get_queryset().available()
    
    def in_stock(self):
        return self.get_queryset().in_stock()
    
    def by_category(self, category):
        return self.get_queryset().by_category(category)
    
    def affordable_for_user(self, user):
        return self.get_queryset().affordable_for_user(user)
    
    def for_tier(self, tier):
        return self.get_queryset().for_tier(tier)
    
    def with_redemption_counts(self):
        return self.get_queryset().with_redemption_counts()


class RewardRedemptionQuerySet(models.QuerySet):
    """Optimized queryset for RewardRedemption model"""
    
    def with_related_data(self):
        """Prefetch related data"""
        return self.select_related(
            'membership__user',
            'membership__tier',
            'reward'
        )
    
    def pending(self):
        """Get pending redemptions"""
        return self.filter(status='pending')
    
    def completed(self):
        """Get completed redemptions"""
        return self.filter(status__in=['redeemed', 'fulfilled'])
    
    def for_user(self, user):
        """Get redemptions for specific user"""
        return self.filter(membership__user=user)
    
    def by_status(self, status):
        """Filter by redemption status"""
        return self.filter(status=status)
    
    def recent(self, days=30):
        """Get recent redemptions"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(redeemed_at__gte=cutoff_date)


class RewardRedemptionManager(models.Manager):
    """Manager for RewardRedemption model"""
    
    def get_queryset(self):
        return RewardRedemptionQuerySet(self.model, using=self._db)
    
    def with_related_data(self):
        return self.get_queryset().with_related_data()
    
    def pending(self):
        return self.get_queryset().pending()
    
    def completed(self):
        return self.get_queryset().completed()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def recent(self, days=30):
        return self.get_queryset().recent(days)


class LoyaltyPromotionQuerySet(models.QuerySet):
    """Optimized queryset for LoyaltyPromotion model"""
    
    def active(self):
        """Get only active promotions"""
        return self.filter(is_active=True)
    
    def current(self):
        """Get currently running promotions"""
        now = timezone.now()
        return self.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )
    
    def for_tier(self, tier):
        """Get promotions available for specific tier"""
        return self.filter(
            Q(eligible_tiers__isnull=True) |
            Q(eligible_tiers=tier)
        ).distinct()
    
    def with_usage_stats(self):
        """Annotate with usage statistics"""
        return self.annotate(
            usage_count=Count('promotion_usage'),
            unique_users=Count('promotion_usage__membership__user', distinct=True)
        )


class LoyaltyPromotionManager(models.Manager):
    """Manager for LoyaltyPromotion model"""
    
    def get_queryset(self):
        return LoyaltyPromotionQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def current(self):
        return self.get_queryset().current()
    
    def for_tier(self, tier):
        return self.get_queryset().for_tier(tier)
    
    def with_usage_stats(self):
        return self.get_queryset().with_usage_stats()


# Utility functions for complex queries
def get_membership_with_full_data(user):
    """Get membership with all related data optimized"""
    try:
        return LoyaltyMembership.objects.select_related(
            'user', 'tier', 'previous_tier'
        ).prefetch_related(
            Prefetch(
                'points_transactions',
                queryset=PointsTransaction.objects.select_related('membership').order_by('-created_at')[:20]
            ),
            Prefetch(
                'reward_redemptions',
                queryset=RewardRedemption.objects.select_related('reward').order_by('-redeemed_at')[:10]
            )
        ).get(user=user, is_active=True)
    except LoyaltyMembership.DoesNotExist:
        return None


def get_loyalty_dashboard_data(user):
    """Get all data needed for loyalty dashboard in optimized queries"""
    membership = get_membership_with_full_data(user)
    if not membership:
        return None
    
    # Get tier progression data
    tiers = LoyaltyTier.objects.active().ordered()
    
    # Get available rewards
    available_rewards = Reward.objects.available().in_stock().for_tier(membership.tier)[:10]
    
    # Get recent transactions
    recent_transactions = PointsTransaction.objects.for_user(user).with_membership_data().recent(30)[:10]
    
    # Get active promotions
    active_promotions = LoyaltyPromotion.objects.current().for_tier(membership.tier)
    
    return {
        'membership': membership,
        'tiers': tiers,
        'available_rewards': available_rewards,
        'recent_transactions': recent_transactions,
        'active_promotions': active_promotions,
    }


def get_admin_loyalty_stats():
    """Get comprehensive loyalty program statistics for admin"""
    stats = {}
    
    # Membership statistics
    membership_stats = LoyaltyMembership.objects.active().with_statistics().aggregate(
        total_members=Count('id'),
        total_points_in_system=Sum('points_balance'),
        total_lifetime_points=Sum('lifetime_points'),
        avg_points_per_member=Avg('points_balance')
    )
    stats['membership'] = membership_stats
    
    # Tier distribution
    tier_distribution = LoyaltyTier.objects.with_member_counts().values(
        'name', 'member_count'
    )
    stats['tier_distribution'] = list(tier_distribution)
    
    # Transaction statistics
    transaction_stats = PointsTransaction.objects.summary_stats()
    stats['transactions'] = transaction_stats
    
    # Reward statistics
    reward_stats = Reward.objects.with_redemption_counts().aggregate(
        total_rewards=Count('id'),
        active_rewards=Count('id', filter=Q(is_active=True)),
        total_redemptions=Sum('total_redemptions'),
        avg_redemptions_per_reward=Avg('total_redemptions')
    )
    stats['rewards'] = reward_stats
    
    return stats