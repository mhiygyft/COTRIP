from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
from datetime import date, timedelta
from hotels.models import (
    Country, City, HotelChain, Amenity, Hotel, 
    RoomType, RoomAvailability, HotelFacility
)


class Command(BaseCommand):
    help = 'Populate database with sample hotel data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        with transaction.atomic():
            self.stdout.write('Creating sample data...')
            
            # Create countries and cities
            countries_cities = self.create_countries_cities()
            
            # Create hotel chains
            hotel_chains = self.create_hotel_chains()
            
            # Create amenities
            amenities = self.create_amenities()
            
            # Create hotels
            hotels = self.create_hotels(countries_cities, hotel_chains, amenities)
            
            # Create room types
            room_types = self.create_room_types(hotels, amenities)
            
            # Create room availability
            self.create_room_availability(room_types)
            
            # Create hotel facilities
            self.create_hotel_facilities(hotels)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )

    def clear_data(self):
        """Clear existing data"""
        RoomAvailability.objects.all().delete()
        HotelFacility.objects.all().delete()
        RoomType.objects.all().delete()
        Hotel.objects.all().delete()
        Amenity.objects.all().delete()
        HotelChain.objects.all().delete()
        City.objects.all().delete()
        Country.objects.all().delete()

    def create_countries_cities(self):
        """Create sample countries and cities"""
        countries_data = [
            {
                'name': 'United States',
                'code': 'US',
                'cities': [
                    {'name': 'New York', 'popular': True, 'lat': 40.7128, 'lng': -74.0060},
                    {'name': 'Los Angeles', 'popular': True, 'lat': 34.0522, 'lng': -118.2437},
                    {'name': 'Chicago', 'popular': False, 'lat': 41.8781, 'lng': -87.6298},
                    {'name': 'Miami', 'popular': True, 'lat': 25.7617, 'lng': -80.1918},
                ]
            },
            {
                'name': 'United Kingdom',
                'code': 'GB',
                'cities': [
                    {'name': 'London', 'popular': True, 'lat': 51.5074, 'lng': -0.1278},
                    {'name': 'Manchester', 'popular': False, 'lat': 53.4808, 'lng': -2.2426},
                    {'name': 'Edinburgh', 'popular': True, 'lat': 55.9533, 'lng': -3.1883},
                ]
            },
            {
                'name': 'France',
                'code': 'FR',
                'cities': [
                    {'name': 'Paris', 'popular': True, 'lat': 48.8566, 'lng': 2.3522},
                    {'name': 'Nice', 'popular': True, 'lat': 43.7102, 'lng': 7.2620},
                    {'name': 'Lyon', 'popular': False, 'lat': 45.7640, 'lng': 4.8357},
                ]
            },
            {
                'name': 'Japan',
                'code': 'JP',
                'cities': [
                    {'name': 'Tokyo', 'popular': True, 'lat': 35.6762, 'lng': 139.6503},
                    {'name': 'Kyoto', 'popular': True, 'lat': 35.0116, 'lng': 135.7681},
                    {'name': 'Osaka', 'popular': False, 'lat': 34.6937, 'lng': 135.5023},
                ]
            },
            {
                'name': 'India',
                'code': 'IN',
                'cities': [
                    {'name': 'Mumbai', 'popular': True, 'lat': 19.0760, 'lng': 72.8777},
                    {'name': 'Delhi', 'popular': True, 'lat': 28.7041, 'lng': 77.1025},
                    {'name': 'Bangalore', 'popular': False, 'lat': 12.9716, 'lng': 77.5946},
                    {'name': 'Goa', 'popular': True, 'lat': 15.2993, 'lng': 74.1240},
                ]
            },
            {
                'name': 'Thailand',
                'code': 'TH',
                'cities': [
                    {'name': 'Bangkok', 'popular': True, 'lat': 13.7563, 'lng': 100.5018},
                    {'name': 'Phuket', 'popular': True, 'lat': 7.8804, 'lng': 98.3923},
                    {'name': 'Chiang Mai', 'popular': False, 'lat': 18.7883, 'lng': 98.9853},
                ]
            }
        ]

        countries_cities = {}
        for country_data in countries_data:
            country = Country.objects.create(
                name=country_data['name'],
                code=country_data['code'],
                is_popular=True
            )
            
            cities = []
            for city_data in country_data['cities']:
                city = City.objects.create(
                    name=city_data['name'],
                    country=country,
                    latitude=city_data['lat'],
                    longitude=city_data['lng'],
                    is_popular=city_data['popular'],
                    description=f"Beautiful city in {country.name}"
                )
                cities.append(city)
            
            countries_cities[country] = cities
            
        self.stdout.write(f'Created {Country.objects.count()} countries and {City.objects.count()} cities')
        return countries_cities

    def create_hotel_chains(self):
        """Create sample hotel chains"""
        chains_data = [
            'Marriott International',
            'Hilton Worldwide',
            'InterContinental Hotels Group',
            'Hyatt Hotels Corporation',
            'Accor',
            'Radisson Hotel Group',
            'Best Western Hotels & Resorts',
        ]
        
        chains = []
        for chain_name in chains_data:
            chain = HotelChain.objects.create(
                name=chain_name,
                description=f"{chain_name} - Premium hospitality worldwide"
            )
            chains.append(chain)
            
        self.stdout.write(f'Created {len(chains)} hotel chains')
        return chains

    def create_amenities(self):
        """Create sample amenities"""
        amenities_data = [
            ('Free Wi-Fi', 'internet', 'bi-wifi', True),
            ('Swimming Pool', 'wellness', 'bi-droplet', True),
            ('Fitness Center', 'wellness', 'bi-heart-pulse', True),
            ('Spa', 'wellness', 'bi-flower1', False),
            ('Restaurant', 'food_drink', 'bi-cup-hot', True),
            ('Bar/Lounge', 'food_drink', 'bi-cup', False),
            ('Room Service', 'services', 'bi-bell', False),
            ('Concierge', 'services', 'bi-person-badge', False),
            ('Parking', 'parking', 'bi-car-front', True),
            ('Airport Shuttle', 'transportation', 'bi-bus-front', False),
            ('Pet Friendly', 'general', 'bi-heart', False),
            ('Business Center', 'business', 'bi-briefcase', False),
            ('Meeting Rooms', 'business', 'bi-people', False),
            ('Air Conditioning', 'general', 'bi-thermometer', True),
            ('Laundry Service', 'services', 'bi-basket', False),
            ('24/7 Front Desk', 'services', 'bi-clock', True),
            ('Non-Smoking Rooms', 'general', 'bi-ban', True),
            ('Family Rooms', 'family', 'bi-house', False),
            ('Accessibility Features', 'accessibility', 'bi-universal-access', False),
            ('Safe Deposit Box', 'safety', 'bi-safe', False),
        ]
        
        amenities = []
        for name, category, icon, is_popular in amenities_data:
            amenity = Amenity.objects.create(
                name=name,
                category=category,
                icon=icon,
                is_popular=is_popular
            )
            amenities.append(amenity)
            
        self.stdout.write(f'Created {len(amenities)} amenities')
        return amenities

    def create_hotels(self, countries_cities, hotel_chains, amenities):
        """Create sample hotels"""
        hotels = []
        hotel_names_templates = [
            '{city} Grand Hotel',
            '{city} Palace',
            '{city} Luxury Resort',
            'The {city} Hotel',
            '{city} Business Hotel',
            '{city} Boutique Inn',
            'Royal {city} Hotel',
            '{city} Suites',
            'Premium {city} Resort',
            '{city} Executive Hotel'
        ]
        
        descriptions = [
            "Experience luxury and comfort in the heart of the city. Our hotel offers world-class amenities and exceptional service.",
            "A perfect blend of modern convenience and classic elegance. Ideal for both business and leisure travelers.",
            "Located in the prime area with easy access to major attractions. Enjoy premium accommodations and top-notch facilities.",
            "Discover unparalleled hospitality in our beautifully appointed rooms and suites with stunning city views.",
            "Your home away from home with personalized service and attention to detail that exceeds expectations.",
        ]
        
        hotel_counter = 0
        for country, cities in countries_cities.items():
            for city in cities:
                # Create 3-8 hotels per city
                num_hotels = random.randint(3, 8)
                
                for i in range(num_hotels):
                    hotel_name = random.choice(hotel_names_templates).format(city=city.name)
                    
                    # Avoid duplicate names
                    if Hotel.objects.filter(name=hotel_name).exists():
                        hotel_name = f"{hotel_name} {random.choice(['Plaza', 'Tower', 'Central', 'Executive'])}"
                    
                    hotel = Hotel.objects.create(
                        name=hotel_name,
                        city=city,
                        address=f"{random.randint(1, 999)} {random.choice(['Main St', 'Broadway', 'Park Ave', 'Central Blvd', 'Royal Road'])}, {city.name}",
                        latitude=city.latitude + random.uniform(-0.1, 0.1),
                        longitude=city.longitude + random.uniform(-0.1, 0.1),
                        description=random.choice(descriptions),
                        star_rating=random.randint(3, 5),
                        hotel_chain=random.choice(hotel_chains) if random.choice([True, False]) else None,
                        price_from=Decimal(str(random.randint(50, 500))),
                        currency='VND',
                        is_active=True,
                        is_featured=random.choice([True, False, False, False]),  # 25% chance of being featured
                        is_verified=True,
                        average_rating=Decimal(str(round(random.uniform(6.5, 9.8), 1))),
                        total_reviews=random.randint(45, 2500),
                        meta_title=f"Book {hotel_name} - Best Rates Guaranteed",
                        meta_description=f"Book {hotel_name} in {city.name}. Great location, excellent amenities, and competitive rates."
                    )
                    
                    # Add random amenities (5-12 amenities per hotel)
                    hotel_amenities = random.sample(amenities, random.randint(5, 12))
                    hotel.amenities.set(hotel_amenities)
                    
                    hotels.append(hotel)
                    hotel_counter += 1
                    
                    if hotel_counter % 10 == 0:
                        self.stdout.write(f'Created {hotel_counter} hotels...')
        
        self.stdout.write(f'Created {len(hotels)} hotels')
        return hotels

    def create_room_types(self, hotels, amenities):
        """Create sample room types"""
        room_types = []
        
        room_templates = [
            {
                'name': 'Standard Room',
                'description': 'Comfortable room with essential amenities for a pleasant stay.',
                'size_range': (20, 30),
                'occupancy': (1, 2),
                'bed_type': 'double',
                'price_multiplier': 1.0
            },
            {
                'name': 'Superior Room',
                'description': 'Spacious room with enhanced amenities and city view.',
                'size_range': (25, 35),
                'occupancy': (2, 3),
                'bed_type': 'queen',
                'price_multiplier': 1.3
            },
            {
                'name': 'Deluxe Room',
                'description': 'Elegant room featuring premium furnishing and modern amenities.',
                'size_range': (30, 40),
                'occupancy': (2, 3),
                'bed_type': 'king',
                'price_multiplier': 1.6
            },
            {
                'name': 'Executive Suite',
                'description': 'Luxurious suite with separate living area and executive privileges.',
                'size_range': (45, 60),
                'occupancy': (2, 4),
                'bed_type': 'king',
                'price_multiplier': 2.2
            },
            {
                'name': 'Presidential Suite',
                'description': 'Ultimate luxury suite with panoramic views and exclusive services.',
                'size_range': (80, 120),
                'occupancy': (3, 6),
                'bed_type': 'king',
                'price_multiplier': 4.0
            }
        ]
        
        room_counter = 0
        for hotel in hotels:
            # Each hotel gets 2-4 room types
            num_room_types = random.randint(2, 4)
            selected_rooms = random.sample(room_templates, num_room_types)
            
            for room_template in selected_rooms:
                size_min, size_max = room_template['size_range']
                occ_min, occ_max = room_template['occupancy']
                
                room_type = RoomType.objects.create(
                    hotel=hotel,
                    name=room_template['name'],
                    description=room_template['description'],
                    size_sqm=random.randint(size_min, size_max),
                    max_occupancy=random.randint(occ_min, occ_max),
                    max_adults=random.randint(occ_min, occ_max),
                    max_children=random.randint(0, 2),
                    bed_type=room_template['bed_type'],
                    number_of_beds=1,
                    base_price=hotel.price_from * Decimal(str(room_template['price_multiplier'])),
                    is_refundable=random.choice([True, True, False]),  # 67% refundable
                    free_cancellation_hours=random.choice([24, 48, 72]),
                    is_active=True,
                    total_rooms=random.randint(5, 25)
                )
                
                # Add random amenities to room (3-8 amenities per room type)
                room_amenities = random.sample(amenities, random.randint(3, 8))
                room_type.amenities.set(room_amenities)
                
                # Update hotel's total_rooms
                hotel.total_rooms += room_type.total_rooms
                
                room_types.append(room_type)
                room_counter += 1
        
        # Update all hotels' total_rooms
        for hotel in hotels:
            hotel.save()
        
        self.stdout.write(f'Created {len(room_types)} room types')
        return room_types

    def create_room_availability(self, room_types):
        """Create room availability for the next 90 days"""
        availability_counter = 0
        start_date = date.today()
        
        for room_type in room_types:
            for i in range(90):  # Next 90 days
                current_date = start_date + timedelta(days=i)
                
                # Weekend pricing (Friday, Saturday)
                is_weekend = current_date.weekday() in [4, 5]
                
                # Random holiday simulation (5% chance)
                is_holiday = random.choice([False] * 19 + [True])
                
                # Base availability (70-100% of total rooms)
                available_rooms = random.randint(
                    int(room_type.total_rooms * 0.7),
                    room_type.total_rooms
                )
                
                # Dynamic pricing multiplier
                if is_holiday:
                    demand_multiplier = Decimal(str(round(random.uniform(1.5, 2.5), 2)))
                elif is_weekend:
                    demand_multiplier = Decimal(str(round(random.uniform(1.2, 1.8), 2)))
                else:
                    demand_multiplier = Decimal(str(round(random.uniform(0.9, 1.3), 2)))
                
                final_price = room_type.base_price * demand_multiplier
                
                RoomAvailability.objects.create(
                    room_type=room_type,
                    date=current_date,
                    available_rooms=available_rooms,
                    price=final_price,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    demand_multiplier=demand_multiplier
                )
                
                availability_counter += 1
                
                if availability_counter % 1000 == 0:
                    self.stdout.write(f'Created {availability_counter} availability records...')
        
        self.stdout.write(f'Created {availability_counter} room availability records')

    def create_hotel_facilities(self, hotels):
        """Create hotel facilities"""
        facilities_data = [
            ('Restaurant', 'dining', 'Enjoy delicious cuisine at our on-site restaurant', True),
            ('Coffee Shop', 'dining', '24/7 coffee and light snacks', True),
            ('Rooftop Bar', 'dining', 'Stunning views with craft cocktails', False),
            ('Swimming Pool', 'recreation', 'Outdoor pool with sun deck', True),
            ('Fitness Center', 'wellness', 'Modern gym equipment available 24/7', True),
            ('Spa & Wellness', 'wellness', 'Full-service spa with massage treatments', False),
            ('Business Center', 'business', 'Complete business services and meeting facilities', True),
            ('Conference Rooms', 'business', 'Professional meeting and event spaces', False),
            ('Free WiFi', 'connectivity', 'High-speed internet throughout the property', True),
            ('Parking', 'transportation', 'Secure on-site parking available', True),
            ('Airport Shuttle', 'transportation', 'Complimentary shuttle service', False),
            ('Concierge Service', 'services', '24/7 concierge assistance', False),
            ('Laundry Service', 'services', 'Professional laundry and dry cleaning', False),
            ('Room Service', 'services', '24-hour room service available', False),
            ('ATM/Bank', 'services', 'On-site banking services', True),
        ]
        
        facilities_counter = 0
        for hotel in hotels:
            # Each hotel gets 5-10 facilities
            num_facilities = random.randint(5, 10)
            selected_facilities = random.sample(facilities_data, num_facilities)
            
            for name, category, description, is_free in selected_facilities:
                additional_cost = None if is_free else Decimal(str(random.randint(10, 100)))
                
                HotelFacility.objects.create(
                    hotel=hotel,
                    name=name,
                    description=description,
                    category=category,
                    is_free=is_free,
                    additional_cost=additional_cost,
                    operating_hours='24 hours' if random.choice([True, False]) else '6:00 AM - 10:00 PM',
                    is_24_hours=random.choice([True, False])
                )
                
                facilities_counter += 1
        
        self.stdout.write(f'Created {facilities_counter} hotel facilities')
