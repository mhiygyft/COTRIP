from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import (
    LoyaltyMembership, LoyaltyTier, PointsTransaction, 
    LoyaltyPromotion, PromotionUsage
)


class LoyaltyPointsManager:
    """
    Utility class for managing loyalty points earning, spending, and tier upgrades
    """
    
    @staticmethod
    def get_or_create_membership(user):
        """
        Get existing membership or create a new basic membership for user
        """
        try:
            return user.loyalty_membership, False
        except LoyaltyMembership.DoesNotExist:
            # Get the basic tier (lowest order)
            basic_tier = LoyaltyTier.objects.filter(
                is_active=True
            ).order_by('order').first()
            
            if not basic_tier:
                raise Exception("No basic loyalty tier configured")
            
            membership = LoyaltyMembership.objects.create(
                user=user,
                tier=basic_tier
            )
            return membership, True
    
    @staticmethod
    def calculate_points_from_booking(booking_amount, tier_multiplier=1.0, promotion_multiplier=1.0):
        """
        Calculate points earned from a booking
        Base rate: 1 point per $1 spent
        """
        base_points = int(booking_amount)  # 1:1 ratio
        tier_bonus = int(base_points * (tier_multiplier - 1))
        promotion_bonus = int(base_points * (promotion_multiplier - 1))
        
        total_points = base_points + tier_bonus + promotion_bonus
        
        return {
            'base_points': base_points,
            'tier_bonus': tier_bonus,
            'promotion_bonus': promotion_bonus,
            'total_points': total_points
        }
    
    @staticmethod
    def get_applicable_promotions(membership, booking_amount):
        """
        Get promotions that apply to this member and booking
        """
        now = timezone.now()
        
        # Get active promotions
        active_promotions = LoyaltyPromotion.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )
        
        applicable_promotions = []
        
        for promotion in active_promotions:
            if promotion.is_eligible(membership):
                # Check if member hasn't exceeded usage limit
                usage_count = PromotionUsage.objects.filter(
                    promotion=promotion,
                    membership=membership
                ).count()
                
                if usage_count < promotion.max_uses_per_member:
                    # Check minimum spending requirement
                    if booking_amount >= promotion.minimum_spending:
                        applicable_promotions.append(promotion)
        
        return applicable_promotions
    
    @staticmethod
    @transaction.atomic
    def award_points_for_booking(user, booking_reference, booking_amount, flight_count=1):
        """
        Award points for a completed booking
        """
        # Get or create membership
        membership, created = LoyaltyPointsManager.get_or_create_membership(user)
        
        # Check for applicable promotions
        applicable_promotions = LoyaltyPointsManager.get_applicable_promotions(
            membership, booking_amount
        )
        
        # Calculate base points with tier multiplier
        tier_multiplier = float(membership.tier.points_multiplier)
        
        # Apply best promotion (highest multiplier)
        best_promotion = None
        promotion_multiplier = 1.0
        
        for promotion in applicable_promotions:
            if promotion.promotion_type in ['points_multiplier', 'double_points']:
                if float(promotion.multiplier) > promotion_multiplier:
                    promotion_multiplier = float(promotion.multiplier)
                    best_promotion = promotion
        
        # Calculate points breakdown
        points_breakdown = LoyaltyPointsManager.calculate_points_from_booking(
            booking_amount, tier_multiplier, promotion_multiplier
        )
        
        # Award base points with tier bonus
        base_and_tier_points = points_breakdown['base_points'] + points_breakdown['tier_bonus']
        
        # Update membership
        membership.points_balance += points_breakdown['total_points']
        membership.lifetime_points += points_breakdown['total_points']
        membership.annual_spending += booking_amount
        membership.annual_flights += flight_count
        membership.annual_points_earned += points_breakdown['total_points']
        membership.save()
        
        # Create transaction record for base + tier points
        transaction_description = f"Flight booking {booking_reference}"
        if points_breakdown['tier_bonus'] > 0:
            transaction_description += f" ({membership.tier.name} {tier_multiplier}x bonus)"
        
        PointsTransaction.objects.create(
            membership=membership,
            transaction_type='earning',
            points=base_and_tier_points,
            balance_after=membership.points_balance - points_breakdown['promotion_bonus'],
            description=transaction_description,
            reference_id=booking_reference,
            expires_at=timezone.now() + timezone.timedelta(days=365*2)  # 2 years
        )
        
        # Create separate transaction for promotion bonus if applicable
        if best_promotion and points_breakdown['promotion_bonus'] > 0:
            PointsTransaction.objects.create(
                membership=membership,
                transaction_type='bonus',
                points=points_breakdown['promotion_bonus'],
                balance_after=membership.points_balance,
                description=f"Promotion bonus: {best_promotion.name}",
                reference_id=booking_reference,
                expires_at=timezone.now() + timezone.timedelta(days=365*2)
            )
            
            # Record promotion usage
            PromotionUsage.objects.create(
                promotion=best_promotion,
                membership=membership,
                points_earned=points_breakdown['promotion_bonus'],
                spending_amount=booking_amount,
                booking_reference=booking_reference
            )
        
        # Handle bonus points promotions
        for promotion in applicable_promotions:
            if promotion.promotion_type == 'bonus_points' and promotion != best_promotion:
                bonus_points = promotion.bonus_points
                membership.points_balance += bonus_points
                membership.lifetime_points += bonus_points
                membership.annual_points_earned += bonus_points
                membership.save()
                
                PointsTransaction.objects.create(
                    membership=membership,
                    transaction_type='bonus',
                    points=bonus_points,
                    balance_after=membership.points_balance,
                    description=f"Bonus points: {promotion.name}",
                    reference_id=booking_reference,
                    expires_at=timezone.now() + timezone.timedelta(days=365*2)
                )
                
                PromotionUsage.objects.create(
                    promotion=promotion,
                    membership=membership,
                    points_earned=bonus_points,
                    spending_amount=booking_amount,
                    booking_reference=booking_reference
                )
        
        # Check for tier upgrade
        LoyaltyPointsManager.check_and_upgrade_tier(membership)
        
        return {
            'total_points_awarded': points_breakdown['total_points'],
            'points_breakdown': points_breakdown,
            'promotions_applied': [p.name for p in applicable_promotions],
            'tier_upgraded': False,  # Will be updated by tier check
            'new_balance': membership.points_balance
        }
    
    @staticmethod
    def check_and_upgrade_tier(membership):
        """
        Check if member qualifies for tier upgrade and upgrade if eligible
        """
        if membership.can_upgrade_tier():
            old_tier = membership.tier
            membership.upgrade_tier()
            
            return {
                'upgraded': True,
                'old_tier': old_tier.name,
                'new_tier': membership.tier.name
            }
        
        return {'upgraded': False}
    
    @staticmethod
    @transaction.atomic
    def deduct_points_for_redemption(membership, points_amount, description, reference_id=None):
        """
        Deduct points for reward redemption
        """
        if membership.points_balance < points_amount:
            raise ValueError("Insufficient points balance")
        
        # Deduct points
        membership.points_balance -= points_amount
        membership.save()
        
        # Create transaction record
        PointsTransaction.objects.create(
            membership=membership,
            transaction_type='redemption',
            points=-points_amount,
            balance_after=membership.points_balance,
            description=description,
            reference_id=reference_id
        )
        
        return {
            'points_deducted': points_amount,
            'new_balance': membership.points_balance
        }
    
    @staticmethod
    @transaction.atomic
    def refund_points_for_cancelled_redemption(membership, points_amount, description, reference_id=None):
        """
        Refund points for cancelled redemption
        """
        # Add points back
        membership.points_balance += points_amount
        membership.save()
        
        # Create refund transaction record
        PointsTransaction.objects.create(
            membership=membership,
            transaction_type='refund',
            points=points_amount,
            balance_after=membership.points_balance,
            description=description,
            reference_id=reference_id
        )
        
        return {
            'points_refunded': points_amount,
            'new_balance': membership.points_balance
        }
    
    @staticmethod
    def expire_old_points():
        """
        Expire points that have passed their expiry date
        This should be run as a scheduled task
        """
        expired_transactions = PointsTransaction.objects.filter(
            expires_at__lte=timezone.now(),
            is_expired=False,
            transaction_type__in=['earning', 'bonus', 'adjustment']
        )
        
        expired_count = 0
        total_expired_points = 0
        
        for transaction in expired_transactions:
            # Mark transaction as expired
            transaction.is_expired = True
            transaction.save()
            
            # Deduct points from membership
            membership = transaction.membership
            expired_points = transaction.points
            
            if membership.points_balance >= expired_points:
                membership.points_balance -= expired_points
                membership.save()
                
                # Create expiry transaction record
                PointsTransaction.objects.create(
                    membership=membership,
                    transaction_type='expiry',
                    points=-expired_points,
                    balance_after=membership.points_balance,
                    description=f'Expired points from {transaction.created_at.strftime("%Y-%m-%d")}',
                    reference_id=str(transaction.transaction_id)
                )
                
                expired_count += 1
                total_expired_points += expired_points
        
        return {
            'expired_transactions': expired_count,
            'total_expired_points': total_expired_points
        }
    
    @staticmethod
    def reset_annual_tracking_for_all_members():
        """
        Reset annual tracking counters for new year
        Should be run as a scheduled task on January 1st
        """
        current_year = timezone.now().year
        memberships = LoyaltyMembership.objects.filter(tracking_year__lt=current_year)
        
        reset_count = 0
        for membership in memberships:
            membership.reset_annual_tracking()
            reset_count += 1
        
        return {'reset_count': reset_count}


# Utility functions for integration with booking system

def award_booking_points(user, booking):
    """
    Award points for a completed booking
    Called from booking completion signal/webhook
    """
    try:
        return LoyaltyPointsManager.award_points_for_booking(
            user=user,
            booking_reference=booking.booking_reference,
            booking_amount=booking.total_price,
            flight_count=1  # Adjust based on your booking model
        )
    except Exception as e:
        # Log error but don't break booking process
        print(f"Error awarding loyalty points: {e}")
        return None


def get_member_tier_benefits(user):
    """
    Get tier benefits for displaying during booking process
    """
    try:
        membership = user.loyalty_membership
        return {
            'tier_name': membership.tier.name,
            'points_multiplier': membership.tier.points_multiplier,
            'priority_boarding': membership.tier.priority_boarding,
            'free_baggage_allowance': membership.tier.free_baggage_allowance,
            'lounge_access': membership.tier.lounge_access,
            'free_seat_selection': membership.tier.free_seat_selection
        }
    except LoyaltyMembership.DoesNotExist:
        return None


def calculate_points_preview(user, booking_amount):
    """
    Calculate points that would be earned for a booking (for display purposes)
    """
    try:
        membership, _ = LoyaltyPointsManager.get_or_create_membership(user)
        
        # Get applicable promotions
        applicable_promotions = LoyaltyPointsManager.get_applicable_promotions(
            membership, booking_amount
        )
        
        # Calculate with best promotion
        promotion_multiplier = 1.0
        best_promotion_name = None
        
        for promotion in applicable_promotions:
            if promotion.promotion_type in ['points_multiplier', 'double_points']:
                if float(promotion.multiplier) > promotion_multiplier:
                    promotion_multiplier = float(promotion.multiplier)
                    best_promotion_name = promotion.name
        
        points_breakdown = LoyaltyPointsManager.calculate_points_from_booking(
            booking_amount, 
            float(membership.tier.points_multiplier),
            promotion_multiplier
        )
        
        return {
            'total_points': points_breakdown['total_points'],
            'base_points': points_breakdown['base_points'],
            'tier_bonus': points_breakdown['tier_bonus'],
            'promotion_bonus': points_breakdown['promotion_bonus'],
            'tier_name': membership.tier.name,
            'promotion_name': best_promotion_name
        }
    except Exception:
        return {'total_points': int(booking_amount)}  # Fallback to base rate