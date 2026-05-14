from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta, date
from flights.models import (
    Country, Airport, Airline, Aircraft, Route, Flight, 
    FlightSeat, BaggageAllowance, FlightSearch
)


class Command(BaseCommand):
    help = 'Populate database with sample flight data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing flight data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing flight data...')
            self.clear_data()

        with transaction.atomic():
            self.stdout.write('Creating sample flight data...')
            
            # Create countries
            countries = self.create_countries()
            
            # Create airports
            airports = self.create_airports(countries)
            
            # Create airlines
            airlines = self.create_airlines(countries)
            
            # Create aircraft
            aircraft = self.create_aircraft()
            
            # Create routes
            routes = self.create_routes(airports)
            
            # Create flights
            flights = self.create_flights(airlines, aircraft, airports, routes)
            
            # Create baggage allowances
            self.create_baggage_allowances(airlines)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with flight data!')
        )

    def clear_data(self):
        """Clear existing flight data"""
        Flight.objects.all().delete()
        Route.objects.all().delete()
        Aircraft.objects.all().delete()
        BaggageAllowance.objects.all().delete()
        Airline.objects.all().delete()
        Airport.objects.all().delete()
        Country.objects.all().delete()

    def create_countries(self):
        """Create sample countries for flights"""
        countries_data = [
            {'name': 'United States', 'code': 'USA', 'iso_code': 'US', 'currency': 'USD', 'timezone': 'America/New_York'},
            {'name': 'United Kingdom', 'code': 'GBR', 'iso_code': 'GB', 'currency': 'GBP', 'timezone': 'Europe/London'},
            {'name': 'Germany', 'code': 'DEU', 'iso_code': 'DE', 'currency': 'EUR', 'timezone': 'Europe/Berlin'},
            {'name': 'France', 'code': 'FRA', 'iso_code': 'FR', 'currency': 'EUR', 'timezone': 'Europe/Paris'},
            {'name': 'Japan', 'code': 'JPN', 'iso_code': 'JP', 'currency': 'JPY', 'timezone': 'Asia/Tokyo'},
            {'name': 'Australia', 'code': 'AUS', 'iso_code': 'AU', 'currency': 'AUD', 'timezone': 'Australia/Sydney'},
            {'name': 'Singapore', 'code': 'SGP', 'iso_code': 'SG', 'currency': 'SGD', 'timezone': 'Asia/Singapore'},
            {'name': 'United Arab Emirates', 'code': 'ARE', 'iso_code': 'AE', 'currency': 'AED', 'timezone': 'Asia/Dubai'},
        ]
        
        countries = {}
        for country_data in countries_data:
            country = Country.objects.create(**country_data)
            countries[country.iso_code] = country
            
        self.stdout.write(f'Created {len(countries)} countries')
        return countries

    def create_airports(self, countries):
        """Create major airports worldwide"""
        airports_data = [
            # United States
            {'name': 'John F. Kennedy International Airport', 'iata_code': 'JFK', 'icao_code': 'KJFK', 
             'city': 'New York', 'country': 'US', 'lat': 40.6413, 'lng': -73.7781, 'timezone': 'America/New_York', 'is_international': True, 'is_popular': True},
            {'name': 'Los Angeles International Airport', 'iata_code': 'LAX', 'icao_code': 'KLAX', 
             'city': 'Los Angeles', 'country': 'US', 'lat': 33.9425, 'lng': -118.4081, 'timezone': 'America/Los_Angeles', 'is_international': True, 'is_popular': True},
            {'name': 'Miami International Airport', 'iata_code': 'MIA', 'icao_code': 'KMIA', 
             'city': 'Miami', 'country': 'US', 'lat': 25.7959, 'lng': -80.2870, 'timezone': 'America/New_York', 'is_international': True, 'is_popular': True},
             
            # United Kingdom
            {'name': 'Heathrow Airport', 'iata_code': 'LHR', 'icao_code': 'EGLL', 
             'city': 'London', 'country': 'GB', 'lat': 51.4700, 'lng': -0.4543, 'timezone': 'Europe/London', 'is_international': True, 'is_popular': True},
             
            # Germany
            {'name': 'Frankfurt Airport', 'iata_code': 'FRA', 'icao_code': 'EDDF', 
             'city': 'Frankfurt', 'country': 'DE', 'lat': 50.0379, 'lng': 8.5622, 'timezone': 'Europe/Berlin', 'is_international': True, 'is_popular': True},
             
            # France
            {'name': 'Charles de Gaulle Airport', 'iata_code': 'CDG', 'icao_code': 'LFPG', 
             'city': 'Paris', 'country': 'FR', 'lat': 49.0097, 'lng': 2.5479, 'timezone': 'Europe/Paris', 'is_international': True, 'is_popular': True},
             
            # Japan
            {'name': 'Tokyo Haneda Airport', 'iata_code': 'HND', 'icao_code': 'RJTT', 
             'city': 'Tokyo', 'country': 'JP', 'lat': 35.5494, 'lng': 139.7798, 'timezone': 'Asia/Tokyo', 'is_international': True, 'is_popular': True},
            {'name': 'Narita International Airport', 'iata_code': 'NRT', 'icao_code': 'RJAA', 
             'city': 'Tokyo', 'country': 'JP', 'lat': 35.7647, 'lng': 140.3864, 'timezone': 'Asia/Tokyo', 'is_international': True, 'is_popular': True},
             
            # Australia
            {'name': 'Sydney Kingsford Smith Airport', 'iata_code': 'SYD', 'icao_code': 'YSSY', 
             'city': 'Sydney', 'country': 'AU', 'lat': -33.9399, 'lng': 151.1753, 'timezone': 'Australia/Sydney', 'is_international': True, 'is_popular': True},
             
            # Other major airports
            {'name': 'Singapore Changi Airport', 'iata_code': 'SIN', 'icao_code': 'WSSS', 
             'city': 'Singapore', 'country': 'SG', 'lat': 1.3644, 'lng': 103.9915, 'timezone': 'Asia/Singapore', 'is_international': True, 'is_popular': True},
            {'name': 'Dubai International Airport', 'iata_code': 'DXB', 'icao_code': 'OMDB', 
             'city': 'Dubai', 'country': 'AE', 'lat': 25.2532, 'lng': 55.3657, 'timezone': 'Asia/Dubai', 'is_international': True, 'is_popular': True},
        ]
        
        airports = {}
        for airport_data in airports_data:
            country_code = airport_data.pop('country')
            country = countries[country_code]
            airport = Airport.objects.create(
                country=country,
                latitude=Decimal(str(airport_data.pop('lat'))),
                longitude=Decimal(str(airport_data.pop('lng'))),
                **airport_data
            )
            airports[airport.iata_code] = airport
            
        self.stdout.write(f'Created {len(airports)} airports')
        return airports

    def create_airlines(self, countries):
        """Create major airlines"""
        airlines_data = [
            {'name': 'American Airlines', 'iata_code': 'AA', 'icao_code': 'AAL', 'country': 'US', 'is_low_cost': False},
            {'name': 'Delta Air Lines', 'iata_code': 'DL', 'icao_code': 'DAL', 'country': 'US', 'is_low_cost': False},
            {'name': 'United Airlines', 'iata_code': 'UA', 'icao_code': 'UAL', 'country': 'US', 'is_low_cost': False},
            {'name': 'British Airways', 'iata_code': 'BA', 'icao_code': 'BAW', 'country': 'GB', 'is_low_cost': False},
            {'name': 'Lufthansa', 'iata_code': 'LH', 'icao_code': 'DLH', 'country': 'DE', 'is_low_cost': False},
            {'name': 'Air France', 'iata_code': 'AF', 'icao_code': 'AFR', 'country': 'FR', 'is_low_cost': False},
            {'name': 'Japan Airlines', 'iata_code': 'JL', 'icao_code': 'JAL', 'country': 'JP', 'is_low_cost': False},
            {'name': 'Singapore Airlines', 'iata_code': 'SQ', 'icao_code': 'SIA', 'country': 'SG', 'is_low_cost': False},
            {'name': 'Emirates', 'iata_code': 'EK', 'icao_code': 'UAE', 'country': 'AE', 'is_low_cost': False},
            {'name': 'Qantas', 'iata_code': 'QF', 'icao_code': 'QFA', 'country': 'AU', 'is_low_cost': False},
        ]
        
        airlines = {}
        for airline_data in airlines_data:
            country_code = airline_data.pop('country')
            country = countries[country_code]
            airline = Airline.objects.create(
                country=country,
                average_rating=Decimal(str(round(random.uniform(3.5, 4.8), 1))),
                total_reviews=random.randint(500, 5000),
                **airline_data
            )
            airlines[airline.iata_code] = airline
            
        self.stdout.write(f'Created {len(airlines)} airlines')
        return airlines

    def create_aircraft(self):
        """Create aircraft types"""
        aircraft_data = [
            {'manufacturer': 'Boeing', 'model': '737', 'variant': '800', 'total_seats': 189, 'economy_seats': 162, 'business_seats': 16, 'first_class_seats': 8},
            {'manufacturer': 'Boeing', 'model': '777', 'variant': '300ER', 'total_seats': 396, 'economy_seats': 296, 'premium_economy_seats': 40, 'business_seats': 42, 'first_class_seats': 8},
            {'manufacturer': 'Airbus', 'model': 'A320', 'variant': 'neo', 'total_seats': 180, 'economy_seats': 150, 'business_seats': 20, 'first_class_seats': 8},
            {'manufacturer': 'Airbus', 'model': 'A350', 'variant': '900', 'total_seats': 325, 'economy_seats': 253, 'premium_economy_seats': 36, 'business_seats': 28, 'first_class_seats': 8},
        ]
        
        aircraft = []
        for ac_data in aircraft_data:
            ac = Aircraft.objects.create(
                has_wifi=random.choice([True, False]),
                has_entertainment=True,
                has_power_outlets=random.choice([True, False]),
                **ac_data
            )
            aircraft.append(ac)
            
        self.stdout.write(f'Created {len(aircraft)} aircraft types')
        return aircraft

    def create_routes(self, airports):
        """Create popular flight routes"""
        popular_routes = [
            ('JFK', 'LHR', 5585, 450),  # New York - London
            ('LAX', 'NRT', 8815, 660),  # Los Angeles - Tokyo
            ('LHR', 'CDG', 344, 75),    # London - Paris
            ('FRA', 'JFK', 6194, 480),  # Frankfurt - New York
            ('SIN', 'LHR', 10890, 780), # Singapore - London
            ('DXB', 'LHR', 5493, 420),  # Dubai - London
            ('SYD', 'SIN', 6317, 480),  # Sydney - Singapore
            ('HND', 'SIN', 5302, 420),  # Tokyo - Singapore
        ]
        
        routes = []
        for origin_code, dest_code, distance, duration in popular_routes:
            if origin_code in airports and dest_code in airports:
                route = Route.objects.create(
                    origin=airports[origin_code],
                    destination=airports[dest_code],
                    distance_km=distance,
                    typical_duration_minutes=duration,
                    base_price=Decimal(str(random.randint(200, 1500))),
                    is_popular=True
                )
                routes.append(route)
                
                # Create reverse route
                reverse_route = Route.objects.create(
                    origin=airports[dest_code],
                    destination=airports[origin_code],
                    distance_km=distance,
                    typical_duration_minutes=duration,
                    base_price=Decimal(str(random.randint(200, 1500))),
                    is_popular=True
                )
                routes.append(reverse_route)
        
        self.stdout.write(f'Created {len(routes)} routes')
        return routes

    def create_flights(self, airlines, aircraft, airports, routes):
        """Create sample flights for the next 7 days"""
        flights = []
        flight_counter = 0
        
        # Create flights for the next 7 days
        for days_ahead in range(7):
            flight_date = date.today() + timedelta(days=days_ahead)
            
            for route in routes[:10]:  # Limit to first 10 routes for sample data
                # Create 1-3 flights per route per day
                flights_per_route = random.randint(1, 3)
                
                for flight_num in range(flights_per_route):
                    airline = random.choice(list(airlines.values()))
                    aircraft_type = random.choice(aircraft)
                    
                    # Generate flight number
                    flight_number = f"{random.randint(100, 999)}"
                    
                    # Create departure time
                    base_hour = random.randint(6, 22)
                    departure_time = datetime.combine(flight_date, datetime.min.time()) + timedelta(
                        hours=base_hour,
                        minutes=random.randint(0, 59)
                    )
                    
                    arrival_time = departure_time + timedelta(minutes=route.typical_duration_minutes)
                    
                    # Pricing
                    base_multiplier = Decimal('1.5') if airline.is_low_cost else Decimal('2.0')
                    economy_price = route.base_price * base_multiplier
                    
                    flight = Flight.objects.create(
                        flight_number=flight_number,
                        airline=airline,
                        aircraft=aircraft_type,
                        origin=route.origin,
                        destination=route.destination,
                        route=route,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        duration_minutes=route.typical_duration_minutes,
                        distance_km=route.distance_km,
                        stops=0,
                        economy_price=economy_price,
                        premium_economy_price=economy_price * Decimal('1.5') if aircraft_type.premium_economy_seats > 0 else None,
                        business_price=economy_price * Decimal('3.0') if aircraft_type.business_seats > 0 else None,
                        first_class_price=economy_price * Decimal('5.0') if aircraft_type.first_class_seats > 0 else None,
                        economy_available=random.randint(int(aircraft_type.economy_seats * 0.3), aircraft_type.economy_seats),
                        premium_economy_available=random.randint(0, aircraft_type.premium_economy_seats) if aircraft_type.premium_economy_seats > 0 else 0,
                        business_available=random.randint(0, aircraft_type.business_seats) if aircraft_type.business_seats > 0 else 0,
                        first_class_available=random.randint(0, aircraft_type.first_class_seats) if aircraft_type.first_class_seats > 0 else 0,
                    )
                    
                    flights.append(flight)
                    flight_counter += 1
                    
                    if flight_counter % 10 == 0:
                        self.stdout.write(f'Created {flight_counter} flights...')
        
        self.stdout.write(f'Created {len(flights)} flights')
        return flights

    def create_baggage_allowances(self, airlines):
        """Create baggage allowances for airlines"""
        allowances = []
        fare_types = ['economy', 'premium_economy', 'business', 'first_class']
        
        for airline in airlines.values():
            for fare_type in fare_types:
                if fare_type == 'economy':
                    checked_pieces = 1 if not airline.is_low_cost else 0
                    extra_bag_fee = 50 if airline.is_low_cost else 100
                elif fare_type == 'premium_economy':
                    checked_pieces = 1
                    extra_bag_fee = 75
                elif fare_type == 'business':
                    checked_pieces = 2
                    extra_bag_fee = 0
                else:  # first_class
                    checked_pieces = 2
                    extra_bag_fee = 0
                
                allowance = BaggageAllowance.objects.create(
                    airline=airline,
                    fare_type=fare_type,
                    carryon_pieces=1,
                    carryon_weight_kg=7,
                    carryon_dimensions="56x45x25cm",
                    checked_pieces_included=checked_pieces,
                    checked_weight_kg=23,
                    checked_dimensions="158cm total",
                    extra_bag_fee=Decimal(str(extra_bag_fee)),
                    overweight_fee_per_kg=Decimal('15.0')
                )
                allowances.append(allowance)
        
        self.stdout.write(f'Created {len(allowances)} baggage allowances')
        return allowances