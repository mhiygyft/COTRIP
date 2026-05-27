from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from loyalty.models import LoyaltyTier, Reward, LoyaltyPromotion


class Command(BaseCommand):
    help = 'Set up initial loyalty program data including tiers, rewards, and promotions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-tiers',
            action='store_true',
            help='Skip creating loyalty tiers'
        )
        parser.add_argument(
            '--skip-rewards',
            action='store_true',
            help='Skip creating sample rewards'
        )
        parser.add_argument(
            '--skip-promotions',
            action='store_true',
            help='Skip creating sample promotions'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up loyalty program data...')
        )

        if not options['skip_tiers']:
            self.create_loyalty_tiers()

        if not options['skip_rewards']:
            self.create_sample_rewards()

        if not options['skip_promotions']:
            self.create_sample_promotions()

        self.stdout.write(
            self.style.SUCCESS('Successfully set up loyalty program data!')
        )

    def create_loyalty_tiers(self):
        self.stdout.write('Creating loyalty tiers...')

        tiers_data = [
            {
                'name': 'Bronze',
                'slug': 'bronze',
                'description': 'Welcome to COTRIPVn loyalty! Start earning points and enjoying benefits.',
                'color_code': '#CD7F32',
                'icon': 'fas fa-medal',
                'order': 0,
                'min_spending': 0,
                'min_flights': 0,
                'min_points': 0,
                'points_multiplier': 1.00,
                'priority_boarding': False,
                'free_baggage_allowance': 0,
                'lounge_access': False,
                'free_seat_selection': False,
                'upgrade_priority': 0
            },
            {
                'name': 'Silver',
                'slug': 'silver',
                'description': 'Enjoy enhanced benefits and priority service with Silver status.',
                'color_code': '#C0C0C0',
                'icon': 'fas fa-medal',
                'order': 1,
                'min_spending': 2000,
                'min_flights': 10,
                'min_points': 5000,
                'points_multiplier': 1.25,
                'priority_boarding': True,
                'free_baggage_allowance': 5,
                'lounge_access': False,
                'free_seat_selection': True,
                'upgrade_priority': 1
            },
            {
                'name': 'Gold',
                'slug': 'gold',
                'description': 'Experience premium service and exclusive benefits with Gold status.',
                'color_code': '#FFD700',
                'icon': 'fas fa-medal',
                'order': 2,
                'min_spending': 5000,
                'min_flights': 25,
                'min_points': 15000,
                'points_multiplier': 1.50,
                'priority_boarding': True,
                'free_baggage_allowance': 10,
                'lounge_access': True,
                'free_seat_selection': True,
                'upgrade_priority': 2
            },
            {
                'name': 'Platinum',
                'slug': 'platinum',
                'description': 'The ultimate travel experience with our highest tier benefits.',
                'color_code': '#E5E4E2',
                'icon': 'fas fa-crown',
                'order': 3,
                'min_spending': 10000,
                'min_flights': 50,
                'min_points': 50000,
                'points_multiplier': 2.00,
                'priority_boarding': True,
                'free_baggage_allowance': 20,
                'lounge_access': True,
                'free_seat_selection': True,
                'upgrade_priority': 3
            }
        ]

        for tier_data in tiers_data:
            tier, created = LoyaltyTier.objects.get_or_create(
                slug=tier_data['slug'],
                defaults=tier_data
            )
            if created:
                self.stdout.write(f'  Created tier: {tier.name}')
            else:
                self.stdout.write(f'  Tier already exists: {tier.name}')

    def create_sample_rewards(self):
        self.stdout.write('Creating sample rewards...')

        # Get silver and gold tiers for restrictions
        try:
            silver_tier = LoyaltyTier.objects.get(slug='silver')
            gold_tier = LoyaltyTier.objects.get(slug='gold')
        except LoyaltyTier.DoesNotExist:
            silver_tier = None
            gold_tier = None

        rewards_data = [
            # Flight Rewards
            {
                'name': '$50 Flight Credit',
                'slug': 'flight-credit-50',
                'category': 'flight',
                'description': 'Redeem for $50 off any flight booking. Valid for 12 months from redemption date.',
                'points_required': 5000,
                'cash_equivalent': 50.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': True
            },
            {
                'name': '$100 Flight Credit',
                'slug': 'flight-credit-100',
                'category': 'flight',
                'description': 'Redeem for $100 off any flight booking. Valid for 12 months from redemption date.',
                'points_required': 9500,
                'cash_equivalent': 100.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': True
            },
            {
                'name': '$250 Flight Credit',
                'slug': 'flight-credit-250',
                'category': 'flight',
                'description': 'Redeem for $250 off any flight booking. Valid for 12 months from redemption date.',
                'points_required': 22500,
                'cash_equivalent': 250.00,
                'is_available': True,
                'minimum_tier': silver_tier,
                'featured': False
            },

            # Upgrade Rewards
            {
                'name': 'Single Cabin Upgrade',
                'slug': 'cabin-upgrade-single',
                'category': 'upgrade',
                'description': 'Upgrade to the next cabin class on any domestic flight. Subject to availability.',
                'points_required': 7500,
                'cash_equivalent': 75.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': True
            },
            {
                'name': 'Premium Cabin Upgrade',
                'slug': 'cabin-upgrade-premium',
                'category': 'upgrade',
                'description': 'Upgrade to premium cabin on any international flight. Subject to availability.',
                'points_required': 15000,
                'cash_equivalent': 200.00,
                'is_available': True,
                'minimum_tier': silver_tier,
                'featured': False
            },

            # Service Rewards
            {
                'name': 'Priority Boarding',
                'slug': 'priority-boarding',
                'category': 'service',
                'description': 'Skip the line with priority boarding on your next flight.',
                'points_required': 1500,
                'cash_equivalent': 25.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': False
            },
            {
                'name': 'Airport Lounge Access',
                'slug': 'lounge-access',
                'category': 'service',
                'description': 'One-time access to any COTRIPVn partner lounge worldwide.',
                'points_required': 3000,
                'cash_equivalent': 45.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': True
            },
            {
                'name': 'Extra Baggage Allowance',
                'slug': 'extra-baggage',
                'category': 'service',
                'description': 'Additional 10kg baggage allowance for your next flight.',
                'points_required': 2500,
                'cash_equivalent': 35.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': False
            },

            # Merchandise
            {
                'name': 'COTRIPVn Backpack',
                'slug': 'travel-backpack',
                'category': 'merchandise',
                'description': 'Premium travel backpack with laptop compartment and TSA-friendly design.',
                'points_required': 8000,
                'cash_equivalent': 120.00,
                'is_available': True,
                'stock_quantity': 50,
                'minimum_tier': None,
                'featured': False
            },
            {
                'name': 'Wireless Noise-Cancelling Headphones',
                'slug': 'noise-cancelling-headphones',
                'category': 'merchandise',
                'description': 'Premium wireless headphones perfect for long flights.',
                'points_required': 20000,
                'cash_equivalent': 300.00,
                'is_available': True,
                'stock_quantity': 25,
                'minimum_tier': gold_tier,
                'featured': True
            },

            # Partner Rewards
            {
                'name': 'Hotel Stay Gift Card ($100)',
                'slug': 'hotel-gift-card-100',
                'category': 'partner',
                'description': 'Use at any of our partner hotels worldwide. Valid for 18 months.',
                'points_required': 10000,
                'cash_equivalent': 100.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': False
            },
            {
                'name': 'Car Rental Credit ($75)',
                'slug': 'car-rental-credit',
                'category': 'partner',
                'description': 'Credit for car rentals with our partner companies.',
                'points_required': 7500,
                'cash_equivalent': 75.00,
                'is_available': True,
                'minimum_tier': None,
                'featured': False
            },

            # Experiences
            {
                'name': 'City Food Tour',
                'slug': 'city-food-tour',
                'category': 'experience',
                'description': 'Guided food tour in select cities. Must be booked in advance.',
                'points_required': 12000,
                'cash_equivalent': 150.00,
                'is_available': True,
                'stock_quantity': 10,
                'minimum_tier': silver_tier,
                'featured': True
            }
        ]

        for reward_data in rewards_data:
            reward, created = Reward.objects.get_or_create(
                slug=reward_data['slug'],
                defaults=reward_data
            )
            if created:
                self.stdout.write(f'  Created reward: {reward.name}')
            else:
                self.stdout.write(f'  Reward already exists: {reward.name}')

    def create_sample_promotions(self):
        self.stdout.write('Creating sample promotions...')

        # Get tiers for restrictions
        try:
            silver_tier = LoyaltyTier.objects.get(slug='silver')
            gold_tier = LoyaltyTier.objects.get(slug='gold')
        except LoyaltyTier.DoesNotExist:
            silver_tier = None
            gold_tier = None

        now = timezone.now()
        promotions_data = [
            {
                'name': 'Double Points December',
                'slug': 'double-points-december',
                'description': 'Earn double points on all flights booked and traveled in December. Perfect time to boost your tier status!',
                'promotion_type': 'double_points',
                'multiplier': 2.0,
                'bonus_points': 0,
                'minimum_spending': 0,
                'valid_from': now,
                'valid_until': now + timedelta(days=60),
                'max_uses_per_member': 3,
                'is_active': True
            },
            {
                'name': 'Silver Status Challenge',
                'slug': 'silver-status-challenge',
                'description': 'Earn 1.5x points when you spend $1000+ on flights. Exclusive to Silver members and above.',
                'promotion_type': 'points_multiplier',
                'multiplier': 1.5,
                'bonus_points': 0,
                'minimum_spending': 1000,
                'valid_from': now,
                'valid_until': now + timedelta(days=90),
                'max_uses_per_member': 2,
                'is_active': True
            },
            {
                'name': 'New Member Bonus',
                'slug': 'new-member-bonus',
                'description': 'Welcome bonus! Earn 2000 bonus points on your first flight booking.',
                'promotion_type': 'bonus_points',
                'multiplier': 1.0,
                'bonus_points': 2000,
                'minimum_spending': 200,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'max_uses_per_member': 1,
                'is_active': True
            },
            {
                'name': 'Weekend Warrior',
                'slug': 'weekend-warrior',
                'description': 'Book weekend flights and earn 25% bonus points. Valid for Saturday and Sunday departures.',
                'promotion_type': 'points_multiplier',
                'multiplier': 1.25,
                'bonus_points': 0,
                'minimum_spending': 0,
                'valid_from': now,
                'valid_until': now + timedelta(days=30),
                'max_uses_per_member': 5,
                'is_active': True
            }
        ]

        for promo_data in promotions_data:
            promotion, created = LoyaltyPromotion.objects.get_or_create(
                slug=promo_data['slug'],
                defaults=promo_data
            )
            
            if created:
                self.stdout.write(f'  Created promotion: {promotion.name}')
                
                # Set tier eligibility
                if promo_data['slug'] == 'silver-status-challenge' and silver_tier and gold_tier:
                    promotion.eligible_tiers.add(silver_tier, gold_tier)
            else:
                self.stdout.write(f'  Promotion already exists: {promotion.name}')