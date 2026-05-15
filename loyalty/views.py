from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import (
    LoyaltyMembership, LoyaltyTier, Reward, RewardRedemption,
    PointsTransaction, LoyaltyPromotion
)
from .forms import RewardRedemptionForm


@login_required
def loyalty_dashboard(request):
    """Main loyalty program dashboard for members"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        # Create basic membership if doesn't exist
        basic_tier = LoyaltyTier.objects.filter(
            is_active=True, order=0
        ).first()
        
        if not basic_tier:
            messages.error(request, "Loyalty program is not currently available.")
            return redirect('users:dashboard')
        
        membership = LoyaltyMembership.objects.create(
            user=request.user,
            tier=basic_tier
        )
    
    # Get recent transactions
    recent_transactions = membership.point_transactions.select_related('membership')[:5]
    
    # Get active promotions
    active_promotions = LoyaltyPromotion.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    )
    
    # Filter promotions by eligibility
    eligible_promotions = []
    for promotion in active_promotions:
        if promotion.is_eligible(membership):
            eligible_promotions.append(promotion)
    
    # Get recent redemptions
    recent_redemptions = membership.redemptions.select_related('reward')[:5]
    
    # Calculate progress to next tier
    next_tier = membership.tier.next_tier
    tier_progress = None
    if next_tier:
        tier_progress = {
            'next_tier': next_tier,
            'points_needed': membership.points_to_next_tier,
            'spending_needed': membership.spending_to_next_tier,
            'flights_needed': membership.flights_to_next_tier,
            'can_upgrade': membership.can_upgrade_tier()
        }
    
    context = {
        'membership': membership,
        'recent_transactions': recent_transactions,
        'eligible_promotions': eligible_promotions,
        'recent_redemptions': recent_redemptions,
        'tier_progress': tier_progress,
    }
    
    return render(request, 'loyalty/dashboard.html', context)


@login_required
def rewards_catalog(request):
    """Browse available rewards for redemption"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    # Filter rewards
    rewards = Reward.objects.filter(
        is_available=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    ).select_related('minimum_tier')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        rewards = rewards.filter(category=category)
    
    # Filter by points range
    max_points = request.GET.get('max_points')
    if max_points:
        try:
            rewards = rewards.filter(points_required__lte=int(max_points))
        except ValueError:
            pass
    
    # Filter by availability to user
    show_available_only = request.GET.get('available_only') == 'true'
    if show_available_only:
        # Filter rewards the user can actually redeem
        available_rewards = []
        for reward in rewards:
            if reward.can_redeem(membership):
                available_rewards.append(reward.id)
        rewards = rewards.filter(id__in=available_rewards)
    
    # Order by featured first, then by points
    rewards = rewards.order_by('-featured', 'points_required')
    
    # Pagination
    paginator = Paginator(rewards, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get reward categories for filter
    categories = Reward.REWARD_CATEGORIES
    
    context = {
        'membership': membership,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'current_max_points': max_points,
        'show_available_only': show_available_only,
    }
    
    return render(request, 'loyalty/rewards_catalog.html', context)


@login_required
def reward_detail(request, reward_slug):
    """View detailed information about a specific reward"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    reward = get_object_or_404(
        Reward.objects.select_related('minimum_tier'),
        slug=reward_slug,
        is_available=True
    )
    
    # Check if user can redeem this reward
    can_redeem = reward.can_redeem(membership)
    redemption_issues = []
    
    if not can_redeem:
        if membership.points_balance < reward.points_required:
            redemption_issues.append(
                f"Insufficient points. You need {reward.points_required - membership.points_balance:,} more points."
            )
        
        if reward.minimum_tier and membership.tier.order < reward.minimum_tier.order:
            redemption_issues.append(
                f"Requires {reward.minimum_tier.name} tier or higher."
            )
        
        if not reward.is_in_stock:
            redemption_issues.append("Currently out of stock.")
        
        if not reward.is_valid_now:
            redemption_issues.append("This reward is no longer available.")
    
    # Handle redemption form submission
    if request.method == 'POST' and can_redeem:
        form = RewardRedemptionForm(request.POST)
        if form.is_valid():
            return process_redemption(request, membership, reward, form)
    else:
        form = RewardRedemptionForm()
    
    context = {
        'membership': membership,
        'reward': reward,
        'can_redeem': can_redeem,
        'redemption_issues': redemption_issues,
        'form': form,
    }
    
    return render(request, 'loyalty/reward_detail.html', context)


@login_required
@require_POST
def redeem_reward(request, reward_slug):
    """Process reward redemption"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    reward = get_object_or_404(
        Reward.objects.select_related('minimum_tier'),
        slug=reward_slug,
        is_available=True
    )
    
    # Verify user can redeem
    if not reward.can_redeem(membership):
        messages.error(request, "You are not eligible to redeem this reward.")
        return redirect('loyalty:reward_detail', reward_slug=reward_slug)
    
    form = RewardRedemptionForm(request.POST)
    if form.is_valid():
        return process_redemption(request, membership, reward, form)
    else:
        messages.error(request, "Please correct the errors in your redemption request.")
        return redirect('loyalty:reward_detail', reward_slug=reward_slug)


def process_redemption(request, membership, reward, form):
    """Process the actual redemption transaction"""
    try:
        with transaction.atomic():
            # Create redemption record
            redemption = RewardRedemption.objects.create(
                membership=membership,
                reward=reward,
                points_redeemed=reward.points_required,
                booking_reference=form.cleaned_data.get('booking_reference', ''),
                notes=form.cleaned_data.get('notes', ''),
                status='pending'
            )
            
            # Deduct points from membership
            membership.points_balance -= reward.points_required
            membership.save()
            
            # Create points transaction record
            PointsTransaction.objects.create(
                membership=membership,
                transaction_type='redemption',
                points=-reward.points_required,
                balance_after=membership.points_balance,
                description=f'Redeemed: {reward.name}',
                reference_id=str(redemption.redemption_id)
            )
            
            messages.success(
                request,
                f'Successfully redeemed {reward.name}! '
                f'Your redemption ID is {redemption.redemption_id}. '
                f'We will process your request shortly.'
            )
            
            return redirect('loyalty:redemption_history')
            
    except Exception as e:
        messages.error(
            request,
            'An error occurred while processing your redemption. Please try again.'
        )
        return redirect('loyalty:reward_detail', reward_slug=reward.slug)


@login_required
def points_history(request):
    """View complete points transaction history"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    # Get all transactions
    transactions = membership.point_transactions.select_related('membership')
    
    # Filter by transaction type
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Order by most recent first
    transactions = transactions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_earned = membership.point_transactions.filter(
        transaction_type__in=['earning', 'bonus', 'adjustment']
    ).aggregate(total=Sum('points'))['total'] or 0
    
    total_redeemed = abs(membership.point_transactions.filter(
        transaction_type__in=['redemption']
    ).aggregate(total=Sum('points'))['total'] or 0)
    
    context = {
        'membership': membership,
        'page_obj': page_obj,
        'transaction_types': PointsTransaction.TRANSACTION_TYPES,
        'current_type': transaction_type,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
    }
    
    return render(request, 'loyalty/points_history.html', context)


@login_required
def redemption_history(request):
    """View reward redemption history"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    # Get all redemptions
    redemptions = membership.redemptions.select_related('reward')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        redemptions = redemptions.filter(status=status)
    
    # Order by most recent first
    redemptions = redemptions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(redemptions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'membership': membership,
        'page_obj': page_obj,
        'status_choices': RewardRedemption.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'loyalty/redemption_history.html', context)


@login_required
def tier_benefits(request):
    """View all tier benefits and requirements"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    # Get all active tiers
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('order')
    
    context = {
        'membership': membership,
        'tiers': tiers,
        'current_tier': membership.tier,
    }
    
    return render(request, 'loyalty/tier_benefits.html', context)


@login_required
def promotions(request):
    """View active promotions"""
    try:
        membership = request.user.loyalty_membership
    except LoyaltyMembership.DoesNotExist:
        messages.error(request, "Please join our loyalty program first.")
        return redirect('loyalty:dashboard')
    
    # Get active promotions
    now = timezone.now()
    active_promotions = LoyaltyPromotion.objects.filter(
        is_active=True,
        valid_from__lte=now,
        valid_until__gte=now
    )
    
    # Separate eligible and non-eligible promotions
    eligible_promotions = []
    other_promotions = []
    
    for promotion in active_promotions:
        if promotion.is_eligible(membership):
            eligible_promotions.append(promotion)
        else:
            other_promotions.append(promotion)
    
    context = {
        'membership': membership,
        'eligible_promotions': eligible_promotions,
        'other_promotions': other_promotions,
    }
    
    return render(request, 'loyalty/promotions.html', context)


# API Views for AJAX requests

@login_required
def api_tier_progress(request):
    """API endpoint for tier progress information"""
    try:
        membership = request.user.loyalty_membership
        next_tier = membership.tier.next_tier
        
        if not next_tier:
            return JsonResponse({
                'current_tier': membership.tier.name,
                'is_max_tier': True
            })
        
        return JsonResponse({
            'current_tier': membership.tier.name,
            'next_tier': next_tier.name,
            'points_needed': membership.points_to_next_tier,
            'spending_needed': float(membership.spending_to_next_tier),
            'flights_needed': membership.flights_to_next_tier,
            'can_upgrade': membership.can_upgrade_tier(),
            'progress_percentage': {
                'points': max(0, min(100, (membership.lifetime_points / next_tier.min_points) * 100)),
                'spending': max(0, min(100, (float(membership.annual_spending) / float(next_tier.min_spending)) * 100)),
                'flights': max(0, min(100, (membership.annual_flights / next_tier.min_flights) * 100))
            }
        })
        
    except LoyaltyMembership.DoesNotExist:
        return JsonResponse({'error': 'Membership not found'}, status=404)


@login_required
def api_points_balance(request):
    """API endpoint for current points balance"""
    try:
        membership = request.user.loyalty_membership
        return JsonResponse({
            'points_balance': membership.points_balance,
            'lifetime_points': membership.lifetime_points,
        })
    except LoyaltyMembership.DoesNotExist:
        return JsonResponse({'error': 'Membership not found'}, status=404)
