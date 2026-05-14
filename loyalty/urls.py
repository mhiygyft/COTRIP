from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

app_name = 'loyalty'

# API Router setup
router = DefaultRouter()
router.register(r'tiers', api_views.LoyaltyTierViewSet)
router.register(r'memberships', api_views.LoyaltyMembershipViewSet, basename='membership')
router.register(r'transactions', api_views.PointsTransactionViewSet, basename='transaction')
router.register(r'rewards', api_views.RewardViewSet)
router.register(r'redemptions', api_views.RewardRedemptionViewSet, basename='redemption')
router.register(r'promotions', api_views.LoyaltyPromotionViewSet)
router.register(r'promotion-usage', api_views.PromotionUsageViewSet, basename='promotion-usage')

urlpatterns = [
    # Main dashboard
    path('', views.loyalty_dashboard, name='dashboard'),
    
    # Rewards catalog and redemption
    path('rewards/', views.rewards_catalog, name='rewards'),
    path('rewards/<slug:reward_slug>/', views.reward_detail, name='reward_detail'),
    path('rewards/<slug:reward_slug>/redeem/', views.redeem_reward, name='redeem_reward'),
    
    # Points and transaction history
    path('points/', views.points_history, name='points_history'),
    path('redemptions/', views.redemption_history, name='redemption_history'),
    
    # Tier information and benefits
    path('tiers/', views.tier_benefits, name='tier-benefits'),
    
    # Promotions
    path('promotions/', views.promotions, name='promotions'),
    
    # API endpoints for AJAX requests
    path('api/tier-progress/', views.api_tier_progress, name='api_tier_progress'),
    path('api/points-balance/', views.api_points_balance, name='api_points_balance'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
]
