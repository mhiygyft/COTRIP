from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Specific imports to avoid conflicts
from hotels.models import Country, City, Hotel, Amenity, Review, HotelChain, HotelImage
from users.models import User
from flights.models import Flight, Airline, Airport
from loyalty.models import LoyaltyTier, LoyaltyMembership

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with realistic travel data'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting to populate realistic travel data...')
        
        # Clear existing data
        self.stdout.write('🧹 Clearing existing data...')
        self.clear_existing_data()
        
        # Create countries and cities
        self.stdout.write('🌍 Creating countries and cities...')
        self.create_countries_and_cities()
        
        # Create airlines
        self.stdout.write('✈️ Creating airlines...')
        self.create_airlines()
        
        # Create airports
        self.stdout.write('🛫 Creating airports...')
        self.create_airports()
        
        # Create amenities
        self.stdout.write('🏨 Creating hotel amenities...')
        self.create_amenities()
        
        # Create realistic users
        self.stdout.write('👥 Creating sample users...')
        self.create_sample_users()
        
        # Create loyalty data
        self.stdout.write('⭐ Setting up loyalty program...')
        self.setup_loyalty_program()
        
        # Create hotels with realistic data
        self.stdout.write('🏢 Creating realistic hotels...')
        self.create_realistic_hotels()
        
        # Create flights
        self.stdout.write('🛩️ Creating realistic flights...')
        self.create_realistic_flights()
        
        # Create reviews
        self.stdout.write('📝 Creating realistic reviews...')
        self.create_realistic_reviews()
        
        # Create user credentials file
        self.stdout.write('📄 Creating user credentials file...')
        self.create_credentials_file()
        
        self.stdout.write(self.style.SUCCESS('✅ Successfully populated database with realistic data!'))

    def clear_existing_data(self):
        """Clear existing data except superuser"""
        Review.objects.all().delete()
        # Only import Booking model from bookings
        from bookings.models import Booking
        Booking.objects.all().delete()
        Flight.objects.all().delete()
        Hotel.objects.all().delete()
        Airport.objects.all().delete()
        Airline.objects.all().delete()
        City.objects.all().delete()
        Country.objects.all().delete()
        Amenity.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        LoyaltyMembership.objects.all().delete()
        # Only clear PointsTransaction if it exists
        try:
            PointsTransaction.objects.all().delete()
        except NameError:
            pass
        
    def create_countries_and_cities(self):
        """Create realistic countries and cities"""
        countries_cities = {
            'United States': {
                'code': 'US',
                'cities': [('New York', 'NYC'), ('Los Angeles', 'LAX'), ('Chicago', 'CHI'), 
                          ('Miami', 'MIA'), ('San Francisco', 'SFO'), ('Las Vegas', 'LAS'),
                          ('Boston', 'BOS'), ('Seattle', 'SEA')]
            },
            'United Kingdom': {
                'code': 'GB',
                'cities': [('London', 'LON'), ('Manchester', 'MAN'), ('Edinburgh', 'EDI'),
                          ('Birmingham', 'BHX')]
            },
            'France': {
                'code': 'FR',
                'cities': [('Paris', 'PAR'), ('Nice', 'NCE'), ('Lyon', 'LYS')]
            },
            'Germany': {
                'code': 'DE',
                'cities': [('Berlin', 'BER'), ('Munich', 'MUC'), ('Frankfurt', 'FRA')]
            },
            'Japan': {
                'code': 'JP',
                'cities': [('Tokyo', 'NRT'), ('Osaka', 'KIX'), ('Kyoto', 'KYO')]
            },
            'Australia': {
                'code': 'AU',
                'cities': [('Sydney', 'SYD'), ('Melbourne', 'MEL'), ('Brisbane', 'BNE')]
            },
            'Italy': {
                'code': 'IT',
                'cities': [('Rome', 'ROM'), ('Milan', 'MIL'), ('Venice', 'VCE')]
            },
            'Spain': {
                'code': 'ES',
                'cities': [('Madrid', 'MAD'), ('Barcelona', 'BCN'), ('Seville', 'SVQ')]
            },
            'India': {
                'code': 'IN',
                'cities': [('Mumbai', 'BOM'), ('Delhi', 'DEL'), ('Bangalore', 'BLR'), 
                          ('Chennai', 'MAA'), ('Kolkata', 'CCU'), ('Hyderabad', 'HYD'),
                          ('Pune', 'PNQ'), ('Ahmedabad', 'AMD'), ('Jaipur', 'JAI'), 
                          ('Goa', 'GOI'), ('Kochi', 'COK'), ('Udaipur', 'UDR')]
            },
            'Thailand': {
                'code': 'TH', 
                'cities': [('Bangkok', 'BKK'), ('Phuket', 'HKT'), ('Chiang Mai', 'CNX')]
            },
            'Singapore': {
                'code': 'SG',
                'cities': [('Singapore', 'SIN')]
            }
        }
        
        for country_name, country_data in countries_cities.items():
            country, _ = Country.objects.get_or_create(
                name=country_name,
                defaults={'code': country_data['code']}
            )
            
            for city_name, code in country_data['cities']:
                City.objects.get_or_create(
                    name=city_name,
                    country=country,
                    defaults={}
                )

    def create_airlines(self):
        """Create realistic airlines"""
        # Skip airline creation for now - focus on hotel data first
        self.stdout.write('Skipping airline creation - focusing on hotel data')
        pass

    def create_airports(self):
        """Create realistic airports"""
        # Skip airport creation for now - focus on hotel data first
        self.stdout.write('Skipping airport creation - focusing on hotel data')
        pass

    def create_amenities(self):
        """Create hotel amenities"""
        amenities = [
            'Free WiFi', 'Swimming Pool', 'Fitness Center', 'Spa', 'Restaurant',
            'Room Service', 'Business Center', 'Parking', 'Airport Shuttle',
            'Pet Friendly', 'Air Conditioning', 'Balcony', 'Ocean View',
            'City View', 'Minibar', 'Safe', 'Concierge', 'Laundry Service',
            'Meeting Rooms', 'Conference Facilities', 'Bar/Lounge', 'Beach Access',
            'Tennis Court', 'Golf Course', 'Kids Club', 'Babysitting'
        ]
        
        for amenity_name in amenities:
            Amenity.objects.get_or_create(name=amenity_name)

    def create_sample_users(self):
        """Create realistic sample users for testing"""
        sample_users = [
            {
                'email': 'john.doe@email.com',
                'password': 'TravelLover2024!',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '+1-555-0123',
                'city': 'New York',
                'country': 'United States',
                'date_of_birth': '1985-03-15'
            },
            {
                'email': 'sarah.smith@email.com', 
                'password': 'Explorer123!',
                'first_name': 'Sarah',
                'last_name': 'Smith',
                'phone_number': '+1-555-0456',
                'city': 'Los Angeles',
                'country': 'United States',
                'date_of_birth': '1990-07-22'
            },
            {
                'email': 'mike.johnson@email.com',
                'password': 'Adventure2024!',
                'first_name': 'Mike',
                'last_name': 'Johnson', 
                'phone_number': '+44-20-7946-0958',
                'city': 'London',
                'country': 'United Kingdom',
                'date_of_birth': '1988-12-01'
            },
            {
                'email': 'emma.wilson@email.com',
                'password': 'Wanderlust!2024',
                'first_name': 'Emma',
                'last_name': 'Wilson',
                'phone_number': '+33-1-23-45-67-89',
                'city': 'Paris',
                'country': 'France',
                'date_of_birth': '1992-05-18'
            },
            {
                'email': 'david.brown@email.com',
                'password': 'Business2024!',
                'first_name': 'David',
                'last_name': 'Brown',
                'phone_number': '+81-3-1234-5678',
                'city': 'Tokyo',
                'country': 'Japan',
                'date_of_birth': '1982-09-30'
            }
        ]
        
        self.created_users = []
        
        for user_data in sample_users:
            try:
                user = User.objects.create_user(
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone_number=user_data.get('phone_number', ''),
                    city=user_data['city'],
                    country=user_data['country'],
                    date_of_birth=user_data.get('date_of_birth'),
                    is_active=True,
                    is_email_verified=True
                )
                self.created_users.append(user)
                
            except Exception as e:
                self.stdout.write(f'Error creating user {user_data["email"]}: {e}')

    def setup_loyalty_program(self):
        """Setup loyalty program with tiers and rewards"""
        # Create loyalty tiers (should already exist from loyalty app setup)
        tiers_data = [
            {'name': 'Bronze', 'min_points': 0, 'multiplier': 1.0},
            {'name': 'Silver', 'min_points': 1000, 'multiplier': 1.2},
            {'name': 'Gold', 'min_points': 5000, 'multiplier': 1.5},
            {'name': 'Platinum', 'min_points': 15000, 'multiplier': 2.0},
        ]
        
        for tier_data in tiers_data:
            LoyaltyTier.objects.get_or_create(
                name=tier_data['name'],
                defaults={
                    'min_points_required': tier_data['min_points'],
                    'points_multiplier': tier_data['multiplier'],
                    'benefits': f"{tier_data['name']} tier benefits including {tier_data['multiplier']}x points"
                }
            )
        
        # Create loyalty memberships for users
        bronze_tier = LoyaltyTier.objects.get(name='Bronze')
        silver_tier = LoyaltyTier.objects.get(name='Silver')
        gold_tier = LoyaltyTier.objects.get(name='Gold')
        
        for i, user in enumerate(self.created_users):
            if i == 0:  # First user gets Gold status
                tier = gold_tier
                points = 7500
            elif i == 1:  # Second user gets Silver status
                tier = silver_tier  
                points = 2500
            else:  # Others get Bronze
                tier = bronze_tier
                points = random.randint(100, 999)
                
            membership, created = LoyaltyMembership.objects.get_or_create(
                user=user,
                defaults={
                    'tier': tier,
                    'points_balance': points,
                    'lifetime_points': points + random.randint(0, 1000)
                }
            )

    def create_realistic_hotels(self):
        """Create realistic hotels with proper data"""
        realistic_hotels = [
            {
                'name': 'The Plaza Hotel New York',
                'city': 'New York',
                'address': '768 5th Ave, New York, NY 10019',
                'star_rating': 5,
                'base_price': 899,
                'description': 'An iconic luxury hotel in the heart of Manhattan, steps from Central Park and Fifth Avenue shopping. The Plaza offers elegantly appointed rooms and suites with classic European décor.',
                'amenities': ['Free WiFi', 'Spa', 'Restaurant', 'Room Service', 'Concierge', 'Fitness Center', 'Business Center'],
                'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop'
            },
            {
                'name': 'Beverly Hills Hotel',
                'city': 'Los Angeles', 
                'address': '9641 Sunset Blvd, Beverly Hills, CA 90210',
                'star_rating': 5,
                'base_price': 1200,
                'description': 'The legendary "Pink Palace" of Beverly Hills, offering timeless glamour and modern luxury. Set on 12 acres of lush tropical gardens.',
                'amenities': ['Swimming Pool', 'Spa', 'Restaurant', 'Room Service', 'Tennis Court', 'Fitness Center', 'Parking'],
                'image_url': 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=800&h=600&fit=crop'
            },
            {
                'name': 'The Savoy London',
                'city': 'London',
                'address': 'Strand, London WC2R 0EU',
                'star_rating': 5,
                'base_price': 650,
                'description': 'A legendary luxury hotel on the banks of the Thames, offering Art Deco glamour and modern British style in the heart of London.',
                'amenities': ['Restaurant', 'Bar/Lounge', 'Spa', 'Fitness Center', 'Business Center', 'Concierge', 'Room Service'],
                'image_url': 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&h=600&fit=crop'
            },
            {
                'name': 'Hotel de Crillon Paris',
                'city': 'Paris',
                'address': '10 Place de la Concorde, 75008 Paris',
                'star_rating': 5,
                'base_price': 1100,
                'description': 'An 18th-century palace hotel overlooking Place de la Concorde, combining French heritage with contemporary luxury and Michelin-starred dining.',
                'amenities': ['Spa', 'Restaurant', 'Bar/Lounge', 'Room Service', 'Concierge', 'Business Center', 'Meeting Rooms'],
                'image_url': 'https://images.unsplash.com/photo-1549294413-26f195200c16?w=800&h=600&fit=crop'
            },
            {
                'name': 'Hotel Adlon Kempinski Berlin',
                'city': 'Berlin',
                'address': 'Unter den Linden 77, 10117 Berlin',
                'star_rating': 5,
                'base_price': 550,
                'description': 'Legendary luxury hotel located at the Brandenburg Gate, offering panoramic views and world-class amenities in the heart of Berlin.',
                'amenities': ['Spa', 'Swimming Pool', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Room Service'],
                'image_url': 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&h=600&fit=crop'
            },
            {
                'name': 'The Ritz-Carlton Tokyo',
                'city': 'Tokyo',
                'address': '9-7-1 Akasaka, Minato-ku, Tokyo 107-6245',
                'star_rating': 5,
                'base_price': 750,
                'description': 'Luxury hotel in the heart of Tokyo with stunning city views, featuring traditional Japanese hospitality and modern amenities.',
                'amenities': ['Spa', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Room Service', 'City View'],
                'image_url': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&h=600&fit=crop'
            },
            {
                'name': 'Park Hyatt Sydney',
                'city': 'Sydney',
                'address': '7 Hickson Rd, The Rocks NSW 2000',
                'star_rating': 5,
                'base_price': 650,
                'description': 'Contemporary luxury hotel with unparalleled views of Sydney Harbour, Opera House, and Harbour Bridge from every room.',
                'amenities': ['Restaurant', 'Bar/Lounge', 'Spa', 'Fitness Center', 'Room Service', 'Business Center', 'Ocean View'],
                'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&h=600&fit=crop'
            },
            {
                'name': 'Hotel Danieli Venice',
                'city': 'Venice',
                'address': 'Riva degli Schiavoni, 4196, 30122 Venice',
                'star_rating': 5,
                'base_price': 850,
                'description': 'Historic palace hotel on the Grand Canal, offering Venetian elegance with antique furnishings and lagoon views.',
                'amenities': ['Restaurant', 'Bar/Lounge', 'Room Service', 'Concierge', 'Business Center', 'Ocean View', 'Balcony'],
                'image_url': 'https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&h=600&fit=crop'
            }
        ]
        
        # Add Indian luxury hotels
        indian_hotels = [
            {
                'name': 'The Taj Mahal Palace Mumbai',
                'city': 'Mumbai',
                'address': 'Apollo Bunder, Colaba, Mumbai, Maharashtra 400001',
                'star_rating': 5,
                'base_price': 450,
                'description': 'Iconic luxury hotel overlooking the Gateway of India, blending Moorish, Oriental and Florentine styles. A heritage landmark offering world-class hospitality since 1903.',
                'amenities': ['Spa', 'Swimming Pool', 'Restaurant', 'Room Service', 'Business Center', 'Concierge', 'Fitness Center'],
                'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop'
            },
            {
                'name': 'The Oberoi New Delhi',
                'city': 'Delhi',
                'address': 'Dr. A P J Abdul Kalam Road, New Delhi 110011',
                'star_rating': 5,
                'base_price': 380,
                'description': 'Luxury hotel in the heart of New Delhi, offering panoramic views of the Delhi Golf Course and Humayun\'s Tomb. Known for exceptional service and elegant accommodations.',
                'amenities': ['Spa', 'Swimming Pool', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Room Service'],
                'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&h=600&fit=crop'
            },
            {
                'name': 'ITC Grand Chola Chennai',
                'city': 'Chennai',
                'address': '63 Mount Road, Guindy, Chennai, Tamil Nadu 600032',
                'star_rating': 5,
                'base_price': 320,
                'description': 'Magnificent luxury hotel inspired by the grandeur of the Chola dynasty. Features world-class amenities and authentic South Indian hospitality.',
                'amenities': ['Spa', 'Swimming Pool', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Meeting Rooms'],
                'image_url': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800&h=600&fit=crop'
            },
            {
                'name': 'Taj Lake Palace Udaipur',
                'city': 'Udaipur',
                'address': 'Pichola Lake, Udaipur, Rajasthan 313001',
                'star_rating': 5,
                'base_price': 650,
                'description': 'Floating palace hotel on Lake Pichola, originally built in 1746. A breathtaking white marble palace offering royal luxury and unforgettable experiences.',
                'amenities': ['Spa', 'Restaurant', 'Bar/Lounge', 'Room Service', 'Concierge', 'Business Center', 'Lake View'],
                'image_url': 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=600&fit=crop'
            },
            {
                'name': 'The Leela Palace Bangalore',
                'city': 'Bangalore',
                'address': '23 Kodihalli, Old Airport Road, Bangalore, Karnataka 560008',
                'star_rating': 5,
                'base_price': 280,
                'description': 'Contemporary luxury hotel offering world-class amenities and elegant accommodations in India\'s Silicon Valley. Perfect for business and leisure travelers.',
                'amenities': ['Spa', 'Swimming Pool', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Airport Shuttle'],
                'image_url': 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=800&h=600&fit=crop'
            },
            {
                'name': 'Taj Exotica Resort & Spa Goa',
                'city': 'Goa',
                'address': 'Calwaddo, Benaulim, Goa 403716',
                'star_rating': 5,
                'base_price': 420,
                'description': 'Beachfront resort nestled among 56 acres of lush gardens along the Benaulim beach. Offers authentic Goan hospitality with world-class amenities.',
                'amenities': ['Beach Access', 'Spa', 'Swimming Pool', 'Restaurant', 'Bar/Lounge', 'Tennis Court', 'Water Sports'],
                'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&h=600&fit=crop'
            }
        ]
        
        # Add mid-range hotels
        mid_range_hotels = [
            {
                'name': 'Hampton Inn Manhattan/Times Square',
                'city': 'New York',
                'address': '851 8th Avenue, New York, NY 10019',
                'star_rating': 3,
                'base_price': 285,
                'description': 'Modern hotel in the heart of Times Square, perfect for business and leisure travelers with comfortable accommodations.',
                'amenities': ['Free WiFi', 'Fitness Center', 'Business Center', 'Air Conditioning'],
                'image_url': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800&h=600&fit=crop'
            },
            {
                'name': 'Holiday Inn Express London City',
                'city': 'London',
                'address': '275 Old St, London EC1V 9LN',
                'star_rating': 3,
                'base_price': 155,
                'description': 'Contemporary hotel in the vibrant Shoreditch area, offering comfortable rooms and easy access to the City.',
                'amenities': ['Free WiFi', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Air Conditioning'],
                'image_url': 'https://images.unsplash.com/photo-1596436889106-be35e843f974?w=800&h=600&fit=crop'
            },
            {
                'name': 'Ibis Paris Bastille Opera',
                'city': 'Paris',
                'address': '15 Rue Breguet, 75011 Paris',
                'star_rating': 3,
                'base_price': 120,
                'description': 'Modern hotel near Place de la Bastille and Opera, offering comfortable accommodations in central Paris.',
                'amenities': ['Free WiFi', 'Restaurant', 'Bar/Lounge', 'Air Conditioning', 'Business Center'],
                'image_url': 'https://images.unsplash.com/photo-1551918120-9739cb430c6d?w=800&h=600&fit=crop'
            },
            {
                'name': 'Hotel Vivanta Bengaluru',
                'city': 'Bangalore',
                'address': 'Lal Bagh Road, Bangalore, Karnataka 560027',
                'star_rating': 4,
                'base_price': 150,
                'description': 'Contemporary business hotel in the heart of Bangalore, offering modern amenities and comfortable accommodation for business travelers.',
                'amenities': ['Free WiFi', 'Restaurant', 'Bar/Lounge', 'Fitness Center', 'Business Center', 'Swimming Pool'],
                'image_url': 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&h=600&fit=crop'
            },
            {
                'name': 'Lemon Tree Hotel Delhi',
                'city': 'Delhi',
                'address': 'Asset No 6, Aerocity Hospitality District, New Delhi 110037',
                'star_rating': 3,
                'base_price': 95,
                'description': 'Modern business hotel near Delhi airport with contemporary design, efficient service and all essential amenities for travelers.',
                'amenities': ['Free WiFi', 'Restaurant', 'Fitness Center', 'Business Center', 'Airport Shuttle'],
                'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop'
            }
        ]
        
        all_hotels = realistic_hotels + indian_hotels + mid_range_hotels
        
        for hotel_data in all_hotels:
            try:
                city = City.objects.get(name=hotel_data['city'])
                
                # Create hotel
                hotel, created = Hotel.objects.get_or_create(
                    name=hotel_data['name'],
                    defaults={
                        'slug': slugify(hotel_data['name']),
                        'city': city,
                        'address': hotel_data['address'],
                        'star_rating': hotel_data['star_rating'],
                        'price_from': hotel_data['base_price'],
                        'description': hotel_data['description'],
                        'image_url': hotel_data.get('image_url', ''),
                        'check_in_time': '15:00:00',
                        'check_out_time': '11:00:00',
                        'total_rooms': random.randint(50, 300),
                        'is_active': True
                    }
                )
                
                if created:
                    # Add amenities
                    for amenity_name in hotel_data['amenities']:
                        try:
                            amenity = Amenity.objects.get(name=amenity_name)
                            hotel.amenities.add(amenity)
                        except Amenity.DoesNotExist:
                            pass
                    
                    self.stdout.write(f'Created hotel: {hotel.name}')
                
            except City.DoesNotExist:
                self.stdout.write(f'Warning: City {hotel_data["city"]} not found for hotel {hotel_data["name"]}')

    def create_realistic_flights(self):
        """Create realistic flight data"""
        # Skip flight creation for now due to complex model requirements
        # The flights app has complex relationships with Aircraft, Route models
        # that would require significant setup
        self.stdout.write('Skipping flight creation - complex model relationships need proper setup')
        pass

    def create_realistic_reviews(self):
        """Create realistic hotel reviews"""
        hotels = list(Hotel.objects.all())
        users = list(User.objects.all())
        
        review_texts = [
            "Absolutely wonderful stay! The staff was incredibly friendly and the location couldn't be better. Highly recommend!",
            "Great hotel with excellent amenities. The room was clean and comfortable. Will definitely stay here again.",
            "Perfect location for exploring the city. The breakfast was delicious and the concierge was very helpful.",
            "Beautiful hotel with stunning views. The spa was amazing and really helped me relax during my business trip.",
            "Good value for money. The room was spacious and the WiFi was fast. Minor issues with noise but overall satisfactory.",
            "Outstanding service from check-in to check-out. The restaurant on-site serves excellent food. A truly luxury experience.",
            "Decent hotel in a great location. The fitness center was well-equipped but the room could use some updates.",
            "Exceeded my expectations! The attention to detail was impressive and the bed was incredibly comfortable.",
            "The hotel lived up to its reputation. Every aspect of our stay was perfect, from the room to the dining options.",
            "Good hotel for business travelers. The business center was well-equipped and the meeting rooms were professional."
        ]
        
        for hotel in hotels:
            # Create 5-15 reviews per hotel
            num_reviews = min(random.randint(5, 15), len(users))  # Don't exceed number of users
            selected_users = random.sample(users, num_reviews)  # No duplicates
            
            for user in selected_users:
                rating = random.choices([3, 4, 5], weights=[10, 40, 50])[0]  # Weighted towards higher ratings
                
                Review.objects.create(
                    hotel=hotel,
                    user=user,
                    rating=rating,
                    title=f"{'Great' if rating >= 4 else 'Good'} stay at {hotel.name}",
                    comment=random.choice(review_texts),
                    created_at=timezone.now() - timedelta(days=random.randint(1, 365))
                )

    def create_credentials_file(self):
        """Create a file with all user login credentials"""
        credentials_content = """# NOVARYO SAMPLE USER CREDENTIALS

## Test User Accounts

Here are the sample user accounts created for testing the Novaryo platform:

### 1. John Doe (Gold Tier Member)
- **Email:** john.doe@email.com
- **Password:** TravelLover2024!
- **Profile:** Business traveler from New York with Gold loyalty status
- **Loyalty Points:** 7,500+ points

### 2. Sarah Smith (Silver Tier Member)  
- **Email:** sarah.smith@email.com
- **Password:** Explorer123!
- **Profile:** Frequent traveler from Los Angeles with Silver status
- **Loyalty Points:** 2,500+ points

### 3. Mike Johnson (Explorer)
- **Email:** mike.johnson@email.com
- **Password:** Adventure2024!
- **Profile:** UK-based traveler, loves European destinations
- **Location:** London, UK

### 4. Emma Wilson (French Local)
- **Email:** emma.wilson@email.com  
- **Password:** Wanderlust!2024
- **Profile:** Paris-based user who travels frequently for leisure
- **Location:** Paris, France

### 5. David Brown (Business Professional)
- **Email:** david.brown@email.com
- **Password:** Business2024!
- **Profile:** Tokyo-based business traveler
- **Location:** Tokyo, Japan

## Admin Access

If you created a superuser account during setup, use those credentials to access:
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **API Documentation:** http://127.0.0.1:8000/api/docs/

## Quick Test Features

1. **Login with any account above** to test user functionality
2. **Search hotels** - realistic data for major cities worldwide
3. **Check loyalty dashboard** - John and Sarah have points and tier status
4. **View hotel details** - realistic descriptions and amenities
5. **API Testing** - use API docs with these accounts

## Notes

- All accounts have verified email addresses
- Passwords follow strong security requirements
- Users have realistic profile data including phone numbers and locations
- Loyalty program data is pre-populated with realistic point balances
"""

        with open('USER_CREDENTIALS.md', 'w', encoding='utf-8') as f:
            f.write(credentials_content)