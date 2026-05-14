from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    LoyaltyTier, LoyaltyMembership, PointsTransaction,
    Reward, RewardRedemption, LoyaltyPromotion, PromotionUsage
)


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'order', 'min_spending', 'min_flights', 'min_points',
        'points_multiplier', 'member_count', 'color_badge', 'is_active'
    ]
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'priority_boarding', 'lounge_access', 'free_seat_selection']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'color_code', 'icon', 'order')
        }),
        ('Requirements', {
            'fields': ('min_spending', 'min_flights', 'min_points')
        }),
        ('Benefits', {
            'fields': (
                'points_multiplier', 'priority_boarding', 'free_baggage_allowance',
                'lounge_access', 'free_seat_selection', 'upgrade_priority'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def member_count(self, obj):
        count = obj.members.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:loyalty_loyaltymembership_changelist')
            return format_html(
                '<a href="{}?tier__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    member_count.short_description = 'Active Members'
    
    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.color_code, obj.name
        )
    color_badge.short_description = 'Color'


@admin.register(LoyaltyMembership)
class LoyaltyMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'member_id', 'user_email', 'tier', 'points_balance',
        'annual_spending', 'annual_flights', 'tier_progress', 'is_active'
    ]
    list_filter = [
        'tier', 'is_active', 'tier_achieved_date', 'tracking_year'
    ]
    search_fields = [
        'member_id', 'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'member_id', 'joined_date', 'tier_achieved_date', 'last_activity_date',
        'lifetime_points', 'tier_progress_display'
    ]
    raw_id_fields = ['user', 'previous_tier']
    
    fieldsets = (
        ('Member Information', {
            'fields': ('user', 'member_id', 'is_active', 'joined_date')
        }),
        ('Current Status', {
            'fields': (
                'tier', 'tier_achieved_date', 'tier_expires_date',
                'previous_tier', 'tier_progress_display'
            )
        }),
        ('Points & Activity', {
            'fields': (
                'points_balance', 'lifetime_points', 'annual_points_earned',
                'last_activity_date'
            )
        }),
        ('Annual Tracking', {
            'fields': (
                'annual_spending', 'annual_flights', 'tracking_year'
            )
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def tier_progress(self, obj):
        next_tier = obj.tier.next_tier
        if not next_tier:
            return "Max Tier"
        
        points_needed = obj.points_to_next_tier
        spending_needed = obj.spending_to_next_tier
        flights_needed = obj.flights_to_next_tier
        
        if points_needed == 0 and spending_needed == 0 and flights_needed == 0:
            return format_html('<span style="color: green;">✓ Can Upgrade</span>')
        
        progress_items = []
        if points_needed > 0:
            progress_items.append(f"{points_needed:,} pts")
        if spending_needed > 0:
            progress_items.append(f"${spending_needed:,.0f}")
        if flights_needed > 0:
            progress_items.append(f"{flights_needed} flights")
        
        return " | ".join(progress_items)
    tier_progress.short_description = 'Next Tier Progress'
    
    def tier_progress_display(self, obj):
        return self.tier_progress(obj)
    tier_progress_display.short_description = 'Progress to Next Tier'
    
    actions = ['upgrade_qualifying_members', 'reset_annual_tracking']
    
    def upgrade_qualifying_members(self, request, queryset):
        upgraded_count = 0
        for membership in queryset:
            if membership.can_upgrade_tier():
                membership.upgrade_tier()
                upgraded_count += 1
        
        self.message_user(
            request,
            f"Successfully upgraded {upgraded_count} members to higher tiers."
        )
    upgrade_qualifying_members.short_description = "Upgrade qualifying members to next tier"
    
    def reset_annual_tracking(self, request, queryset):
        for membership in queryset:
            membership.reset_annual_tracking()
        
        self.message_user(
            request,
            f"Reset annual tracking for {queryset.count()} members."
        )
    reset_annual_tracking.short_description = "Reset annual tracking counters"


class PointsTransactionInline(admin.TabularInline):
    model = PointsTransaction
    extra = 0
    readonly_fields = ['transaction_id', 'balance_after', 'created_at']
    fields = [
        'transaction_type', 'points', 'balance_after', 'description',
        'reference_id', 'expires_at', 'created_at'
    ]
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'membership_id', 'transaction_type', 'points',
        'balance_after', 'description', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'is_expired', 'created_at', 'expires_at'
    ]
    search_fields = [
        'transaction_id', 'membership__member_id', 'description', 'reference_id'
    ]
    readonly_fields = [
        'transaction_id', 'balance_after', 'created_at'
    ]
    raw_id_fields = ['membership', 'created_by']
    date_hierarchy = 'created_at'
    
    def membership_id(self, obj):
        return obj.membership.member_id
    membership_id.short_description = 'Member ID'
    membership_id.admin_order_field = 'membership__member_id'
    
    def has_change_permission(self, request, obj=None):
        # Only allow editing of manual adjustments
        if obj and obj.transaction_type not in ['adjustment']:
            return False
        return super().has_change_permission(request, obj)


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'points_required', 'cash_equivalent',
        'stock_status', 'validity_status', 'minimum_tier', 'featured', 'is_available', 'order'
    ]
    list_editable = ['featured', 'is_available', 'order']
    list_filter = [
        'category', 'is_available', 'featured', 'minimum_tier',
        'valid_from', 'valid_until'
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['minimum_tier']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'image')
        }),
        ('Redemption Details', {
            'fields': ('points_required', 'cash_equivalent')
        }),
        ('Availability', {
            'fields': (
                'is_available', 'stock_quantity', 'valid_from', 'valid_until'
            )
        }),
        ('Restrictions', {
            'fields': ('minimum_tier',)
        }),
        ('Display', {
            'fields': ('featured', 'order')
        })
    )
    
    def stock_status(self, obj):
        if obj.stock_quantity is None:
            return "Unlimited"
        
        redeemed = obj.redemptions.filter(status='completed').count()
        remaining = obj.stock_quantity - redeemed
        
        if remaining <= 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif remaining <= 5:
            return format_html('<span style="color: orange;">{} left</span>', remaining)
        else:
            return f"{remaining} available"
    stock_status.short_description = 'Stock'
    
    def validity_status(self, obj):
        now = timezone.now()
        
        if obj.valid_from and now < obj.valid_from:
            return format_html('<span style="color: gray;">Not yet active</span>')
        elif obj.valid_until and now > obj.valid_until:
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')
    validity_status.short_description = 'Status'


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = [
        'redemption_id', 'membership_id', 'reward_name', 'points_redeemed',
        'status', 'booking_reference', 'created_at'
    ]
    list_filter = [
        'status', 'reward__category', 'created_at', 'fulfilled_at'
    ]
    search_fields = [
        'redemption_id', 'membership__member_id', 'reward__name',
        'booking_reference'
    ]
    readonly_fields = ['redemption_id', 'created_at', 'updated_at']
    raw_id_fields = ['membership', 'reward', 'fulfilled_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Redemption Details', {
            'fields': (
                'redemption_id', 'membership', 'reward', 'points_redeemed',
                'status', 'booking_reference'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Fulfillment', {
            'fields': ('fulfilled_at', 'fulfilled_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def membership_id(self, obj):
        return obj.membership.member_id
    membership_id.short_description = 'Member ID'
    membership_id.admin_order_field = 'membership__member_id'
    
    def reward_name(self, obj):
        return obj.reward.name
    reward_name.short_description = 'Reward'
    reward_name.admin_order_field = 'reward__name'
    
    actions = ['mark_as_completed', 'mark_as_processing']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(
            status='completed',
            fulfilled_at=timezone.now(),
            fulfilled_by=request.user
        )
        self.message_user(
            request,
            f"Marked {queryset.count()} redemptions as completed."
        )
    mark_as_completed.short_description = "Mark selected redemptions as completed"
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(
            request,
            f"Marked {queryset.count()} redemptions as processing."
        )
    mark_as_processing.short_description = "Mark selected redemptions as processing"


@admin.register(LoyaltyPromotion)
class LoyaltyPromotionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'promotion_type', 'multiplier', 'bonus_points',
        'validity_period', 'usage_count', 'is_active'
    ]
    list_editable = ['is_active']
    list_filter = [
        'promotion_type', 'is_active', 'valid_from', 'valid_until'
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['eligible_tiers']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'promotion_type')
        }),
        ('Parameters', {
            'fields': ('multiplier', 'bonus_points', 'minimum_spending')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Restrictions', {
            'fields': ('eligible_tiers', 'max_uses_per_member')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def validity_period(self, obj):
        return f"{obj.valid_from.strftime('%Y-%m-%d')} to {obj.valid_until.strftime('%Y-%m-%d')}"
    validity_period.short_description = 'Valid Period'
    
    def usage_count(self, obj):
        count = obj.usages.count()
        if count > 0:
            url = reverse('admin:loyalty_promotionusage_changelist')
            return format_html(
                '<a href="{}?promotion__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    usage_count.short_description = 'Total Uses'


@admin.register(PromotionUsage)
class PromotionUsageAdmin(admin.ModelAdmin):
    list_display = [
        'promotion_name', 'membership_id', 'points_earned',
        'spending_amount', 'booking_reference', 'used_at'
    ]
    list_filter = ['promotion', 'used_at']
    search_fields = [
        'promotion__name', 'membership__member_id', 'booking_reference'
    ]
    raw_id_fields = ['promotion', 'membership']
    date_hierarchy = 'used_at'
    
    def promotion_name(self, obj):
        return obj.promotion.name
    promotion_name.short_description = 'Promotion'
    promotion_name.admin_order_field = 'promotion__name'
    
    def membership_id(self, obj):
        return obj.membership.member_id
    membership_id.short_description = 'Member ID'
    membership_id.admin_order_field = 'membership__member_id'
    
    def has_change_permission(self, request, obj=None):
        return False


# Add inline to LoyaltyMembership for points transactions
LoyaltyMembershipAdmin.inlines = [PointsTransactionInline]
