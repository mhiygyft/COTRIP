"""
API ViewSets for the Loyalty Program
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import (
    LoyaltyTierPermissions, LoyaltyMembershipPermissions, RewardPermissions,
    IsOwnerOrAdmin, CanRedeemRewards, IsAdminOrReadOnlyForPublic
)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    LoyaltyTier, LoyaltyMembership, PointsTransaction, Reward,
    RewardRedemption, LoyaltyPromotion, PromotionUsage
)
from .serializers import (
    LoyaltyTierSerializer, LoyaltyMembershipSerializer, PointsTransactionSerializer,
    RewardSerializer, RewardRedemptionSerializer, LoyaltyPromotionSerializer,
    PromotionUsageSerializer, MembershipStatsSerializer, TierProgressSerializer,
    PointsCalculationSerializer, RewardAvailabilitySerializer,
    BulkPointsTransactionSerializer, MembershipUpgradeSerializer,
    PublicRewardSerializer, PublicLoyaltyTierSerializer, PublicPromotionSerializer
)
from .utils import LoyaltyPointsManager


class LoyaltyTierViewSet(viewsets.ModelViewSet):
    """API ViewSet for loyalty tiers"""
    queryset = LoyaltyTier.objects.all().order_by('order')
    serializer_class = LoyaltyTierSerializer
    permission_classes = [LoyaltyTierPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'min_points', 'created_at']
    ordering = ['order']

    def get_permissions(self):
        """Admin permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Public tier information (no authentication required)"""
        tiers = self.queryset.filter(is_active=True)
        serializer = PublicLoyaltyTierSerializer(tiers, many=True)
        return Response(serializer.data)


class LoyaltyMembershipViewSet(viewsets.ModelViewSet):
    """API ViewSet for loyalty memberships"""
    serializer_class = LoyaltyMembershipSerializer
    permission_classes = [LoyaltyMembershipPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'tier__name']
    search_fields = ['member_id', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['points_balance', 'lifetime_points', 'joined_date']
    ordering = ['-lifetime_points']

    def get_queryset(self):
        """Filter memberships based on user permissions"""
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return LoyaltyMembership.objects.none()
        if self.request.user.is_staff:
            return LoyaltyMembership.objects.select_related('user', 'tier').all()
        return LoyaltyMembership.objects.select_related('user', 'tier').filter(
            user=self.request.user
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed membership statistics"""
        membership = self.get_object()
        
        # Calculate next tier and points needed
        current_tier = membership.tier
        next_tier = LoyaltyTier.objects.filter(
            min_points__gt=current_tier.min_points,
            is_active=True
        ).order_by('min_points').first()
        
        points_to_next_tier = None
        if next_tier:
            points_to_next_tier = max(0, next_tier.min_points - membership.lifetime_points)
        
        # Count total redemptions
        total_redemptions = RewardRedemption.objects.filter(
            membership=membership,
            status__in=['redeemed', 'fulfilled']
        ).count()
        
        stats_data = {
            'total_points': membership.points_balance,
            'lifetime_points': membership.lifetime_points,
            'annual_points_earned': membership.annual_points_earned,
            'current_tier': membership.tier,
            'next_tier': next_tier,
            'points_to_next_tier': points_to_next_tier,
            'tier_expires_date': membership.tier_expires_date,
            'total_redemptions': total_redemptions,
            'last_activity': membership.last_activity_date,
        }
        
        serializer = MembershipStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tier_progress(self, request, pk=None):
        """Get tier progress information"""
        membership = self.get_object()
        
        current_tier = membership.tier
        next_tier = LoyaltyTier.objects.filter(
            min_points__gt=current_tier.min_points,
            is_active=True
        ).order_by('min_points').first()
        
        if next_tier:
            points_needed = max(0, next_tier.min_points - membership.lifetime_points)
            progress_percentage = min(100, 
                (membership.lifetime_points - current_tier.min_points) / 
                (next_tier.min_points - current_tier.min_points) * 100
            )
        else:
            points_needed = None
            progress_percentage = 100.0
        
        # Points earned this year
        year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        points_earned_this_period = PointsTransaction.objects.filter(
            membership=membership,
            transaction_type='earning',
            created_at__gte=year_start
        ).aggregate(total=Sum('points'))['total'] or 0
        
        progress_data = {
            'current_tier': current_tier,
            'next_tier': next_tier,
            'progress_percentage': progress_percentage,
            'points_earned_this_period': points_earned_this_period,
            'points_needed': points_needed,
            'tier_expires_date': membership.tier_expires_date,
        }
        
        serializer = TierProgressSerializer(progress_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_membership(self, request):
        """Get current user's membership"""
        try:
            membership = LoyaltyMembership.objects.select_related('user', 'tier').get(
                user=request.user
            )
            serializer = self.get_serializer(membership)
            return Response(serializer.data)
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found for this user'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PointsTransactionViewSet(viewsets.ModelViewSet):
    """API ViewSet for points transactions"""
    serializer_class = PointsTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'is_expired']
    search_fields = ['description', 'reference_id']
    ordering_fields = ['points', 'created_at', 'expires_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter transactions based on user permissions"""
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return PointsTransaction.objects.none()
        if self.request.user.is_staff:
            return PointsTransaction.objects.select_related('membership__user').all()
        return PointsTransaction.objects.select_related('membership__user').filter(
            membership__user=self.request.user
        )

    def get_permissions(self):
        """Admin permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_create(self, request):
        """Bulk create points transactions"""
        serializer = BulkPointsTransactionSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            memberships = LoyaltyMembership.objects.filter(
                id__in=data['membership_ids']
            )
            
            transactions = []
            for membership in memberships:
                transaction = PointsTransaction(
                    membership=membership,
                    transaction_type=data['transaction_type'],
                    points=data['points'],
                    description=data['description'],
                    expires_at=data.get('expires_at'),
                )
                transactions.append(transaction)
            
            created_transactions = PointsTransaction.objects.bulk_create(transactions)
            
            # Update membership balances
            for membership in memberships:
                membership.update_balance()
                membership.check_tier_qualification()
            
            return Response({
                'message': f'{len(created_transactions)} transactions created successfully',
                'count': len(created_transactions)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def calculate_points(self, request):
        """Calculate points for a given booking amount"""
        amount = request.data.get('amount', 0)
        promotion_code = request.data.get('promotion_code')
        
        try:
            membership = LoyaltyMembership.objects.get(user=request.user)
            points_manager = LoyaltyPointsManager()
            
            calculation = points_manager.calculate_points_from_booking(
                amount=Decimal(str(amount)),
                membership=membership,
                promotion_code=promotion_code
            )
            
            serializer = PointsCalculationSerializer(calculation)
            return Response(serializer.data)
            
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class RewardViewSet(viewsets.ModelViewSet):
    """API ViewSet for rewards"""
    queryset = Reward.objects.all().order_by('points_required')
    serializer_class = RewardSerializer
    permission_classes = [RewardPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available', 'minimum_tier']
    search_fields = ['name', 'description']
    ordering_fields = ['points_required', 'created_at', 'name']
    ordering = ['points_required']

    def get_permissions(self):
        """Admin permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Public rewards catalog (no authentication required)"""
        rewards = self.queryset.filter(is_available=True)
        serializer = PublicRewardSerializer(rewards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get rewards available for current user"""
        try:
            membership = LoyaltyMembership.objects.get(user=request.user)
            available_rewards = []
            
            for reward in self.queryset.filter(is_available=True):
                can_redeem = True
                reason = None
                points_needed = None
                tier_required = None
                
                # Check points requirement
                if reward.points_required > membership.points_balance:
                    can_redeem = False
                    reason = "Insufficient points"
                    points_needed = reward.points_required - membership.points_balance
                
                # Check tier requirement
                if reward.minimum_tier and reward.minimum_tier.min_points > membership.tier.min_points:
                    can_redeem = False
                    reason = "Tier requirement not met"
                    tier_required = reward.minimum_tier
                
                # Check stock
                if not reward.unlimited_stock and reward.stock_quantity <= 0:
                    can_redeem = False
                    reason = "Out of stock"
                
                # Check validity period
                now = timezone.now()
                if reward.valid_from and reward.valid_from > now:
                    can_redeem = False
                    reason = "Not yet available"
                
                if reward.valid_until and reward.valid_until < now:
                    can_redeem = False
                    reason = "Expired"
                
                availability_data = {
                    'reward': reward,
                    'can_redeem': can_redeem,
                    'reason': reason,
                    'points_needed': points_needed,
                    'tier_required': tier_required,
                }
                
                available_rewards.append(availability_data)
            
            serializer = RewardAvailabilitySerializer(available_rewards, many=True)
            return Response(serializer.data)
            
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def redeem(self, request, pk=None):
        """Redeem a reward"""
        reward = self.get_object()
        
        try:
            membership = LoyaltyMembership.objects.get(user=request.user)
            
            # Use the utility to redeem the reward
            points_manager = LoyaltyPointsManager()
            redemption = points_manager.redeem_reward(membership, reward)
            
            serializer = RewardRedemptionSerializer(redemption)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class RewardRedemptionViewSet(viewsets.ModelViewSet):
    """API ViewSet for reward redemptions"""
    serializer_class = RewardRedemptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['redemption_id', 'reward__name']
    ordering_fields = ['created_at', 'points_redeemed']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter redemptions based on user permissions"""
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return RewardRedemption.objects.none()
        if self.request.user.is_staff:
            return RewardRedemption.objects.select_related('membership__user', 'reward').all()
        return RewardRedemption.objects.select_related('membership__user', 'reward').filter(
            membership__user=self.request.user
        )

    def get_permissions(self):
        """Admin permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def fulfill(self, request, pk=None):
        """Mark redemption as fulfilled"""
        redemption = self.get_object()
        
        if redemption.status != 'pending':
            return Response(
                {'error': 'Only pending redemptions can be fulfilled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        redemption.status = 'fulfilled'
        redemption.fulfilled_at = timezone.now()
        redemption.notes = request.data.get('notes', redemption.notes)
        redemption.save()
        
        serializer = self.get_serializer(redemption)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def cancel(self, request, pk=None):
        """Cancel a redemption and refund points"""
        redemption = self.get_object()
        
        if redemption.status not in ['pending', 'redeemed']:
            return Response(
                {'error': 'Only pending or redeemed redemptions can be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refund points
        PointsTransaction.objects.create(
            membership=redemption.membership,
            transaction_type='refund',
            points=redemption.points_redeemed,
            description=f'Refund for cancelled redemption: {redemption.reward.name}',
            reference_id=str(redemption.redemption_id),
        )
        
        redemption.status = 'cancelled'
        redemption.cancelled_at = timezone.now()
        redemption.notes = request.data.get('notes', redemption.notes)
        redemption.save()
        
        # Update membership balance
        redemption.membership.update_balance()
        
        serializer = self.get_serializer(redemption)
        return Response(serializer.data)


class LoyaltyPromotionViewSet(viewsets.ModelViewSet):
    """API ViewSet for loyalty promotions"""
    queryset = LoyaltyPromotion.objects.all().order_by('-created_at')
    serializer_class = LoyaltyPromotionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['promotion_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['valid_from', 'valid_until', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """Admin permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Public promotions (no authentication required)"""
        now = timezone.now()
        promotions = self.queryset.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )
        serializer = PublicPromotionSerializer(promotions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active promotions for current user"""
        try:
            membership = LoyaltyMembership.objects.get(user=request.user)
            now = timezone.now()
            
            # Filter promotions by user's tier eligibility
            promotions = self.queryset.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            )
            
            # Filter by tier eligibility
            eligible_promotions = []
            for promotion in promotions:
                if promotion.eligible_tiers.exists():
                    if membership.tier in promotion.eligible_tiers.all():
                        eligible_promotions.append(promotion)
                else:
                    eligible_promotions.append(promotion)
            
            serializer = self.get_serializer(eligible_promotions, many=True)
            return Response(serializer.data)
            
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def validate_code(self, request, pk=None):
        """Validate a promotion code"""
        promotion = self.get_object()
        
        try:
            membership = LoyaltyMembership.objects.get(user=request.user)
            points_manager = LoyaltyPointsManager()
            
            is_valid = points_manager.validate_promotion(promotion, membership)
            
            return Response({
                'valid': is_valid,
                'promotion': self.get_serializer(promotion).data
            })
            
        except LoyaltyMembership.DoesNotExist:
            return Response(
                {'error': 'No loyalty membership found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PromotionUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for promotion usage (read-only)"""
    serializer_class = PromotionUsageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['promotion__name']
    ordering_fields = ['used_at', 'points_earned', 'spending_amount']
    ordering = ['-used_at']

    def get_queryset(self):
        """Filter usage based on user permissions"""
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return PromotionUsage.objects.none()
        if self.request.user.is_staff:
            return PromotionUsage.objects.select_related(
                'membership__user', 'promotion'
            ).all()
        return PromotionUsage.objects.select_related(
            'membership__user', 'promotion'
        ).filter(membership__user=self.request.user)
