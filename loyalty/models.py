from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class LoyaltyTier(models.Model):
    """Loyalty program tiers (Bronze, Silver, Gold, Platinum)"""
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default='#000000')
    icon = models.CharField(max_length=50, blank=True)
    
    # Tier requirements
    min_spending = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Minimum annual spending to achieve/maintain this tier"
    )
    min_flights = models.PositiveIntegerField(
        default=0,
        help_text="Minimum annual flights to achieve/maintain this tier"
    )
    min_points = models.PositiveIntegerField(
        default=0,
        help_text="Minimum points required to achieve this tier"
    )
    
    # Tier benefits
    points_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.00,
        help_text="Points earning multiplier (e.g., 1.5 = 50% bonus)"
    )
    priority_boarding = models.BooleanField(default=False)
    free_baggage_allowance = models.PositiveIntegerField(
        default=0,
        help_text="Additional free baggage allowance in kg"
    )
    lounge_access = models.BooleanField(default=False)
    free_seat_selection = models.BooleanField(default=False)
    upgrade_priority = models.PositiveIntegerField(
        default=0,
        help_text="Priority for automatic upgrades (higher = better priority)"
    )
    
    # System fields
    order = models.PositiveIntegerField(default=0, help_text="Tier hierarchy order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Loyalty Tier"
        verbose_name_plural = "Loyalty Tiers"
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['min_points']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def next_tier(self):
        """Get the next tier in the hierarchy"""
        return LoyaltyTier.objects.filter(
            order__gt=self.order, is_active=True
        ).first()
    
    @property
    def previous_tier(self):
        """Get the previous tier in the hierarchy"""
        return LoyaltyTier.objects.filter(
            order__lt=self.order, is_active=True
        ).last()


class LoyaltyMembership(models.Model):
    """User's loyalty program membership"""
    
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='loyalty_membership'
    )
    member_id = models.CharField(max_length=20, unique=True)
    tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.PROTECT,
        related_name='members'
    )
    
    # Points and status
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    
    # Annual tracking (resets yearly)
    annual_spending = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_flights = models.PositiveIntegerField(default=0)
    annual_points_earned = models.PositiveIntegerField(default=0)
    
    # Tier tracking
    tier_achieved_date = models.DateTimeField(auto_now_add=True)
    tier_expires_date = models.DateTimeField(null=True, blank=True)
    previous_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='previous_members'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    last_activity_date = models.DateTimeField(auto_now=True)
    
    # Tracking year for annual resets
    tracking_year = models.PositiveIntegerField(default=2024)
    
    class Meta:
        ordering = ['-tier__order', '-points_balance']
        verbose_name = "Loyalty Membership"
        verbose_name_plural = "Loyalty Memberships"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['member_id']),
            models.Index(fields=['tier']),
            models.Index(fields=['points_balance']),
            models.Index(fields=['is_active']),
            models.Index(fields=['tier', 'points_balance']),
            models.Index(fields=['is_active', 'tier']),
            models.Index(fields=['last_activity_date']),
            models.Index(fields=['tracking_year']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.tier.name} ({self.member_id})"
    
    def save(self, *args, **kwargs):
        if not self.member_id:
            self.member_id = self.generate_member_id()
        super().save(*args, **kwargs)
    
    def generate_member_id(self):
        """Generate a unique member ID"""
        import random
        import string
        
        while True:
            # Format: NV + 8 digits
            member_id = 'NV' + ''.join(random.choices(string.digits, k=8))
            if not LoyaltyMembership.objects.filter(member_id=member_id).exists():
                return member_id
    
    @property
    def points_to_next_tier(self):
        """Calculate points needed for next tier"""
        next_tier = self.tier.next_tier
        if not next_tier:
            return 0
        return max(0, next_tier.min_points - self.lifetime_points)
    
    @property
    def spending_to_next_tier(self):
        """Calculate spending needed for next tier"""
        next_tier = self.tier.next_tier
        if not next_tier:
            return Decimal('0.00')
        return max(Decimal('0.00'), next_tier.min_spending - self.annual_spending)
    
    @property
    def flights_to_next_tier(self):
        """Calculate flights needed for next tier"""
        next_tier = self.tier.next_tier
        if not next_tier:
            return 0
        return max(0, next_tier.min_flights - self.annual_flights)
    
    def can_upgrade_tier(self):
        """Check if member qualifies for tier upgrade"""
        next_tier = self.tier.next_tier
        if not next_tier:
            return False
        
        return (
            self.annual_spending >= next_tier.min_spending and
            self.annual_flights >= next_tier.min_flights and
            self.lifetime_points >= next_tier.min_points
        )
    
    def upgrade_tier(self):
        """Upgrade member to next qualifying tier"""
        if not self.can_upgrade_tier():
            return False
        
        next_tier = self.tier.next_tier
        self.previous_tier = self.tier
        self.tier = next_tier
        self.tier_achieved_date = timezone.now()
        self.save()
        
        # Create tier upgrade transaction
        PointsTransaction.objects.create(
            membership=self,
            transaction_type='tier_upgrade',
            points=0,
            description=f'Upgraded to {next_tier.name} tier'
        )
        
        return True
    
    def reset_annual_tracking(self):
        """Reset annual counters for new tracking year"""
        current_year = timezone.now().year
        if self.tracking_year < current_year:
            self.annual_spending = Decimal('0.00')
            self.annual_flights = 0
            self.annual_points_earned = 0
            self.tracking_year = current_year
            self.save()


class PointsTransaction(models.Model):
    """Points earning and redemption transactions"""
    
    TRANSACTION_TYPES = [
        ('earning', 'Points Earned'),
        ('redemption', 'Points Redeemed'),
        ('expiry', 'Points Expired'),
        ('adjustment', 'Manual Adjustment'),
        ('bonus', 'Bonus Points'),
        ('tier_upgrade', 'Tier Upgrade'),
        ('refund', 'Refund'),
    ]
    
    membership = models.ForeignKey(
        LoyaltyMembership, on_delete=models.CASCADE,
        related_name='point_transactions'
    )
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Points details
    points = models.IntegerField(help_text="Positive for earning, negative for spending")
    balance_after = models.PositiveIntegerField()
    
    # Transaction context
    description = models.CharField(max_length=255)
    reference_id = models.CharField(
        max_length=50, blank=True,
        help_text="Booking reference, order ID, etc."
    )
    
    # Expiry for earned points
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Staff member who created manual adjustments"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Points Transaction"
        verbose_name_plural = "Points Transactions"
    
    def __str__(self):
        action = "earned" if self.points > 0 else "redeemed"
        return f"{self.membership.member_id} {action} {abs(self.points)} points"


class Reward(models.Model):
    """Available rewards for points redemption"""
    
    REWARD_CATEGORIES = [
        ('flight', 'Flight Rewards'),
        ('upgrade', 'Cabin Upgrades'),
        ('service', 'Service Rewards'),
        ('merchandise', 'Merchandise'),
        ('partner', 'Partner Rewards'),
        ('experience', 'Experiences'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=REWARD_CATEGORIES)
    description = models.TextField()
    
    # Redemption details
    points_required = models.PositiveIntegerField()
    cash_equivalent = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Equivalent cash value for reference"
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave blank for unlimited"
    )
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Tier restrictions
    minimum_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Minimum tier required to redeem this reward"
    )
    
    # Display
    image = models.ImageField(upload_to='rewards/', blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'points_required']
        verbose_name = "Reward"
        verbose_name_plural = "Rewards"
    
    def __str__(self):
        return f"{self.name} ({self.points_required:,} points)"
    
    @property
    def is_in_stock(self):
        """Check if reward is in stock"""
        if self.stock_quantity is None:
            return True
        redeemed_count = self.redemptions.filter(status='completed').count()
        return redeemed_count < self.stock_quantity
    
    @property
    def is_valid_now(self):
        """Check if reward is currently valid"""
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True
    
    def can_redeem(self, membership):
        """Check if a member can redeem this reward"""
        if not self.is_available or not self.is_in_stock or not self.is_valid_now:
            return False
        
        if membership.points_balance < self.points_required:
            return False
        
        if self.minimum_tier and membership.tier.order < self.minimum_tier.order:
            return False
        
        return True


class RewardRedemption(models.Model):
    """Record of reward redemptions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    membership = models.ForeignKey(
        LoyaltyMembership, on_delete=models.CASCADE,
        related_name='redemptions'
    )
    reward = models.ForeignKey(
        Reward, on_delete=models.CASCADE,
        related_name='redemptions'
    )
    
    # Redemption details
    redemption_id = models.UUIDField(default=uuid.uuid4, unique=True)
    points_redeemed = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Context
    booking_reference = models.CharField(
        max_length=10, blank=True,
        help_text="Associated booking if applicable"
    )
    notes = models.TextField(blank=True)
    
    # Fulfillment
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    fulfilled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fulfilled_redemptions'
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Reward Redemption"
        verbose_name_plural = "Reward Redemptions"
    
    def __str__(self):
        return f"{self.membership.member_id} redeemed {self.reward.name}"


class LoyaltyPromotion(models.Model):
    """Special promotions for loyalty program"""
    
    PROMOTION_TYPES = [
        ('points_multiplier', 'Points Multiplier'),
        ('bonus_points', 'Bonus Points'),
        ('tier_bonus', 'Tier Bonus'),
        ('spending_bonus', 'Spending Bonus'),
        ('double_points', 'Double Points'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    
    # Promotion parameters
    multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.00,
        help_text="Points multiplier (e.g., 2.0 for double points)"
    )
    bonus_points = models.PositiveIntegerField(
        default=0,
        help_text="Fixed bonus points to award"
    )
    minimum_spending = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Minimum spending to qualify"
    )
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Restrictions
    eligible_tiers = models.ManyToManyField(
        LoyaltyTier, blank=True,
        help_text="Leave empty for all tiers"
    )
    max_uses_per_member = models.PositiveIntegerField(
        default=1,
        help_text="Maximum times a member can benefit from this promotion"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Loyalty Promotion"
        verbose_name_plural = "Loyalty Promotions"
    
    def __str__(self):
        return self.name
    
    @property
    def is_valid_now(self):
        """Check if promotion is currently valid"""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until
    
    def is_eligible(self, membership):
        """Check if a member is eligible for this promotion"""
        if not self.is_active or not self.is_valid_now:
            return False
        
        # Check tier eligibility
        if self.eligible_tiers.exists():
            if membership.tier not in self.eligible_tiers.all():
                return False
        
        # Check usage limit
        usage_count = PromotionUsage.objects.filter(
            promotion=self, membership=membership
        ).count()
        
        if usage_count >= self.max_uses_per_member:
            return False
        
        return True


class PromotionUsage(models.Model):
    """Track promotion usage by members"""
    
    promotion = models.ForeignKey(
        LoyaltyPromotion, on_delete=models.CASCADE,
        related_name='usages'
    )
    membership = models.ForeignKey(
        LoyaltyMembership, on_delete=models.CASCADE,
        related_name='promotion_usages'
    )
    
    # Usage details
    points_earned = models.PositiveIntegerField(default=0)
    spending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_reference = models.CharField(max_length=10, blank=True)
    
    # System fields
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['promotion', 'membership', 'booking_reference']
        ordering = ['-used_at']
        verbose_name = "Promotion Usage"
        verbose_name_plural = "Promotion Usages"
    
    def __str__(self):
        return f"{self.membership.member_id} used {self.promotion.name}"
